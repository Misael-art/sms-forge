"""Audit preserved owner checkpoints without producing art, ROMs or approvals."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/sms_wrapper'))
from audit_art_review_checklist import audit


def main():
    project = ROOT / 'SMS_projects/master_of_fighters'
    rows = []
    for name in ['hayato_short_cut_timing_only_v7_checkpoint.json', 'jj_zillion_character_checkpoint_v7.json']:
        path = project / 'doc' / name
        manifest = json.loads(path.read_text())
        report = audit(manifest, project, True)
        expected_exit = 0 if name.startswith('hayato') else 2
        assert report['exit_code'] == expected_exit and not report['problems'], report
        assert manifest['axes']['owner_acceptance']['status'] == 'pass'
        # Validate explicit closure using existing evidence only, no new decision.
        closed = copy.deepcopy(manifest)
        closed.update(owner_decision_closed=True, owner_request=None)
        result = audit(closed, project, True)
        assert result['owner_decision_closed'] and result['exit_code'] == expected_exit, result
        negative = copy.deepcopy(closed)
        negative['sequence']['duration_ticks'][0] += 1
        rejected = audit(negative, project, True)
        assert any('owner-approved timing' in p for p in rejected['problems']), rejected
        refs = []
        for ref in [*manifest['subjects'].values(), *[o['report'] for o in manifest['observations']]]:
            actual = hashlib.sha256((project / ref['path']).read_bytes()).hexdigest()
            assert actual == ref['sha256']
            refs.append(ref)
        rows.append({'checkpoint': str(path.relative_to(ROOT)),
                     'checkpoint_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'verified_refs': refs, 'actual_report': report, 'closure_contract': result,
                     'negative_changed_timing': rejected['problems']})
    print(json.dumps({'scope': 'Preserved evidence custody; no new playback or acceptance', 'cases': rows}, indent=2))


if __name__ == '__main__':
    main()
