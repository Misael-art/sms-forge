"""Observation custody regressions; fixture bytes are not artistic evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_art_review_checklist import audit, TEMPORAL_METHODS


def temporal_fixture(root):
    def ref(name):
        path = root / name
        path.write_text('synthetic custody fixture: ' + name)
        return {'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    source, rom, media, report = (ref(n) for n in ['source.png', 'rom.sms', 'movie.mp4', 'review.json'])
    (root / 'review.json').write_text(json.dumps({'artifacts': [source, rom, media]}))
    report['sha256'] = hashlib.sha256((root / 'review.json').read_bytes()).hexdigest()
    observations, axes = [], {}
    for axis, method in zip(TEMPORAL_METHODS,
                            ['still', 'framewise', 'timeline', 'continuous', 'rom_framewise', 'owner_decision']):
        target = 'rom' if axis == 'rom_presentation' else 'source'
        obs = {'id': axis, 'target': target, 'subject_sha256': (rom if target == 'rom' else source)['sha256'],
               'method': method, 'reviewer': 'independent', 'report': report, 'media': media}
        if method == 'continuous':
            obs.update(normal_speed_perceived=True, capture_mode='authored_preview')
        if target == 'rom':
            obs.update(rom_sha256=rom['sha256'], session_id='fixture-session')
        if method == 'owner_decision':
            obs.update(reviewer='owner', decision='accepted')
        observations.append(obs)
        axes[axis] = {'status': 'pass', 'note': 'Synthetic declaration only', 'observation_ids': [axis]}
    return {'schema': 'sms_art_temporal_review_v1', 'producer': 'producer',
            'subjects': {'source': source, 'rom': rom},
            'sequence': {'expected_ids': ['A', 'A', 'B'], 'actual_ids': ['A', 'A', 'B'],
                         'duration_ticks': [2, 3, 1], 'tick_definition': 'fixture tick',
                         'expected_terminal': 'guard', 'terminal': 'guard',
                         'registration': [{'id': x, 'scale': [2, 3], 'offset': [i, -i],
                                           'rationale': 'authored body travel'} for i, x in enumerate(['A', 'A', 'B'])]},
            'observations': observations, 'axes': axes, 'next_decision': 'keep'}


def check_temporal_cases(base, root):
    assert audit(base, root, True)['exit_code'] == 0
    waiting = copy.deepcopy(base)
    waiting['observations'] = [o for o in waiting['observations'] if o['method'] not in {'continuous', 'owner_decision'}]
    for axis in ['continuous_motion', 'owner_acceptance']:
        waiting['axes'][axis].update(status='needs_evidence', observation_ids=[])
    waiting['next_decision'] = 'keep_control'
    r = audit(waiting, root, True)
    assert r['exit_code'] == 2 and not r['problems'], r
    # Cross-axis laundering, wrong identity and incomplete candidates all fail.
    for method in ['still', 'framewise', 'timeline', 'fps', 'framebuffer_match']:
        bad = copy.deepcopy(base)
        bad['observations'][3]['method'] = method
        r = audit(bad, root, True)
        assert r['exit_code'] == 1 and any('method cannot' in p for p in r['problems']), r
    changes = [
        lambda b: b['observations'][0].update(subject_sha256='0' * 64),
        lambda b: b['observations'][4].update(rom_sha256='0' * 64),
        lambda b: b['observations'][3].update(capture_mode='stepping'),
        lambda b: b['observations'][3].update(normal_speed_perceived=False),
        lambda b: b['observations'][0]['report'].update(sha256='0' * 64),
        lambda b: b['sequence'].update(actual_ids=['A', 'B']),
        lambda b: b['sequence'].update(actual_ids=['B', 'A', 'A']),
        lambda b: b['sequence'].update(terminal='attack'),
        lambda b: b['sequence'].update(duration_ticks=[2, True, 1]),
        lambda b: b['sequence']['registration'][1].update(scale=[1, 2]),
        lambda b: b['observations'][5].update(reviewer='producer'),
        lambda b: b['observations'][5].update(decision='rejected'),
        lambda b: b.update(next_decision='repair_pose'),
        lambda b: b['axes']['continuous_motion'].update(observation_ids=['missing']),
        lambda b: b['axes'].update(continuous_motion=None),
        lambda b: b['observations'][0].update(method=[]),
        lambda b: b.update(next_decision=[]),
        lambda b: b['axes']['continuous_motion'].update(status=[]),
    ]
    for change in changes:
        bad = copy.deepcopy(base)
        change(bad)
        r = audit(bad, root, True)
        assert r['exit_code'] == 1, (change, r)
    # Intentional repeated image/hold, motion offsets and equivalent ratios pass.
    equivalent = copy.deepcopy(base)
    equivalent['sequence']['registration'][1]['scale'] = [4, 6]
    assert audit(equivalent, root, True)['exit_code'] == 0
    return waiting


def test_temporal_contract_and_negative_controls(tmp_path):
    check_temporal_cases(temporal_fixture(tmp_path), tmp_path)


def test_cli_pending_is_not_failure_or_approval(tmp_path):
    import subprocess
    waiting = check_temporal_cases(temporal_fixture(tmp_path), tmp_path)
    manifest = tmp_path / 'checkpoint.json'
    manifest.write_text(json.dumps(waiting))
    result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'audit_art_review_checklist.py'),
                             '--manifest', str(manifest), '--project-root', str(tmp_path), '--verify-hashes'],
                            capture_output=True, text=True)
    assert result.returncode == 2 and 'needs_evidence' not in result.stderr
    assert 'continuous_motion' in result.stdout


def test_report_contents_cannot_contradict_declared_observation(tmp_path):
    base = temporal_fixture(tmp_path)
    document = json.loads((tmp_path / 'review.json').read_text())
    for changes in [{'subject_sha256': '0' * 64}, {'full_conclusion': {'final_temporal_approval': False}},
                    {'artifacts': []}]:
        (tmp_path / 'review.json').write_text(json.dumps(dict(document, **changes)))
        ref = base['observations'][0]['report']
        ref['sha256'] = hashlib.sha256((tmp_path / 'review.json').read_bytes()).hexdigest()
        assert audit(base, tmp_path, True)['exit_code'] == 1


def test_indexed_edit_boundary_preserves_non_roi_pixels_and_palette(tmp_path):
    from PIL import Image
    base = temporal_fixture(tmp_path)
    before = Image.new('P', (8, 8))
    before.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
    before.save(tmp_path / 'before.png', transparency=0)
    after = before.copy()
    after.putpixel((2, 2), 1)
    after.save(tmp_path / 'after.png', transparency=0)
    def ref(name):
        return {'path': name, 'sha256': hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()}
    base['edit_boundary'] = {'before': ref('before.png'), 'after': ref('after.png'), 'rectangles': [[2, 2, 3, 3]]}
    assert audit(base, tmp_path, True)['exit_code'] == 0
    after.putpixel((3, 2), 1)
    after.save(tmp_path / 'after.png', transparency=0)
    base['edit_boundary']['after'] = ref('after.png')
    r = audit(base, tmp_path, True)
    assert any('outside authorized' in x for x in r['problems'])
    after = before.copy()
    after.putpalette([0] * 768)
    after.save(tmp_path / 'after.png', transparency=0)
    base['edit_boundary']['after'] = ref('after.png')
    assert any('palette' in x for x in audit(base, tmp_path, True)['problems'])


def test_static_checklist_cannot_claim_temporal_without_current_checkpoint(tmp_path):
    from selftest import _art_review_manifest
    static_root = tmp_path / 'static'
    manifest_path = _art_review_manifest(static_root, required_axes=['continuous_motion'])
    static = json.loads(Path(manifest_path).read_text())
    assert any('requires temporal_checkpoint' in p for p in audit(static, static_root, True)['problems'])
    temporal_root = static_root / 'temporal'
    temporal_root.mkdir()
    temporal = temporal_fixture(temporal_root)
    # Point relative paths at the same root, while keeping independent evidence.
    def relocate(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                value['path'] = 'temporal/' + value['path']
            for v in value.values():
                relocate(v)
        elif isinstance(value, list):
            for v in value:
                relocate(v)
    # Copy through JSON so shared fixture refs are only relocated once per value.
    temporal = json.loads(json.dumps(temporal))
    relocate(temporal)
    path = static_root / 'checkpoint.json'
    path.write_text(json.dumps(temporal))
    static['temporal_checkpoint'] = {'path': 'checkpoint.json', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    r = audit(static, static_root, True)
    assert any('different asset SHA' in p for p in r['problems']), r
    static['asset'] = dict(temporal['subjects']['source'], kind='concept')
    r = audit(static, static_root, True)
    assert r['exit_code'] == 0, r
    temporal['axes']['continuous_motion'].update(status='needs_evidence', observation_ids=[])
    temporal['next_decision'] = 'keep_control'
    path.write_text(json.dumps(temporal))
    static['temporal_checkpoint']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    r = audit(static, static_root, True)
    assert any('contradicts checkpoint' in p for p in r['problems']), r
