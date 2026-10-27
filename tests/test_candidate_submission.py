"""Integrity checks for a historical DZ-16 artifact, never current approval.

The data_public/ files preserve an older candidate and calibrated-gate audit.
Their local byte checks remain useful provenance, but current authorization is
controlled by evidence/run_card.json plus a separate selector release.
"""
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


def test_archived_candidate_is_not_the_current_project_release():
    cand = _load('candidate.json')
    archived_card = _load('run_card.json')
    archived_audit = _load('final_audit.json')
    for record in (cand, archived_card, archived_audit):
        assert record['archive_status']['state'] == 'HISTORICAL_ONLY'
        assert record['archive_status']['current_project_authorization'] is False
        assert record['archive_status']['current_disposition'] == '../evidence/run_card.json'

    current = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert current['verdict'] == 'negative'
    assert current['ok_to_submit'] is False
    assert current['ok_to_download_new_tif'] is False
    assert current['raster_sha256'] is None
    assert current['submission_name'] is None
    assert current['submission_note'] is None
    assert not (ROOT / 'evidence/submission_release.json').exists()

    note = (ROOT / 'docs/downloads/README.txt').read_text()
    assert Path(cand['file']).name in note and 'DO NOT SUBMIT ANY FILE' in note
    assert 'historical' in note.lower() and 'literal uniqueness FAIL' in note


def test_historical_candidate_sha256_matches_archived_bytes():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    archived = ROOT / 'docs' / 'downloads' / Path(cand['file']).name
    assert archived.read_bytes() == (ROOT / cand['file']).read_bytes()


def test_historical_local_format_receipt_is_not_release_authorization():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all()
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert int((arr > 0).sum()) == cand['dots']
    assert _load('run_card.json')['archive_status']['current_project_authorization'] is False

    # The mirrored sample grid is ignored, not an authenticated organizer copy.
    template = ROOT / 'data_public' / 'official' / 'sample_submission.tif'
    if template.exists():
        with rasterio.open(template) as src:
            sub = src.read(1)
            footprint = np.isfinite(sub) & (sub != src.nodata)
        assert np.all(arr[~footprint] == 0.0)
        inside = arr[footprint]
        assert np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0


def test_historical_candidate_geometry_has_no_touching_dots():
    """Keep a geometric integrity check; it makes no scientific claim."""
    from scipy import ndimage as ndi
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        sup = src.read(1) > 0
    pairs = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum())
    assert pairs - int(sup.sum()) == 0


def test_historical_calibrated_audit_is_not_current_literal_uniqueness_clearance():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    local_calibrated_pass = (v['normalized_rule']['result'] == 'PASS'
                             and v['surface_rule']['result'] == 'PASS'
                             and v['exact_bytes']['result'] == 'PASS')
    assert audit['ok_to_submit'] is local_calibrated_pass  # historical lane rules only
    assert audit['archive_status']['current_project_authorization'] is False
    assert v['literal_rule']['result'] == 'FAIL'
    assert audit['scope']['rasters_measured'] >= 90
    assert audit['focus_overlap_summary']['max'] < 0.70
    assert 'focus_pairwise_overlap' in audit
    current = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert current['ok_to_submit'] is False


def test_historical_estimate_is_bounded_and_labelled_not_a_current_forecast():
    est = _load('candidate_estimate.json')
    assert 0.0 <= est['point_estimate'] <= 1.0
    lo, hi = est['interval95']
    assert lo <= est['point_estimate'] <= hi
    assert est['external_test_rmse'] > 0
    assert 'not' in json.dumps(est).lower() and 'estimate' in json.dumps(est).lower()


def test_historical_empirical_model_preserves_its_out_of_sample_failure():
    model = _load('score_model.json')
    ext = model['external_test_nine_focus_sites']
    assert ext['n'] >= 9
    for key in ('mae', 'rmse', 'r2', 'spearman'):
        assert key in ext
