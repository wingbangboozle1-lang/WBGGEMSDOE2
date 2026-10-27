import csv
from html.parser import HTMLParser
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation
import audit_portfolio

ROOT = Path(__file__).resolve().parents[1]
PORT = json.loads((ROOT/'docs/data/portfolio.json').read_text())


def test_euclidean_radius_includes_3px_not_diagonal_3_3():
    kernel = audit_portfolio.disk(3)
    assert kernel[3,6] and kernel[6,3] and not kernel[6,6]
    assert int(kernel.sum()) == 29


def test_counting_bound_for_example_budget_only():
    witness = PORT['literal_registry_witness']
    assert witness['footprint_pixels'] == witness['within_3px_pixels'] + witness['outside_3px_pixels']
    n = witness['example_budget_distinct_dots']; outside = witness['outside_3px_pixels']
    assert np.isclose(witness['minimum_possible_overlap_at_example_budget'], max(0,n-outside)/n)
    assert witness['minimum_possible_overlap_at_example_budget'] > 0.7
    # A sufficiently small support could sit outside the binary-lattice halo.
    assert max(0, 1-outside) / 1 == 0


def test_priority_scores_are_labeled_and_all_nine_have_a_witness():
    expected = {'GEMSDOE24','GEMSDOE25','GEMSDOE27','GEMSDOE28','GEMSDOE30','GEMSDOE31','GEMSDOE32','GEMSDOE33','GEMSDOE36'}
    rows = PORT['sites']
    assert {r['site'] for r in rows} == expected
    for r in rows:
        assert 'USER-REPORTED' in r['score_evidence']
        assert r['max_3px_overlap_vs_other_focus'] > 0.7
        assert r['max_overlap_witness_site'] != r['site']
        assert not r['eligible_for_submission'] and r['estimated_leaderboard_score'] is None
        assert np.isclose(PORT['pairwise_overlap'][r['site']][r['max_overlap_witness_site']], r['max_3px_overlap_vs_other_focus'])


def test_decoded_identity_and_b2_forensic_evidence():
    rows = {r['site']:r for r in PORT['sites']}
    assert rows['GEMSDOE25']['decoded_prediction_sha256'] == rows['GEMSDOE30']['decoded_prediction_sha256']
    assert rows['GEMSDOE25']['sha256'] != rows['GEMSDOE30']['sha256']
    b2=PORT['champion_lineage']
    assert b2['b2_equals_d28_excluding_cat_distance_lte_2_pixels']
    assert b2['d28_pixels'] - b2['d28_pixels_removed'] == b2['b2_pixels']
    assert b2['b2_pixels_not_in_d28'] == 0


def test_dense_witness_is_a_continuous_prior_and_scope_is_disclosed():
    r=PORT['dense_probability_witness']
    assert r['uncovered_allowed_pixels'] == 0 and r['universal_overlap_blocker']
    assert 'Continuous' in r['definition_caveat']
    assert not PORT['preplacement_surfaces_replayed']
    assert 'not a current exhaustive' in PORT['audited_scope']


def test_run_card_never_invents_a_candidate_or_result():
    card=json.loads((ROOT/'docs/data/run-card.json').read_text())
    assert card['verdict']=='negative' and not card['ok_to_submit']
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['holdout_dti']['status']=='NOT RUN' and card['holdout_dti']['value'] is None
    assert card['holdout_dti']['withheld_positives'] is None and card['holdout_dti']['ci95'] is None
    assert card['registry']['final_dot_overlap'] is None and not card['registry']['all_current_registry_rasters_checked']
    assert card['experiment_count']==0 and card['weekly_submission_slots_used']==0


def test_broad_ledger_has_provenance_and_empty_values_not_zeroed():
    with (ROOT/'docs/data/user-reported-ledger.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert len(rows) == 126
    assert all(r['evidence_class'].startswith('USER-REPORTED') for r in rows)
    assert any(r['site']=='GEMSDOE88' and not r['reported_public_dti'] for r in rows)


class LinkParser(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.ids=[]; self.tables=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if 'id' in a: self.ids.append(a['id'])
        if tag=='table': self.tables+=1


def test_site_links_and_current_disposition_are_fail_closed():
    """Old positive candidate evidence must never create a current download CTA."""
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['ok_to_download_new_tif'] is False and card['raster_sha256'] is None
    index = (ROOT / 'docs' / 'submission' / 'index.html').read_text()
    assert 'DO NOT SUBMIT' in index and 'Research archive' in index
    assert 'No candidate is cleared' in index
    parser = LinkParser(); parser.feed(index)
    assert not any(link.split('?', 1)[0].split('#', 1)[0].lower().endswith(('.tif', '.zip'))
                   for link in parser.links)
    dashboard = (ROOT / 'docs' / 'index.html').read_text()
    assert 'DO NOT SUBMIT' in dashboard and 'no candidate is cleared for download' in dashboard.lower()
    assert 'Download the submission GeoTIFF' not in dashboard
    submit = (ROOT / 'docs' / 'submit' / 'index.html').read_text()
    assert 'DO NOT SUBMIT' in submit and 'No GeoTIFF is approved' in submit
    assert '.tif' not in submit.lower() and '.zip' not in submit.lower()
    archive = (ROOT / 'docs' / 'downloads' / 'README.txt').read_text()
    assert 'DO NOT SUBMIT ANY FILE' in archive
    page_files = (list((ROOT / 'docs').glob('*.html'))
                  + list((ROOT / 'docs/submission').rglob('*.html'))
                  + list((ROOT / 'docs/submit').rglob('*.html')))
    for f in page_files:
        html = f.read_text(); parser = LinkParser(); parser.feed(html)
        assert len(parser.ids) == len(set(parser.ids)), f
        for link in parser.links:
            if link.startswith(('https://', 'http://', 'mailto:', '#')):
                continue
            target = link.split('#', 1)[0].split('?', 1)[0]
            if target:
                assert (f.parent / target).exists(), (f, link)
    assert 'USER-REPORTED' in index
