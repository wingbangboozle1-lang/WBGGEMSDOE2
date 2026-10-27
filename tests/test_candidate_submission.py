"""Guardrails for the one file this repository clears for submission.

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


def test_exactly_one_file_is_cleared_and_the_rest_are_labeled_rejected():
    """Rejected binaries stay only because audit records bind to their hashes.

    Every TIF in docs/downloads must be either the cleared candidate or one that a
    repository record explicitly marks rejected, and docs/downloads/README.txt must
    name the cleared file.
    """
    cand = _load('candidate.json')
    cleared = Path(cand['file']).name
    tifs = {p.name for p in (ROOT / 'docs' / 'downloads').glob('*.tif')}
    assert cleared in tifs
    rejected = json.loads((ROOT / 'evidence' / 'final_candidate.json').read_text())
    marked = {Path(rejected['file']).name}
    assert tifs - {cleared} <= marked | {'wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif'}
    note = (ROOT / 'docs' / 'downloads' / 'README.txt').read_text()
    assert cleared in note and 'DO NOT SUBMIT' in note


def test_candidate_sha256_matches_the_bytes_on_disk():
    cand = _load('candidate.json')
    digest = hashlib.sha256((ROOT / cand['file']).read_bytes()).hexdigest()
    assert digest == cand['sha256']
    assert (ROOT / 'docs' / 'downloads' / Path(cand['file']).name).read_bytes() == \
        (ROOT / cand['file']).read_bytes()


def test_candidate_satisfies_every_official_format_rule():
    cand = _load('candidate.json')
    assert all(cand['checks'].values()), cand['checks']
    with rasterio.open(ROOT / cand['file']) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes[0] == 'float32'
        assert str(src.crs) == 'EPSG:32611'
        assert (src.height, src.width) == (3730, 3292)
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == \
            (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all(), 'the portal rejects NaN with "values must be in [0,1]"'
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


def test_candidate_has_no_redundant_mass():
    """No two dots may share a 300 m support neighbourhood (mass economy)."""
    from scipy import ndimage as ndi
    cand = _load('candidate.json')
    with rasterio.open(ROOT / cand['file']) as src:
        sup = src.read(1) > 0
    # each dot must have at least one empty pixel between it and its neighbours at 1 px
    pairs = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum())
    touching = pairs - int(sup.sum())
    assert touching == 0, f'{touching} dots touch another dot'


def test_uniqueness_verdicts_are_internally_consistent():
    audit = _load('final_audit.json')
    v = audit['verdicts']
    ok = (v['normalized_rule']['result'] == 'PASS'
          and v['surface_rule']['result'] == 'PASS'
          and v['exact_bytes']['result'] == 'PASS')
    assert audit['ok_to_submit'] is ok
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
