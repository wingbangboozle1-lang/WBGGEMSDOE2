"""Unit and byte-level contract tests for the promoted WBG2-HVGF campaign."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

rasterio = pytest.importorskip("rasterio")

ROOT = Path(__file__).resolve().parents[1]


def test_hvgf_run_card_protocol_and_holdout_contracts():
    card = json.loads((ROOT / "evidence/RUN_CARD_HVGF.json").read_text())
    docs_card = json.loads((ROOT / "docs/data/RUN_CARD_HVGF.json").read_text())
    results = json.loads((ROOT / "evidence/wbg2_hvgf_results.json").read_text())
    assert card == docs_card

    assert card["verdict"] == "promote"
    assert card["ok_to_download_and_submit"] is True
    assert card["live_slots_used"] == 0
    assert card["experiments_used"] == 3
    assert card["experiment_budget"] == 3
    assert len(card["submission_note"]) <= 140
    assert card["submission_note_chars"] == len(card["submission_note"])
    assert "non_fault_mimic" in card and len(card["non_fault_mimic"]) > 40

    # Leakage canaries: every feature across all 4 folds must be <= 0.90 two-sided AUC
    lc = card["leakage_canary"]
    assert lc["all_passed"] is True
    assert lc["features_tested"] == 91
    assert lc["folds_tested"] == 4
    assert lc["max_two_sided_auc"] <= 0.90

    # Holdout DTI across all three independent instruments must beat baselines
    hd = card["holdout_dti"]
    q8 = hd["primary_quadrant_8km"]
    assert q8["evidence_class"] == "HOLDOUT-DTI"
    assert q8["evaluator_version"] == "gems57-pooled-hide-v2"
    assert q8["withheld_positive_pixels"] > 50000
    assert q8["dti"] > hd["ablation_quadrant_8km"]["ctrl_19b"]["dti"] * 3.0
    assert q8["ci95"][0] <= q8["dti"] <= q8["ci95"][1]

    inst_b = hd["within_network_component_hide"]
    assert inst_b["evidence_class"] == "HOLDOUT-DTI"
    assert inst_b["dti"] > hd["ablation_component_hide"]["ctrl_19b"]["dti"] * 2.0

    inst_c = hd["independent_sgmc_piedmont_offcatalogue"]
    assert inst_c["evidence_class"] == "HOLDOUT-DTI"
    sgmc_baselines = results["instrument_C_sgmc_piedmont_offcatalogue"]["scores"]
    assert inst_c["dti"] > sgmc_baselines["wbg2_dz16_baseline"]["dti"]
    assert inst_c["dti"] > sgmc_baselines["wbg2_msptcd_e3"]["dti"] * 5.0

    # Registry uniqueness contracts
    reg = card["registry_uniqueness"]
    assert reg["preplacement_max_abs_spearman"] <= 0.90
    assert reg["smoothed_surface_max_abs_pearson"] <= 0.90
    assert reg["max_discrete_peer_3px_overlap"] <= 0.70
    assert reg["max_focus_site_3px_overlap"] <= 0.70
    assert reg["calibrated_discrete_peer_gate"] == "PASS"
    assert results["uniqueness_summary"]["normalized_enriched_violations_gt1p5x_and_gt50pct"] == []


def test_hvgf_geotiff_and_zip_match_hashes_and_all_finite_rules():
    card = json.loads((ROOT / "evidence/RUN_CARD_HVGF.json").read_text())
    cand = json.loads((ROOT / "data_public/candidate.json").read_text())
    assert cand["sha256"] == card["raster_sha256"]

    tif_docs = ROOT / "docs/downloads" / f"{card['submission_name']}.tif"
    tif_dl = ROOT / "downloads" / f"{card['submission_name']}.tif"
    zip_docs = ROOT / "docs/downloads/hvgf" / f"{card['submission_name']}.zip"

    assert tif_docs.is_file() and tif_dl.is_file() and zip_docs.is_file()
    tif_bytes = tif_docs.read_bytes()
    assert tif_dl.read_bytes() == tif_bytes
    assert hashlib.sha256(tif_bytes).hexdigest() == card["raster_sha256"]
    assert hashlib.sha256(zip_docs.read_bytes()).hexdigest() == card["zip_sha256"]

    with zipfile.ZipFile(zip_docs, "r") as zf:
        names = zf.namelist()
        assert names == [f"{card['submission_name']}.tif"]
        assert zf.read(names[0]) == tif_bytes

    with rasterio.open(tif_docs) as src:
        assert src.count == 1
        assert src.dtypes[0] == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.nodata is None
        arr = src.read(1)

    assert np.isfinite(arr).all(), "Zero NaN/Inf anywhere required to survive DrivenData [0, 1] check"
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    sup = arr > 0
    assert int(sup.sum()) == 37654
    pairs = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum())
    assert pairs - int(sup.sum()) == 0, "No two emitted dots may touch"


def test_hvgf_hypotheses_preregistered():
    hyps = json.loads((ROOT / "docs/data/hvgf_hypotheses.json").read_text())
    assert 3 <= len(hyps["hypotheses"]) <= 5
    for h in hyps["hypotheses"]:
        for key in (
            "id",
            "rank",
            "title",
            "layers",
            "physical_signature",
            "why_missing_from_catalogues",
            "difference_from_existing_repo",
            "non_fault_mimic",
            "implementation_cost",
            "external_sources",
        ):
            assert h.get(key), f"Missing {key} in {h.get('id')}"
