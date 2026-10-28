#!/usr/bin/env python3
"""Package the preregistered DISTAL quota arms' full maps from cached surfaces.

This is PACKAGING of already-evaluated arms, not a new experiment: the
holdout was run by scripts/run_wbg2_distal.py (natural_oof 0.1770,
quota35 0.1548, piedmont40 0.1515; evidence/wbg2_distal_results.json).
The lane script emitted only the automatic winner (natural_oof). This
script emits the quota35 and piedmont40 full maps from the identical
cached quantile-matched OOF surface (.cache/distal_features/
oof_smooth_matched.npy, which already includes the full-catalogue relay
modulator) so the selector can compare all three preregistered arms on
full-map composition, fleet uniqueness and the empirical score model.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".cache" / "shared-template" / "src"))

import run_wbg2_dphs as dphs_run  # noqa: E402
import run_wbg2_distal as distal  # noqa: E402
from gems57 import evaluate_holdout, submission_writer  # noqa: E402
from wbggems.dphs import compute_relay_tip_modulator  # noqa: E402


def main() -> int:
    sample_path = ROOT / "data/official/sample_submission.tif"
    cat_path = ROOT / "data/official/existing_faults.tif"
    with rasterio.open(sample_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(cat_path) as ds:
        catalogue = ds.read(1) > 0

    surface_full = np.load(ROOT / ".cache/distal_features/oof_smooth_matched.npy")
    assert surface_full.shape == footprint.shape
    _, d_cat_full = compute_relay_tip_modulator(catalogue, footprint)
    pi_true_full = float((catalogue & footprint).sum()) / float(footprint.sum())
    allowed_full = footprint & ~catalogue & (d_cat_full > distal.COLLAR_PX)
    k_est_full = pi_true_full * float(allowed_full.sum())

    # Piedmont boost inputs, recomputed from cached feature files exactly as
    # in the lane script (strided footprint percentiles).
    scarp = np.nan_to_num(np.load(ROOT / ".cache/dphs_features/dem10_deconfounded_piedmont_scarp.npy"), nan=0.0)
    slope = np.nan_to_num(np.load(ROOT / ".cache/features/band-19.npy"), nan=0.0)
    sub = (slice(None, None, 7), slice(None, None, 7))
    fp_sub = footprint[sub]
    sc_p50, sc_p90 = (float(np.percentile(scarp[sub][fp_sub], q)) for q in (50, 90))
    sl_p30, sl_p70 = (float(np.percentile(slope[sub][fp_sub], q)) for q in (30, 70))
    scarp_norm = np.clip((scarp - sc_p50) / max(sc_p90 - sc_p50, 1e-6), 0.0, 1.0).astype(np.float32)
    low_slope_ramp = np.clip((sl_p70 - slope) / max(sl_p70 - sl_p30, 1e-6), 0.0, 1.0).astype(np.float32)
    del scarp, slope

    lane = json.loads((ROOT / "evidence/wbg2_distal_results.json").read_text())
    scores = lane["pooled_holdout_summary_vs_quota35"]["scores"]
    out_dir = ROOT / "docs/downloads/distal"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = ROOT / ".cache/distal_features"
    emitted = []
    for arm in ("quota35", "piedmont40"):
        alloc_surface = surface_full
        if arm == "piedmont40":
            alloc_surface = distal.piedmont_boost(surface_full, d_cat_full, scarp_norm, low_slope_ramp)
        np.save(cache_dir / f"preplacement_surface_{arm}.npy", alloc_surface)
        dots = distal.allocate_stratified(
            alloc_surface, allowed_full, d_cat_full,
            max_dots=distal.FULL_MAP_BUDGET, quotas=distal.QUOTAS[arm],
            k_truth=k_est_full, ref_mask=footprint)
        mask = dots > 0
        n = int(mask.sum())
        bf = distal.band_fractions(mask, d_cat_full)
        h8 = hashlib.sha256(dots.tobytes()).hexdigest()[:8]
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stem = f"wbg2-distaloof-{arm}-{n}dots-{ts}-{h8}-zeros"
        note = (f"WBG2-DISTAL {arm} 100pctOOF CELF300m {n}dots "
                f"gt32={bf['frac_gt_32px']:.2f} HOLDOUT-DTI={float(scores[arm]['dti']):.4f}")[:140]
        tif_path = out_dir / f"{stem}.tif"
        receipt = submission_writer.write_submission(
            tif_path, dots, sample_path, footprint, name=stem, note=note, catalogue=catalogue,
            metadata={"lane": "WBG2-DISTAL", "winning_experiment": arm,
                      "evaluator_version": evaluate_holdout.VERSION,
                      "holdout_dti": scores[arm]["dti"], "holdout_ci95": scores[arm]["ci95"],
                      "full_map_surface": "100% spatial-OOF, quantile-matched, zero in-sample pixels"})
        emitted.append({
            "arm": arm, "name": stem, "note": note,
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(tif_path.with_suffix(".zip").relative_to(ROOT)),
            "tif_sha256": dphs_run.sha256_file(tif_path),
            "tif_bytes": tif_path.stat().st_size, "dots": n,
            "min_dist_to_catalogue_px": round(float(d_cat_full[mask].min()), 4) if n else None,
            **bf,
            "preplacement_surface_cache": f".cache/distal_features/preplacement_surface_{arm}.npy",
            "holdout_dti": scores[arm]["dti"], "holdout_ci95": scores[arm]["ci95"],
            "writer_receipt": receipt,
        })
        print(f"[pack] {stem} ({n:,} dots, gt32={bf['frac_gt_32px']:.3f}, median={bf['median_px']}px)", flush=True)
        # Per-arm candidate receipt in the results-json shape the fleet audit reads
        (ROOT / f"evidence/wbg2_distal_{arm}_candidate.json").write_text(
            json.dumps({"emitted_candidate": emitted[-1]}, indent=2) + "\n", encoding="utf-8")

    payload = {
        "schema": "wbggems.distal-arm-packaging.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane_results": "evidence/wbg2_distal_results.json",
        "surface_cache": ".cache/distal_features/oof_smooth_matched.npy",
        "note": "Packaging of preregistered arms already scored on the shared holdout; not a new experiment.",
        "emitted_candidates": emitted,
    }
    (ROOT / "evidence/wbg2_distal_arm_packaging.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
