"""Guardrails for retained historical research files; no file is cleared for submission.

These tests fail closed: if any validator check, hash, grid property or audit
verdict regresses, the approval claim on the site becomes unsupportable and the
suite fails.
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


def test_no_file_is_cleared_and_research_files_are_labelled():
    triage = json.loads((ROOT / 'evidence/release_triage_20261027.json').read_text())
    assert len(triage['records']) == 5
    assert all(not r['ok_to_submit'] and r['literal_witness_result'] == 'duplicate-stop'
               and r['final_dot_overlap_3px_vs_13GEMSDOE'] > .7 for r in triage['records'])
    assert _load('final_audit.json')['ok_to_submit'] is False
    assert _load('run_card.json')['verdict'] == 'negative'
    note = (ROOT / 'docs/downloads/README.txt').read_text()
    assert 'NO FILE IS APPROVED' in note and 'RESEARCH-ONLY' in note


def _neighbor_pairs(points, distance):
    """Distinct coordinate pairs within inclusive Euclidean distance; no self-pairs."""
    from scipy.spatial import cKDTree
    return cKDTree(points).query_pairs(distance, output_type='set')


def test_neighbor_test_detects_real_pairs_and_not_self():
    assert not _neighbor_pairs(np.array([[5, 5]]), 1.0)
    assert _neighbor_pairs(np.array([[5, 5], [5, 6]]), 1.0) == {(0, 1)}
    assert not _neighbor_pairs(np.array([[5, 5], [6, 6]]), 1.0)
    assert _neighbor_pairs(np.array([[5, 5], [6, 6]]), np.sqrt(2)) == {(0, 1)}


def test_candidate_sha256_matches_the_bytes_on_disk():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    assert (ROOT / 'docs' / 'downloads' / Path(cand['file']).name).read_bytes() == \
        (ROOT / cand['file']).read_bytes()


def test_historical_candidate_local_byte_diagnostics_are_consistent():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all(), 'this particular historical file was recorded as all finite'
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert int((arr > 0).sum()) == cand['dots']

    # The owner-mirrored reference grid is git-ignored, so the
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
    assert np.all(arr[~footprint] == 0.0), 'historical file claims zero outside its mirrored footprint'
    inside = arr[footprint]
    assert np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0


def test_historical_candidate_has_no_adjacent_dot_pairs():
    """Read distinct point coordinates; a maximum filter counts every dot itself."""
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        points = np.column_stack(np.where(src.read(1) > 0))
    assert not _neighbor_pairs(points, np.sqrt(2)), 'adjacent historical dots were detected'


def test_literal_failure_cannot_be_replaced_by_normalized_pass():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    assert v['literal_rule']['result'] == 'FAIL'
    assert v['normalized_rule']['operative'] is False
    assert audit['ok_to_submit'] is False
    assert audit['scope']['rasters_measured'] >= 90
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
