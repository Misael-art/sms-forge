"""Recheck preserved art-method evidence. No generation, build or emulator.

Run from checkout root through run_host.sh. Outputs go to an unused --out
directory (normally tools/sms_wrapper/out/art_method_transfer). Real corpus
must be restored; missing files fail, never substitute synthetic game art.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/sms_wrapper'))
from audit_art_review_checklist import audit, TEMPORAL_METHODS
from prepare_authored_sprite_sample import prepare


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def ref(path):
    path = path.resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    project = ROOT / 'SMS_projects/master_of_fighters'
    diag = project / 'out/diagnostics'
    hayato = diag / 'hayato_short_cut_v2'
    social = diag / 'dr_social_cps2_sample_v1/contact_grid_v8'
    records = []
    # Rebuild data with the UNCHANGED converter; compare every public PNG and
    # emitted header, not paths/timestamps in diagnostic JSON.
    for name, config, baseline in [
        ('social', 'dr_social_cps2_sample_v8.json', social / 'converted'),
        ('hayato_left', 'hayato_short_cut_body_sequence_v4_left.json', hayato / 'converted_v4_left'),
        ('hayato_right', 'hayato_short_cut_body_sequence_v4_right.json', hayato / 'converted_v4_right'),
    ]:
        config = project / '.mddev' / config
        output = args.out / name
        report = prepare(config, output)
        compared = []
        for path in sorted(output.glob('*.png')) + [output / 'sample_data.h']:
            old = baseline / path.name
            assert path.read_bytes() == old.read_bytes(), (name, path.name, 'data regression')
            compared.append(ref(old))
        assert all(c['legal'] for c in report['compositions'])
        records.append({'case': name, 'config': ref(config), 'exact_outputs': compared,
                        'patterns': report['patterns'], 'max_sat': max(c['sat'] for c in report['compositions']),
                        'max_scanline': max(c['peak'] for c in report['compositions'])})

    # Preserve source/report roles; never replace or edit the actual reviews.
    checkpoints = {}
    for character in ['hayato', 'social']:
        if character == 'hayato':
            source = project / 'data/source_art/sprite_studies/hayato/review_drafts/cps2_short_cut_v2/sequence_v4/cut_source.png'
            review = project / 'doc/hayato_short_cut_body_temporal_independent_review_v4.json'
            board = hayato / 'final_review_v4/source_sequence.png'
            runtime = hayato / 'performance_v4/1b1f33e71f704e05bd064e688d3378cf'
            rom = runtime / 'bundle/1b1f33e71f704e05bd064e688d3378cf/rom.sms'
            media = runtime / 'hayato_cut_realtime.mp4'
            ids, durations = ['R01', 'R02', 'R03', 'R04', 'R05', 'R06'], [4, 1, 2, 3, 1, 3]
        else:
            candidate = json.loads((project / 'doc/curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json').read_text())
            source = project / 'data/source_art/sprite_studies/dr_social/review_drafts/cps2_sample_v1/contact_revision_v8/jab_source.png'
            # Resolve actual source path by the recorded source SHA, not a guessed revision name.
            source_hash = candidate['followup_compensated_grid_v8']['source_sha256']
            matches = [p for p in (project / 'data/source_art/sprite_studies/dr_social/review_drafts/cps2_sample_v1').rglob('jab_source.png') if sha(p) == source_hash]
            assert matches, 'preserved Social v8 source missing'
            source = matches[0]
            review = project / 'doc/dr_social_cps2_sample_independent_review_v8.json'
            document = json.loads(review.read_text())
            # The reviewer binds the exact source sheet in its artifact list.
            entries = [r for r in document['artifacts'] if r['sha256'] == source_hash]
            assert entries, 'Social source absent from preserved review'
            board = source
            ids, durations = ['J01', 'J02', 'J03', 'J04', 'J05', 'J06'], [2, 1, 1, 1, 1, 3]
        obs = {'id': 'static', 'method': 'framewise', 'target': 'source',
               'subject_sha256': sha(source), 'report': ref(review), 'media': ref(board),
               'reviewer': json.loads(review.read_text())['reviewer']}
        checkpoint = {'schema': 'sms_art_temporal_review_v1', 'producer': '/root',
                      'subjects': {'source': ref(source)},
                      'sequence': {'expected_ids': ids, 'actual_ids': ids, 'duration_ticks': durations,
                                   'tick_definition': 'diagnostic NTSC presentation ticks; no competitive frame data',
                                   'expected_terminal': 'guard' if character == 'hayato' else 'idle',
                                   'terminal': 'guard' if character == 'hayato' else 'idle'},
                      'observations': [obs], 'axes': {}, 'next_decision': 'keep_control'}
        for axis in TEMPORAL_METHODS:
            passed = axis in {'image_inspection', 'frame_analysis'}
            checkpoint['axes'][axis] = {'status': 'pass' if passed else 'needs_evidence',
                                       'note': 'Preserved independent review scope; no new perceptual review.',
                                       'observation_ids': ['static'] if passed else []}
        if character == 'hayato':
            checkpoint['subjects']['rom'] = ref(rom)
            for oid, method, axis in [('timeline', 'timeline', 'order_exposure'), ('rom', 'rom_framewise', 'rom_presentation')]:
                checkpoint['observations'].append(dict(obs, id=oid, method=method, target='rom',
                    subject_sha256=sha(rom), rom_sha256=sha(rom), session_id='1b1f33e71f704e05bd064e688d3378cf', media=ref(media)))
                checkpoint['axes'][axis].update(status='pass', observation_ids=[oid])
            assembly_path = source.parent / 'source_assembly.json'
            assembly = json.loads(assembly_path.read_text())
            patch = next(r for r in assembly['selected'] if r['id'] == 'R03')
            checkpoint['edit_boundary'] = {'before': ref(project / assembly['hair_delta']['original']),
                'after': ref(project / patch['path']), 'rectangles': [assembly['hair_delta']['source_roi']]}
        result = audit(checkpoint, ROOT, True)
        assert result['exit_code'] == 2 and not result['problems'], result
        (args.out / f'{character}_checkpoint.json').write_text(json.dumps(checkpoint, indent=2) + '\n')
        checkpoints[character] = result
        # Real report + deliberately false wrapper claim; never stored as review.
        bad = copy.deepcopy(checkpoint)
        bad['axes']['continuous_motion'].update(status='pass', observation_ids=['static'])
        rejection = audit(bad, ROOT, True)
        assert rejection['exit_code'] == 1 and any('method cannot' in p for p in rejection['problems'])
        records.append({'case': character + '_static_as_temporal_negative', 'problems': rejection['problems'],
                        'control_type': 'mutated declaration only; actual review unchanged'})
    result = {'scope': 'archived custody + deterministic data replay, not fresh ROM QA or new art acceptance',
              'adapter': ref(ROOT / 'tools/sms_wrapper/prepare_authored_sprite_sample.py'),
              'cases': records, 'checkpoints': checkpoints}
    (args.out / 'transfer.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
