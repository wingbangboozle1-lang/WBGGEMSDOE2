import numpy as np
from audit_candidate import stage


def test_witness_stops_before_rank_and_before_final():
    fp = np.ones((9, 9), bool)
    raster = np.zeros((9, 9))
    raster[4, 4] = 1
    dots = np.zeros_like(fp)
    dots[4, 4] = True
    # Constant surface would have undefined rank: witness stops earlier.
    result = stage(np.zeros((9, 9)), dots, fp, [('lattice', raster)])
    assert result['status'] == 'duplicate-stop'
    assert result['witness'] == 'lattice'
    assert result['overlap_3px'] == 1 and result['spearman'] is None


def test_continuous_positive_prior_blocks_even_one_preview_dot():
    from audit_candidate import stage
    fp = np.ones((7, 7), dtype=bool)
    candidate = np.zeros((7, 7), dtype=float); candidate[3, 3] = .5
    dots = candidate > 0
    prior = np.full((7, 7), .01)
    result = stage(candidate, dots, fp, [('continuous_prior', prior)])
    assert result['status'] == 'duplicate-stop'
    assert result['witness'] == 'continuous_prior' and result['overlap_3px'] == 1


def test_surface_preflight_stops_before_opening_preview_or_later_witnesses(tmp_path, monkeypatch):
    import json
    import rasterio
    from rasterio.transform import from_origin
    from audit_candidate import run
    shape = (9, 9)
    profile = dict(driver='GTiff', width=9, height=9, count=1, dtype='float32',
                   crs='EPSG:32611', transform=from_origin(0, 900, 100, 100))
    def write(path, arr):
        path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(path, 'w', **profile) as dst:
            dst.write(arr.astype('float32'), 1)
    ref = tmp_path / 'ref.tif'
    surface = tmp_path / 'surface.tif'
    registry = tmp_path / 'registry/13GEMSDOE.tif'
    write(ref, np.zeros(shape))
    write(surface, np.full(shape, .2))
    write(registry, np.ones(shape))
    manifest = tmp_path / 'registry.json'
    # The second witness is intentionally missing; a decisive first witness
    # should stop without reading it, the preview, or the final candidate.
    entry = lambda ident: {'id': ident, 'bytes': 1, 'sha256': 'a'*64, 'git_blob': 'b'*40}
    manifest.write_text(json.dumps({'inputs': [entry('later'), entry('13GEMSDOE')]}))
    monkeypatch.setattr('audit_candidate.verified', lambda path, *a, **kw: path == registry)
    report = run(surface, tmp_path/'missing-preview.tif', tmp_path/'missing-final.tif',
                 ref, manifest, tmp_path)
    assert report['pre_placement']['status'] == 'duplicate-stop'
    assert report['pre_placement']['phase'] == 'surface-before-placement'
    assert report['pre_placement']['witness'] == '13GEMSDOE'
    assert report['pre_placement']['overlap_3px'] == 1.0
    assert report['preview']['status'] == report['final']['status'] == 'not-run'
    assert report['preview_sha256'] is None and not report['ok_to_submit']


def test_stage_fails_closed_for_nonfinite_and_empty_surface():
    import pytest
    fp = np.ones((4, 4), bool)
    dots = np.zeros((4, 4), bool)
    with pytest.raises(ValueError, match='nonempty'):
        stage(np.ones((4, 4)), dots, fp, [])
    dots[0, 0] = True
    a = np.ones((4, 4)); a[2, 2] = np.nan
    with pytest.raises(ValueError, match='finite'):
        stage(a, dots, fp, [])
