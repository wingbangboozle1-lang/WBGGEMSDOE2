#!/usr/bin/env python3
"""WBG2-DISTAL: 100% spatial-OOF, distance-stratified piedmont allocation.

Preregistration: research/distal_preregistration_20261027.md (read it first).

What this run changes relative to WBG2-DPHS EXP-3 (HOLDOUT-DTI 0.1735) and
nothing else:
  * Per-fold training/surface construction is copied operation-for-operation
    from scripts/run_wbg2_dphs.py EXP-3 (same 60 zero-catalogue features,
    same seeds, same shared evaluator/writer).
  * Three ALLOCATION experiments are scored on that one OOF surface:
      EXP-1 natural_oof  : DPHS CELF allocation unchanged (control).
      EXP-2 quota35      : distance-stratified CELF, quotas 30/35/35 across
                           (2.05,10] / (10,32] / (32,inf) px from VISIBLE faults.
      EXP-3 piedmont40   : low-slope piedmont-scarp boost beyond 10 px,
                           quotas 25/35/40.
  * The full map is built from the pooled pre-modulator OOF surface ONLY
    (zero in-sample pixels; DPHS blended 55% in-sample and collapsed to
    frac_gt_32px = 3.64%), quantile-matched across quadrants, then allocated
    with the winning experiment's rule against the full catalogue.

Protocol: leakage canary (61 features, hard stop > 0.90), unchanged shared
gems57 evaluate_holdout (alpha 0.2, beta 0.8, 300 m triangular kernel) and
submission_writer, 3 experiments, 0 competition slots.
"""
from __future__ import annotations

import datetime as dt
import gc
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.isotonic import IsotonicRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".cache" / "shared-template" / "src"))

import run_wbg2_dphs as dphs_run  # noqa: E402  (reuse, do not rebuild)
from gems57 import evaluate_holdout, spatial, submission_writer  # noqa: E402
from wbggems.dphs import (  # noqa: E402
    EXP2_FEATURE_NAMES,
    allocate_submodular_300m,
    build_or_load_dphs_cache,
    compute_relay_tip_modulator,
)

SEED = dphs_run.SEED
FULL_MAP_BUDGET = 38000
MIN_SEP_PX = 2.2
COLLAR_PX = 2.05
NONINFERIORITY_MARGIN = 0.02

BAND_EDGES = ((COLLAR_PX, 10.0), (10.0, 32.0), (32.0, np.inf))
BAND_MIN_GAINS = (0.020, 0.012, 0.006)
QUOTAS = {
    "quota35": (0.30, 0.35, 0.35),
    "piedmont40": (0.25, 0.35, 0.40),
}


def effective_band_quotas(
    allowed: np.ndarray,
    dist_px: np.ndarray,
    ref_mask: np.ndarray,
    quotas: tuple[float, float, float],
    max_dots: int,
) -> tuple[int, int, int]:
    """Area-normalized band quotas (Amendment A1).

    Target fractions define a per-band dot *density* using band areas over
    ``ref_mask`` (whole footprint, same visible/full distance field). The
    number allocated in ``allowed`` is density x allowed band area,
    renormalized to ``max_dots``. When ``allowed`` covers the full map this
    returns exactly ``quotas * max_dots``.
    """
    shares = []
    for band_idx, (lo, hi) in enumerate(BAND_EDGES):
        band = (dist_px > lo) & (dist_px <= hi)
        a_ref = float((band & ref_mask).sum())
        a_fold = float((band & allowed).sum())
        density = quotas[band_idx] / a_ref if a_ref > 0 else 0.0
        shares.append(density * a_fold)
    total = sum(shares)
    if total <= 0:
        return (0, 0, 0)
    raw = [s / total * max_dots for s in shares]
    out = [int(np.floor(v)) for v in raw]
    for i in np.argsort([-(v - np.floor(v)) for v in raw])[: max_dots - sum(out)]:
        out[int(i)] += 1
    return (out[0], out[1], out[2])


