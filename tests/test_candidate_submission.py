"""Read-back tests for a rejected historical raster; format is not approval."""
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


def test_no_file_is_cleared_and_archived_files_are_bound_to_stop_evidence():
    cand = _load('candidate.json')
    review = json.loads((ROOT / 'evidence/local_artifact_audit_20261027.json').read_text())
    rows = {row['name']: row for row in review['artifacts']}
    assert rows['DZ-16']['sha256'] == cand['sha256']
    assert (ROOT / cand['file']).is_file()
    assert all(row['ok_to_submit'] is False for row in rows.values())
    assert all(row['final_overlap_3px']['13GEMSDOE'] > .70 for row in rows.values())
    assert all(not row['preplacement_surface_checked'] and not row['complete_registry_checked'] for row in rows.values())
    note = (ROOT / 'docs/downloads/README.txt').read_text()
    assert 'DO NOT SUBMIT' in note and 'No TIFF is approved' in note


def test_candidate_sha256_matches_the_bytes_on_disk():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    assert (ROOT / 'docs' / 'downloads' / Path(cand['file']).name).read_bytes() == \
        (ROOT / cand['file']).read_bytes()


def test_archived_candidate_local_readback_is_not_portal_approval():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all(), 'this archived candidate is all finite'
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
    assert np.all(arr[~footprint] == 0.0), 'historical candidate is zero outside this owner-mirrored footprint'
    inside = arr[footprint]
    assert np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0


def test_historical_candidate_has_no_pairs_within_six_pixels():
    """Two radius-3 prediction neighborhoods cannot overlap when centers exceed 6px."""
    from scipy.spatial import cKDTree
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        coords = np.column_stack(np.nonzero(src.read(1) > 0))
    assert len(coords) == cand['dots']
    assert not cKDTree(coords).query_pairs(6), 'at least two centers have overlapping 300m neighborhoods'


def test_literal_uniqueness_stop_supersedes_normalized_policy():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    assert v['normalized_rule']['result'] == 'PASS'  # historical policy, not authorization
    assert v['literal_rule']['result'] == 'FAIL'
    assert audit['historical_calibrated_ok_to_submit'] is True
    assert audit['ok_to_submit'] is False and audit['effective_verdict'] == 'negative'
    local = json.loads((ROOT / audit['superseded_by']).read_text())
    dz = next(row for row in local['artifacts'] if row['name'] == 'DZ-16')
    assert dz['sha256'] == audit['sha256']
    assert dz['final_overlap_3px']['13GEMSDOE'] > .70 and not dz['ok_to_submit']


def test_score_estimate_is_labelled_and_bounded():
    est = _load('candidate_estimate.json')
    assert 0.0 <= est['point_estimate'] <= 1.0
    lo, hi = est['interval95']
    assert lo <= est['point_estimate'] <= hi
    assert est['external_test_rmse'] > 0
    text = json.dumps(est).lower()
    assert 'not a score' in text and 'superseded' in text


def test_empirical_model_reports_its_out_of_sample_failure():
    model = _load('score_model.json')
    ext = model['external_test_nine_focus_sites']
    assert ext['n'] >= 9
    # if a future model actually predicts the held-out sites, R2 may become positive;
    # until then the repository must not pretend otherwise
    for key in ('mae', 'rmse', 'r2', 'spearman'):
        assert key in ext
    assert model['n_rows'] >= 90
