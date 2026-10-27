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


def test_b2_score_explainer_separates_lineage_from_claims_and_keeps_stop():
    html = (ROOT / 'docs/research/why-b2-scored-2778.html').read_text()
    markdown = (ROOT / 'docs/research/why-b2-scored-2778.md').read_text()
    archive = (ROOT / 'docs/research/hypotheses_v2.md').read_text()
    assert 'USER-REPORTED historical claim' in html
    assert 'not a per-file receipt' in html
    assert 'No defensible score estimate' in html
    assert 'DO NOT SUBMIT' in html and 'UNASSIGNED' in html
    assert 'new expert truth can be within 300 m' in html
    assert 'no surrounding buffer' in html
    assert 'the method lane remains unassigned' in markdown.lower()
    assert 'P1 is not nominated or authorized' in markdown
    assert 'H1 is not nominated or authorized' in archive
    assert 'no next experiment or slot is selected' in archive.lower()


def test_score_sources_and_freshness_are_not_claimed_as_current_receipts():
    ledger = load('docs/data/leaderboard.json')
    assert ledger['status'] in ('fresh', 'stale')
    assert ledger['evidence_class'] == 'OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT'
    assert 0 <= ledger['top_public_dti'] <= 1 and ledger['captured_utc']
    if ledger['status'] == 'stale':
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
    assert card['hypothesis'].startswith('No experimental method was assigned')
    assert card['verdict'] == 'negative'
    assert card['experiment_count'] == 0
    assert card['holdout']['dti'] is None and card['holdout']['ci95'] is None
    assert card['raster_sha256'] is None
    assert card['submission_name'] is None and card['submission_note'] is None
    assert card['ok_to_submit'] is False and card['ok_to_download_new_tif'] is False


def test_pinned_readme_review_preserves_scope_and_corrects_prior_work():
    receipt = load('evidence/focus_readme_review_20261027.json')
    freshness = load('docs/data/focus-freshness.json')
    assert len(receipt['sites']) == 9
    assert {item['site'] for item in receipt['sites']} == {item['site'] for item in freshness['sites']}
    for item in receipt['sites']:
        assert len(item['commit_sha']) == 40
        int(item['commit_sha'], 16)
        assert item['commit_sha'] in item['readme_url']
        assert len(item['readme_sha256']) == 64
        int(item['readme_sha256'], 16)
    assert 'not a new TIFF byte audit' in receipt['scope']
    assert load('docs/data/focus_readme_review_20261027.json') == receipt
    assert load('site/data/focus_readme_review_20261027.json') == receipt
    notes = (ROOT / 'research/focus-head-readme-review-20261027.md').read_text()
    assert '0.1647' in notes and '0.2314' in notes
    assert 'phase congruency' in notes and 'not independently reproduced' in notes
    assert 'README-only recheck' in (ROOT / 'docs/index.html').read_text()
    titles = [row['title'].lower() for row in load('config/research_hypotheses.json')['hypotheses']]
    assert all('phase-congruen' not in title and 'radiometric compositional' not in title for title in titles)


def test_msptcd_published_values_match_source_record_without_implying_replay():
    raw = load('evidence/wbg2_msptcd_results.json')
    canaries = load('evidence/wbg2_msptcd_canaries.json')
    findings = (ROOT / 'research/msptcd_findings.md').read_text()
    page = (ROOT / 'docs/msptcd/index.html').read_text()
    assert 'not independently reproduced' in findings and 'not independently reproduced' in page
    for arm in raw['holdout_pooled']['scores'].values():
        values = [arm['dti'], *arm['ci95']]
        for value in values:
            assert f'{value:.6f}' in findings
            assert f'{value:.6f}' in page
        assert arm['withheld_positive_pixels'] == 60988
        assert arm['evaluator_version'] == 'gems57-pooled-hide-v2'
    delta = raw['paired_vs_ctrl_19b']['exp3_msptcd_submod_greedy']
    for value in [delta['delta'], *delta['ci95']]:
        assert f'{value:.6f}' in findings
    assert canaries['features_tested'] * canaries['folds_tested'] == canaries['total_checks'] == 124
    assert f"{canaries['max_two_sided_auc']:.4f}" in findings
