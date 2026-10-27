"""Format-gate regression tests: reject legacy outside-footprint NaN TIFFs and pass promoted HVGF TIFF."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbg3.validate import validate_submission  # noqa: E402

SAMPLE = ROOT / "data/official/sample_submission.tif"
LEGACY_H3_RECEIPT = ROOT / "evidence/h3_submission.json"
HVGF_CARD = ROOT / "evidence/RUN_CARD_HVGF.json"


def test_legacy_h3_nan_raster_is_flagged_fail_closed():
    """Prove the validator catches the exact 7,111,787-NaN defect that caused '[0, 1]' portal rejection."""
    if not SAMPLE.exists() or not LEGACY_H3_RECEIPT.exists():
        pytest.skip("sample or legacy h3 receipt not present")
    rec = json.loads(LEGACY_H3_RECEIPT.read_text())
    legacy_tif = ROOT / "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif"
    if not legacy_tif.exists():
        pytest.skip("legacy h3 raster not present")
    assert rec["nan_outside_footprint"] == 7111787
    rep = validate_submission(legacy_tif, SAMPLE)
    assert rep["ok"] is False
    assert rep["nan_outside_footprint"] == 7111787
    assert any("Predicted values must be in range [0, 1]" in f for f in rep["failures"])


def test_promoted_hvgf_raster_passes_strict_all_finite_gate():
    """Promoted WBG2-HVGF GeoTIFF must be 100% finite in [0, 1] with 0.0 outside footprint and nodata=None."""
    assert HVGF_CARD.exists()
    card = json.loads(HVGF_CARD.read_text())
    assert card["verdict"] == "promote"
    assert card["ok_to_download_and_submit"] is True
    assert card["submission_note_chars"] <= 140
    v = card["validator_output"]
    assert v["all_checks_passed"] is True
    assert v["n_nan"] == 0
    assert v["n_infinite"] == 0
    assert v["nodata"] is None
    assert 0.0 <= v["min"] <= v["max"] <= 1.0

    if not SAMPLE.exists():
        pytest.skip("pinned sample not restored")
    tif = ROOT / "docs/downloads" / f"{card['submission_name']}.tif"
    assert tif.is_file()
    rep = validate_submission(tif, SAMPLE)
    assert rep["ok"] is True, rep["failures"]
    assert rep["nan_cells"] == 0
    assert rep["inf_cells"] == 0
    assert rep["nonzero_outside_footprint"] == 0
    assert rep["nodata"] is None
    assert rep["positive_cells"] == 37654


def test_projection_is_labelled_a_projection_and_brackets_a_gain():
    analysis = json.loads((ROOT / "evidence/h3_analysis.json").read_text())
    proj = analysis["candidate"]["projection"]
    assert "PROJECTION" in proj["assumption"]
    assert proj["regression_only"] <= proj["half_packing_transfer"] <= proj["full_packing_transfer"]

