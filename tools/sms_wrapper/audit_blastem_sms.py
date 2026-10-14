#!/usr/bin/env python3
"""Audit a bounded BlastEm SMS diagnostic bundle, not game quality or FPS (§108).

Checks recorded identities, dumps, VDP boundaries, source freshness when asked,
baseline predicates and cleanup. It cannot authenticate ROM semantics, host
security, cycle timing, artistic quality or physical hardware compatibility.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import tempfile

from blastem_sms import ARCHIVE_SHA, BINARY_SHA, sha, validate_script, write_json

SIZES = {'ram': 8192, 'vram': 16384, 'cram_internal': 64,
         'vdp_regs': 11, 'psg_frequency': 8, 'psg_volume': 4}

def audit(root, current_rom=None, require_current_tool=False):
    root = Path(root).resolve()
    errors = []
    def demand(value, message):
        if not value:
            errors.append(message)
    try:
        meta = json.loads((root / 'session.json').read_text())
        doc = validate_script(json.loads((root / 'sequence.json').read_text()))
        demand(meta.get('schema') == 'sms_blastem_session_v1', 'wrong session schema')
        demand(meta.get('session_id') == root.name, 'session directory identity mismatch')
        demand(meta.get('state') == 'completed', 'diagnostic run did not complete')
        demand(meta.get('machine') == 'sms' and meta.get('model') in ('sms1', 'sms2') and
               meta.get('model') == doc.get('model', 'sms2'), 'unqualified machine/model')
        demand(meta.get('region') == 'ntsc', 'PAL is not qualified')
        demand(meta.get('emulator_sha256') == BINARY_SHA and meta.get('archive_sha256') == ARCHIVE_SHA,
               'emulator differs from qualified pin')
        demand(meta.get('claim_scope') == 'diagnostic_states_only' and
               meta.get('fps_claim') is False and meta.get('hardware_validation') is False,
               'diagnostic evidence overclaimed')
        demand(meta.get('audio') == 'dummy_not_tested' and meta.get('frame_clock') == 'VDP_debugger' and
               meta.get('input') == 'native_debugger_process_local_bindings', 'unexpected clock/audio/input contract')
        demand(meta.get('baseline_checked_before_input') is True, 'baseline gate unpaid')
        count = len(doc.get('preconditions', []))
        demand(meta.get('baseline_precondition_count') == count, 'predicate coverage differs')
        demand(meta.get('case_applicability') == ('preconditions_passed' if count else
               'not_declared_generic_diagnostic_only'), 'applicability overclaimed')
        demand(sha(root / 'adapter_source.py') == meta.get('wrapper_sha256'), 'adapter source binding differs')
        demand(meta.get('rom_sha256') == sha(root / 'rom.sms'), 'ROM identity changed')
        demand(meta.get('sequence_sha256') == sha(root / 'sequence.json'), 'sequence changed')
        config = root / '.config/blastem/blastem.cfg'
        demand(meta.get('config_sha256') == sha(config), 'configuration changed')
        demand(meta.get('cleanup') == {'sandbox_exited': True, 'xvfb_exited': True}, 'cleanup missing or failed')
        from session_bridge.isolated import alive
        for key in ('sandbox_process', 'xvfb_process'):
            proc = meta.get(key)
            demand(isinstance(proc, dict) and set(proc) == {'pid', 'start_ticks'}, 'process identity absent: ' + key)
            if isinstance(proc, dict) and set(proc) == {'pid', 'start_ticks'}:
                demand(not alive(proc), 'owned process still alive: ' + key)
        if current_rom is not None:
            demand(sha(current_rom) == meta.get('rom_sha256'), 'bundle ineligible for current ROM')
        if require_current_tool:
            demand(sha(Path(__file__).with_name('blastem_sms.py')) == meta.get('wrapper_sha256'),
                   'bundle was generated with another wrapper revision')
            if meta.get('diagnostics_sha256'):
                demand(sha(Path(__file__).with_name('blastem_diagnostics.py'))==meta['diagnostics_sha256'],
                       'bundle generated with another diagnostics revision')
        files = meta.get('files', {})
        demand(isinstance(files, dict) and bool(files), 'artifact bindings absent')
        for name, record in files.items():
            path = root / name
            demand(not Path(name).is_absolute() and root in path.resolve().parents, 'artifact path escape')
            if Path(name).is_absolute() or root not in path.resolve().parents:
                continue
            demand(path.is_file() and not path.is_symlink(), 'missing/linked artifact: ' + name)
            if path.is_file():
                demand(sha(path) == record.get('sha256') and path.stat().st_size == record.get('bytes'),
                       'artifact changed: ' + name)
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and
                  p.name not in {'session.json', 'Xauthority'}}
        demand(actual == set(files), 'unbound/missing artifacts')
        log = (root / 'debugger.log').read_text()
        demand('SMSFORGE_SITE_MISMATCH' not in log, 'VDP site opcode changed at runtime')
        bounds = [{'index': int(i), 'vdp_frame': int(f)} for i, f in
                  re.findall(r'SMSFORGE_BOUNDARY (\d+) (\d+)', log)]
        demand(bounds == meta.get('boundaries') and len(bounds) == len(doc['steps']) + 1,
               'boundary metadata differs from native log')
        if len(bounds) == len(doc['steps']) + 1:
            demand([p['index'] for p in bounds] == list(range(len(bounds))), 'unordered boundaries')
            demand(bounds[0]['vdp_frame'] == doc.get('warmup_frames', 120), 'initial VDP frame differs from warmup')
            for i, step in enumerate(doc['steps'], 1):
                demand(bounds[i]['vdp_frame'] - bounds[i-1]['vdp_frame'] == step['frames'],
                       'VDP delta differs from script')
        cpu = re.findall(r'SMSFORGE_CPU (\d+) ((?:\d+ ){9}\d+)', log)
        fields = ('pc', 'sp', 'af', 'bc', 'de', 'hl', 'ix', 'iy', 'internal_cycle', 'iff1')
        decoded = [dict(index=int(i), **dict(zip(fields, map(int, v.split())))) for i, v in cpu]
        demand(decoded == meta.get('cpu_snapshots') and len(decoded) == len(doc['steps']) + 1,
               'CPU snapshots absent or divergent')
        demand([p['index'] for p in decoded] == list(range(len(doc['steps']) + 1)) and
               [p['index'] for p in decoded] == [p['index'] for p in bounds],
               'CPU indices do not match boundaries')
        for i in range(len(doc['steps']) + 1):
            for name, size in SIZES.items():
                path = root / f'snapshots/{i:03d}/{name}.bin'
                demand(path.stat().st_size == size, 'invalid dump size: ' + str(path.relative_to(root)))
            regs = (root / f'snapshots/{i:03d}/vdp_regs.bin').read_bytes()
            demand(bool(regs[0] & 4) and not (regs[1] & 0x18), 'unsupported Mode4 height/profile')
        ram = (root / 'snapshots/000/ram.bin').read_bytes()
        for cond in doc.get('preconditions', []):
            expected = bytes.fromhex(cond['equals_hex']); offset = cond['address'] - 0xC000
            demand(ram[offset:offset + len(expected)] == expected, 'baseline RAM predicate failed')
        shots = list((root / 'screenshots').glob('*.png'))
        demand(len(shots) == 1 and meta.get('screenshot_extra_frames') == 1, 'screenshot timeline/capture absent')
        if len(shots) == 1:
            from PIL import Image
            with Image.open(shots[0]) as im:
                demand(im.size == (256, 192), 'native capture is not SMS 256x192')
                informative = len(im.convert('RGB').getcolors(65536) or []) > 1
                demand(informative == meta.get('screenshot_informative'), 'capture classification differs')
        demand('falling back to SDL2 renderer' not in log, 'unqualified SDL capture fallback')
        demand('Initialization of GLEW failed' not in log, 'OpenGL initialization failed')
        if meta.get('diagnostics_sha256') or doc.get('diagnostics'):
            from blastem_diagnostics import validate_features, instrumentation, decode_events, media_summary
            from blastem_sms import configuration
            demand(sha(root/'diagnostics_source.py')==meta.get('diagnostics_sha256'), 'diagnostics source binding differs')
            demand(config.read_text()==configuration(Path(meta['root']),meta['model']), 'configuration semantics differ')
            features=validate_features(doc)
            commands,definitions=instrumentation(features,(root/'rom.sms').read_bytes())
            demand(definitions==meta.get('event_definitions'), 'event definitions differ')
            events=decode_events(log,definitions)
            demand(events==meta.get('events'), 'native events differ from log')
            counts=[sum(e['index']==i for e in events) for i in range(len(definitions))]
            demand(counts==meta.get('event_counts'), 'native event coverage differs')
            demand([(int(i),int(n)) for i,n in re.findall(r'SMSFORGE_HITS (\d+) (\d+)',log)]==list(enumerate(counts)),
                   'programmed native counters differ')
            if bounds:
                for e in events:
                    demand(bounds[0]['vdp_frame']<=e['vdp_frame']<=bounds[-1]['vdp_frame'], 'event outside active sequence')
                    demand(0<=e['observed_pc']<=65535 and 0<=e['value']<=255, 'event value/range invalid')
                    demand(0<=e['vdp_internal_vcounter']<=65535 and 0<=e['vdp_internal_hslot']<=255 and
                           0<=e['vdp_internal_address']<=0xFFFFFFFF and 0<=e['vdp_internal_cd']<=255,
                           'VDP internal observation exceeds upstream field types')
                    definition=definitions[e['index']]
                    if definition['kind']=='vdp_io_before_out':
                        demand(e['port'] in (190,191), 'VDP event port differs')
                    else:demand(e['port']==0, 'CPU event has I/O port')
            media=media_summary(root)
            demand(media==meta.get('native_media'), 'native media measurements differ')
            if features.get('record_av'):
                demand('apng' in media and 'wave' in media, 'requested APNG/WAVE absent')
                if 'apng' in media:
                    demand(media['apng']['frames']==sum(s['frames'] for s in doc['steps']), 'APNG coverage differs from active VDP frames')
            else:demand('apng' not in media and 'wave' not in media, 'unexpected native AV')
            demand(('vgm' in media)==features.get('vgm',False), 'native VGM coverage differs')
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        errors.append('unreadable/invalid bundle: ' + str(exc))
    return {'schema': 'sms_blastem_audit_v1', 'ok': not errors, 'errors': errors,
            'scope': 'record_consistency_only_not_gameplay_fps_audio_or_hardware'}

def fixture(root):
    """Synthetic contract fixture; never emulator runtime evidence."""
    root = Path(root) / 'blastem-sms-selfcheck'; root.mkdir()
    (root / '.config/blastem').mkdir(parents=True)
    config = root / '.config/blastem/blastem.cfg';config.write_text('synthetic\n')
    (root / 'adapter_source.py').write_bytes(b'synthetic-source-not-runtime')
    (root / 'screenshots').mkdir();(root / 'rom.sms').write_bytes(b'synthetic-not-a-ROM')
    doc = {'schema': 'sms_blastem_sequence_v1', 'steps': [{'frames': 7}]}
    write_json(root / 'sequence.json', doc)
    for i in range(2):
        folder = root / f'snapshots/{i:03d}'; folder.mkdir(parents=True)
        for name, size in SIZES.items():
            data = bytearray(size)
            if name == 'vdp_regs': data[0] = 4
            (folder / (name + '.bin')).write_bytes(data)
    from PIL import Image
    im = Image.new('RGB', (256, 192));im.putpixel((0, 0), (255, 255, 255));im.save(root / 'screenshots/native.png')
    (root / 'debugger.log').write_text('SMSFORGE_BOUNDARY 0 120\nSMSFORGE_CPU 0 1 2 3 4 5 6 7 8 9 1\nSMSFORGE_BOUNDARY 1 127\nSMSFORGE_CPU 1 1 2 3 4 5 6 7 8 9 1\n')
    meta = {'schema': 'sms_blastem_session_v1', 'session_id': root.name, 'state': 'completed',
            'machine': 'sms', 'model': 'sms2', 'region': 'ntsc', 'emulator_sha256': BINARY_SHA,
            'archive_sha256': ARCHIVE_SHA, 'claim_scope': 'diagnostic_states_only',
            'fps_claim': False, 'hardware_validation': False, 'audio': 'dummy_not_tested',
            'frame_clock': 'VDP_debugger', 'input': 'native_debugger_process_local_bindings',
            'baseline_checked_before_input': True, 'rom_sha256': sha(root / 'rom.sms'),
            'baseline_precondition_count': 0, 'case_applicability': 'not_declared_generic_diagnostic_only',
            'wrapper_sha256': sha(root / 'adapter_source.py'),
            'sequence_sha256': sha(root / 'sequence.json'), 'config_sha256': sha(config),
            'cleanup': {'sandbox_exited': True, 'xvfb_exited': True},
            'sandbox_process': {'pid': 999999999, 'start_ticks': 'absent'},
            'xvfb_process': {'pid': 999999998, 'start_ticks': 'absent'},
            'boundaries': [{'index': 0, 'vdp_frame': 120}, {'index': 1, 'vdp_frame': 127}],
            'cpu_snapshots': [dict(index=i, **dict(zip(('pc','sp','af','bc','de','hl','ix','iy','internal_cycle','iff1'),
                                                    (1,2,3,4,5,6,7,8,9,1)))) for i in range(2)],
            'screenshot_extra_frames': 1, 'screenshot_informative': True}
    meta['files'] = {str(p.relative_to(root)): {'sha256': sha(p), 'bytes': p.stat().st_size}
                     for p in root.rglob('*') if p.is_file()}
    write_json(root / 'session.json', meta)
    return root, meta

def self_check():
    with tempfile.TemporaryDirectory(prefix='sms_blastem_audit_') as tmp:
        root, good = fixture(tmp)
        assert audit(root)['ok'], audit(root)
        for key, value in [('machine', 'gen'), ('region', 'pal'), ('fps_claim', True),
                           ('baseline_checked_before_input', False), ('emulator_sha256', '0'*64),
                           ('cleanup', {'sandbox_exited': False, 'xvfb_exited': True})]:
            bad = copy.deepcopy(good);bad[key] = value;write_json(root / 'session.json', bad)
            assert not audit(root)['ok'], key
        write_json(root / 'session.json', good)
        for corrupt in ('cpu_indices','glew'):
            bad=copy.deepcopy(good)
            original=(root/'debugger.log').read_text()
            if corrupt=='cpu_indices':
                (root/'debugger.log').write_text(original.replace('SMSFORGE_CPU 1','SMSFORGE_CPU 0'))
                bad['cpu_snapshots'][1]['index']=0
            else:(root/'debugger.log').write_text(original+'Initialization of GLEW failed\n')
            bad['files']['debugger.log']={'sha256':sha(root/'debugger.log'),'bytes':(root/'debugger.log').stat().st_size}
            write_json(root/'session.json',bad)
            assert not audit(root)['ok'],corrupt
            (root/'debugger.log').write_text(original)
        write_json(root/'session.json',good)
        (root / 'snapshots/001/ram.bin').write_bytes(b'stale')
        assert not audit(root)['ok'], 'altered/truncated dump'
    print('[SELF-CHECK OK] BlastEm SMS audit: synthetic valid record, MD/PAL/claims/pin/baseline/cleanup/tamper rejection')
    return 0

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-check', action='store_true')
    ap.add_argument('--session')
    ap.add_argument('--current-rom')
    ap.add_argument('--require-current-tool', action='store_true')
    ap.add_argument('--json')
    args = ap.parse_args()
    if args.self_check: return self_check()
    if not args.session: ap.error('--session required')
    result = audit(args.session, args.current_rom, args.require_current_tool)
    if args.json: write_json(args.json, result)
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
