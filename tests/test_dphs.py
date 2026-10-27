"""Automated verification for the WBG2-DPHS lane, 467-raster fleet audit, and Run Card."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

rasterio = pytest.importorskip("rasterio")


def test_dphs_preregistered_hypotheses_complete():
    cfg = json.loads((ROOT / "config" / "dphs_hypotheses.json").read_text())
    hyps = cfg["hypotheses"]
    assert 3 <= len(hyps) <= 5
    ranks = [h["rank"] for h in hyps]
    assert ranks == sorted(ranks)
    for h in hyps:
        for req in (
            "id",
            "title",
            "specific_layers",
            "physical_signature",
            "why_catches_uncatalogued_faults",
            "non_fault_mimic",
            "difference_from_repo",
            "expected_holdout_dti_gain",
            "implementation_cost",
        ):
            assert h.get(req), f"Missing {req} in {h.get('id')}"


def test_dphs_holdout_protocol_and_canary_receipt():
    res = json.loads((ROOT / "evidence" / "wbg2_dphs_results.json").read_text())
    assert res["evaluator_version"] == "gems57-pooled-hide-v2"
    assert res["withheld_positives_total"] == 60988
    assert res["experiments_executed"] == 3
    assert res["experiment_cap"] == 3
    assert res["leakage_canary"]["all_passed"] is True
    assert res["leakage_canary"]["max_symmetric_auc_observed"] <= 0.90

    summary = res["pooled_holdout_summary"]
    assert summary["alpha"] == 0.2 and summary["beta"] == 0.8
    assert summary["triangular_radius_m"] == 300.0
    exp3 = summary["scores"]["exp3_dphs_submodular"]
    assert exp3["evidence_class"] == "HOLDOUT-DTI"
    assert exp3["dti"] > 0.17
    assert exp3["ci95"][0] > 0.15

    for ctrl in ("ctrl_19b", "msptcd_31", "h3_blind_lattice", "exp1_scarpspec", "exp2_hydromultiscale"):
        diff = summary["paired_differences"][ctrl]
        assert diff["delta"] > 0.08
        assert diff["ci95"][0] > 0.05


def test_dphs_geotiff_byte_validation_and_zero_nan_portal_safety():
    res = json.loads((ROOT / "evidence" / "wbg2_dphs_results.json").read_text())
    cand = res["emitted_candidate"]
    tif_path = ROOT / cand["tif_path"]
    assert tif_path.is_file()
    assert len(cand["name"]) <= 140
    assert len(cand["note"]) <= 140

    digest = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    assert digest == cand["tif_sha256"]

    with rasterio.open(tif_path) as src:
        assert src.count == 1
        assert src.dtypes[0] == "float32"
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.nodata is None
        assert tuple(round(float(v), 6) for v in list(src.transform)[:6]) == (
            100.0,
            0.0,
            243350.0,
            0.0,
            -100.0,
            4508550.0,
        )
        arr = src.read(1)

    assert np.isfinite(arr).all(), "All pixels must be finite to prevent portal [0, 1] range error"
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    sup = arr > 0
    assert int(sup.sum()) == 36500
    touching = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum()) - int(sup.sum())
    assert touching == 0, f"Expected 0 touching 3x3 dots, got {touching}"


def test_dphs_fleet_uniqueness_audit_and_run_card_fail_closed():
    aud = json.loads((ROOT / "evidence" / "dphs_uniqueness_and_fleet_audit.json").read_text())
    u = aud["uniqueness_summary"]
    assert u["rasters_measured"] >= 460
    assert u["exact_bytes_pass"] is True
    assert u["surface_rule_pass"] is True
    assert u["preplacement_surface_spearman_max_abs"] <= 0.90
    assert u["focus_sites_3px_max"] <= 0.70
    assert u["discrete_non_blanket_pass"] is False
    assert u["literal_all_registry_pass"] is False

    models = aud["empirical_score_models"]
    loso = models["physics_sgmc_geometry_11feat_loso_all_sites"]
    assert loso["n"] >= 90 and loso["r2"] > 0.40 and loso["spearman"] > 0.60
    ext = models["physics_sgmc_geometry_11feat_external_9focus"]
    assert ext["spearman"] > 0.70

    for card_path in (ROOT / "evidence" / "RUN_CARD_DPHS.json", ROOT / "docs" / "data" / "run-card-dphs.json"):
        card = json.loads(card_path.read_text())
        for key in (
            "run_id",
            "hypothesis",
            "method_lane",
            "holdout_dti",
            "incumbent_dti",
            "ci95",
            "leakage_canary_max_auc",
            "max_registry_corr",
            "max_registry_dot_overlap",
            "format_valid",
            "status",
        ):
            assert key in card
        assert card["status"] == "negative"
        assert card["format_valid"] is True
        assert card["leakage_canary_max_auc"] <= 0.90
        assert card["max_registry_corr"] <= 0.90
        assert card["max_registry_dot_overlap"] > 0.70
        assert card["evidence_details"]["ok_to_submit"] is False


def test_prompt_ledger_20261027_preserves_scored_and_blank_rows():
    with (ROOT / "docs" / "data" / "user-reported-ledger-20261027.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 144
    scored = [r for r in rows if r["reported_public_dti"]]
    blank = [r for r in rows if not r["reported_public_dti"]]
    assert len(scored) == 128
    assert len(blank) == 16
    assert all(r["evidence_class"].startswith("USER-REPORTED") for r in rows)


def test_allocate_submodular_300m_enforces_spacing_and_bounds():
    from wbggems.dphs import allocate_submodular_300m

    prob = np.zeros((40, 40), dtype=np.float32)
    prob[8:32, 19:21] = 0.35
    allowed = np.ones((40, 40), dtype=bool)
    emitted = allocate_submodular_300m(
        prob,
        allowed,
        max_dots=20,
        min_sep_px=2.2,
        min_marginal_gain=0.01,
        k_truth=40.0,
    )
    assert emitted.dtype == np.float32
    assert np.isfinite(emitted).all()
    assert float(emitted.min()) >= 0.0 and float(emitted.max()) <= 1.0
    ys, xs = np.nonzero(emitted > 0)
    assert len(ys) >= 4
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            dist = float(np.hypot(ys[i] - ys[j], xs[i] - xs[j]))
            assert dist >= 2.2 - 1e-6


def test_all_dphs_json_receipts_are_strict_rfc8259():
    def _reject_const(c: str):
        raise ValueError(f"Non-RFC8259 token {c}")

    for rel in (
        "config/dphs_hypotheses.json",
        "evidence/prompt_ledger_audit_20261027.json",
        "evidence/external_layers_provenance.json",
        "evidence/wbg2_dphs_results.json",
        "evidence/dphs_uniqueness_and_fleet_audit.json",
        "evidence/RUN_CARD_DPHS.json",
        "docs/data/run-card-dphs.json",
        "docs/data/dphs_audit_summary.json",
        "docs/downloads/dphs/wbg2-dphs-exp3-submod300m-20261027T194500Z-46a3a89a-zeros.json",
    ):
        txt = (ROOT / rel).read_text(encoding="utf-8")
        json.loads(txt, parse_constant=_reject_const)


def test_dphs_html_pages_clear_and_unambiguous():
    idx = (ROOT / "docs" / "dphs" / "index.html").read_text(encoding="utf-8")
    howto = (ROOT / "docs" / "dphs" / "how-to-submit.html").read_text(encoding="utf-8")
    exec_sum = (ROOT / "docs" / "dphs" / "executive-summary.html").read_text(encoding="utf-8")

    assert "DO NOT SUBMIT" in idx and "0.1735" in idx and "31f3d8e61d195dd5" in idx
    assert "OK TO DOWNLOAD AND SUBMIT" in idx
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in idx
    assert "Predicted values must be in range [0, 1]" in howto
    assert "0.2778" in exec_sum and "0.3195" in exec_sum and "0.4544" in exec_sum

