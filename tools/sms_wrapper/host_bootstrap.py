#!/usr/bin/env python3
"""Install/inspect an isolated SMSForge host; no game-quality promotion.

System packages require explicit --install-system. SDK, venv, downloads,
receipts and optional private PulseAudio stay under the selected workspace.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEM_PACKAGES = [
    'ca-certificates', 'git', 'curl', 'build-essential', 'sdcc',
    'python3', 'python3-venv', 'openjdk-17-jdk', 'fonts-dejavu-core', 'xvfb', 'xauth',
    'bubblewrap', 'ffmpeg', 'pulseaudio-utils', 'libasound2-dev',
    'unzip', 'zstd', 'libarchive-tools', 'p7zip-full',
]


class HostError(RuntimeError):
    pass


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def command(args, *, env=None, cwd=None, timeout=600, capture=False):
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                            capture_output=capture, text=True, timeout=timeout)
    if result.returncode:
        detail = (result.stderr or result.stdout or '')[-1500:] if capture else ''
        raise HostError(f'command failed ({result.returncode}): {args[0]} {detail}')
    return result.stdout if capture else ''


def write_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        temp = Path(stream.name)
    temp.replace(path)


def checked_members(archive, *, max_bytes=2 * 1024**3):
    """Accept regular files/directories only, with portable contained paths."""
    total, names, result = 0, set(), []
    for member in archive.getmembers():
        name = member.name
        parts = name.split('/')
        if (not name or name.startswith('/') or '\\' in name or
                '..' in parts or ':' in parts[0] or name in names):
            raise HostError(f'unsafe/duplicate archive path: {name}')
        if not (member.isfile() or member.isdir()):
            raise HostError(f'archive links/devices are not accepted: {name}')
        total += member.size
        if total > max_bytes:
            raise HostError('archive exceeds declared extraction budget')
        names.add(name)
        result.append(member)
    return result


def extract(archive_path, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, 'r:*') as archive:
        members = checked_members(archive)
        # Destination is a new private staging directory, never a working tree.
        for member in members:
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                target.mkdir(exist_ok=True)
            else:
                with archive.extractfile(member) as source, target.open('xb') as out:
                    shutil.copyfileobj(source, out)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)


def download(spec, cache, offline_dir=None):
    name = spec['name']
    if Path(name).name != name or not re.fullmatch(r'[a-f0-9]{64}', spec['sha256']):
        raise HostError('invalid download lock')
    path = Path(cache) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and digest(path) == spec['sha256']:
        return path
    if path.exists():
        raise HostError(f'cached asset hash differs; preserve and inspect: {path}')
    source = Path(offline_dir) / name if offline_dir else None
    temp = path.with_suffix(path.suffix + '.partial')
    try:
        with temp.open('xb') as out:
            if source:
                with source.open('rb') as stream:
                    shutil.copyfileobj(stream, out)
            else:
                if not spec['url'].startswith('https://'):
                    raise HostError('HTTPS download required')
                with urllib.request.urlopen(spec['url'], timeout=60) as stream:
                    shutil.copyfileobj(stream, out)
        if digest(temp) != spec['sha256']:
            raise HostError(f'download digest mismatch: {name}')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return path


def dependency_assets(dependencies, skip_project_restore=False):
    return {name: spec for name, spec in dependencies['assets'].items()
            if not (skip_project_restore and name in ('rev2_runtime', 'rev2_manifest'))}


def environment(root, jobs=2):
    env = os.environ.copy()
    paths = [root / '.venv/bin', root / '.runtime/bin', root / 'sdk/sdcc-portable/bin']
    env['PATH'] = os.pathsep.join(map(str, paths)) + os.pathsep + env.get('PATH', '')
    env['PYTHONPATH'] = str(root / 'tools/sms_wrapper')
    env['SMS_DEVKITSMS'] = str(root / 'sdk/devkitSMS')
    env['PIP_CACHE_DIR'] = str(root / '.runtime/cache/pip')
    env['PYTHONPYCACHEPREFIX'] = str(root / '.runtime/cache/pycache')
    env['MAKEFLAGS'] = f'-j{jobs}'
    env['OMP_NUM_THREADS'] = env['OPENBLAS_NUM_THREADS'] = str(jobs)
    return env


@contextlib.contextmanager
def audio_environment(root, env):
    """Reuse reachable audio, or start only an owned, idle-expiring server."""
    probe = subprocess.run(['pactl', 'info'], env=env, capture_output=True, timeout=10)
    if probe.returncode == 0:
        yield env
        return
    runtime = root / '.runtime/pulse'
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    sock = runtime / 'native'
    private = dict(env, PULSE_SERVER='unix:' + str(sock))
    # Multiple commands share this workspace server. It expires after 60s idle;
    # never send a kill command to the user's default server.
    with (runtime / 'start.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        check = subprocess.run(['pactl', 'info'], env=private, capture_output=True, timeout=10)
        if check.returncode:
            command(['pulseaudio', '--daemonize=yes', '--exit-idle-time=60',
                     '--use-pid-file=no', '-n',
                     '--load=module-native-protocol-unix socket=' + str(sock),
                     '--load=module-null-sink sink_name=smsforge_base'], env=env)
    yield private


def system_install():
    os_release = Path('/etc/os-release').read_text()
    if not re.search(r'(?m)^ID=(?:"?)(ubuntu|debian)(?:"?)$', os_release):
        raise HostError('--install-system currently supports Ubuntu/Debian; use doctor elsewhere')
    prefix = [] if os.geteuid() == 0 else ['sudo']
    packages = list(SYSTEM_PACKAGES)
    # A Desktop may already provide the Pulse protocol through PipeWire.
    # Never install a competing daemon or permit apt to remove desktop packages.
    if not shutil.which('pipewire-pulse'):
        pulse = subprocess.run(['pactl', 'info'], capture_output=True, timeout=10) if shutil.which('pactl') else None
        if pulse is None or pulse.returncode:
            packages.append('pulseaudio')
    command(prefix + ['apt-get', 'update'])
    command(prefix + ['apt-get', 'install', '-y', '--no-remove', '--no-install-recommends'] + packages)


def python_ready(python, requirements, env):
    expected = dict(line.split('==', 1) for line in requirements.read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
    script = ('import importlib.metadata as m,json,sys; expected=json.loads(sys.argv[1]); '
              'sys.exit(0 if all(m.version(k)==v for k,v in expected.items()) else 1)')
    result = subprocess.run([str(python), '-c', script, json.dumps(expected)], env=env,
                            capture_output=True, timeout=30)
    if result.returncode:
        return False
    return subprocess.run([str(python), '-m', 'pip', 'check'], env=env,
                          capture_output=True, timeout=30).returncode == 0


def sdk_install(root, source_archive, env):
    canon = root / 'sdk/devkitSMS'
    receipt = root / '.runtime/sdk_receipt.json'
    sdcc = shutil.which('sdcc', path=env['PATH'])
    if not sdcc:
        raise HostError('SDCC absent; use --install-system or install SDCC >=4.2')
    version = command([sdcc, '--version'], env=env, capture=True).splitlines()[0]
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', version)
    if not match or tuple(map(int, match.groups())) < (4, 2, 0):
        raise HostError('SDCC >=4.2 required')
    signature = {'source_sha256': digest(source_archive), 'compiler_sha256': digest(sdcc)}
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old.get('signature') == signature and all(
                (root / name).is_file() and digest(root / name) == sha
                for name, sha in old.get('files', {}).items()) and old.get('files'):
            return old
    if canon.exists() and not receipt.exists():
        raise HostError('unmanaged sdk/devkitSMS exists; preserve it and use a clean clone')
    with tempfile.TemporaryDirectory(prefix='sdk-', dir=root / '.runtime') as temp:
        temp = Path(temp)
        extract(source_archive, temp)
        source = temp / 'devkitSMS-source'
        for library in ['SMSlib', 'PSGlib']:
            # Compile the required target from a fresh source extraction.
            # Do not reuse objects built by the compiler of a different host.
            command(['make', library + '.lib'], cwd=source / library / 'src', env=env)
        staged = temp / 'canonical'
        for folder in ['SMSlib', 'PSGlib', 'crt0', 'tools']:
            (staged / folder).mkdir(parents=True)
        for library in ['SMSlib', 'PSGlib']:
            for suffix in ['h', 'lib']:
                shutil.copy2(source / library / 'src' / f'{library}.{suffix}', staged / library)
        shutil.copy2(source / 'crt0/crt0_sms.rel', staged / 'crt0')
        if (source / 'peep-rules.txt').is_file():
            shutil.copy2(source / 'peep-rules.txt', staged)
        command(['cc', '-O2', '-o', staged / 'tools/makesms', source / 'makesms/src/makesms.c'], env=env)
        # Do not publish until the compiler/linker/makesms chain actually works.
        smoke = temp / 'smoke'
        smoke.mkdir()
        (smoke / 'main.c').write_text('#include "SMSlib.h"\n#include "PSGlib.h"\nSMS_EMBED_SEGA_ROM_HEADER_16KB(9999,0);\nvoid main(void){SMS_init();PSGStop();for(;;){SMS_waitForVBlank();PSGFrame();}}\n')
        command([sdcc, '-c', '-mz80', '-I' + str(staged / 'SMSlib'),
                 '-I' + str(staged / 'PSGlib'), 'main.c'], cwd=smoke, env=env)
        command([sdcc, '-o', 'smoke.ihx', '-mz80', '--no-std-crt0', '--data-loc', '0xC000',
                 staged / 'crt0/crt0_sms.rel', 'main.rel', staged / 'SMSlib/SMSlib.lib', staged / 'PSGlib/PSGlib.lib'], cwd=smoke, env=env)
        command([staged / 'tools/makesms', 'smoke.ihx', 'smoke.sms'], cwd=smoke, env=env)
        size = (smoke / 'smoke.sms').stat().st_size
        if not size or size % 16384:
            raise HostError('invalid smoke ROM size')
        if (smoke / 'smoke.sms').read_bytes()[0x3ff0:0x3ff8] != b'TMR SEGA':
            raise HostError('smoke ROM has no SEGA header at its declared location')
        old_path = canon.with_name('devkitSMS.previous')
        if old_path.exists():
            raise HostError('SDK previous backup exists; inspect before updating')
        canon.parent.mkdir(parents=True, exist_ok=True)
        if canon.exists():
            canon.rename(old_path)
        try:
            shutil.copytree(staged, canon)
        except Exception:
            if canon.exists():
                shutil.rmtree(canon)
            if old_path.exists():
                old_path.rename(canon)
            raise
        files = {str(p.relative_to(root)): digest(p) for p in canon.rglob('*') if p.is_file()}
        record = {'signature': signature, 'sdcc_version': version, 'files': files,
                  'smoke_rom_bytes': size, 'claim_ceiling': 'build_toolchain_only'}
        write_json(receipt, record)
        return record


def install(args):
    root = args.root.resolve()
    (root / '.runtime').mkdir(parents=True, exist_ok=True)
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise HostError('qualified installer target: Linux x86_64 (Ubuntu 24.04 or WSL2 Ubuntu)')
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise HostError('at least 2 GiB free needed before installation')
    with (root / '.runtime/bootstrap.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.install_system:
            system_install()
        env = environment(root, args.jobs)
        for tool in ['git', 'cc', 'make', 'sdcc', 'java', 'bwrap', 'Xvfb', 'ffmpeg', 'pactl']:
            if not shutil.which(tool, path=env['PATH']):
                raise HostError(f'missing {tool}; run bootstrap_host.sh --install-system')
        dependencies = json.loads((HERE / 'host_dependencies.lock.json').read_text())
        cache = root / '.runtime/downloads'
        assets = {name: download(spec, cache, args.offline_dir)
                  for name, spec in dependency_assets(dependencies, args.skip_project_restore).items()}
        if not args.skip_project_restore:
            from recovery_bundle import restore
            restore_receipt = root / '.runtime/project_restore.json'
            snapshot = json.loads(assets['rev2_manifest'].read_text())
            if not restore_receipt.exists():
                count = restore(assets['rev2_runtime'], snapshot, root)
                write_json(restore_receipt, {'archive_sha256': snapshot['archive_sha256'],
                                            'files_restored': count,
                                            'note': 'Initial restore only; later edits are never replaced by bootstrap.'})
            elif json.loads(restore_receipt.read_text())['archive_sha256'] != snapshot['archive_sha256']:
                raise HostError('another project snapshot is installed; restore in a separate clone')
        venv = root / '.venv'
        requirements = HERE / 'host_requirements.txt'
        if not (venv / 'bin/python').is_file():
            command([sys.executable, '-m', 'venv', venv], env=env)
        pip_marker = root / '.runtime/python_requirements.sha256'
        if (not pip_marker.exists() or pip_marker.read_text().strip() != digest(requirements)
                or not python_ready(venv / 'bin/python', requirements, env)):
            command([venv / 'bin/python', '-m', 'pip', 'install', '--disable-pip-version-check',
                     '-r', requirements], env=env)
            pip_marker.write_text(digest(requirements) + '\n')
        sdk = sdk_install(root, assets['devkitsms_source'], env)
        # Two content-addressed, immutable files; never import personal ini/SRAM.
        emulator = root / 'tools/emuladores/emulicious'
        emulator.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root / '.runtime') as temp:
            extract(assets['emulicious'], temp)
            for name in ['Emulicious.jar', 'License.txt']:
                source = Path(temp) / name
                target = emulator / name
                if target.exists() and digest(target) != digest(source):
                    raise HostError(f'preserve different emulator before installing: {target}')
                if not target.exists():
                    shutil.copy2(source, target)
        if not shutil.which('rtk', path=env['PATH']):
            with tempfile.TemporaryDirectory(dir=root / '.runtime') as temp:
                extract(assets['rtk'], temp)
                candidates = [p for p in Path(temp).rglob('rtk') if p.is_file()]
                if len(candidates) != 1:
                    raise HostError('RTK archive must contain exactly one rtk binary')
                (root / '.runtime/bin').mkdir(exist_ok=True)
                shutil.copy2(candidates[0], root / '.runtime/bin/rtk')
                (root / '.runtime/bin/rtk').chmod(0o755)
        command(['rtk', '--version'], env=env)
        record = {'schema': 'smsforge.host_install/v1', 'root': str(root),
                  'platform': platform.platform(), 'sdk': sdk, 'assets': {
                      key: digest(path) for key, path in assets.items()},
                  'python': command([venv / 'bin/python', '--version'], capture=True, env=env).strip(),
                  'jobs': args.jobs, 'installed_at': time.time(),
                  'claim_ceiling': 'host_dependencies_and_compile_smoke_only'}
        write_json(root / '.runtime/install_receipt.json', record)
        print('[OK] dependencies + real compile/link/ROM smoke; no emulator/FPS claim')
        print('Next: tools/sms_wrapper/run_host.sh python tools/sms_wrapper/host_bootstrap.py doctor')


def doctor(root):
    env = environment(root)
    checks = {tool: shutil.which(tool, path=env['PATH']) for tool in
              ['git', 'cc', 'make', 'sdcc', 'java', 'javac', 'bwrap', 'Xvfb', 'ffmpeg', 'ffprobe', 'pactl', 'rtk']}
    probe = subprocess.run(['bwrap', '--unshare-user', '--ro-bind', '/', '/', 'true'],
                           capture_output=True, text=True, env=env, timeout=15) if checks['bwrap'] else None
    pulse = subprocess.run(['pactl', 'info'], env=env, capture_output=True, timeout=10) if checks['pactl'] else None
    audio_ready = bool(pulse is not None and pulse.returncode == 0) or bool(shutil.which('pulseaudio', path=env['PATH']))
    record = {'schema': 'smsforge.host_doctor/v1', 'tools': checks, 'audio_server_or_private_daemon': audio_ready,
              'disk_free_bytes': shutil.disk_usage(root).free,
              'loadavg': os.getloadavg(), 'user_namespace': probe is not None and probe.returncode == 0,
              'namespace_error': (probe.stderr[-1500:] if probe and probe.returncode else None),
              'claim_ceiling': 'environment_only_not_game_quality'}
    write_json(root / '.runtime/doctor.json', record)
    print(json.dumps(record, indent=2))
    return 0 if all(checks.values()) and record['user_namespace'] and audio_ready else 2


def main(argv=None):
    if argv == ['--self-check'] or (argv is None and sys.argv[1:] == ['--self-check']):
        return self_check()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=ROOT)
    sub = parser.add_subparsers(dest='operation', required=True)
    setup = sub.add_parser('install')
    setup.add_argument('--install-system', action='store_true')
    setup.add_argument('--offline-dir', type=Path)
    setup.add_argument('--skip-project-restore', action='store_true', help='host dependencies only; preserve active project')
    setup.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
    sub.add_parser('doctor')
    run = sub.add_parser('run')
    run.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.operation == 'install':
            install(args)
            return 0
        if args.operation == 'doctor':
            return doctor(args.root.resolve())
        cmd = args.args[1:] if args.args[:1] == ['--'] else args.args
        if not cmd:
            raise HostError('run requires a command')
        env = environment(args.root.resolve())
        with audio_environment(args.root.resolve(), env) as env:
            return subprocess.call(cmd, cwd=args.root, env=env)
    except (HostError, OSError, subprocess.TimeoutExpired) as error:
        print('[FAIL_AMBIENTE]', error, file=sys.stderr)
        return 2


def self_check():
    import io
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name, kind in [('ok/file', 'file'), ('../escape', 'file'),
                           ('/absolute', 'file'), ('link', 'link')]:
            archive = root / ('a' + str(len(name)) + kind + '.tar')
            with tarfile.open(archive, 'w') as tar:
                info = tarfile.TarInfo(name)
                if kind == 'link':
                    info.type = tarfile.SYMTYPE
                    info.linkname = '/tmp/other'
                    tar.addfile(info)
                else:
                    info.size = 4
                    tar.addfile(info, io.BytesIO(b'data'))
            with tarfile.open(archive) as tar:
                try:
                    valid = bool(checked_members(tar))
                except HostError:
                    valid = False
            assert valid == (name == 'ok/file')
        source = root / 'asset.tar'
        source.write_bytes(b'asset')
        spec = {'name': source.name, 'url': 'https://unused.invalid', 'sha256': digest(source)}
        target = download(spec, root / 'cache', root)
        assert target.read_bytes() == b'asset'
        assert download(spec, root / 'cache', root) == target
        target.write_bytes(b'changed')
        try:
            download(spec, root / 'cache', root)
        except HostError:
            pass
        else:
            raise AssertionError('tampered cache accepted')
        assert target.read_bytes() == b'changed'
        env = environment(root, 2)
        assert env['MAKEFLAGS'] == '-j2' and env['OPENBLAS_NUM_THREADS'] == '2'
        assert str(root / '.venv/bin') in env['PATH']
        requirements = root / 'requirements.txt'
        requirements.write_text('missing_smsforge_fixture_package==1.0\n')
        # A matching marker cannot authenticate a recreated/empty environment.
        (root / 'python_requirements.sha256').write_text(digest(requirements))
        assert not python_ready(sys.executable, requirements, env)
        requirements.write_text('pip==0.0.0\n')
        assert not python_ready(sys.executable, requirements, env)
        available = {'assets': {name: {'url': 'https://unreachable.invalid'} for name in
                               ['devkitsms_source', 'emulicious', 'rtk', 'rev2_runtime', 'rev2_manifest']}}
        assert set(dependency_assets(available, True)) == {'devkitsms_source', 'emulicious', 'rtk'}
        assert len(dependency_assets(available, False)) == 5
    print('[SELF-CHECK OK] host bootstrap: contained archives, hashes, cache preservation, bounded jobs')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
