import csv
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

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


def test_promoted_run_card_is_receipt_bound():
    card=json.loads((ROOT/'docs/data/run-card.json').read_text())
    campaign=json.loads((ROOT/'evidence/campaign_20261027.json').read_text())
    soft=json.loads((ROOT/'evidence/soft_novelty_refinement.json').read_text())
    unique=json.loads((ROOT/'evidence/final_uniqueness.json').read_text())
    fmt=json.loads((ROOT/'evidence/final_format.json').read_text())
    assert card['schema']=='wbggems.run-card.v2'
    assert card['verdict']=='promote-to-selector-only' and card['ok_to_submit'] is True
    assert card['raster_sha256']==campaign['tif_sha256']==unique['tif_sha256']==fmt['sha256']
    assert abs(card['holdout']['dti']-soft['best_passing']['dti'])<1e-12
    assert card['holdout']['withheld_positive_pixels']==soft['withheld_positive_pixels']==11321
    assert card['holdout']['ci95'][0] < card['holdout']['dti'] < card['holdout']['ci95'][1]
    assert card['holdout']['paired_delta_ci95'][0] > 0
    assert card['uniqueness']['candidate_final_overlap'] < .70
    assert card['uniqueness']['candidate_surface_correlation'] < .90
    assert card['uniqueness']['unique_vs_nine_focus'] and card['uniqueness']['literal_reading_fires']
    assert card['validator']['values_in_0_1'] and card['validator']['no_nan_inside_footprint']
    assert not card['feature_canary']['alarmed_features']
    assert card['experiment_budget']['experiments_run']==3
    assert card['weekly_submission_slots_used']==0
    assert len(card['note'])<=140 and len(card['submission_name'])<=140
    assert card['score_estimate']['leaderboard_estimate'] is None


def test_broad_ledger_has_provenance_and_empty_values_not_zeroed():
    with (ROOT/'docs/data/user-reported-ledger.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert len(rows) == 126
    assert all(r['evidence_class'].startswith('USER-REPORTED') for r in rows)
    assert any(r['site']=='GEMSDOE88' and not r['reported_public_dti'] for r in rows)


class LinkParser(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.ids=[]; self.tables=0; self.base=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='base' and a.get('href'): self.base=a['href']
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if 'id' in a: self.ids.append(a['id'])
        if tag=='table': self.tables+=1


def test_site_links_and_promoted_copy():
    # Only the four current dashboard entrypoints carry the current decision;
    # nested docs/research/ and docs/submission/ pages are historical snapshots.
    current = [ROOT/'docs'/n for n in ('index.html', 'executive-summary.html',
                                       'research.html', 'sources.html')]
    for f in current:
        html=f.read_text(); parser=LinkParser(); parser.feed(html)
        assert len(parser.ids)==len(set(parser.ids))
        assert 'OK TO DOWNLOAD AND SUBMIT' in html
        assert 'wbg2-blind-discontinuity-E3-soft88' in html
        for link in parser.links:
            if link.startswith(('https://', 'http://', 'mailto:', '#')):
                continue
            target = link.split('#', 1)[0].split('?', 1)[0]
            if target:
                assert (f.parent/target).exists(), (f,link)
    assert 'USER-REPORTED' in (ROOT/'docs/index.html').read_text()
    # "DO NOT SUBMIT" appears only as the explicit conditional for reviewers who
    # reject the documented two-reading policy; the primary decision stays green.
    assert 'If your reviewer requires literal compliance, DO NOT SUBMIT' in (ROOT/'docs/index.html').read_text()
