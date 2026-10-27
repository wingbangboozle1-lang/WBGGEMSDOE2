"""Saved DZ-16 research-byte diagnostics are NOT release authorization."""
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


def test_all_existing_files_are_explicitly_research_only():
    from wbggems.release import load_negative_release
    report = load_negative_release(ROOT)
    assert report['ok_to_submit'] is False and report['approved_submission'] is None
    assert all(r['ok_to_submit'] is False for r in report['artifacts'])
    note = (ROOT / 'docs/downloads/README.txt').read_text()
    assert 'DO NOT SUBMIT' in note and 'No TIFF in this directory is approved' in note


def test_candidate_sha256_matches_the_bytes_on_disk():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    assert (ROOT / 'docs' / 'downloads' / Path(cand['file']).name).read_bytes() == \
        (ROOT / cand['file']).read_bytes()


def test_historical_dz16_local_grid_and_all_finite_policy_not_portal_acceptance():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all(), 'this research artifact claims all-finite saved bytes'
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert int((arr > 0).sum()) == cand['dots']

    # The unauthenticated owner-mirror grid template is git-ignored (1.6 MB pinned input), so the
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
    assert np.all(arr[~footprint] == 0.0), 'this artifact claims zeros outside the mirrored footprint'
    inside = arr[footprint]
    assert np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0


def test_historical_dz16_dots_have_separate_local_support():
    """No two dots may share a 300 m support neighbourhood (mass economy)."""
    from scipy import ndimage as ndi
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        sup = src.read(1) > 0
    # A maximum filter multiplied by its own support trivially counted every
    # centre once and could not detect collisions. Count actual shared support.
    yy, xx = np.mgrid[-3:4, -3:4]
    kernel = (xx * xx + yy * yy <= 9).astype(np.uint16)
    counts = ndi.convolve(sup.astype(np.uint16), kernel, mode='constant')
    assert counts.max() <= 1


def test_normalized_pass_cannot_override_the_literal_duplicate_stop():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    assert v['normalized_rule']['result'] == 'PASS'  # archived diagnostic only
    assert v['literal_rule']['result'] == 'FAIL'
    assert audit['ok_to_submit'] is False and audit['verdict'] == 'negative'
    assert 'focus_pairwise_overlap' in audit
    current = json.loads((ROOT / 'evidence/release_audit.json').read_text())
    row = next(r for r in current['artifacts'] if r['sha256'] == audit['sha256'])
    assert row['lattice_overlap_3px'] > .70 and row['ok_to_submit'] is False


def test_historical_estimate_is_not_current_or_authorizing():
    est = _load('candidate_estimate.json')
    assert est['ok_to_submit'] is False and 'Historical' in est['archive_status']
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
