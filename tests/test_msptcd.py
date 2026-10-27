"""Unit and byte-level integration tests for WBG2-MSPTCD physics & campaign receipts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import re

import pytest
import rasterio

from wbggems.msptcd import (
    ALL_FEATURE_NAMES,
    CORE_PHYSICS_NAMES,
    STRAIN_SEIS_NAMES,
    _bilinear_sample,
    compute_physics_features_from_arrays,
)
from wbggems.validate import sha256
import run_wbg2_msptcd

ROOT = Path(__file__).resolve().parents[1]


def _synthetic_bands(h: int = 48, w: int = 48) -> tuple[dict[int, np.ndarray], np.ndarray]:
    yy, xx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    fp = np.ones((h, w), dtype=bool)
    fp[:3, :] = False
    fp[:, -3:] = False

    # Dipping step: gravity step at x=22, magnetic step shifted 2 px downdip at x=24.
    grav = np.tanh((xx - 22.0) / 1.8) * 15.0
    rtp = np.tanh((xx - 24.0) / 1.8) * 120.0
    depth = np.where(xx >= 22.0, 420.0, 40.0).astype(np.float32)
    cond = np.where(xx >= 22.0, 85.0, 15.0).astype(np.float32)
    elev = (1500.0 - 30.0 * np.tanh((xx - 22.0) / 1.5)).astype(np.float32)
    slope = (20.0 / np.cosh((xx - 22.0) / 1.5)).astype(np.float32)
    tc = (18.0 + 4.0 * np.tanh((xx - 22.0) / 1.6)).astype(np.float32)

    bands = {i: np.zeros((h, w), dtype=np.float32) for i in range(1, 20)}
    bands[2] = rtp.astype(np.float32)
    bands[4] = np.full((h, w), 12.0, dtype=np.float32)
    bands[6] = tc
    bands[7] = (3.0 * np.tanh((yy - 20.0) / 4.0)).astype(np.float32)
    bands[8] = np.full((h, w), 4.0, dtype=np.float32)
    bands[9] = np.gradient(rtp, axis=1).astype(np.float32)
    bands[10] = np.full((h, w), 500.0, dtype=np.float32)
    bands[11] = np.gradient(grav, axis=1).astype(np.float32)
    bands[12] = elev
    bands[13] = grav.astype(np.float32)
    bands[15] = depth
    bands[16] = np.full((h, w), 900.0, dtype=np.float32)
    bands[17] = cond
    bands[19] = slope
    # Inject an isolated interior NaN to verify smooth derivative imputation without NaN halo growth.
    bands[6][h // 2, w // 2] = np.nan
    return bands, fp


def test_msptcd_physics_features_finite_and_polarity_invariant():
    bands, fp = _synthetic_bands()
    out = compute_physics_features_from_arrays(bands, fp)
    expected = set(CORE_PHYSICS_NAMES + STRAIN_SEIS_NAMES)
    assert set(out.keys()) == expected
    assert len(ALL_FEATURE_NAMES) == 31

    for name, arr in out.items():
        assert arr.shape == fp.shape and arr.dtype == np.float32
        assert np.isfinite(arr[fp]).all(), f"{name} produced nonfinite values inside footprint"
        assert np.isnan(arr[~fp]).all(), f"{name} was not masked outside footprint"

    # Reversing magnetic remanence polarity (-rtp, -tmi_vg) preserves dip_offset_concordance.
    bands_neg = {k: v.copy() for k, v in bands.items()}
    bands_neg[2] = -bands_neg[2]
    bands_neg[9] = -bands_neg[9]
    out_neg = compute_physics_features_from_arrays(bands_neg, fp)
    assert np.allclose(
        out["dip_offset_concordance"][fp],
        out_neg["dip_offset_concordance"][fp],
        rtol=1e-5,
        atol=1e-5,
    )
    # Fault corridor x in [21..25] has substantially stronger concordance than background x=8.
    assert float(out["dip_offset_concordance"][24, 22]) > 3.0 * float(out["dip_offset_concordance"][24, 8])
    assert float(out["cond_flank_asymmetry"][24, 22]) > 3.0 * float(out["cond_flank_asymmetry"][24, 8])


def test_bayes_recalibration_preserves_order_and_unit_bounds():
    raw = np.array([0.0, 0.05, 0.20, 0.50, 0.90, 1.0], dtype=np.float32)
    cal = run_wbg2_msptcd.bayes_recalibrate(raw, pi_sample=0.20, pi_true=0.012)
    assert cal.dtype == np.float32
    assert np.isfinite(cal).all()
    assert (cal >= 0.0).all() and (cal <= 1.0).all()
    assert np.all(np.diff(cal) > 0.0)
    # At raw == pi_sample (0.20), calibrated posterior must equal pi_true (0.012).
    assert np.isclose(float(cal[2]), 0.012, atol=1e-5)


def test_msptcd_edge_cases_and_constant_fields():
    # Exact boundary bilinear interpolation on bottom-right corner.
    grid = np.arange(16, dtype=np.float32).reshape(4, 4)
    val = _bilinear_sample(
        grid,
        np.array([[3.0, 0.0]], dtype=np.float32),
        np.array([[3.0, 3.0]], dtype=np.float32),
    )
    assert np.allclose(val, np.array([[15.0, 3.0]], dtype=np.float32))

    # Degenerate 1x4 grid must fail closed with ValueError.
    with pytest.raises(ValueError):
        _bilinear_sample(np.ones((1, 4), dtype=np.float32), np.zeros((1, 4)), np.zeros((1, 4)))

    bands, fp = _synthetic_bands(12, 12)
    # Constant-valued bands must never divide by zero or emit NaNs inside footprint.
    zero_bands = {k: np.zeros_like(v) for k, v in bands.items()}
    zero_out = compute_physics_features_from_arrays(zero_bands, fp)
    for name, arr in zero_out.items():
        assert np.isfinite(arr[fp]).all(), f"constant input caused nonfinite {name}"

    # Missing band index and shape mismatch must fail closed.
    incomplete = dict(bands)
    del incomplete[6]
    with pytest.raises(ValueError, match="missing required GeoDAWN band"):
        compute_physics_features_from_arrays(incomplete, fp)

    bad_shape = dict(bands)
    bad_shape[2] = np.zeros((10, 12), dtype=np.float32)
    with pytest.raises(ValueError, match="must match footprint shape"):
        compute_physics_features_from_arrays(bad_shape, fp)


def test_markdown_local_links_resolve():
    md_files = [
        ROOT / "README.md",
        ROOT / "research/findings.md",
        ROOT / "research/hypotheses.md",
        ROOT / "research/sources.md",
        ROOT / "evidence/review.md",
    ]
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in md_files:
        text = md.read_text()
        for raw_target in pattern.findall(text):
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = raw_target.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            resolved = (md.parent / clean).resolve()
            assert resolved.exists(), f"{md.name}: broken local markdown link {raw_target}"


def test_msptcd_saved_geotiff_zip_and_receipts_match_bytes():
    res = json.loads((ROOT / "evidence/wbg2_msptcd_results.json").read_text())
    can = json.loads((ROOT / "evidence/wbg2_msptcd_canaries.json").read_text())

    assert res["verdict"] == "negative" and res["ok_to_submit"] is False
    assert res["budget_compliance"]["experiments_run"] == 3
    assert res["budget_compliance"]["weekly_slots_used"] == 0
    assert can["all_passed"] is True and can["total_checks"] == 124
    assert can["max_two_sided_auc"] <= 0.90

    # Verify statistical lift of EXP-1 and EXP-3 over CTRL-19B.
    scores = res["holdout_pooled"]["scores"]
    assert scores["exp1_msptcd_core"]["dti"] > scores["ctrl_19b"]["dti"]
    assert scores["exp3_msptcd_submod_greedy"]["dti"] > scores["exp1_msptcd_core"]["dti"]
    assert res["paired_vs_ctrl_19b"]["exp1_msptcd_core"]["ci95"][0] > 0.0
    assert res["paired_vs_ctrl_19b"]["exp3_msptcd_submod_greedy"]["ci95"][0] > 0.0

    # Verify novelty vs all 9 focus sites AND fail-closed stop vs blanket witnesses.
    reg = res["registry_comparison"]
    assert reg["unique_vs_all_9_focus_sites"] is True
    assert reg["max_focus_forward_overlap_3px"] <= 0.70
    assert reg["max_focus_abs_surface_spearman"] <= 0.90
    assert reg["unique_vs_literal_all_registry"] is False
    assert "13GEMSDOE" in reg["blanket_witnesses_triggered"]
    assert "17GEMSDOE_dense_prior" in reg["blanket_witnesses_triggered"]

    art = res["artifact"]
    tif_path = ROOT / art["tif_path"]
    zip_path = ROOT / art["zip_path"]
    assert tif_path.is_file() and zip_path.is_file()
    assert sha256(tif_path) == art["tif_sha256"]
    assert sha256(zip_path) == art["zip_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert names == [tif_path.name]
        assert hashlib.sha256(zf.read(names[0])).hexdigest() == art["tif_sha256"]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert str(ds.crs) == "EPSG:32611" and ds.shape == (3730, 3292)
        assert ds.nodata is None
        arr = ds.read(1)
        assert np.isfinite(arr).all()
        assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
        assert int((arr > 0).sum()) == art["dots"]