def allocate_stratified(
    prob_map: np.ndarray,
    allowed: np.ndarray,
    dist_px: np.ndarray,
    *,
    max_dots: int,
    quotas: tuple[float, float, float],
    k_truth: float,
    ref_mask: np.ndarray,
) -> np.ndarray:
    """CELF per distance band, distal first, with cross-band min-separation.

    Bands use distance to VISIBLE faults in holdout folds (full catalogue on
    the full map). Band budgets are area-normalized via
    ``effective_band_quotas`` so the same density policy is tested in folds
    and applied on the full map. Already-placed dots block a >= MIN_SEP_PX
    neighbourhood so the union keeps pairwise separation.
    """
    eff = effective_band_quotas(allowed, dist_px, ref_mask, quotas, max_dots)
    out = np.zeros(prob_map.shape, dtype=np.float32)
    # order: distal (band 2), mid (1), proximal (0)
    for band_idx in (2, 1, 0):
        lo, hi = BAND_EDGES[band_idx]
        quota = int(eff[band_idx])
        if quota <= 0:
            continue
        band_allowed = allowed & (dist_px > lo) & (dist_px <= hi)
        placed = out > 0
        if placed.any():
            d_placed = ndi.distance_transform_edt(~placed)
            band_allowed &= d_placed >= MIN_SEP_PX
        if not band_allowed.any():
            continue
        dots = allocate_submodular_300m(
            prob_map,
            band_allowed,
            max_dots=quota,
            min_sep_px=MIN_SEP_PX,
            min_marginal_gain=BAND_MIN_GAINS[band_idx],
            k_truth=k_truth * (quota / max(max_dots, 1)),
            candidate_pool=max(60000, quota * 6),
        )
        out = np.maximum(out, dots)
    return out


def piedmont_boost(
    surface: np.ndarray,
    dist_px: np.ndarray,
    scarp_norm: np.ndarray,
    low_slope_ramp: np.ndarray,
) -> np.ndarray:
    """DISTAL-H2: boost low-slope piedmont scarps only beyond 10 px."""
    boost = 1.0 + 0.75 * scarp_norm * low_slope_ramp
    boost = np.where(dist_px > 10.0, boost, 1.0).astype(np.float32)
    return (surface * boost).astype(np.float32)


def quantile_match_regions(
    pooled: np.ndarray,
    region_masks: list[np.ndarray],
    footprint: np.ndarray,
) -> np.ndarray:
    """Monotone per-region quantile match to the pooled OOF distribution.

    Label-free: uses only predicted values. Within-region ranking is
    preserved exactly; only the marginal scale is harmonised across
    quadrant seams.
    """
    fp_vals = np.sort(pooled[footprint])
    out = np.zeros_like(pooled)
    n_grid = 2001
    pooled_q = np.quantile(fp_vals, np.linspace(0.0, 1.0, n_grid))
    for region in region_masks:
        mask = region & footprint
        vals = pooled[mask]
        if vals.size == 0:
            continue
        region_q = np.quantile(vals, np.linspace(0.0, 1.0, n_grid))
        # map each value to its region percentile, then to pooled value
        pct = np.interp(vals, region_q, np.linspace(0.0, 1.0, n_grid))
        out[mask] = np.interp(pct, np.linspace(0.0, 1.0, n_grid), pooled_q)
    return out.astype(np.float32)


def band_fractions(dots_mask: np.ndarray, dist_px: np.ndarray) -> dict[str, float]:
    if not dots_mask.any():
        return {"frac_2_to_10px": 0.0, "frac_10_to_32px": 0.0, "frac_gt_32px": 0.0,
                "frac_le_2px": 0.0, "median_px": 0.0}
    dv = dist_px[dots_mask]
    return {
        "frac_le_2px": round(float((dv <= 2.0).mean()), 4),
        "frac_2_to_10px": round(float(((dv > 2.0) & (dv <= 10.0)).mean()), 4),
        "frac_10_to_32px": round(float(((dv > 10.0) & (dv <= 32.0)).mean()), 4),
        "frac_gt_32px": round(float((dv > 32.0).mean()), 4),
        "median_px": round(float(np.median(dv)), 3),
    }


