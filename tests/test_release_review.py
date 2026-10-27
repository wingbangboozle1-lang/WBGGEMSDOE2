"""No contradictory approvals, stale-byte publishing, or private gate overrides."""
import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest
from build_release_review import check_evidence

ROOT = Path(__file__).resolve().parents[1]


def report():
    return json.loads((ROOT / 'evidence/release_recheck_20261027.json').read_text())


def test_review_is_byte_bound_and_rejects_both_candidates():
    data = report()
    check_evidence(data)
    assert data['experiments_run'] == data['slots_used'] == 0
    for row in data['candidates']:
        assert hashlib.sha256((ROOT / row['file']).read_bytes()).hexdigest() == row['sha256']
        assert row['final_dot_overlap_3px']['13GEMSDOE'] > .7
        assert row['preplacement_surface_rank_correlation'] is None
        assert row['leaderboard_estimate'] is None
        assert row['validator']['submission_approval'] is False


@pytest.mark.parametrize('mutation', ['approval', 'literal', 'hash', 'missing'])
def test_rendering_fails_closed_for_changed_evidence(mutation):
    data = copy.deepcopy(report())
    if mutation == 'approval':
        data['candidates'][0]['ok_to_submit'] = True
    elif mutation == 'literal':
        data['candidates'][0]['final_dot_overlap_3px']['13GEMSDOE'] = .5
    elif mutation == 'hash':
        data['candidates'][0]['sha256'] = '0' * 64
    else:
        data['candidates'].pop()
    with pytest.raises(ValueError):
        check_evidence(data)


def test_every_current_candidate_card_rejects_promotion():
    for rel in ('data_public/final_audit.json', 'data_public/run_card.json',
                'evidence/RUN_CARD_H3.json', 'docs/data/RUN_CARD_H3.json',
                'docs/data/run-card-current.json'):
        value = json.loads((ROOT / rel).read_text())
        assert value['ok_to_submit'] is False, rel
        assert value['verdict'] == 'negative', rel


def test_every_public_release_entrypoint_rejects_submission():
    for rel in ('docs/index.html', 'docs/executive-summary.html'):
        text = (ROOT / rel).read_text()
        assert 'DO NOT SUBMIT' in text, rel
        assert 'OK TO DOWNLOAD AND SUBMIT' not in text, rel
    for rel in ('docs/submission/index.html', 'docs/submission/executive-summary.html',
                'docs/submit/index.html'):
        text = (ROOT / rel).read_text()
        assert 'DO NOT SUBMIT' in text, rel
    for path in (ROOT / 'docs/submission/sites').glob('*.html'):
        text = path.read_text()
        assert 'USER-REPORTED' in text and 'DO NOT SUBMIT' in text
        assert 'leaderboard' in text and 'USER-REPORTED' in text


def test_retired_experiment_entrypoints_stop_before_any_work():
    import subprocess, sys
    for filename in ('make_candidate.py', 'generate_h3_pack.py',
                     'write_h3_submission.py', 'run_wbg2_msptcd.py',
                     'run_wbg2_cbs.py', 'run_campaign_20261027.py'):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / filename)],
                                capture_output=True, text=True, timeout=10)
        assert result.returncode != 0 and 'STOP' in result.stdout+result.stderr, filename


def test_pages_and_tests_build_release_review():
    for name in ('pages.yml', 'tests.yml'):
        assert 'python scripts/build_release_review.py' in (ROOT / '.github/workflows' / name).read_text()
    text = (ROOT / '.github/workflows/tests.yml').read_text()
    assert text.index('python scripts/build_release_review.py') < text.index('python -m pytest')
