"""Automated verification for the WBG2-DISTAL lane (100% spatial-OOF)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
rasterio = pytest.importorskip("rasterio")


def test_distal_holdout_protocol_and_canary():
    res = json.loads((ROOT / "evidence/wbg2_distal_results.json").read_text())
    assert res["evaluator_version"] == "gems57-pooled-hide-v2"
    assert res["withheld_positives_total"] == 60988
    assert res["experiments_executed"] == 3 and res["experiment_cap"] == 3
    assert res["leakage_canary"]["all_passed"] is True
    assert res["leakage_canary"]["n_features_checked"] == 61
    assert res["leakage_canary"]["max_symmetric_auc_observed"] <= 0.90

    summary = res["pooled_holdout_summary_vs_quota35"]
    assert summary["alpha"] == 0.2 and summary["beta"] == 0.8
    assert summary["triangular_radius_m"] == 300.0
    nat = summary["scores"]["natural_oof"]
    assert nat["evidence_class"] == "HOLDOUT-DTI"
    assert nat["dti"] > 0.173477  # beats the DPHS EXP-3 incumbent point estimate
    quota = summary["scores"]["quota35"]
    pied = summary["scores"]["piedmont40"]
    assert quota["dti"] < nat["dti"] and pied["dti"] < nat["dti"]
    # preregistered selection: neither quota arm was within 0.02 of natural
    assert res["selection"]["winner"] == "natural_oof"
    assert res["selection"]["eligible"] == []


def test_distal_recommended_tif_byte_validation():
    card = json.loads((ROOT / "evidence/RUN_CARD_DISTAL_OOF.json").read_text())
    det = card["evidence_details"]
    tif_path = ROOT / det["candidate_file"]
    assert tif_path.is_file()
    assert len(det["submission_name"]) <= 140
    assert len(det["submission_note"]) <= 140
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == det["candidate_sha256"]
    with rasterio.open(tif_path) as src:
        assert src.count == 1 and src.dtypes[0] == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.nodata is None
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == (
            100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        arr = src.read(1)
    assert np.isfinite(arr).all()  # portal [0,1] range error impossible
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    sup = arr > 0
    assert int(sup.sum()) == 38000
    touching = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum()) - int(sup.sum())
    assert touching == 0


def test_distal_uniqueness_and_run_card_promote_to_selector_only():
    card = json.loads((ROOT / "evidence/RUN_CARD_DISTAL_OOF.json").read_text())
    for key in ("run_id", "hypothesis", "mechanism", "named_non_fault_mimic",
                "method_lane", "holdout_dti", "ci95", "verdict", "evidence_details"):
        assert card.get(key), f"missing run-card field {key}"
    assert card["verdict"] == "promote"
    assert card["status"] == "promote_to_selector"
    assert card["ok_to_submit"] is False  # slot selection is a separate step

    audit = json.loads((ROOT / "evidence/distal_uniqueness_and_fleet_audit.json").read_text())
    u = audit["uniqueness_summary"]
    assert u["rasters_measured"] >= 470
    assert u["exact_bytes_pass"] is True
    assert u["surface_rule_pass"] is True
    assert u["preplacement_surface_spearman_max_abs"] <= 0.90
    # literal dense/blanket gate fails, as it does for the B2 champion
    assert u["discrete_non_blanket_pass"] is False
    assert u["literal_all_registry_pass"] is False

    scope = card["evidence_details"]["uniqueness_audit_scope"]
    assert scope["sparse_peer_pass_le_0.70"] is True
    assert scope["sparse_peer_max_overlap"] <= 0.70
    assert max(card["evidence_details"]["focus_primary_overlap"].values()) <= 0.70

    diag = card["b2_gate_diagnostic"]["references"]
    assert diag["GEMSDOE22_h23a_dense_6pct"]["literal_gate_rejects_b2"] is True
    assert diag["13GEMSDOE_stride5_lattice"]["literal_gate_rejects_b2"] is True

    est = card["evidence_details"]["empirical_estimate"]
    assert est["evidence_class"].startswith("EMPIRICAL-ESTIMATE")
    assert est["pi95"][0] <= est["point"] <= est["pi95"][1]

    # all published aliases are byte-identical
    aliases = ["docs/data/run-card-distal-oof.json"]
    canonical = (ROOT / "evidence/RUN_CARD_DISTAL_OOF.json").read_bytes()
    for rel in aliases:
        assert (ROOT / rel).read_bytes() == canonical


def test_distal_site_pages_exist_and_are_qualified():
    for rel in ("docs/distal/index.html", "docs/distal/executive-summary.html",
                "docs/distal/how-to-submit.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "DO NOT SUBMIT" in text, rel
        assert "OK TO DOWNLOAD AND SUBMIT" not in text, rel
    index = (ROOT / "docs/distal/index.html").read_text(encoding="utf-8")
    card = json.loads((ROOT / "evidence/RUN_CARD_DISTAL_OOF.json").read_text())
    assert card["evidence_details"]["submission_name"] in index
    assert "HOLDOUT-DTI" in index
    assert "no current leaderboard-score estimate is available" in index
    assert "Research TIFF" not in index and ".tif" not in index
