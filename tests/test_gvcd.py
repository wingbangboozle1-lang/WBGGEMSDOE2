"""Automated verification for WBG2-GVCD, 8-org 499-raster audit, axial stress math, and Run Card."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

rasterio = pytest.importorskip("rasterio")


def test_gvcd_preregistered_hypotheses_complete():
    cfg = json.loads((ROOT / "config" / "gvcd_hypotheses.json").read_text(encoding="utf-8"))
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


def test_axial_north_up_stress_dilation_math_exact():
    """Verify north-up EPSG:32611 strike tangent (t_E, t_N) = (gy, gx) resolves SHmin accurately."""
    y, x = np.mgrid[0:32, 0:32].astype(np.float32)

    # Case 1: N-S striking fault step -> varies East-West (gx != 0, gy = 0), strike = 0 deg (North).
    # Under E-W extension (SHmin = 90 deg), strike is perpendicular to SHmin -> T_d = 1.0!
    ns_step = 1.0 / (1.0 + np.exp(-(x - 16.0)))
    gy_ns, gx_ns = np.gradient(ns_step)
    denom_ns = gx_ns * gx_ns + gy_ns * gy_ns + 1e-12
    cos2_strike_ns = (gx_ns * gx_ns - gy_ns * gy_ns) / denom_ns
    sin2_strike_ns = (2.0 * gx_ns * gy_ns) / denom_ns
    shmin_90 = np.deg2rad(90.0)
    td_ns_90 = 0.5 * (1.0 - (cos2_strike_ns * np.cos(2.0 * shmin_90) + sin2_strike_ns * np.sin(2.0 * shmin_90)))
    td_ns_0 = 0.5 * (1.0 - (cos2_strike_ns * np.cos(0.0) + sin2_strike_ns * np.sin(0.0)))
    assert float(td_ns_90[16, 16]) == pytest.approx(1.0, abs=1e-5)
    assert float(td_ns_0[16, 16]) == pytest.approx(0.0, abs=1e-5)

    # Case 2: NE-SW (045 deg) striking fault -> z increases toward SE (+row, +col => gx > 0, gy > 0).
    # Strike = 045 deg -> perpendicular to NW-SE SHmin = 135 deg -> T_d(135) = 1.0, T_d(45) = 0.0!
    ne_step = 1.0 / (1.0 + np.exp(-((x + y - 32.0) / np.sqrt(2.0))))
    gy_ne, gx_ne = np.gradient(ne_step)
    denom_ne = gx_ne * gx_ne + gy_ne * gy_ne + 1e-12
    cos2_strike_ne = (gx_ne * gx_ne - gy_ne * gy_ne) / denom_ne
    sin2_strike_ne = (2.0 * gx_ne * gy_ne) / denom_ne
    shmin_135 = np.deg2rad(135.0)
    shmin_45 = np.deg2rad(45.0)
    td_ne_135 = 0.5 * (1.0 - (cos2_strike_ne * np.cos(2.0 * shmin_135) + sin2_strike_ne * np.sin(2.0 * shmin_135)))
    td_ne_45 = 0.5 * (1.0 - (cos2_strike_ne * np.cos(2.0 * shmin_45) + sin2_strike_ne * np.sin(2.0 * shmin_45)))
    assert float(td_ne_135[16, 16]) == pytest.approx(1.0, abs=1e-4)
    assert float(td_ne_45[16, 16]) == pytest.approx(0.0, abs=1e-4)


def test_dual_regime_submodular_300m_respects_cross_boundary_spacing():
    from wbggems.gvcd import allocate_dual_regime_submodular_300m

    prox = np.full((50, 50), 0.45, dtype=np.float32)
    dist = np.full((50, 50), 0.40, dtype=np.float32)
    allowed = np.ones((50, 50), dtype=bool)
    # Boundary right down column 25 (<=25 proximal, >25 distal)
    d_vis = np.broadcast_to(np.arange(50, dtype=np.float32)[None, :] + 10.0, (50, 50)).copy()

    out = allocate_dual_regime_submodular_300m(
        prox,
        dist,
        allowed,
        d_vis,
        total_budget=60,
        distal_threshold_px=35.0,
        distal_quota_fraction=0.45,
        min_sep_px=2.65,
        min_marginal_gain_distal=0.005,
        min_marginal_gain_proximal=0.005,
    )
    assert out.dtype == np.float32
    assert np.isfinite(out).all()
    assert float(out.min()) >= 0.0 and float(out.max()) <= 1.0
    ys, xs = np.nonzero(out > 0)
    assert len(ys) == 60
    distal_frac = float((d_vis[ys, xs] > 35.0).mean())
    assert distal_frac == pytest.approx(0.45, abs=0.03)
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            sep = float(np.hypot(ys[i] - ys[j], xs[i] - xs[j]))
            assert sep >= 2.65 - 1e-5, f"Cross-boundary spacing violated: {sep}"


def test_gvcd_holdout_protocol_beats_dphs_incumbent_and_passes_73_canaries():
    res = json.loads((ROOT / "evidence" / "wbg2_gvcd_results.json").read_text(encoding="utf-8"))
    dphs = json.loads((ROOT / "evidence" / "wbg2_dphs_results.json").read_text(encoding="utf-8"))

    assert res["evaluator_version"] == "gems57-pooled-hide-v2"
    assert res["withheld_positives_total"] == 60988
    assert res["experiments_executed"] == 3
    assert res["experiment_cap"] == 3
    assert res["leakage_canary"]["all_passed"] is True
    assert res["leakage_canary"]["n_features_checked"] == 73
    assert res["leakage_canary"]["max_symmetric_auc_observed"] <= 0.90

    scores = res["pooled_holdout_summary"]["scores"]
    dphs_dti = dphs["pooled_holdout_summary"]["scores"]["exp3_dphs_submodular"]["dti"]
    assert scores["gvcd_exp1_ventstress72_celf"]["dti"] > dphs_dti
    assert scores["gvcd_exp2_subsurface_ens_celf"]["dti"] > scores["gvcd_exp1_ventstress72_celf"]["dti"]
    assert scores["gvcd_exp3_dualregime_celf"]["dti"] > scores["gvcd_exp2_subsurface_ens_celf"]["dti"]
    assert scores["gvcd_exp3_dualregime_celf"]["ci95"][0] > 0.155


def test_gvcd_emitted_geotiff_zip_and_zero_nan_portal_safety():
    res = json.loads((ROOT / "evidence" / "wbg2_gvcd_results.json").read_text(encoding="utf-8"))
    cand = res["emitted_candidate"]
    tif_path = ROOT / cand["tif_path"]
    zip_path = ROOT / cand["zip_path"]
    assert tif_path.is_file() and zip_path.is_file()
    assert (tif_path.stat().st_mode & 0o777) == 0o644
    assert (zip_path.stat().st_mode & 0o777) == 0o644
    assert len(cand["name"]) <= 140
    assert len(cand["note"]) <= 140
    assert cand["in_sample_refit_fraction"] == 0.0
    assert cand["out_of_fold_footprint_fraction"] == 1.0

    tif_sha = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    assert tif_sha == cand["tif_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == tif_sha

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

    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    sup = arr > 0
    assert int(sup.sum()) == 37400
    touching = int((ndi.maximum_filter(sup.astype(np.uint8), size=3) * sup).sum()) - int(sup.sum())
    assert touching == 0


def test_gvcd_8org_uniqueness_zero_discrete_violations_and_prompt_pure_scores():
    aud = json.loads((ROOT / "evidence" / "gvcd_8org_fleet_audit.json").read_text(encoding="utf-8"))
    u = aud["uniqueness_summary"]
    assert u["rasters_measured"] >= 495
    assert u["discrete_rasters_measured"] >= 490
    assert u["exact_bytes_pass"] is True
    assert u["surface_rule_pass"] is True
    assert u["preplacement_surface_spearman_raw_max_abs"] <= 0.90
    assert u["preplacement_surface_spearman_1km_max_abs"] <= 0.90
    assert u["postplacement_surface_pearson_max_abs"] <= 0.90
    # Crucial breakthrough: ZERO discrete overlap violations across all 496 discrete 8-org rasters!
    assert u["discrete_non_blanket_pass"] is True
    assert u["discrete_non_blanket_violations_count"] == 0
    assert u["discrete_non_blanket_3px_max"] <= 0.70
    assert u["focus_sites_3px_max"] <= 0.70
    # Honest fail-closed on the 3 mathematical blanket controls
    assert u["literal_all_registry_pass"] is False

    # Verify prompt-pure LOSO model (zero external README score pollution!)
    loso = aud["empirical_score_models"]["physics_sgmc_geometry_11feat_loso_all_sites"]
    assert loso["n"] >= 95
    assert loso["r2"] > 0.45
    assert loso["spearman"] > 0.70

    for card_rel in ("evidence/RUN_CARD_GVCD.json", "docs/data/run-card-gvcd.json"):
        card = json.loads((ROOT / card_rel).read_text(encoding="utf-8"))
        assert card["verdict"] == "negative"
        assert card["status"] == "negative"
        assert card["ok_to_submit"] is False
        assert card["format_valid"] is True
        assert card["raster_sha256"] == aud["candidate"]["tif_sha256"]
        assert card["max_discrete_registry_dot_overlap"] <= 0.70
        assert card["leakage_canary_max_auc"] <= 0.90
        assert len(card["submission_note"]) <= 140


def test_prompt_ledger_8org_20261027_and_markdown_links():
    with (ROOT / "docs" / "data" / "user-reported-ledger-8org-20261027.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 154
    orgs = {r["org"] for r in rows}
    assert orgs == {
        "buffedlizard55-lab",
        "kanlerxz87-cyber",
        "wingbangboozle1-lang",
        "karagemop466-tech",
        "apartanish22-droid",
        "sassnarep3-star",
        "eugboogieman123-ops",
        "ginnymcfiner23-ux",
    }
    scored = [float(r["reported_public_dti"]) for r in rows if r["reported_public_dti"]]
    assert len(scored) == 128
    assert max(scored) == pytest.approx(0.2778)

    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in (ROOT / "research/gvcd_hypotheses.md", ROOT / "research/gvcd_findings.md", ROOT / "README.md"):
        txt = md.read_text(encoding="utf-8")
        for target in pattern.findall(txt):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if clean:
                assert (md.parent / clean).resolve().exists(), f"{md.name}: broken link {target}"


def test_gvcd_and_howto_html_pages_and_rfc8259_json():
    def _reject_const(c: str):
        raise ValueError(f"Non-RFC8259 token {c}")

    for rel in (
        "config/gvcd_hypotheses.json",
        "evidence/wbg2_gvcd_results.json",
        "evidence/gvcd_8org_fleet_audit.json",
        "evidence/RUN_CARD_GVCD.json",
        "docs/data/run-card-gvcd.json",
        "evidence/prompt_ledger_8org_audit_20261027.json",
        "docs/data/user-reported-ledger-8org-20261027.json",
    ):
        json.loads((ROOT / rel).read_text(encoding="utf-8"), parse_constant=_reject_const)

    gvcd_html = (ROOT / "docs/gvcd/index.html").read_text(encoding="utf-8")
    howto_html = (ROOT / "docs/how-to-submit/index.html").read_text(encoding="utf-8")
    assert "NO FILE APPROVED" in gvcd_html and "DO NOT SUBMIT" in gvcd_html
    assert ".tif" not in gvcd_html and ".zip" not in gvcd_html
    assert "OK TO DOWNLOAD AND SUBMIT" not in gvcd_html
    assert "Predicted values must be in range [0, 1]" in howto_html and "DO NOT SUBMIT" in howto_html
