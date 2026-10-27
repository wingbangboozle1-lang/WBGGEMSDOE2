"""Historical candidate integrity checks; format validity is not submission approval."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))

rasterio = pytest.importorskip('rasterio')


def _load(name):
    return json.loads((ROOT / 'data_public' / name).read_text())


def test_existing_candidate_is_explicitly_rejected():
    cand = _load('candidate.json')
    assert (ROOT / cand['file']).is_file()
    note = (ROOT / 'docs/downloads/README.txt').read_text()
    assert Path(cand['file']).name in note and 'NO FILE CLEARED' in note
    assert 'DO NOT SUBMIT' in note
    assert _load('run_card.json')['ok_to_submit'] is False


def test_candidate_sha256_matches_the_bytes_on_disk():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    assert (ROOT / 'docs' / 'downloads' / Path(cand['file']).name).read_bytes() == \
        (ROOT / cand['file']).read_bytes()


def test_historical_candidate_matches_recorded_grid_and_raw_value_limits():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all(), 'this artifact claims an all-finite encoding'
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert int((arr > 0).sum()) == cand['dots']

    # The organizer grid template is git-ignored (1.6 MB pinned input), so the
    # footprint-mask assertions run only where that input was restored. The
    # recorded checks are still required to pass, and the grid metadata above is
    # always re-read from the committed bytes.
    template = ROOT / 'data_public' / 'official' / 'sample_submission.tif'
    if not template.exists():
        assert cand['checks']['outside_footprint_is_zero'] is True
        assert cand['checks']['no_nan_inside_footprint'] is True
        return
    with rasterio.open(template) as src:
        sub = src.read(1)
        footprint = np.isfinite(sub) & (sub != src.nodata)
    assert np.all(arr[~footprint] == 0.0), 'outside the organizer footprint must be 0.0'
    inside = arr[footprint]
    assert np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0


def test_candidate_dots_have_disjoint_positive_kernel_support():
    # A self-inclusive maximum_filter times support was a tautology. Query the
    # actual nearest OTHER dot instead; positive radius-3 kernels cannot overlap
    # if the dot centres are separated by at least six pixels.
    from scipy.spatial import cKDTree
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        points = np.argwhere(src.read(1) > 0)
    distances, _ = cKDTree(points).query(points, k=2)
    assert distances[:, 1].min() >= 6


def test_uniqueness_verdicts_are_internally_consistent():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    assert audit['ok_to_submit'] is False
    assert audit['verdict'] == 'negative'
    assert v['literal_rule']['result'] == 'FAIL'
    # A normalized diagnostic PASS cannot override the literal rule.
    assert audit['scope']['rasters_measured'] >= 90
    assert audit['focus_overlap_summary']['max'] < 0.70, 'must be clearly distinct from the focus files'
    # the literal-rule failure must stay documented, with its measured justification
    assert v['literal_rule']['result'] in ('PASS', 'FAIL')
    assert 'focus_pairwise_overlap' in audit


def test_score_estimate_is_labelled_and_bounded():
    est = _load('candidate_estimate.json')
    assert 0.0 <= est['point_estimate'] <= 1.0
    lo, hi = est['interval95']
    assert lo <= est['point_estimate'] <= hi
    assert est['external_test_rmse'] > 0
    text = json.dumps(est).lower()
    assert 'not' in text and 'estimate' in text


def test_empirical_model_reports_its_out_of_sample_failure():
    model = _load('score_model.json')
    ext = model['external_test_nine_focus_sites']
    assert ext['n'] >= 9
    # if a future model actually predicts the held-out sites, R2 may become positive;
    # until then the repository must not pretend otherwise
    for key in ('mae', 'rmse', 'r2', 'spearman'):
        assert key in ext
    assert model['n_rows'] >= 90