def main() -> int:
    t_start = time.time()
    sample_path = ROOT / "data/official/sample_submission.tif"
    cat_path = ROOT / "data/official/existing_faults.tif"
    with rasterio.open(sample_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(cat_path) as ds:
        catalogue = ds.read(1) > 0
    total_offcat_fp = float((footprint & ~catalogue).sum())
    print(f"[distal] Footprint {int(footprint.sum()):,} | catalogue "
          f"{int((catalogue & footprint).sum()):,}", flush=True)

    feats = build_or_load_dphs_cache(ROOT, footprint)
    fp_mm, fp_idx_grid = dphs_run.build_or_load_fp_memmap(
        feats, EXP2_FEATURE_NAMES, footprint, ROOT / ".cache/dphs_features"
    )

    # Piedmont boost inputs (label-free global percentiles from a strided sample)
    scarp = np.nan_to_num(np.asarray(feats["dem10_deconfounded_piedmont_scarp"]), nan=0.0)
    slope = np.nan_to_num(np.asarray(feats["det_elev_slope"]), nan=0.0)
    sub = (slice(None, None, 7), slice(None, None, 7))
    fp_sub = footprint[sub]
    sc_p50, sc_p90 = (float(np.percentile(scarp[sub][fp_sub], q)) for q in (50, 90))
    sl_p30, sl_p70 = (float(np.percentile(slope[sub][fp_sub], q)) for q in (30, 70))
    scarp_norm = np.clip((scarp - sc_p50) / max(sc_p90 - sc_p50, 1e-6), 0.0, 1.0).astype(np.float32)
    low_slope_ramp = np.clip((sl_p70 - slope) / max(sl_p70 - sl_p30, 1e-6), 0.0, 1.0).astype(np.float32)
    del scarp, slope
    print(f"[distal] piedmont percentiles scarp p50={sc_p50:.4f} p90={sc_p90:.4f} | "
          f"slope p30={sl_p30:.4f} p70={sl_p70:.4f}", flush=True)

    folds_list = list(spatial.folds(catalogue, footprint, buffer_px=80))
    canary = dphs_run.run_leakage_canary(fp_mm, fp_idx_grid, EXP2_FEATURE_NAMES, folds_list, footprint)
    print(f"[canary] PASS {canary['n_features_checked']} features, max symmetric AUC "
          f"{canary['max_symmetric_auc_observed']:.4f} on {canary['highest_signal_feature']}", flush=True)

    arms = ["natural_oof", "quota35", "piedmont40"]
    terms_by_arm: dict[str, np.ndarray | None] = {k: None for k in arms}
    per_fold: dict[str, list[dict]] = {k: [] for k in arms}
    oof_smooth = np.zeros(footprint.shape, dtype=np.float32)
    region_masks: list[np.ndarray] = []

    for fold in folds_list:
        f_idx = int(fold["fold"])
        t_f = time.time()
        region, visible, train_mask = fold["region"], fold["visible"], fold["train"]
        region_masks.append(region.copy())
        active_eval = footprint & region & ~visible
        fold_budget = int(round(FULL_MAP_BUDGET * (float(active_eval.sum()) / total_offcat_fp)))

        rows, cols, y_tr, pi_sample, pi_true = dphs_run._sample_train_pixels(
            train_mask, visible, footprint, n_neg_mult=5, seed=SEED + 101 * f_idx
        )
        X_60 = np.asarray(fp_mm[fp_idx_grid[rows, cols], :], dtype=np.float32)
        k_est = pi_true * float(active_eval.sum())

        # --- DPHS EXP-3 surface, operation-for-operation (seeds identical) ---
        clf_e2 = dphs_run._fit_single_hgbr(X_60, y_tr, seed=SEED + 30 + f_idx,
                                           max_leaf_nodes=63, max_iter=220)
        prob_e2 = dphs_run._predict_from_memmap(
            [(1.0, clf_e2)], fp_mm, 60, fp_idx_grid, active_eval,
            pi_sample=pi_sample, pi_true=pi_true)
        is_cal = (((rows // 200) + (cols // 200)) % 7) == (f_idx % 7)
        if is_cal.sum() < 2000 or y_tr[is_cal].sum() < 50 or (~is_cal).sum() < 10000:
            is_cal = np.zeros(rows.size, dtype=bool)
            is_cal[::7] = True
        clf_deep = dphs_run._fit_single_hgbr(
            X_60[~is_cal], y_tr[~is_cal], seed=SEED + 40 + f_idx, max_iter=250,
            max_leaf_nodes=95, min_samples_leaf=70, learning_rate=0.045, l2_regularization=3.0)
        clf_reg = dphs_run._fit_single_hgbr(
            X_60[~is_cal], y_tr[~is_cal], seed=SEED + 50 + f_idx, max_iter=240,
            max_leaf_nodes=39, min_samples_leaf=140, learning_rate=0.05, l2_regularization=5.0)
        raw_cal = dphs_run._prior_correct(
            0.55 * clf_deep.predict_proba(X_60[is_cal])[:, 1]
            + 0.45 * clf_reg.predict_proba(X_60[is_cal])[:, 1], pi_sample, pi_true)
        neg_w = ((1.0 - pi_true) / max(pi_true, 1e-6)) * (pi_sample / max(1.0 - pi_sample, 1e-6))
        iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso.fit(raw_cal, y_tr[is_cal],
                sample_weight=np.where(y_tr[is_cal] == 1, 1.0, neg_w).astype(np.float64))
        del X_60
        ens_eval = dphs_run._predict_from_memmap(
            [(0.55, clf_deep), (0.45, clf_reg)], fp_mm, 60, fp_idx_grid, active_eval,
            pi_sample=pi_sample, pi_true=pi_true)
        cal_eval = np.zeros_like(ens_eval)
        ev_r, ev_c = np.nonzero(active_eval)
        cal_eval[ev_r, ev_c] = (0.50 * iso.transform(ens_eval[ev_r, ev_c])
                                + 0.50 * prob_e2[ev_r, ev_c]).astype(np.float32)
        smooth_eval = (0.72 * cal_eval + 0.28 * ndi.gaussian_filter(cal_eval, sigma=0.75)).astype(np.float32)
        mod_fold, d_vis_fold = compute_relay_tip_modulator(visible, footprint)
        weighted_eval = (smooth_eval * mod_fold).astype(np.float32)
        oof_smooth[region & footprint] = smooth_eval[region & footprint]
        allowed_eval = active_eval & (d_vis_fold > COLLAR_PX)
        del clf_e2, clf_deep, clf_reg, prob_e2, ens_eval, cal_eval
        gc.collect()

        # --- the 3 allocation experiments on this one surface ---
        preds: dict[str, np.ndarray] = {}
        preds["natural_oof"] = allocate_submodular_300m(
            weighted_eval, allowed_eval, max_dots=fold_budget,
            min_sep_px=MIN_SEP_PX, min_marginal_gain=0.020, k_truth=k_est)
        preds["quota35"] = allocate_stratified(
            weighted_eval, allowed_eval, d_vis_fold, max_dots=fold_budget,
            quotas=QUOTAS["quota35"], k_truth=k_est, ref_mask=footprint)
        boosted = piedmont_boost(weighted_eval, d_vis_fold, scarp_norm, low_slope_ramp)
        preds["piedmont40"] = allocate_stratified(
            boosted, allowed_eval, d_vis_fold, max_dots=fold_budget,
            quotas=QUOTAS["piedmont40"], k_truth=k_est, ref_mask=footprint)
        del boosted, smooth_eval, weighted_eval

        line = f"[fold {f_idx}] ({time.time() - t_f:.1f}s)"
        for arm in arms:
            res, terms = evaluate_holdout.evaluate(preds[arm], fold, footprint)
            terms_by_arm[arm] = terms if terms_by_arm[arm] is None else terms_by_arm[arm] + terms
            bf = band_fractions(preds[arm] > 0, d_vis_fold)
            per_fold[arm].append({
                "fold": f_idx, "dti": round(float(res["dti"]), 6),
                "tpw": round(float(res["tpw"]), 3), "fpw": round(float(res["fpw"]), 3),
                "fnw": round(float(res["fnw"]), 3), "emitted": int(res["emitted"]),
                "n_truth": int(res["n_truth"]), **bf,
            })
            line += f" | {arm}={res['dti']:.4f} ({res['emitted']:,}, gt32={bf['frac_gt_32px']:.2f})"
        print(line, flush=True)
        del preds
        gc.collect()

    # Pooled summary twice: paired deltas vs each quota arm (cheap, same terms)
    summary_q = evaluate_holdout.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate="quota35")
    summary_p = evaluate_holdout.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate="piedmont40")
    scores = summary_q["scores"]
    print("\n=== POOLED HOLDOUT-DTI (gems57-pooled-hide-v2) ===", flush=True)
    for arm in arms:
        s = scores[arm]
        print(f"  {arm:14s}: DTI={s['dti']:.4f} 95% CI [{s['ci95'][0]:.4f}, {s['ci95'][1]:.4f}]", flush=True)

    # --- preregistered winner selection ---
    e1 = float(scores["natural_oof"]["dti"])
    eligible = [a for a in ("quota35", "piedmont40")
                if float(scores[a]["dti"]) >= e1 - NONINFERIORITY_MARGIN]
    if eligible:
        winner = max(eligible, key=lambda a: float(scores[a]["dti"]))
        winner_is_quota = True
    else:
        winner, winner_is_quota = "natural_oof", False
    print(f"[select] E1={e1:.4f} eligible={eligible} winner={winner} quota={winner_is_quota}", flush=True)

    # --- full map: 100% OOF, quantile-matched, full-catalogue modulator ---
    matched = quantile_match_regions(oof_smooth, region_masks, footprint)
    mod_full, d_cat_full = compute_relay_tip_modulator(catalogue, footprint)
    surface_full = (matched * mod_full).astype(np.float32)
    surface_full[~footprint] = 0.0
    # pi_true for the DTI bar over the full footprint (catalogue density)
    pi_true_full = float((catalogue & footprint).sum()) / float(footprint.sum())
    allowed_full = footprint & ~catalogue & (d_cat_full > COLLAR_PX)
    k_est_full = pi_true_full * float(allowed_full.sum())

    alloc_surface = surface_full
    if winner == "piedmont40":
        alloc_surface = piedmont_boost(surface_full, d_cat_full, scarp_norm, low_slope_ramp)
    cache_dir = ROOT / ".cache/distal_features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.save(cache_dir / "preplacement_surface.npy", alloc_surface)
    np.save(cache_dir / "oof_smooth_matched.npy", surface_full)

    if winner == "natural_oof":
        final_dots = allocate_submodular_300m(
            surface_full, allowed_full, max_dots=FULL_MAP_BUDGET,
            min_sep_px=MIN_SEP_PX, min_marginal_gain=0.020, k_truth=k_est_full)
    else:
        final_dots = allocate_stratified(
            alloc_surface, allowed_full, d_cat_full, max_dots=FULL_MAP_BUDGET,
            quotas=QUOTAS[winner], k_truth=k_est_full, ref_mask=footprint)

    dots_mask = final_dots > 0
    n_dots = int(dots_mask.sum())
    full_bf = band_fractions(dots_mask, d_cat_full)
    surf_hash8 = hashlib.sha256(final_dots.tobytes()).hexdigest()[:8]
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sub_stem = f"wbg2-distaloof-{winner}-{n_dots}dots-{ts}-{surf_hash8}-zeros"
    sub_note = (f"WBG2-DISTAL {winner} 100pctOOF CELF300m {n_dots}dots "
                f"gt32={full_bf['frac_gt_32px']:.2f} HOLDOUT-DTI={float(scores[winner]['dti']):.4f}")[:140]
    out_dir = ROOT / "docs/downloads/distal"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("wbg2-distaloof-*"):
        old.unlink()
    tif_path = out_dir / f"{sub_stem}.tif"
    writer_receipt = submission_writer.write_submission(
        tif_path, final_dots, sample_path, footprint, name=sub_stem, note=sub_note,
        catalogue=catalogue,
        metadata={
            "lane": "WBG2-DISTAL",
            "winning_experiment": winner,
            "evaluator_version": evaluate_holdout.VERSION,
            "holdout_dti": scores[winner]["dti"],
            "holdout_ci95": scores[winner]["ci95"],
            "full_map_surface": "100% spatial-OOF, quantile-matched, zero in-sample pixels",
        },
    )
    payload = {
        "schema": "wbggems.distal-results.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.time() - t_start, 2),
        "lane": "WBG2-DISTAL (100% spatial-OOF distance-stratified piedmont allocation)",
        "preregistration": "research/distal_preregistration_20261027.md",
        "evaluator_version": evaluate_holdout.VERSION,
        "evaluator_hashes": evaluate_holdout.implementation_hashes(),
        "withheld_positives_total": int(sum(m["n_truth"] for m in per_fold["natural_oof"])),
        "experiments_executed": 3,
        "experiment_cap": 3,
        "full_map_budget_cap": FULL_MAP_BUDGET,
        "leakage_canary": canary,
        "pooled_holdout_summary_vs_quota35": summary_q,
        "pooled_holdout_summary_vs_piedmont40": summary_p,
        "per_fold_metrics": per_fold,
        "selection": {
            "rule": "eligible if pooled DTI >= natural_oof - 0.02; pick higher DTI; else natural_oof",
            "eligible": eligible, "winner": winner, "winner_is_quota_arm": winner_is_quota,
            "prior_holdout_best_dphs_exp3": 0.1735,
        },
        "emitted_candidate": {
            "name": sub_stem, "note": sub_note,
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(tif_path.with_suffix(".zip").relative_to(ROOT)),
            "tif_sha256": dphs_run.sha256_file(tif_path),
            "tif_bytes": tif_path.stat().st_size,
            "dots": n_dots,
            "min_dist_to_catalogue_px": round(float(d_cat_full[dots_mask].min()), 4) if n_dots else None,
            **full_bf,
            "preplacement_surface_cache": ".cache/distal_features/preplacement_surface.npy",
            "writer_receipt": writer_receipt,
        },
    }
    out_json = ROOT / "evidence/wbg2_distal_results.json"
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[done] {tif_path.name} ({n_dots:,} dots, gt32={full_bf['frac_gt_32px']:.3f}, "
          f"median={full_bf['median_px']}px) in {time.time() - t_start:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
