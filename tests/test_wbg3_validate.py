"""The shipped submission must keep passing the format gates it was built to pass."""
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data/official/sample_submission.tif"
RECEIPT = ROOT / "evidence/h3_submission.json"

pytestmark = pytest.mark.skipif(not RECEIPT.exists(),
                                reason="submission receipt not generated in this checkout")


@pytest.fixture(scope="module")
def receipt():
    return json.loads(RECEIPT.read_text())


def test_receipt_records_a_passing_validator(receipt):
    assert receipt["ok"] is True
    assert receipt["failures"] == []


def test_receipt_numbers_internally_consistent(receipt):
    assert receipt["nonfinite_inside_footprint"] == 0
    assert receipt["finite_outside_footprint"] == 0
    assert receipt["nan_outside_footprint"] == receipt["outside_footprint_cells"]
    assert receipt["finite_cells"] == receipt["reference_footprint_cells"]
    assert receipt["positive_cells"] == receipt["dots"]
    assert 0.0 <= receipt["min_inside"] <= receipt["max_inside"] <= 1.0
    assert len(receipt["note"]) <= 140


@pytest.mark.skipif(not SAMPLE.exists(), reason="pinned sample not restored")
def test_written_raster_matches_the_official_grid(receipt):
    path = ROOT / receipt["file"].replace(str(ROOT) + "/", "")
    if not path.exists():
        pytest.skip("submission raster not present in this checkout")
    with rasterio.open(path) as ds, rasterio.open(SAMPLE) as ref:
        assert ds.crs == ref.crs
        assert ds.shape == ref.shape
        assert ds.transform == ref.transform
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        a = ds.read(1)
        fp = np.isfinite(ref.read(1))
        assert np.isfinite(a[fp]).all()
        assert a[fp].min() >= 0.0 and a[fp].max() <= 1.0
        assert (~np.isfinite(a[~fp])).all()


def test_projection_is_labelled_a_projection_and_brackets_a_gain():
    analysis = json.loads((ROOT / "evidence/h3_analysis.json").read_text())
    proj = analysis["candidate"]["projection"]
    assert "PROJECTION" in proj["assumption"]
    assert proj["regression_only"] <= proj["half_packing_transfer"] <= proj["full_packing_transfer"]
