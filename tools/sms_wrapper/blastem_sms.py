#!/usr/bin/env python3
"""Bounded, private BlastEm SMS diagnostics; no desktop input or delivery claims.

Uses the upstream native Z80 debugger, not the SGDK SDL presentation counter.
Install is explicit and workspace local. Each run owns a new Xvfb and sandbox.
SMSFORGE_BLASTEM_RUNTIME optionally selects the host's explicit runtime path;
the default remains compatible with existing qualified installations.
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import pty
import re
import select
import shutil
import signal
import subprocess
import tarfile
import termios
import tempfile
import time
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]

def runtime_path(override):
    return Path(override or WORKSPACE / 'out/host_tools/blastem/1.0.0').expanduser().resolve()

RUNTIME = runtime_path(os.environ.get('SMSFORGE_BLASTEM_RUNTIME'))
URL = 'https://www.retrodev.com/blastem/blastem64-1.0.0.tar.gz'
ARCHIVE_SHA = '9e47b68a555e24db5ef5bd77e67967124ac3e28ae04ae32e9f3af3eaecf31860'
BINARY_SHA = '1bd0f40ddcc6d769f6cc2aea59bb2973601b6db30bdd849b68315b9d83ad06ec'
BUTTONS = ('up', 'down', 'left', 'right', '1', '2')
# BlastEm shares MD names: SMS 1/2 are MD B/C (bits 4/5), not A/B.
BINDINGS = ('up', 'down', 'left', 'right', 'b', 'c')
LOADED_SOURCE = Path(__file__).read_bytes()
LOADED_SHA = hashlib.sha256(LOADED_SOURCE).hexdigest()
DUMP_SIZES = {'ram': 8192, 'vram': 16384, 'cram_internal': 64,
              'vdp_regs': 11, 'psg_frequency': 8, 'psg_volume': 4}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')

def install():
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise ValueError('pinned runtime supports Linux x86_64 only')
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNTIME.parent / 'install.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (RUNTIME / 'installation.json').exists():
            return runtime()
        with tempfile.TemporaryDirectory(dir=RUNTIME.parent) as tmp:
            tmp = Path(tmp)
            archive = tmp / 'release.tar.gz'
            with urllib.request.urlopen(URL, timeout=30) as src, archive.open('wb') as out:
                shutil.copyfileobj(src, out)
            if sha(archive) != ARCHIVE_SHA:
                raise ValueError('upstream archive hash mismatch; do not update the pin implicitly')
            with tarfile.open(archive) as tar:
                tar.extractall(tmp / 'release', filter='data')
            release = tmp / 'release/blastem64-1.0.0'
            # Retain licenses, shaders and data, not just an executable.
            if RUNTIME.exists():
                raise ValueError('partial installation exists; inspect it before retrying')
            shutil.copytree(release, RUNTIME)
            write_json(RUNTIME / 'installation.json', {
                'version': '1.0.0', 'url': URL, 'archive_sha256': ARCHIVE_SHA,
                'files': {str(p.relative_to(RUNTIME)): sha(p) for p in RUNTIME.rglob('*') if p.is_file()},
            })
    return runtime()

def runtime():
    record = json.loads((RUNTIME / 'installation.json').read_text())
    if record.get('archive_sha256') != ARCHIVE_SHA or record.get('version') != '1.0.0':
        raise ValueError('installation pin mismatch')
    if not record.get('files') or 'blastem' not in record['files']:
        raise ValueError('incomplete installation binding')
    for name, expected in record['files'].items():
        p = RUNTIME / name
        if p.resolve().parent != RUNTIME and RUNTIME not in p.resolve().parents:
            raise ValueError('invalid installation path')
        if sha(p) != expected:
            raise ValueError('runtime file changed: ' + name)
    if sha(RUNTIME / 'blastem') != BINARY_SHA:
        raise ValueError('binary differs from the pinned official release')
    return RUNTIME / 'blastem'

def validate_script(doc):
    if not isinstance(doc, dict) or doc.get('schema') != 'sms_blastem_sequence_v1':
        raise ValueError('expected sms_blastem_sequence_v1')
    if set(doc) - {'schema', 'model', 'region', 'warmup_frames', 'steps', 'preconditions', 'diagnostics'}:
        raise ValueError('unknown sequence fields')
    from blastem_diagnostics import validate_features
    validate_features(doc)
    if doc.get('region', 'ntsc') != 'ntsc':
        raise ValueError('PAL is not qualified in this backend; use Emulicious')
    if doc.get('model', 'sms2') not in ('sms1', 'sms2'):
        raise ValueError('SMS model must be sms1 or sms2, not Genesis PBC')
    def integer(v, lo, hi):
        if type(v) is not int or not lo <= v <= hi:
            raise ValueError('integer outside diagnostic bounds')
    integer(doc.get('warmup_frames', 120), 1, 600)
    steps = doc.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
        raise ValueError('1..100 steps required')
    total = doc.get('warmup_frames', 120)
    for step in steps:
        if not isinstance(step, dict) or set(step) - {'frames', 'p1', 'p2', 'pause'}:
            raise ValueError('invalid step fields; raw debugger commands are not accepted')
        integer(step.get('frames'), 1, 600)
        total += step['frames']
        for player in ('p1', 'p2'):
            integer(step.get(player, 0), 0, 63)
        if type(step.get('pause', False)) is not bool:
            raise ValueError('pause must be boolean')
    if total > 3600:
        raise ValueError('run limited to 3600 VDP frames')
    conditions = doc.get('preconditions', [])
    if not isinstance(conditions, list) or len(conditions) > 32:
        raise ValueError('preconditions must be a list of at most 32 predicates')
    for probe in conditions:
        if not isinstance(probe, dict) or set(probe) != {'address', 'equals_hex'}:
            raise ValueError('invalid ROM precondition')
        integer(probe['address'], 0xC000, 0xDFFF)
        if not isinstance(probe['equals_hex'], str):
            raise ValueError('precondition equals_hex must be a string')
        payload = bytes.fromhex(probe['equals_hex'])
        if not payload or probe['address'] + len(payload) > 0xE000:
            raise ValueError('precondition outside SMS RAM')
    return doc

def configuration(root, model):
    # Upstream 1.0.0 paths.c uses HOME/.config, not XDG_CONFIG_HOME.
    # No config migration, host mappings or MD default model are inherited.
    return f'''version 13
bindings {{
 keys {{
 }}
 pads {{
 }}
 mice {{
 }}
}}
video {{
 gl on
 width 256
 height 192
 aspect stretch
 scaling nearest
 scanlines off
 fullscreen off
 ntsc {{
  overscan {{
   top 27
   bottom 24
   left 13
   right 14
  }}
 }}
}}
audio {{
 rate 48000
 buffer 512
}}
ui {{
 screenshot_path {root}/screenshots
 screenshot_template frame_%Y%m%d_%H%M%S.png
 video_path {root}/media
 video_template native.apng
 audio_path {root}/media
 audio_template native.wav
 vgm_path {root}/media
 vgm_template native.vgm
 save_path {root}/saves
 remember_path off
 state_format native
}}
system {{
 sync_source audio
 ram_init zero
}}
sms {{
 system {{
  model {model}
 }}
 io {{
  devices {{
   1 gamepad2.1
   2 gamepad2.2
  }}
 }}
}}
'''

def terminate_group(p):
    if p is None:
        return
    # Popen-created private process group; never search/kill by emulator name.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=3)
    # Bubblewrap can exit before its descendant; group cleanup still applies.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(p.pid, signal.SIGKILL)

def check_dumps(root, index):
    for name, size in DUMP_SIZES.items():
        if (root / f'snapshots/{index:03d}/{name}.bin').stat().st_size != size:
            raise RuntimeError('incomplete debugger dump: ' + name)

def cleanup_owned(processes, fds):
    errors = []
    for owned in processes:
        try:
            terminate_group(owned)
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(str(exc))
    for fd in fds:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
    return errors

def run(rom, doc, output, timeout=90):
    if sha(__file__) != LOADED_SHA:
        raise ValueError('wrapper changed since module import; restart the worker')
    doc = validate_script(doc)
    import blastem_diagnostics as diagnostics
    feature_source = Path(diagnostics.__file__)
    feature_sha = diagnostics.LOADED_SHA
    if sha(feature_source)!=feature_sha:
        raise ValueError('diagnostics changed since import; restart the worker')
    if type(timeout) is not int or not 5 <= timeout <= 180:
        raise ValueError('timeout must be 5..180 seconds')
    rom = Path(rom).resolve(strict=True)
    if rom.suffix.lower() != '.sms':
        raise ValueError('existing .sms ROM required')
    binary = runtime()
    xvfb = shutil.which('Xvfb') or str(WORKSPACE / 'out/session_bridge/runtime/xvfb/usr/bin/Xvfb')
    if not Path(xvfb).is_file() or not shutil.which('bwrap'):
        raise ValueError('Xvfb and bwrap required; no desktop fallback')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sid = 'blastem-sms-' + uuid.uuid4().hex
    root = output / sid
    root.mkdir(mode=0o700)
    if any(c in str(root) for c in ('"', '\n', '\r')):
        raise ValueError('path cannot be encoded in debugger strings')
    for folder in ('.config/blastem', 'screenshots', 'saves', 'snapshots', 'media'):
        (root / folder).mkdir(parents=True)
    shutil.copy2(rom, root / 'rom.sms')
    config = root / '.config/blastem/blastem.cfg'
    config.write_text(configuration(root, doc.get('model', 'sms2')))
    write_json(root / 'sequence.json', doc)
    (root / 'adapter_source.py').write_bytes(LOADED_SOURCE)
    (root / 'diagnostics_source.py').write_bytes(diagnostics.LOADED_SOURCE)
    features = diagnostics.validate_features(doc)
    instrument_commands, definitions = diagnostics.instrumentation(features, (root / 'rom.sms').read_bytes())
    from session_bridge.isolated import auth_file, process_record, alive
    auth_file(root / 'Xauthority')
    meta = {'schema': 'sms_blastem_session_v1', 'session_id': sid, 'root': str(root),
            'emulator': 'BlastEm', 'version': '1.0.0', 'machine': 'sms',
            'model': doc.get('model', 'sms2'), 'region': 'ntsc', 'source_rom': str(rom),
            'rom_sha256': sha(root / 'rom.sms'), 'emulator_sha256': sha(binary),
            'archive_sha256': ARCHIVE_SHA, 'wrapper_sha256': LOADED_SHA,
            'config_sha256': sha(config), 'sequence_sha256': sha(root / 'sequence.json'),
            'started_at': time.time(), 'host_load': os.getloadavg(), 'state': 'created',
            'claim_scope': 'diagnostic_states_only', 'audio': 'dummy_not_tested',
            'input': 'native_debugger_process_local_bindings', 'frame_clock': 'VDP_debugger',
            'fps_claim': False, 'hardware_validation': False}
    meta.update(diagnostics_sha256=feature_sha, event_definitions=definitions)
    x = p = None
    master = slave = None
    readfd = writefd = None
    try:
        readfd, writefd = os.pipe()
        with open(root / 'xvfb.log', 'w') as log:
            x = subprocess.Popen([xvfb, '-displayfd', str(writefd), '-screen', '0', '800x600x24',
                                  '-nolisten', 'tcp', '-auth', str(root / 'Xauthority'), '-noreset'],
                                 pass_fds=(writefd,), stdout=log, stderr=log, start_new_session=True)
        os.close(writefd); writefd = None
        data = b''; deadline = time.monotonic() + 10
        while b'\n' not in data:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([readfd], [], [], remaining)[0]:
                raise RuntimeError('private Xvfb readiness timeout')
            part = os.read(readfd, 64)
            if not part:
                raise RuntimeError('Xvfb readiness pipe closed')
            data += part
        number = data.decode().strip()
        if not number.isdigit():
            raise RuntimeError('invalid display allocation')
        os.close(readfd); readfd = None
        meta.update(display=':' + number, xvfb_process=process_record(x.pid))
        env = {k: v for k, v in os.environ.items() if not k.startswith(('SDL_', 'LD_')) and k not in {
            'DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'DBUS_SESSION_BUS_ADDRESS',
            'PULSE_SERVER', 'PULSE_SINK', 'XDG_RUNTIME_DIR'}}
        env.update(DISPLAY=':' + number, XAUTHORITY=str(root / 'Xauthority'), HOME=str(root),
                   XDG_CONFIG_HOME=str(root / '.config'), XDG_DATA_HOME=str(root / 'data'),
                   XDG_CACHE_HOME=str(root / 'cache'), SDL_AUDIODRIVER='dummy',
                   SDL_VIDEODRIVER='x11', SDL_RENDER_DRIVER='software', SDL_JOYSTICK_HIDAPI='0')
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
        command = ['bwrap', '--die-with-parent', '--unshare-net', '--ro-bind', '/', '/',
                   '--dev', '/dev', '--proc', '/proc', '--tmpfs', '/tmp', '--dir', '/tmp/.X11-unix',
                   '--ro-bind', f'/tmp/.X11-unix/X{number}', f'/tmp/.X11-unix/X{number}',
                   '--bind', str(root), str(root), '--chdir', str(root),
                   str(binary), '-d', '-m', 'sms', '-r', 'U', 'rom.sms']
        meta['sandbox_command'] = command
        script = ['help', f'frames {doc.get("warmup_frames", 120)}']
        def snapshot(i):
            folder = root / 'snapshots' / f'{i:03d}'
            folder.mkdir()
            script.append(f'printf "SMSFORGE_BOUNDARY {i} %d\\n" frame')
            script.append(f'printf "SMSFORGE_CPU {i} %d %d %d %d %d %d %d %d %d %d\\n" pc sp af bc de hl ix iy cycle iff1')
            for name, expr, size, count in [('ram', '[0xc000]', 'b', 8192),
                    ('vram', 'vdp:vram', 'b', 16384), ('cram_internal', 'vdp:cram', 'w', 32),
                    ('vdp_regs', 'vdp:reg', 'b', 11), ('psg_frequency', 'psg:frequency', 'w', 4),
                    ('psg_volume', 'psg:volume', 'b', 4)]:
                script.append(f'save/{size} "{folder}/{name}.bin" {expr} {count}')
        snapshot(0)
        baseline_end = len(script)
        script.extend(instrument_commands)
        if features.get('record_av'):
            script.append('bindup "ui.record_video"')
        if features.get('vgm'):
            script.append('bindup "ui.vgm_log"')
        previous = [0, 0]
        for i, step in enumerate(doc['steps'], 1):
            for player, key in enumerate(('p1', 'p2')):
                mask = step.get(key, 0)
                for bit, binding in enumerate(BINDINGS):
                    if bool(previous[player] & (1 << bit)) != bool(mask & (1 << bit)):
                        # Help usage has a typo; the command name is binddown.
                        op = 'binddown' if mask & (1 << bit) else 'bindup'
                        script.append(f'{op} "gamepads.{player + 1}.{binding}"')
                previous[player] = mask
            if step.get('pause'):
                script.append('bindup "ui.sms_pause"')
            script.append(f'frames {step["frames"]}')
            snapshot(i)
        # Snapshot clock ends before the extra screenshot frame. Record this distinction.
        for player in (1, 2):
            for binding in BINDINGS:
                script.append(f'bindup "gamepads.{player}.{binding}"')
        for i in range(len(definitions)):
            script.append(f'printf "SMSFORGE_HITS {i} %d\\n" sms_hits_{i}')
            script.append(f'delete {i}')
        if features.get('record_av'):
            script.append('bindup "ui.record_video"')
        if features.get('vgm'):
            script.append('bindup "ui.vgm_log"')
        script += ['vdpsprites', 'vr', 'bindup "ui.screenshot"', 'frames 1', 'quit']
        (root / 'debugger_commands.txt').write_text('\n'.join(script) + '\n')
        with open(root / 'debugger.log', 'wb') as log:
            # A PTY prevents upstream init_terminal from launching a desktop
            # terminal and preserves line readiness in fgets_timeout/select.
            master, slave = pty.openpty()
            attrs = termios.tcgetattr(slave)
            attrs[3] &= ~termios.ECHO
            termios.tcsetattr(slave, termios.TCSANOW, attrs)
            p = subprocess.Popen(command, env=env, stdin=slave, stdout=slave, stderr=slave,
                                 start_new_session=True)
            os.close(slave); slave = None
            meta['sandbox_process'] = process_record(p.pid)
            write_json(root / 'session.json', meta)
            end = time.monotonic() + timeout
            for seq, line in enumerate(script):
                if len(line.encode()) > 900:
                    raise ValueError('debugger line exceeds upstream input buffer')
                if line == 'quit':
                    os.write(master, b'quit\n')
                    p.wait(timeout=max(0.1, end - time.monotonic()))
                    break
                marker = f'SMSFORGE_ACK_{sid}_{seq}'
                os.write(master, (line + '\nprintf "' + marker + '\\n"\n').encode())
                response = b''
                while (marker + '\r\n').encode() not in response and (marker + '\n').encode() not in response:
                    remaining = end - time.monotonic()
                    if remaining <= 0 or not select.select([master], [], [], remaining)[0]:
                        raise RuntimeError('native debugger timeout; no desktop fallback')
                    part = os.read(master, 65536)
                    if not part:
                        raise RuntimeError('debugger PTY closed before command acknowledgement')
                    response += part
                    log.write(part); log.flush()
                    if log.tell()>16*1024*1024:
                        raise RuntimeError('native event log exceeds 16MiB; narrow watchpoint scope')
                if re.search(rb'(?i)(unrecognized|not a valid binding|did not evaluate|failed to eval|failed to open|unknown command|invalid command)', response):
                    raise RuntimeError('native debugger rejected command; inspect debugger.log')
                if seq + 1 == baseline_end:
                    check_dumps(root, 0)
                    first_ram = (root / 'snapshots/000/ram.bin').read_bytes()
                    for check in doc.get('preconditions', []):
                        off = check['address'] - 0xC000
                        value = bytes.fromhex(check['equals_hex'])
                        if first_ram[off:off + len(value)] != value:
                            raise RuntimeError('ROM baseline precondition failed before input; case inapplicable')
                    meta['baseline_checked_before_input'] = True
                    meta['baseline_precondition_count'] = len(doc.get('preconditions', []))
                    meta['case_applicability'] = ('preconditions_passed' if meta['baseline_precondition_count']
                                                  else 'not_declared_generic_diagnostic_only')
        if p.returncode != 0:
            raise RuntimeError('BlastEm exited with error; inspect debugger.log')
        log_text = (root / 'debugger.log').read_text()
        if 'SMSFORGE_SITE_MISMATCH' in log_text:
            raise RuntimeError('VDP breakpoint live opcode changed; mapping/case no longer applicable')
        if 'falling back to SDL2 renderer' in log_text or 'Initialization of GLEW failed' in log_text:
            raise RuntimeError('OpenGL capture unavailable; SDL screenshot path is not qualified')
        boundaries = re.findall(r'SMSFORGE_BOUNDARY (\d+) (\d+)', log_text)
        if len(boundaries) != len(doc['steps']) + 1:
            raise RuntimeError('missing or duplicate debugger boundaries')
        frames = [int(n) for i, n in boundaries]
        if [int(i) for i, n in boundaries] != list(range(len(frames))):
            raise RuntimeError('out of order debugger boundaries')
        for i, step in enumerate(doc['steps'], 1):
            if frames[i] - frames[i - 1] != step['frames']:
                raise RuntimeError('VDP frame delta differs from requested sequence')
        from PIL import Image
        screenshots = list((root / 'screenshots').glob('*.png'))
        if len(screenshots) != 1:
            raise RuntimeError('expected exactly one fresh native screenshot')
        with Image.open(screenshots[0]) as im:
            if im.size != (256, 192):
                raise RuntimeError('uncalibrated native screenshot; expected SMS 256x192')
            meta['screenshot_informative'] = len(im.convert('RGB').getcolors(65536) or []) > 1
        cpu = re.findall(r'SMSFORGE_CPU (\d+) ((?:\d+ ){9}\d+)', log_text)
        if [int(i) for i, values in cpu] != list(range(len(frames))):
            raise RuntimeError('missing Z80 state snapshots')
        meta['cpu_snapshots'] = [dict(index=int(i), **dict(zip(
            ('pc', 'sp', 'af', 'bc', 'de', 'hl', 'ix', 'iy', 'internal_cycle', 'iff1'),
            map(int, values.split())))) for i, values in cpu]
        meta['cycle_scope'] = 'upstream internal master-clock counter; rebased by emulator; not CPU duration or realtime FPS'
        for i in range(len(frames)):
            check_dumps(root, i)
            diagnostics.render_views(root / f'snapshots/{i:03d}')
        if sha(__file__) != LOADED_SHA or sha(feature_source) != feature_sha:
            raise RuntimeError('wrapper changed during run; evidence is not eligible')
        meta['events'] = diagnostics.decode_events(log_text, definitions)
        meta['event_counts'] = [sum(e['index']==i for e in meta['events']) for i in range(len(definitions))]
        counts = [(int(i),int(n)) for i,n in re.findall(r'SMSFORGE_HITS (\d+) (\d+)',log_text)]
        if counts != list(enumerate(meta['event_counts'])):
            raise RuntimeError('programmed native counters differ from event log')
        meta['native_media'] = diagnostics.media_summary(root, create_derived=True)
        if features.get('record_av') and set(meta['native_media']) & {'apng','wave'} != {'apng','wave'}:
            raise RuntimeError('requested native APNG/WAVE missing')
        if features.get('vgm') and 'vgm' not in meta['native_media']:
            raise RuntimeError('requested native VGM missing')
        meta.update(state='completed', boundaries=[{'index': i, 'vdp_frame': f} for i, f in enumerate(frames)],
                    screenshot_extra_frames=1)
    except BaseException as exc:
        meta.update(state='failed', error=str(exc))
        raise
    finally:
        cleanup_errors = cleanup_owned((p, x), (readfd, writefd, master, slave))
        meta['closed_at'] = time.time()
        meta['cleanup'] = {'sandbox_exited': p is None or p.poll() is not None,
                           'xvfb_exited': x is None or x.poll() is not None}
        if cleanup_errors:
            meta.update(state='failed', cleanup_errors=cleanup_errors)
        meta['files'] = {str(q.relative_to(root)): {'sha256': sha(q), 'bytes': q.stat().st_size}
                         for q in root.rglob('*') if q.is_file() and q.name not in {'session.json', 'Xauthority'}}
        write_json(root / 'session.json', meta)
        if cleanup_errors:
            raise RuntimeError('owned cleanup failed; inspect session.json')
    return root

def self_check():
    assert runtime_path(None) == (WORKSPACE / 'out/host_tools/blastem/1.0.0').resolve()
    assert runtime_path(str(WORKSPACE / '.runtime/host_tools/blastem/1.0.0')) == (
        WORKSPACE / '.runtime/host_tools/blastem/1.0.0').resolve()
    assert BINDINGS == ('up', 'down', 'left', 'right', 'b', 'c')
    valid = {'schema': 'sms_blastem_sequence_v1', 'steps': [{'frames': 7, 'p1': 8}],
             'preconditions': [{'address': 0xC700, 'equals_hex': '534d493101'}]}
    validate_script(valid)
    bads = [{**valid, 'region': 'pal'}, {**valid, 'model': 'md1va3'},
            {**valid, 'steps': [{'frames': 0}]}, {**valid, 'steps': [{'frames': True}]},
            {**valid, 'steps': [{'frames': 7, 'p1': 64}]},
            {**valid, 'steps': [{'frames': 7, 'command': 'set pc 0'}]},
            {**valid, 'preconditions': [{'address': 0xDFFF, 'equals_hex': '0102'}]},
            {**valid, 'preconditions': None}, {**valid, 'preconditions': 'bad'},
            {**valid, 'preconditions': [None]},
            {**valid, 'preconditions': [{'address': 0xC700, 'equals_hex': 3}]}]
    for bad in bads:
        try:
            validate_script(bad)
        except (ValueError, TypeError):
            continue
        raise AssertionError('invalid diagnostic script accepted')
    from unittest.mock import patch
    # Guards are exercised without altering shared source or running emulators.
    with patch.dict(run.__globals__, sha=lambda path: 'changed'):
        try:
            run('missing.sms', valid, 'unused')
        except ValueError as exc:
            assert 'changed since module import' in str(exc)
        else:
            raise AssertionError('stale imported wrapper accepted')
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / 'snapshots/000';folder.mkdir(parents=True)
        for name, size in DUMP_SIZES.items():
            (folder / (name + '.bin')).write_bytes(bytes(size))
        check_dumps(Path(tmp), 0)
        (folder / 'ram.bin').write_bytes(b'valid-prefix-but-truncated')
        try:
            check_dumps(Path(tmp), 0)
        except RuntimeError:
            pass
        else:
            raise AssertionError('truncated baseline accepted')
    calls = []
    def fail_first(p):
        calls.append(p)
        if p == 'sandbox': raise OSError('synthetic cleanup failure')
    with patch.dict(cleanup_owned.__globals__, terminate_group=fail_first):
        assert cleanup_owned(('sandbox', 'xvfb'), ()) and calls == ['sandbox', 'xvfb']
    print('[SELF-CHECK OK] BlastEm SMS script bounds, machine, PAL and injection rejection')
    return 0

def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt('CLI interrupted; closing owned processes')
    signal.signal(signal.SIGTERM, interrupted)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-check', action='store_true')
    sub = ap.add_subparsers(dest='op')
    sub.add_parser('install')
    sub.add_parser('status')
    p = sub.add_parser('run')
    p.add_argument('--rom', required=True)
    p.add_argument('--script', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--timeout', type=int, default=90)
    args = ap.parse_args()
    try:
        if args.self_check:
            return self_check()
        if args.op == 'install':
            print(install())
        elif args.op == 'status':
            print(json.dumps({'version': '1.0.0', 'binary': str(runtime()), 'sha256': sha(runtime())}))
        elif args.op == 'run':
            print(run(args.rom, json.loads(Path(args.script).read_text()), args.output, args.timeout))
        else:
            ap.error('choose install, status or run')
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('[FAIL] ' + str(exc))
        return 1
    except KeyboardInterrupt:
        print('[FAIL] interrupted; owned cleanup attempted')
        return 130

if __name__ == '__main__':
    raise SystemExit(main())
