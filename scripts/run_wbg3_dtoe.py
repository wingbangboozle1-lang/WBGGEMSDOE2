#!/usr/bin/env python3
"""WBG3-DTOE lane: DTI-optimal tail emission on the pinned DPHS spatial-OOF stack.

Preregistration: research/wbg3_preregistration_20261031.md (read it first).

Reuse, do not rebuild (protocol rule 2):
  * shared pinned template  : gems57.spatial / evaluate_holdout / metric /
                              submission_writer (hash-pinned in
                              registry/template_pins.json);
  * shared feature stack    : wbggems.dphs.build_or_load_dphs_cache (60
                              zero-catalogue features) + run_wbg2_dphs training
                              operations (used operation-for-operation);
  * shared allocation       : wbggems.dphs.allocate_submodular_300m (Minoux CELF
                              with exact DW-Tversky break-even bar);
  * shared full-map helpers : run_wbg2_distal_exp2.quantile_match_regions /
                              band_fractions.

New method content (this lane only): the emission stage is a preregistered grid
    budget in {26000, 38000} x marginal-gain bar in {0.020, 0.035} x
    relay/tip modulator in {ON, OFF},
selected by pooled HOLDOUT-DTI on the shared quadrant folds, then gated by the
duplicate stop before any file is published.

Protocol: leakage canary (61 features, hard stop > 0.90); pooled DTI with
alpha 0.2, beta 0.8, 300 m triangular kernel; every score labelled
HOLDOUT-DTI (proxy truth = withheld catalogue segments; never a leaderboard
score); duplicate stop on the surface and final dots; 3 experiments; 0
competition slots.
"""
from __future__ import annotations

import datetime as dt
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.isotonic import IsotonicRegression

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "scripts", ROOT / ".cache" / "shared-template" / "src"):
    sys.path.insert(0, str(p))

import run_wbg2_dphs as dphs_run  # noqa: E402
import run_wbg2_distal_exp2 as distal2  # noqa: E402
from gems57 import evaluate_holdout, spatial, submission_writer  # noqa: E402
from gems57 import uniqueness as uq  # noqa: E402
from wbggems.dphs import (  # noqa: E402
    EXP2_FEATURE_NAMES,
    allocate_submodular_300m,
    build_or_load_dphs_cache,
    compute_relay_tip_modulator,
)

SEED = 20261031
LANE = "WBG3-DTOE (DTI-optimal tail emission on the pinned DPHS OOF stack)"
FULL_MAP_BUDGET_INCUMBENT = 38000
ARM_BUDGETS = {"b38": 38000, "b26": 26000}
ARM_GAINS = {"g020": 0.020, "g035": 0.035}
ARMS = [  # (arm, budget_key, gain_key, modulator)
    ("A0_inc_b38_g020_mod", "b38", "g020", True),   # incumbent control
    ("A1_b26_g020_mod", "b26", "g020", True),
    ("A2_b38_g035_mod", "b38", "g035", True),
    ("A3_b26_g035_mod", "b26", "g035", True),
    ("A4_b26_g020_nomod", "b26", "g020", False),
    ("A5_b38_g035_nomod", "b38", "g035", False),
]
COLLAR_PX = 2.05
MIN_SEP_PX = 2.2
BUDGET_CAP_SECONDS = 2 * 3600

FOCUS_DIR = ROOT / "data_public" / "rasters_focus"
OUT_DIR = ROOT / "docs" / "downloads" / "wbg3"
CACHE_DIR = ROOT / ".cache" / "wbg3"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()



def pooled_dti(terms) -> float:
    """Pooled HOLDOUT-DTI from additive spatial-block terms (tp, fp, fn, n_truth)."""
    a = np.asarray(terms, dtype=float)
    tp, fp, fn = float(a[:, 0].sum()), float(a[:, 1].sum()), float(a[:, 2].sum())
    from gems57.metric import ALPHA, BETA, EPS
    return tp / (tp + ALPHA * fp + BETA * fn + EPS)

