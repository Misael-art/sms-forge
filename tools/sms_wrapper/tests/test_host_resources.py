"""Host diagnostics and build discovery, independent of the Linux emulator."""
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import host_resources as resources
import build_inner
import host_bootstrap


class BuildHostTests(unittest.TestCase):
    def test_incomplete_portable_archive_never_publishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.runtime/windows').mkdir(parents=True)
            seven = root / '7z.exe'
            seven.touch()
            def lookup(name, **kwargs):
                return str(seven) if name == '7z.exe' else None
            with patch.object(host_bootstrap.shutil, 'which', side_effect=lookup), \
                    patch.object(host_bootstrap.platform, 'machine', return_value='AMD64'), \
                    patch.object(host_bootstrap, 'download', return_value=root / 'pinned.exe'), \
                    patch.object(host_bootstrap, 'command'):
                with self.assertRaisesRegex(host_bootstrap.HostError, 'incomplete'):
                    host_bootstrap.prepare_windows_compiler(root, {'PATH': ''}, {}, None)
                target = root / 'sdk/sdcc-portable'
                self.assertFalse(target.exists())
                target.mkdir(parents=True)
                with self.assertRaisesRegex(host_bootstrap.HostError, 'preserve existing'):
                    host_bootstrap.prepare_windows_compiler(root, {'PATH': ''}, {}, None)

    def test_sdk_publication_requires_smoke_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.runtime').mkdir()
            source = root / 'devkitSMS-source'
            for lib in ('SMSlib', 'PSGlib'):
                folder = source / lib / 'src'
                folder.mkdir(parents=True)
                (folder / (lib + '.h')).touch()
            (source / 'crt0').mkdir()
            (source / 'crt0/crt0_sms.rel').touch()
            archive = root / 'sdk.tar'
            with tarfile.open(archive, 'w') as tar:
                tar.add(source, arcname=source.name)
            env = host_bootstrap.environment(root)
            compiler = root / 'compiler'
            compiler.touch()
            header = b'INVALID!'

            def tool(args, **kwargs):
                if '--version' in args:
                    return 'SDCC 4.5.0'
                if args[-1] in ('SMSlib.lib', 'PSGlib.lib'):
                    (kwargs['cwd'] / args[-1]).touch()
                elif args[-1] == 'smoke.sms':
                    (kwargs['cwd'] / 'smoke.sms').write_bytes(bytes(0x3ff0) + header + bytes(8))
                elif '-O2' in args:
                    Path(args[args.index('-o') + 1]).touch()
                return ''

            kit = Path(env['SMS_DEVKITSMS'])
            with patch.object(host_bootstrap.shutil, 'which', return_value=str(compiler)), \
                    patch.object(host_bootstrap, 'command', side_effect=tool):
                with self.assertRaisesRegex(host_bootstrap.HostError, 'SEGA header'):
                    host_bootstrap.sdk_install(root, archive, env)
                self.assertFalse(kit.exists())
                header = b'TMR SEGA'
                receipt = host_bootstrap.sdk_install(root, archive, env)
                self.assertEqual(receipt['smoke_rom_bytes'], 16384)
                self.assertEqual(host_bootstrap.sdk_install(root, archive, env), receipt)
                self.assertTrue((kit / 'SMSlib/SMSlib.lib').is_file())

    def test_sdcc_below_at_above_minimum_and_unparseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suffix = ".exe" if os.name == "nt" else ""
            sdcc = root / "sdcc-portable/bin" / ("sdcc" + suffix)
            sdcc.parent.mkdir(parents=True)
            sdcc.touch()
            kit = root / "devkitSMS"
            for sub, names in (("SMSlib", ("SMSlib.h", "SMSlib.lib")),
                               ("PSGlib", ("PSGlib.h", "PSGlib.lib")),
                               ("crt0", ("crt0_sms.rel",)), ("tools", ("makesms" + suffix,))):
                (kit / sub).mkdir(parents=True)
                for name in names:
                    (kit / sub / name).touch()
            with patch.dict(os.environ, {"SMS_DEVKITSMS": str(kit)}), patch("shutil.which", return_value=None):
                for version, expected in (("3.9.0", False), ("4.0.0", False), ("4.1.99", False),
                                          ("4.2.0", True), ("4.6.0", True), ("5.0.0", True), ("unknown", False)):
                    result = subprocess.CompletedProcess([], 0, stdout="SDCC " + version)
                    with patch.object(build_inner.subprocess, "run", return_value=result):
                        tc, _ = build_inner.find_toolchain(root)
                    self.assertEqual(tc is not None, expected, version)
                result = subprocess.CompletedProcess([], 1, stdout="SDCC 5.0.0")
                with patch.object(build_inner.subprocess, "run", return_value=result):
                    self.assertIsNone(build_inner.find_toolchain(root)[0])

    def test_wsl_forwards_exact_args_and_exit_status(self):
        with patch.object(host_bootstrap.platform, 'system', return_value='Windows'), \
                patch.object(host_bootstrap.subprocess, 'call', return_value=7) as call:
            code = host_bootstrap.main(['run', '--wsl-root', '/space here', '--wsl-distro',
                                        'Demo', '--', 'rtk', 'a b', '$HOME'])
            self.assertEqual(code, 7)
            call.assert_called_once_with(['wsl.exe', '--distribution', 'Demo', '--cd', '/space here',
                                          '--exec', '/bin/bash', 'tools/sms_wrapper/run_host.sh',
                                          'rtk', 'a b', '$HOME'])


class LinuxResourcesTest(unittest.TestCase):
    def test_live_delta_and_optional_sensors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'stat').write_text('cpu 20 0 0 80 0 0 0 0 0 0\n')
            (root / 'vmstat').write_text('pswpin 20\npswpout 11\n')
            (root / 'meminfo').write_text('MemTotal: 6000 kB\nMemAvailable: 2000 kB\n')
            (root / 'pressure').mkdir()
            (root / 'pressure/io').write_text('some avg10=0.25 avg60=1.01 total=123\n')
            chip = root / 'hwmon/hwmon0'
            chip.mkdir(parents=True)
            (chip / 'name').write_text('k10temp')
            (chip / 'temp1_input').write_text('55625')
            (chip / 'temp1_crit').write_text('102000')

            def advance(_):
                (root / 'stat').write_text('cpu 28 0 0 92 0 0 0 0 0 0\n')
                (root / 'vmstat').write_text('pswpin 23\npswpout 11\n')

            with patch.object(resources.time, 'sleep', side_effect=advance), \
                    patch.object(resources.time, 'monotonic', side_effect=[0, 2]), \
                    patch.object(resources.os, 'getloadavg', return_value=(1, 1, 1), create=True):
                sample = resources.linux_sample(False, root, root)
            self.assertAlmostEqual(sample['cpu_percent'], 40)
            self.assertEqual(sample['swap_pages_per_sec'], {'pswpin': 1.5, 'pswpout': 0})
            self.assertEqual(sample['available_bytes'], 2000 * 1024)
            self.assertEqual(sample['psi_avg10_percent']['io']['some'], 0.25)
            self.assertIsNone(sample['psi_avg10_percent']['memory'])
            self.assertEqual(sample['thermal_zones'][0]['current_c'], 55.625)
            self.assertIsNone(sample['thermal_zones'][0]['passive_trip_c'])
            self.assertNotIn('processes', sample)
