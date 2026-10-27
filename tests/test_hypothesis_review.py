import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def test_shortlist_has_complete_fields_and_no_self_assigned_lane():
    data = load('config/research_hypotheses.json')
    rows = data['hypotheses']
    assert 3 <= len(rows) <= 5
    assert [row['potential_rank'] for row in rows] == list(range(1, len(rows) + 1))
    assert len({row['id'] for row in rows}) == len(rows)
    assert data['method_lane']['status'] == 'UNASSIGNED'
    assert data['method_lane']['experiments_run_in_this_review_lane'] == 0
    assert 'not scores' in data['ranking_basis']
    for row in rows:
        for key in ('title', 'layers', 'signature', 'why_uncatalogued',
                    'difference_from_reviewed_methods', 'non_fault_mimic',
                    'data_status', 'potential_label', 'implementation_cost'):
            assert row[key], (row['id'], key)
        external = row.get('external_data')
        if external:
            assert external['url'].startswith('https://')
            assert external['source'] and external['access_check']


def test_hypothesis_sources_are_consistent_across_site_surfaces():
    data = load('config/research_hypotheses.json')
    markdown = (ROOT / 'research/hypotheses.md').read_text()
    docs_page = (ROOT / 'docs/research.html').read_text()
    legacy_page = (ROOT / 'site/research.html').read_text()
    home_page = (ROOT / 'site/index.html').read_text()
    for row in data['hypotheses']:
        assert row['id'] in markdown and row['title'] in markdown
        assert row['id'] in docs_page and row['title'] in docs_page
        assert row['id'] in legacy_page and row['title'] in legacy_page
        assert row['signature'] in docs_page and row['signature'] in legacy_page
        assert 'spatially blocked HOLDOUT-DTI potential' in docs_page
        assert row['non_fault_mimic'] in docs_page and row['non_fault_mimic'] in legacy_page
    for page in (markdown, docs_page, legacy_page, home_page):
        assert 'UNASSIGNED' in page
        assert 'provisional lane' not in page.lower()
    assert 'no experiment or slot is authorized' in home_page.lower()
    assert load('docs/data/research_hypotheses.json') == data
    assert load('site/data/research_hypotheses.json') == data


def test_score_sources_and_freshness_are_not_claimed_as_current_receipts():
    ledger = load('docs/data/leaderboard.json')
    assert ledger['status'] == 'stale'
    assert ledger['top_public_dti'] == 0.4437
    assert ledger['captured_utc'] == '2026-10-26T21:55:19Z'
    assert 'not a live value' in ledger['note'].lower()
    legacy_feed = load('site/data/leaderboard.json')
    assert 'NOT A SUBMISSION RECEIPT' in legacy_feed['leaderboard']['evidence']
    findings = (ROOT / 'research/findings.md').read_text()
    for value in ('0.3195', '0.4413', '0.4437', '0.2778'):
        assert value in findings
    assert 'USER-SUPPLIED' in findings and 'ORGANIZER-PUBLISHED PUBLIC-LEADERBOARD SNAPSHOT' in findings
    assert 'No current leaderboard value was independently verified' in findings
    assert '0.3195' in (ROOT / 'site/index.html').read_text()
    assert '0.4413' in (ROOT / 'docs/index.html').read_text()


def test_run_card_does_not_misrepresent_a_proposal_as_an_experiment():
    card = load('evidence/run_card.json')
    assert card['lane_status'].startswith('UNASSIGNED')
    assert card['hypothesis'].startswith('No experiment hypothesis was assigned')
    assert card['verdict'] == 'negative'
    assert card['experiment_count'] == 0
    assert card['holdout']['dti'] is None and card['holdout']['ci95'] is None
    assert card['raster_sha256'] is None
    assert card['submission_name'] is None and card['submission_note'] is None
    assert card['ok_to_submit'] is False and card['ok_to_download_new_tif'] is False
