import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from wbggems.validate import inspect_tif


def write(path, array, *, dtype='float32', x=10, count=1):
    with rasterio.open(path, 'w', driver='GTiff', width=4, height=3, count=count,
                       dtype=dtype, crs='EPSG:32611', transform=from_origin(x, 100, 100, 100),
                       nodata=np.nan if dtype == 'float32' else None) as out:
        for band in range(1, count + 1):
            out.write(array.astype(dtype), band)


@pytest.fixture
def reference(tmp_path):
    a = np.zeros((3, 4), np.float32)
    a[0, 0] = np.nan
    path = tmp_path / 'reference.tif'
    write(path, a)
    return path


def test_finite_and_nodata_exterior_are_explicit(reference, tmp_path):
    a = np.zeros((3, 4), np.float32)
    a[1, 1] = 1
    f = tmp_path / 'valid.tif'
    write(f, a)
    r = inspect_tif(f, reference, strict_all_finite=True)
    assert r['format_valid_against_reference'] and r['all_finite'] and not r['submission_approval']
    a[0, 0] = np.nan
    write(f, a)
    assert inspect_tif(f, reference)['format_valid_against_reference']
    assert not inspect_tif(f, reference, strict_all_finite=True)['format_valid_against_reference']


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -.1, 1.00001])
def test_reject_interior_bad_values_without_repair(reference, tmp_path, bad):
    a = np.zeros((3, 4), np.float32)
    a[1, 1] = bad
    f = tmp_path / 'bad.tif'
    write(f, a)
    r = inspect_tif(f, reference)
    assert not r['format_valid_against_reference'] and r['failures']
    with rasterio.open(f) as src:
        assert np.isnan(src.read(1)[1, 1]) if np.isnan(bad) else src.read(1)[1, 1] == pytest.approx(bad)


def test_reject_wrong_grid_dtype_multiband_and_exterior_positive(reference, tmp_path):
    f = tmp_path / 'bad.tif'
    a = np.zeros((3, 4), np.float32)
    write(f, a, x=20)
    assert not inspect_tif(f, reference)['grid_match_reference']
    write(f, a, dtype='uint8')
    assert not inspect_tif(f, reference)['format_valid_against_reference']
    write(f, a, count=2)
    assert not inspect_tif(f, reference)['format_valid_against_reference']
    a[0, 0] = .5
    write(f, a)
    assert 'positive value outside reference footprint' in inspect_tif(f, reference)['failures']


def test_reference_crs_and_resolution_are_not_assumed(tmp_path):
    bad_ref = tmp_path / 'wrong-reference.tif'
    candidate = tmp_path / 'candidate.tif'
    a = np.zeros((3, 4), np.float32)
    with rasterio.open(bad_ref, 'w', driver='GTiff', width=4, height=3, count=1,
                       dtype='float32', crs='EPSG:4326', transform=from_origin(10, 100, 100, 100)) as out:
        out.write(a, 1)
    write(candidate, a)
    with pytest.raises(ValueError, match='EPSG:32611'):
        inspect_tif(candidate, bad_ref)
    with rasterio.open(bad_ref, 'w', driver='GTiff', width=4, height=3, count=1,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(10, 100, 50, 50)) as out:
        out.write(a, 1)
    with pytest.raises(ValueError, match='100 m'):
        inspect_tif(candidate, bad_ref)


def test_nodata_flag_inside_is_not_a_valid_zero_prediction(reference, tmp_path):
    path = tmp_path / 'masked.tif'
    a = np.zeros((3, 4), np.float32)
    a[1, 1] = 1
    with rasterio.open(path, 'w', driver='GTiff', width=4, height=3, count=1,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(10, 100, 100, 100), nodata=0) as out:
        out.write(a, 1)
    result = inspect_tif(path, reference)
    assert result['masked_inside'] > 0
    assert 'reference-footprint cells are marked nodata/masked' in result['failures']
    assert not result['format_valid_against_reference']


def test_finite_reference_nodata_is_excluded_from_footprint(tmp_path):
    ref = tmp_path / 'ref-nodata.tif'
    f = tmp_path / 'candidate.tif'
    r = np.zeros((3, 4), np.float32)
    r[0, 0] = -9999
    with rasterio.open(ref, 'w', driver='GTiff', width=4, height=3, count=1,
                       dtype='float32', crs='EPSG:32611', transform=from_origin(10, 100, 100, 100), nodata=-9999) as out:
        out.write(r, 1)
    p = np.zeros((3, 4), np.float32)
    write(f, p)
    result = inspect_tif(f, ref)
    assert result['footprint_cells'] == 11 and result['format_valid_against_reference']