def exp1_fixed_raster_anchors(footprint, folds_list) -> list[dict]:
    """EXP-1: re-evaluate two fixed historical rasters on the shared folds."""
    anchors = []
    for label, path in (
        ("distal2_zeros (repo incumbent)", ROOT / "docs/downloads/distal_exp2/"
         "wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif"),
        ("GEMSDOE32-B2 (user-reported 0.2778)", FOCUS_DIR /
         "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    ):
        with rasterio.open(path) as ds:
            a = ds.read(1).astype("float32")
        pred = np.nan_to_num(a, nan=0.0)
        pred = np.clip(pred, 0.0, 1.0)
        terms = None
        per_fold = []
        for fold in folds_list:
            res, t = evaluate_holdout.evaluate(pred, fold, footprint)
            terms = t if terms is None else terms + t
            per_fold.append({"fold": int(fold["fold"]), "dti": round(float(res["dti"]), 6),
                             "emitted": int(res["emitted"])})
        dti = pooled_dti(terms)
        anchors.append({
            "label": label, "file": str(path.relative_to(ROOT)),
            "evidence_class": "HOLDOUT-DTI (fixed raster on shared folds; NOT a leaderboard score)",
            "evaluator_version": evaluate_holdout.VERSION,
            "pooled_dti": round(dti, 6), "per_fold": per_fold,
        })
        print(f"[exp1] {label}: pooled={dti:.4f}", flush=True)
    return anchors


def fold_budget_for(budget: int, active_sum: int, total_offcat_fp: float) -> int:
    return int(round(budget * (float(active_sum) / total_offcat_fp)))


def main() -> int:
    t_start = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/official/existing_faults.tif") as ds:
        catalogue = ds.read(1) > 0
    total_offcat_fp = float((footprint & ~catalogue).sum())
    print(f"[wbg3] Footprint {int(footprint.sum()):,} | catalogue {int((catalogue & footprint).sum()):,}",
          flush=True)

    feats = build_or_load_dphs_cache(ROOT, footprint)
    fp_mm, fp_idx_grid = dphs_run.build_or_load_fp_memmap(
        feats, EXP2_FEATURE_NAMES, footprint, ROOT / ".cache/dphs_features")

    folds_list = list(spatial.folds(catalogue, footprint, buffer_px=80))
    canary = dphs_run.run_leakage_canary(fp_mm, fp_idx_grid, EXP2_FEATURE_NAMES, folds_list, footprint)
    canary_max = float(canary["max_symmetric_auc_observed"])
    print(f"[canary] {canary['n_features_checked']} features, max symmetric AUC {canary_max:.4f} "
          f"on {canary['highest_signal_feature']}", flush=True)
    if canary_max > 0.90:
        print("[canary] FAIL > 0.90 -- leakage alarm, stopping before placement.", flush=True)
        return 2

    # ---------------- EXP-1: fixed-raster checkout anchors ----------------
    exp1 = exp1_fixed_raster_anchors(footprint, folds_list)

    # ---------------- EXP-2: per-fold arm grid ----------------
    terms_by_arm = {arm: None for arm, _, _, _ in ARMS}
    per_fold = {arm: [] for arm, _, _, _ in ARMS}
    oof_smooth = np.zeros(footprint.shape, dtype=np.float32)
    region_masks: list[np.ndarray] = []

    for fold in folds_list:
        if time.time() - t_start > BUDGET_CAP_SECONDS:
            print("[budget] 2h wall cap reached before finishing folds; stopping honestly.", flush=True)
            return 3
        f_idx = int(fold["fold"])
        t_f = time.time()
        region, visible, train_mask = fold["region"], fold["visible"], fold["train"]
        region_masks.append(region.copy())
        active_eval = footprint & region & ~visible
        fold_budget_inc = fold_budget_for(FULL_MAP_BUDGET_INCUMBENT, int(active_eval.sum()), total_offcat_fp)

        rows, cols, y_tr, pi_sample, pi_true = dphs_run._sample_train_pixels(
            train_mask, visible, footprint, n_neg_mult=5, seed=SEED + 101 * f_idx)
        X_60 = np.asarray(fp_mm[fp_idx_grid[rows, cols], :], dtype=np.float32)
        k_est = pi_true * float(active_eval.sum())

        # --- pinned DPHS EXP-3 surface, operation-for-operation (same seeds family) ---
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
        del clf_e2, clf_deep, clf_reg, prob_e2, ens_eval
        gc.collect()
        smooth_eval = (0.72 * cal_eval + 0.28 * ndi.gaussian_filter(cal_eval, sigma=0.75)).astype(np.float32)
        del cal_eval
        mod_fold, d_vis_fold = compute_relay_tip_modulator(visible, footprint)
        weighted_eval = (smooth_eval * mod_fold).astype(np.float32)
        oof_smooth[region & footprint] = smooth_eval[region & footprint]
        allowed_eval = active_eval & (d_vis_fold > COLLAR_PX)
        gc.collect()

        for arm, bkey, gkey, use_mod in ARMS:
            surf = weighted_eval if use_mod else smooth_eval
            surf = np.where(np.isfinite(surf), surf, 0.0).astype(np.float32)
            budget = fold_budget_for(ARM_BUDGETS[bkey], int(active_eval.sum()), total_offcat_fp)
            pred = allocate_submodular_300m(
                surf, allowed_eval, max_dots=budget, min_sep_px=MIN_SEP_PX,
                min_marginal_gain=ARM_GAINS[gkey], k_truth=k_est)
            res, t = evaluate_holdout.evaluate(pred, fold, footprint)
            terms_by_arm[arm] = t if terms_by_arm[arm] is None else terms_by_arm[arm] + t
            bf = distal2.band_fractions(pred > 0, d_vis_fold)
            per_fold[arm].append({
                "fold": f_idx, "dti": round(float(res["dti"]), 6),
                "tpw": round(float(res["tpw"]), 3), "fpw": round(float(res["fpw"]), 3),
                "fnw": round(float(res["fnw"]), 3), "emitted": int(res["emitted"]),
                "n_truth": int(res["n_truth"]), "budget": budget, **bf})
            del pred, surf
        del weighted_eval, smooth_eval, mod_fold, d_vis_fold, allowed_eval
        gc.collect()
        line = f"[fold {f_idx}] ({time.time() - t_f:.1f}s)"
        for arm, _, _, _ in ARMS:
            line += f" | {arm}={per_fold[arm][-1]['dti']:.4f}({per_fold[arm][-1]['emitted']:,})"
        print(line, flush=True)

    winner_by_dti = {}
    for arm, _, _, _ in ARMS:
        pooled = pooled_dti(terms_by_arm[arm])
        winner_by_dti[arm] = pooled
    order = sorted(winner_by_dti, key=lambda a: -winner_by_dti[a])
    print("[exp2] pooled DTI ranking: " + ", ".join(f"{a}={winner_by_dti[a]:.4f}" for a in order), flush=True)

    # paired CI vs the incumbent control arm
    summary = evaluate_holdout.pooled_summary(terms_by_arm, draws=1000, seed=520810,
                                              candidate=order[0])
    np.save(CACHE_DIR / "oof_smooth.npy", oof_smooth)
    with (CACHE_DIR / "regions.npz").open("wb") as fh:
        np.savez_compressed(fh, **{f"r{i}": m for i, m in enumerate(region_masks)})

    # ---------------- EXP-3: full map for every arm, uniqueness gate, write ----------------
    matched = distal2.quantile_match_regions(oof_smooth, region_masks, footprint)
    mod_full, d_cat_full = compute_relay_tip_modulator(catalogue, footprint)
    pi_true_full = float((catalogue & footprint).sum()) / float(footprint.sum())
    allowed_full = footprint & ~catalogue & (d_cat_full > COLLAR_PX)
    k_est_full = pi_true_full * float(allowed_full.sum())

    full_maps: dict[str, tuple[np.ndarray, dict]] = {}
    for arm, bkey, gkey, use_mod in ARMS:
        surf = (matched * mod_full).astype(np.float32) if use_mod else matched.copy()
        surf[~footprint] = 0.0
        budget = ARM_BUDGETS[bkey]
        dots = allocate_submodular_300m(surf, allowed_full, max_dots=budget,
                                        min_sep_px=MIN_SEP_PX,
                                        min_marginal_gain=ARM_GAINS[gkey],
                                        k_truth=k_est_full)
        bf = distal2.band_fractions(dots > 0, d_cat_full)
        full_maps[arm] = (dots, bf)
        print(f"[exp3] {arm}: {int((dots > 0).sum()):,} dots, gt32={bf['frac_gt_32px']:.2f}", flush=True)

    # duplicate stop vs the nine focus-site rasters (phase A)
    focus_rows = []
    focus_arrays = []
    for p in sorted(FOCUS_DIR.glob("*.tif")):
        with rasterio.open(p) as ds:
            a = ds.read(1)
        focus_arrays.append((p.name, np.nan_to_num(a.astype("float32"), nan=0.0)))
    print(f"[uniqueness] scanning {len(focus_arrays)} focus rasters (phase A)", flush=True)

    def phase_a_rows(dots: np.ndarray) -> list[dict]:
        rows = []
        for name, fa in focus_arrays:
            ov = uq.dot_overlap(dots, fa)
            rho = uq.surface_rho(dots, fa, footprint)["spearman_full_footprint"]
            rows.append({"their_raster": name, "share_of_my_dots_within_3px": round(ov, 4),
                         "spearman_full_footprint": None if rho != rho else round(rho, 4),
                         "duplicate_by_overlap": ov > uq.OVERLAP_LIMIT,
                         "duplicate_by_rho": (rho == rho and rho > uq.RHO_LIMIT)})
        return rows

    chosen = None
    for arm in order:
        dots, bf = full_maps[arm]
        rows = phase_a_rows(dots)
        worst_ov = max(r["share_of_my_dots_within_3px"] for r in rows)
        worst_rho = max((r["spearman_full_footprint"] if r["spearman_full_footprint"] is not None else 0.0) for r in rows)
        ok = (not any(r["duplicate_by_overlap"] or r["duplicate_by_rho"] for r in rows))
        print(f"[gate] {arm}: worst_focus_overlap={worst_ov:.3f} worst_focus_rho={worst_rho:.3f} pass={ok}",
              flush=True)
        if ok:
            chosen = arm
            break
    if chosen is None:
        print("[gate] ALL arms failed the focus-site duplicate stop -- no file written (negative).",
              flush=True)
        return 4

    dots, bf = full_maps[chosen]
    n_dots = int((dots > 0).sum())
    surf_hash8 = hashlib.sha256(dots.tobytes()).hexdigest()[:8]
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    holdout_dti = winner_by_dti[chosen]
    ci = summary["scores"][chosen]["ci95"]
    sub_stem = f"wbg3-dtoe-{chosen}-{n_dots}dots-{ts}-{surf_hash8}-zeros"
    sub_note = (f"WBG3-DTOE {chosen} 100pctOOF CELF300m {n_dots}dots "
                f"HOLDOUT-DTI={holdout_dti:.4f} [{ci[0]:.4f},{ci[1]:.4f}] not-a-score")[:140]
    tif_path = OUT_DIR / f"{sub_stem}.tif"
    writer_receipt = submission_writer.write_submission(
        tif_path, dots, ROOT / "data/official/sample_submission.tif", footprint,
        name=sub_stem, note=sub_note, catalogue=catalogue,
        metadata={
            "lane": LANE,
            "preregistration": "research/wbg3_preregistration_20261031.md",
            "winning_arm": chosen,
            "evaluator_version": evaluate_holdout.VERSION,
            "holdout_dti": holdout_dti,
            "holdout_ci95": list(ci),
            "withheld_positives": int(sum(m["n_truth"] for m in per_fold[chosen])),
            "full_map_surface": "100% spatial-OOF, quantile-matched, zero in-sample pixels",
        })
    print(f"[write] {tif_path.name} sha256={writer_receipt['sha256']}", flush=True)

    focus_rows = phase_a_rows(dots)
    elapsed = time.time() - t_start
    run_card = {
        "schema": "wbggems.wbg3-run-card.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane": LANE,
        "preregistration": "research/wbg3_preregistration_20261031.md",
        "hypothesis": "H1 DTI-optimal tail emission (budget x gain-bar x modulator grid) on the pinned DPHS EXP-3 OOF surface recovers DTI otherwise lost to tail false positives.",
        "mechanism": "Exact DW-Tversky break-even bar in the shared CELF allocator stops emission when expected kernel credit cannot pay the 0.2-alpha FP price; the incumbent always filled its 38k cap.",
        "named_non_fault_mimic": "Miscalibrated distal basins (fans, playas, Lahontan shorelines) could make the bar reject good distal dots, losing recall.",
        "seeds": {"fold_seed_base": SEED, "note": "fresh seed; DPHS EXP-3 training ops otherwise identical"},
        "experiments_run": 3,
        "experiment_cap": 3,
        "weekly_slots_used": 0,
        "leakage_canary": canary,
        "evaluator_version": evaluate_holdout.VERSION,
        "evaluator_hashes": evaluate_holdout.implementation_hashes(),
        "withheld_positives_total": int(sum(m["n_truth"] for m in per_fold[chosen])),
        "exp1_fixed_raster_anchors": exp1,
        "pooled_holdout_summary": summary,
        "per_fold_metrics": per_fold,
        "pooled_dti_by_arm": {a: round(v, 6) for a, v in winner_by_dti.items()},
        "arm_rank_order": order,
        "selection_rule": "argmax pooled HOLDOUT-DTI among preregistered arms, subject to the focus-site duplicate stop; fall through DTI order on failure",
        "chosen_arm": chosen,
        "focus_uniqueness_phaseA": {
            "rows": focus_rows,
            "worst_share_within_3px": max(r["share_of_my_dots_within_3px"] for r in focus_rows),
            "pass": True,
            "note": "literal all-registry scan is phase B (scripts/scan_wbg3_registry.py); dense/lattice witnesses documented in preregistration",
        },
        "candidate": {
            "name": sub_stem, "note_140": sub_note, "note_chars": len(sub_note),
            "tif": str(tif_path.relative_to(ROOT)),
            "zip": str(tif_path.with_suffix(".zip").relative_to(ROOT)),
            "sha256": writer_receipt["sha256"], "bytes": writer_receipt["bytes"],
            "dots": n_dots, "band_fractions": bf,
            "validator": writer_receipt["validator"],
            "approved_for_weekly_slot": writer_receipt["approved_for_weekly_slot"],
        },
        "holdout_dti": holdout_dti,
        "holdout_ci_95": list(ci),
        "evidence_label": ("HOLDOUT-DTI, evaluator " + evaluate_holdout.VERSION +
                           f", {int(sum(m['n_truth'] for m in per_fold[chosen]))} withheld positives; "
                           "never a leaderboard score or projection"),
        "elapsed_seconds": round(elapsed, 1),
        "verdict": "promote_to_selector" if holdout_dti > pooled_dti(terms_by_arm["A0_inc_b38_g020_mod"]) else "negative",
        "verdict_scope": "Promotion is a separate selector decision; this run card spends no weekly slot.",
    }
    (ROOT / "evidence/wbg3_run_card.json").write_text(json.dumps(run_card, indent=1))
    print(f"[done] winner={chosen} holdout={holdout_dti:.4f} elapsed={elapsed:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
