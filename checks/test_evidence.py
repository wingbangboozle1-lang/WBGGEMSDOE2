import csv
from html.parser import HTMLParser
import hashlib
import json
import pytest
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


def test_site_links_and_fail_closed_copy():
    for f in (ROOT/'docs').glob('*.html'):
        html=f.read_text(); parser=LinkParser(); parser.feed(html)
        assert len(parser.ids)==len(set(parser.ids))
        for link in parser.links:
            if link.startswith(('https://','http://','mailto:','#')): continue
            target=link.split('#',1)[0].split('?',1)[0]
            if target:
                assert (f.parent/target).exists(), (f,link)
    # The four generated dashboard pages must still carry the prior-lane negative
    # banner: a cleared candidate in one lane does not retroactively approve the
    # two rejected parallel research files.
    for name in ('index.html','executive-summary.html','research.html','sources.html'):
        html=(ROOT/'docs'/name).read_text()
        assert 'No <em>prior</em> lane file is approved for submission.' in html, name
        assert 'No submission file' in html, name
    assert 'USER-REPORTED' in (ROOT/'docs/index.html').read_text()


def test_submission_desk_is_byte_bound_and_label_honest():
    """The download button may only be green if the committed bytes agree."""
    card=json.loads((ROOT/'docs/data/run-card-lane-b.json').read_text())
    tif=ROOT/card['raster_path']
    assert tif.is_file(), card['raster_path']
    assert hashlib.sha256(tif.read_bytes()).hexdigest()==card['raster_sha256']
    assert tif.stat().st_size==card['raster_bytes']
    assert card['ok_to_download'] is True and card['ok_to_submit_format'] is True
    assert card['beats_incumbent_demonstrated'] is False
    assert card['weekly_submission_slots_used']==0
    assert card['verdict'].startswith('PROMOTE-FOR-FORMAT-AND-UNIQUENESS / SCORE-UNPROVEN')
    uniq=card['uniqueness']
    assert uniq['stops']==[] and uniq['unique_within_registered_scope'] is True
    assert uniq['max_measured_overlap_discriminating']<=uniq['literal_limit']
    assert uniq['max_abs_spearman']<=uniq['correlation_limit']
    strict=card['validator']['strict_all_finite']
    assert strict['format_valid_against_reference'] is True and strict['all_finite'] is True
    assert 0.0<=strict['minimum_inside'] and strict['maximum_inside']<=1.0
    assert strict['nonzero_inside']==card['emission']['emitted']
    assert all(card['validator']['shared_local_checks'].values())
    assert len(card['submission_note'])<=140 and len(card['submission_name'])<=140
    # A projection is never written as a score, and the parity scenario must
    # reproduce the reported value it was derived from.
    proj=card['projection']
    assert 'PROJECTION' in proj['evidence_class'] and 'NOT A SCORE' in proj['evidence_class']
    assert proj['floor']<proj['parity']
    assert abs(proj['derived']['selfcheck_reproduces_reported']-0.2778)<=1e-3
    page=(ROOT/'docs/submit.html').read_text()
    assert 'never a score' in page and 'CALIBRATED PROJECTION' in page
    assert tif.name in page
    assert card['raster_sha256'] in page
    home=(ROOT/'docs/index.html').read_text()
    assert 'OK to download and submit' in home and tif.name in home
    assert 'a projection, never a score' in home


def test_instrument_inversion_is_published_not_buried():
    """The negative result that invalidates cross-family holdout claims stays visible."""
    calib=json.loads((ROOT/'evidence/holdout_calibration.json').read_text())
    inst=calib['instruments']
    assert inst['shared-buffered']['spearman_holdout_vs_reported'] < -0.5
    assert all(v['spearman_holdout_vs_reported'] < 0 for v in inst.values())
    assert 'GEMSDOE32' in calib['decisive_counterexample']
    card=json.loads((ROOT/'docs/data/run-card-lane-b.json').read_text())
    assert card['instrument_validity']['evidence_class']=='MEASURED NEGATIVE RESULT'
    assert card['instrument_validity']['spearman']['shared-buffered'] < -0.5
    assert 'withdrawn' in card['instrument_validity']['consequence']
    assert 'inversion finding' in (ROOT/'docs/submit.html').read_text()


@pytest.mark.skipif(not (ROOT/'data/lane/final_receipt.json').is_file(),
                    reason='lane artefacts are gitignored; needs a prepared workspace')
def test_release_builder_fails_closed(monkeypatch, tmp_path):
    import argparse, importlib.util
    spec=importlib.util.spec_from_file_location(
        'blr', ROOT/'scripts/build_lane_b_release.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    real=mod.load
    args=argparse.Namespace(budget=38000, collar_px=2,
                            page=tmp_path/'s.html', card=tmp_path/'c.json')
    for field, value in (('sha256','0'*64), ('bytes', 1)):
        def bad(rel, field=field, value=value):
            d=real(rel)
            if rel=='data/lane/final_receipt.json':
                d=dict(d); d[field]=value
            return d
        monkeypatch.setattr(mod,'load',bad)
        with pytest.raises(SystemExit):
            mod.build_release(args)
    monkeypatch.setattr(mod,'load',real)
    assert not (tmp_path/'s.html').exists()
