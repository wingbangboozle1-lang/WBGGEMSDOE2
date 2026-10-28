#!/usr/bin/env python3
"""Run the preregistered 3-experiment WBG2-DPHS lane under the Parallel-Run Protocol.

Protocol compliance:
- Unchanged shared evaluator: ``gems57.evaluate_holdout`` (``gems57-pooled-hide-v2``,
  ``alpha=0.2, beta=0.8``, 300 m triangular kernel, 60,988 withheld positives across
  4 label-blind buffered spatial quadrants, 1,000 paired 20 km spatial-block draws).
- Unchanged shared writer: ``gems57.submission_writer.write_submission``.
- Single-feature holdout leakage canary across all 60 zero-catalogue features plus
  the fold-visible relay/tip modulator across all 4 buffered spatial folds
  (``max(AUC, 1 - AUC) <= 0.90`` hard gate).
- Strictly 3 experiments:
    EXP-1: DPHS-ScarpSpec (51 zero-catalogue features: MSPTCD + 1m LiDAR + 10m 3DEP
           de-confounded piedmont scarp + GeoDAWN K/Th/U/shallow-demag)
    EXP-2: DPHS-HydroMultiScale (60 zero-catalogue features: + DOE GDR #1391 blind
           hydrothermal conduits + multi-scale strike ridge integrators)
    EXP-3: DPHS-CalibratedSubmodular (diversified dual-depth HistGBR ensemble on 60
           features + nested 20 km block Isotonic calibration + fold-visible relay/tip
           modulator + Minoux CELF 300 m submodular max-cover outside d_vis <= 2.05 px)
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".cache" / "shared-template" / "src"))

from gems57 import emit, evaluate_holdout, spatial, submission_writer  # noqa: E402
from wbggems.dphs import (  # noqa: E402
    EXP1_FEATURE_NAMES,
    EXP2_FEATURE_NAMES,
    allocate_submodular_300m,
    build_or_load_dphs_cache,
    compute_relay_tip_modulator,
)
from wbggems.msptcd import ALL_FEATURE_NAMES as MSPTCD_NAMES, RAW_BAND_NAMES  # noqa: E402

FULL_MAP_BUDGET = 36500
CANARY_SUBSAMPLE = 120000
SEED = 20261027


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_or_load_fp_memmap(
    feats: dict[str, np.ndarray],
    names: tuple[str, ...],
    footprint: np.ndarray,
    cache_dir: Path,
) -> tuple[np.memmap, np.ndarray]:
    """Pack footprint rows into a single contiguous (N_fp, 60) float32 memmap for fast I/O."""
    n_fp = int(footprint.sum())
    n_cols = len(names)
    mmap_path = cache_dir / f"fp_matrix_{n_cols}.f32.mmap"
    meta_path = cache_dir / f"fp_matrix_{n_cols}.json"

    fp_idx_grid = np.full(footprint.shape, -1, dtype=np.int32)
    fp_r, fp_c = np.nonzero(footprint)
    fp_idx_grid[fp_r, fp_c] = np.arange(n_fp, dtype=np.int32)

    if mmap_path.is_file() and meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("names") == list(names) and meta.get("n_fp") == n_fp:
            mm = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_cols))
            return mm, fp_idx_grid

    print(f"[dphs] Packing contiguous ({n_fp:,} x {n_cols}) float32 matrix in .cache/...", flush=True)
    mm_w = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, n_cols))
    for j, name in enumerate(names):
        mm_w[:, j] = feats[name][fp_r, fp_c]
    mm_w.flush()
    del mm_w
    meta_path.write_text(json.dumps({"names": list(names), "n_fp": n_fp}), encoding="utf-8")
    mm = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_cols))
    return mm, fp_idx_grid


def _prior_correct(prob: np.ndarray, pi_sample: float, pi_true: float) -> np.ndarray:
    """Exact Saerens-Latinne-Decaestecker (2002) Bayes prior-shift correction."""
    p = np.clip(np.asarray(prob, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    a = p * (pi_true / max(pi_sample, 1e-9))
    b = (1.0 - p) * ((1.0 - pi_true) / max(1.0 - pi_sample, 1e-9))
    return (a / (a + b + 1e-12)).astype(np.float32)


def _predict_from_memmap(
    models: list[tuple[float, HistGradientBoostingClassifier]],
    fp_mm: np.memmap,
    col_count: int,
    fp_idx_grid: np.ndarray,
    mask: np.ndarray,
    *,
    pi_sample: float,
    pi_true: float,
    chunk_size: int = 450000,
) -> np.ndarray:
    rows, cols = np.nonzero(mask)
    idx_vec = fp_idx_grid[rows, cols]
    out = np.zeros(mask.shape, dtype=np.float32)
    n = idx_vec.size
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        Xc = np.asarray(fp_mm[idx_vec[start:stop], :col_count], dtype=np.float32)
        p_acc = np.zeros(stop - start, dtype=np.float64)
        for weight, clf in models:
            p_acc += weight * clf.predict_proba(Xc)[:, 1]
        out[rows[start:stop], cols[start:stop]] = _prior_correct(p_acc, pi_sample, pi_true)
    return out


def make_label_blind_hex_lattice(footprint: np.ndarray, visible: np.ndarray, target_dots: int = 34400) -> np.ndarray:
    """Construct a genuinely label-blind uniform hexagonal lattice masked only by fold-visible faults."""
    allowed = footprint & (ndi.distance_transform_edt(~(visible & footprint)) > 2.0)
    # Hexagonal lattice spacing s such that allowed_area / (sqrt(3)/2 * s^2) ~= target_dots
    s_float = np.sqrt(float(allowed.sum()) / (max(target_dots, 1) * 0.8660254))
    dx = max(4, int(round(s_float)))
    dy = max(4, int(round(s_float * 0.8660254)))
    out = np.zeros(footprint.shape, dtype=np.float32)
    h, w = footprint.shape
    row_idx = 0
    for r in range(2, h - 2, dy):
        offset = (dx // 2) if (row_idx % 2 == 1) else 0
        out[r, (2 + offset):(w - 2):dx] = 1.0
        row_idx += 1
    out[~allowed] = 0.0
    return out


def run_leakage_canary(
    fp_mm: np.memmap,
    fp_idx_grid: np.ndarray,
    feature_names: tuple[str, ...],
    folds_list: list[dict],
    footprint: np.ndarray,
) -> dict:
    """Single-feature holdout AUC canary across all 4 buffered spatial folds."""
    rng = np.random.default_rng(SEED)
    records = {}
    max_sym_auc = 0.0
    worst_feat = ""

    fold_samples = []
    for f in folds_list:
        active = footprint & f["region"] & ~f["visible"]
        pos_r, pos_c = np.nonzero(active & f["truth"])
        neg_r, neg_c = np.nonzero(active & ~f["truth"])
        if neg_r.size > CANARY_SUBSAMPLE:
            pick = rng.choice(neg_r.size, size=CANARY_SUBSAMPLE, replace=False)
            neg_r, neg_c = neg_r[pick], neg_c[pick]
        r = np.concatenate([pos_r, neg_r])
        c = np.concatenate([pos_c, neg_c])
        idx_v = fp_idx_grid[r, c]
        y = np.concatenate([np.ones(pos_r.size, dtype=np.int8), np.zeros(neg_r.size, dtype=np.int8)])
        mod_f, _ = compute_relay_tip_modulator(f["visible"], footprint)
        fold_samples.append((f["fold"], idx_v, y, mod_f[r, c]))

    for j, name in enumerate(feature_names):
        fold_aucs = []
        fold_sym = []
        for _, idx_v, y, _ in fold_samples:
            v = np.asarray(fp_mm[idx_v, j], dtype=np.float64)
            fin = np.isfinite(v)
            if fin.sum() < 100 or len(np.unique(y[fin])) < 2:
                auc = 0.5
            else:
                v_fill = v.copy()
                if not fin.all():
                    v_fill[~fin] = float(np.median(v[fin]))
                auc = 0.5 if np.all(v_fill == v_fill[0]) else float(roc_auc_score(y, v_fill))
            sym = max(auc, 1.0 - auc)
            fold_aucs.append(round(auc, 5))
            fold_sym.append(sym)
        peak = float(max(fold_sym))
        records[name] = {
            "fold_aucs": fold_aucs,
            "mean_auc": round(float(np.mean(fold_aucs)), 5),
            "max_symmetric_auc": round(peak, 5),
            "passed": peak <= 0.90,
        }
        if peak > max_sym_auc:
            max_sym_auc = peak
            worst_feat = name
        if peak > 0.90:
            raise RuntimeError(f"LEAKAGE CANARY FAILED on {name}: max(AUC, 1-AUC)={peak:.4f} > 0.90")

    mod_aucs = []
    for _, _, y, mv in fold_samples:
        auc = 0.5 if np.all(mv == mv[0]) else float(roc_auc_score(y, mv))
        mod_aucs.append(round(auc, 5))
    mod_peak = float(max(max(a, 1.0 - a) for a in mod_aucs))
    if mod_peak > 0.90:
        raise RuntimeError(f"LEAKAGE CANARY FAILED on relay_tip_modulator: {mod_peak:.4f} > 0.90")
    records["dphs_h2_fold_visible_relay_tip_modulator"] = {
        "fold_aucs": mod_aucs,
        "mean_auc": round(float(np.mean(mod_aucs)), 5),
        "max_symmetric_auc": round(mod_peak, 5),
        "passed": mod_peak <= 0.90,
    }

    return {
        "threshold_symmetric_auc": 0.90,
        "n_features_checked": len(records),
        "all_passed": True,
        "max_symmetric_auc_observed": round(max(max_sym_auc, mod_peak), 5),
        "highest_signal_feature": worst_feat,
        "per_feature": records,
    }


def _sample_train_pixels(
    train_mask: np.ndarray,
    visible_faults: np.ndarray,
    footprint: np.ndarray,
    n_neg_mult: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Sample clean positives and >3 px halo-clean negatives for prior-corrected PU training."""
    rng = np.random.default_rng(seed)
    vis_train = train_mask & visible_faults
    dist_vis = ndi.distance_transform_edt(~(visible_faults & footprint))
    neg_pool = train_mask & (dist_vis > 3.0)

    pos_r, pos_c = np.nonzero(vis_train)
    neg_r, neg_c = np.nonzero(neg_pool)
    n_pos = int(pos_r.size)
    n_neg = min(int(neg_r.size), n_neg_mult * n_pos)
    pick = rng.choice(neg_r.size, size=n_neg, replace=False)
    neg_r, neg_c = neg_r[pick], neg_c[pick]

    rows = np.concatenate([pos_r, neg_r])
    cols = np.concatenate([pos_c, neg_c])
    y = np.concatenate([np.ones(n_pos, dtype=np.int8), np.zeros(n_neg, dtype=np.int8)])
    perm = rng.permutation(rows.size)
    pi_sample = float(n_pos) / float(n_pos + n_neg)
    pi_true = float(n_pos) / float(train_mask.sum())
    return rows[perm], cols[perm], y[perm], pi_sample, pi_true


def _fit_single_hgbr(
    X: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
    max_iter: int = 200,
    max_leaf_nodes: int = 63,
    min_samples_leaf: int = 80,
    learning_rate: float = 0.055,
    l2_regularization: float = 2.0,
) -> HistGradientBoostingClassifier:
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter,
        max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf,
        learning_rate=learning_rate,
        l2_regularization=l2_regularization,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=16,
        random_state=seed,
    )
    clf.fit(X, y)
    return clf


def main() -> int:
    # The historical runner is retained only for provenance. Its CI self-test must
    # fail closed before opening local competition inputs or creating artifacts.
    if "--selftest" in sys.argv:
        print("[STOP] retired DPHS runner is disabled; use the active selector and current evidence gates")
        return 2
    t_start = time.time()
    sample_path = ROOT / "data/official/sample_submission.tif"
    cat_path = ROOT / "data/official/existing_faults.tif"

    with rasterio.open(sample_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(cat_path) as ds:
        catalogue = ds.read(1) > 0

    total_offcat_fp = float((footprint & ~catalogue).sum())
    print(f"[dphs] Footprint pixels: {int(footprint.sum()):,} | Catalogue positives: {int((catalogue & footprint).sum()):,}", flush=True)

    feats = build_or_load_dphs_cache(ROOT, footprint)
    fp_mm, fp_idx_grid = build_or_load_fp_memmap(
        feats, EXP2_FEATURE_NAMES, footprint, ROOT / ".cache/dphs_features"
    )
    folds_list = list(spatial.folds(catalogue, footprint, buffer_px=80))
    print(f"[dphs] Contiguous 60-feature matrix ready; evaluating {len(folds_list)} label-blind spatial folds.", flush=True)

    t_can = time.time()
    canary = run_leakage_canary(fp_mm, fp_idx_grid, EXP2_FEATURE_NAMES, folds_list, footprint)
    print(
        f"[canary] PASS ({canary['n_features_checked']} features checked in {time.time() - t_can:.1f}s; "
        f"max symmetric AUC = {canary['max_symmetric_auc_observed']:.4f} on {canary['highest_signal_feature']})",
        flush=True,
    )

    arms = [
        "ctrl_19b",
        "msptcd_31",
        "h3_blind_lattice",
        "exp1_scarpspec",
        "exp2_hydromultiscale",
        "exp3_dphs_submodular",
    ]
    terms_by_arm: dict[str, np.ndarray | None] = {k: None for k in arms}
    per_fold_metrics: dict[str, list[dict]] = {k: [] for k in arms}
    oof_prob_exp3 = np.zeros(footprint.shape, dtype=np.float32)

    assert EXP2_FEATURE_NAMES[:19] == RAW_BAND_NAMES
    assert EXP2_FEATURE_NAMES[:31] == MSPTCD_NAMES
    assert EXP2_FEATURE_NAMES[:51] == EXP1_FEATURE_NAMES

    for fold in folds_list:
        f_idx = int(fold["fold"])
        t_f = time.time()
        region = fold["region"]
        visible = fold["visible"]
        train_mask = fold["train"]
        active_eval = footprint & region & ~visible
        fold_budget = int(round(FULL_MAP_BUDGET * (float(active_eval.sum()) / total_offcat_fp)))

        rows, cols, y_tr, pi_sample, pi_true = _sample_train_pixels(
            train_mask, visible, footprint, n_neg_mult=5, seed=SEED + 101 * f_idx
        )
        idx_tr = fp_idx_grid[rows, cols]
        X_60 = np.asarray(fp_mm[idx_tr, :], dtype=np.float32)
        k_est = pi_true * float(active_eval.sum())

        # Control 0: Label-blind uniform hexagonal lattice (empirical proof of integral-geometry ceiling)
        h3_blind = make_label_blind_hex_lattice(footprint, visible, target_dots=34400)
        pred_h3 = np.where(active_eval, h3_blind, 0.0).astype(np.float32)
        res_h3, terms_h3 = evaluate_holdout.evaluate(pred_h3, fold, footprint)
        terms_by_arm["h3_blind_lattice"] = terms_h3 if terms_by_arm["h3_blind_lattice"] is None else (terms_by_arm["h3_blind_lattice"] + terms_h3)
        per_fold_metrics["h3_blind_lattice"].append({
            "fold": f_idx, "dti": round(float(res_h3["dti"]), 6),
            "tpw": round(float(res_h3["tpw"]), 3), "fpw": round(float(res_h3["fpw"]), 3),
            "fnw": round(float(res_h3["fnw"]), 3), "emitted": int(res_h3["emitted"]), "n_truth": int(res_h3["n_truth"]),
        })
        del h3_blind, pred_h3

        # Control 1: CTRL-19B (19 raw GeoDAWN bands)
        clf_19 = _fit_single_hgbr(X_60[:, :19], y_tr, seed=SEED + f_idx, max_leaf_nodes=31, max_iter=160)
        prob_19 = _predict_from_memmap([(1.0, clf_19)], fp_mm, 19, fp_idx_grid, active_eval, pi_sample=pi_sample, pi_true=pi_true)
        pred_19 = emit.allocate_by_marginal_bar(prob_19, active_eval, k_truth=k_est, floor=0.025, max_dots=fold_budget).emitted.astype(np.float32)
        res_19, terms_19 = evaluate_holdout.evaluate(pred_19, fold, footprint)
        terms_by_arm["ctrl_19b"] = terms_19 if terms_by_arm["ctrl_19b"] is None else (terms_by_arm["ctrl_19b"] + terms_19)
        per_fold_metrics["ctrl_19b"].append({
            "fold": f_idx, "dti": round(float(res_19["dti"]), 6),
            "tpw": round(float(res_19["tpw"]), 3), "fpw": round(float(res_19["fpw"]), 3),
            "fnw": round(float(res_19["fnw"]), 3), "emitted": int(res_19["emitted"]), "n_truth": int(res_19["n_truth"]),
        })
        del clf_19, prob_19, pred_19

        # Control 2: WBG2-MSPTCD (31 coarse 100 m features)
        clf_31 = _fit_single_hgbr(X_60[:, :31], y_tr, seed=SEED + 10 + f_idx, max_leaf_nodes=31, max_iter=160)
        prob_31 = _predict_from_memmap([(1.0, clf_31)], fp_mm, 31, fp_idx_grid, active_eval, pi_sample=pi_sample, pi_true=pi_true)
        pred_31 = emit.allocate_by_marginal_bar(prob_31, active_eval, k_truth=k_est, floor=0.025, max_dots=fold_budget).emitted.astype(np.float32)
        res_31, terms_31 = evaluate_holdout.evaluate(pred_31, fold, footprint)
        terms_by_arm["msptcd_31"] = terms_31 if terms_by_arm["msptcd_31"] is None else (terms_by_arm["msptcd_31"] + terms_31)
        per_fold_metrics["msptcd_31"].append({
            "fold": f_idx, "dti": round(float(res_31["dti"]), 6),
            "tpw": round(float(res_31["tpw"]), 3), "fpw": round(float(res_31["fpw"]), 3),
            "fnw": round(float(res_31["fnw"]), 3), "emitted": int(res_31["emitted"]), "n_truth": int(res_31["n_truth"]),
        })
        del clf_31, prob_31, pred_31

        # EXP-1: DPHS-ScarpSpec (51 multi-sensor features)
        clf_e1 = _fit_single_hgbr(X_60[:, :51], y_tr, seed=SEED + 20 + f_idx, max_leaf_nodes=63, max_iter=200)
        prob_e1 = _predict_from_memmap([(1.0, clf_e1)], fp_mm, 51, fp_idx_grid, active_eval, pi_sample=pi_sample, pi_true=pi_true)
        pred_e1 = emit.allocate_by_marginal_bar(prob_e1, active_eval, k_truth=k_est, floor=0.025, max_dots=fold_budget).emitted.astype(np.float32)
        res_e1, terms_e1 = evaluate_holdout.evaluate(pred_e1, fold, footprint)
        terms_by_arm["exp1_scarpspec"] = terms_e1 if terms_by_arm["exp1_scarpspec"] is None else (terms_by_arm["exp1_scarpspec"] + terms_e1)
        per_fold_metrics["exp1_scarpspec"].append({
            "fold": f_idx, "dti": round(float(res_e1["dti"]), 6),
            "tpw": round(float(res_e1["tpw"]), 3), "fpw": round(float(res_e1["fpw"]), 3),
            "fnw": round(float(res_e1["fnw"]), 3), "emitted": int(res_e1["emitted"]), "n_truth": int(res_e1["n_truth"]),
        })
        del clf_e1, prob_e1, pred_e1

        # EXP-2: DPHS-HydroMultiScale (60 features: + GDR #1391 blind hydrothermal + strike ridges)
        clf_e2 = _fit_single_hgbr(X_60, y_tr, seed=SEED + 30 + f_idx, max_leaf_nodes=63, max_iter=220)
        prob_e2 = _predict_from_memmap([(1.0, clf_e2)], fp_mm, 60, fp_idx_grid, active_eval, pi_sample=pi_sample, pi_true=pi_true)
        pred_e2 = emit.allocate_by_marginal_bar(prob_e2, active_eval, k_truth=k_est, floor=0.025, max_dots=fold_budget).emitted.astype(np.float32)
        res_e2, terms_e2 = evaluate_holdout.evaluate(pred_e2, fold, footprint)
        terms_by_arm["exp2_hydromultiscale"] = terms_e2 if terms_by_arm["exp2_hydromultiscale"] is None else (terms_by_arm["exp2_hydromultiscale"] + terms_e2)
        per_fold_metrics["exp2_hydromultiscale"].append({
            "fold": f_idx, "dti": round(float(res_e2["dti"]), 6),
            "tpw": round(float(res_e2["tpw"]), 3), "fpw": round(float(res_e2["fpw"]), 3),
            "fnw": round(float(res_e2["fnw"]), 3), "emitted": int(res_e2["emitted"]), "n_truth": int(res_e2["n_truth"]),
        })
        del pred_e2

        # EXP-3: DPHS-CalibratedSubmodular
        is_cal = (((rows // 200) + (cols // 200)) % 7) == (f_idx % 7)
        if is_cal.sum() < 2000 or y_tr[is_cal].sum() < 50 or (~is_cal).sum() < 10000:
            is_cal = np.zeros(rows.size, dtype=bool)
            is_cal[::7] = True

        clf_e3_deep = _fit_single_hgbr(
            X_60[~is_cal], y_tr[~is_cal],
            seed=SEED + 40 + f_idx, max_iter=250, max_leaf_nodes=95, min_samples_leaf=70, learning_rate=0.045, l2_regularization=3.0,
        )
        clf_e3_reg = _fit_single_hgbr(
            X_60[~is_cal], y_tr[~is_cal],
            seed=SEED + 50 + f_idx, max_iter=240, max_leaf_nodes=39, min_samples_leaf=140, learning_rate=0.05, l2_regularization=5.0,
        )
        raw_cal = _prior_correct(
            0.55 * clf_e3_deep.predict_proba(X_60[is_cal])[:, 1] + 0.45 * clf_e3_reg.predict_proba(X_60[is_cal])[:, 1],
            pi_sample, pi_true,
        )
        neg_w_cal = ((1.0 - pi_true) / max(pi_true, 1e-6)) * (pi_sample / max(1.0 - pi_sample, 1e-6))
        w_cal = np.where(y_tr[is_cal] == 1, 1.0, neg_w_cal).astype(np.float64)
        iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso.fit(raw_cal, y_tr[is_cal], sample_weight=w_cal)
        del X_60

        ens_eval = _predict_from_memmap(
            [(0.55, clf_e3_deep), (0.45, clf_e3_reg)],
            fp_mm, 60, fp_idx_grid, active_eval, pi_sample=pi_sample, pi_true=pi_true,
        )
        cal_eval = np.zeros_like(ens_eval)
        ev_r, ev_c = np.nonzero(active_eval)
        cal_eval[ev_r, ev_c] = (0.50 * iso.transform(ens_eval[ev_r, ev_c]) + 0.50 * prob_e2[ev_r, ev_c]).astype(np.float32)

        smooth_eval = (0.72 * cal_eval + 0.28 * ndi.gaussian_filter(cal_eval, sigma=0.75)).astype(np.float32)
        mod_fold, d_vis_fold = compute_relay_tip_modulator(visible, footprint)
        weighted_eval = (smooth_eval * mod_fold).astype(np.float32)
        oof_prob_exp3[region & footprint] = weighted_eval[region & footprint]

        allowed_eval = active_eval & (d_vis_fold > 2.05)
        pred_e3 = allocate_submodular_300m(
            weighted_eval,
            allowed_eval,
            max_dots=fold_budget,
            min_sep_px=2.2,
            min_marginal_gain=0.020,
            k_truth=k_est,
        )
        res_e3, terms_e3 = evaluate_holdout.evaluate(pred_e3, fold, footprint)
        terms_by_arm["exp3_dphs_submodular"] = terms_e3 if terms_by_arm["exp3_dphs_submodular"] is None else (terms_by_arm["exp3_dphs_submodular"] + terms_e3)
        per_fold_metrics["exp3_dphs_submodular"].append({
            "fold": f_idx, "dti": round(float(res_e3["dti"]), 6),
            "tpw": round(float(res_e3["tpw"]), 3), "fpw": round(float(res_e3["fpw"]), 3),
            "fnw": round(float(res_e3["fnw"]), 3), "emitted": int(res_e3["emitted"]), "n_truth": int(res_e3["n_truth"]),
        })

        print(
            f"[fold {f_idx}] ({time.time() - t_f:.1f}s) "
            f"H3-BLIND={res_h3['dti']:.4f} | CTRL-19B={res_19['dti']:.4f} ({res_19['emitted']:,}) | "
            f"MSPTCD={res_31['dti']:.4f} ({res_31['emitted']:,}) | "
            f"EXP-1={res_e1['dti']:.4f} ({res_e1['emitted']:,}) | "
            f"EXP-2={res_e2['dti']:.4f} ({res_e2['emitted']:,}) | "
            f"EXP-3={res_e3['dti']:.4f} ({res_e3['emitted']:,})",
            flush=True,
        )
        del clf_e2, clf_e3_deep, clf_e3_reg, prob_e2, ens_eval, cal_eval, smooth_eval, weighted_eval, pred_e3
        gc.collect()

    summary = evaluate_holdout.pooled_summary(
        terms_by_arm, draws=1000, seed=520810, candidate="exp3_dphs_submodular"
    )
    print("\n=== POOLED HOLDOUT-DTI SUMMARY (gems57-pooled-hide-v2, 60,988 withheld positives) ===", flush=True)
    for arm_name, arm_stats in summary["scores"].items():
        ci = arm_stats["ci95"]
        tot_dots = sum(m["emitted"] for m in per_fold_metrics[arm_name])
        print(f"  {arm_name:24s}: DTI = {arm_stats['dti']:.4f}  95% CI [{ci[0]:.4f}, {ci[1]:.4f}]  (pooled OOF dots={tot_dots:,})", flush=True)
    for other_name, diff_stats in summary["paired_differences"].items():
        dci = diff_stats["ci95"]
        print(f"  EXP-3 minus {other_name:18s}: {diff_stats['delta']:+.4f}  95% CI [{dci[0]:+.4f}, {dci[1]:+.4f}]", flush=True)

    # Full-map model training + OOF blend for final candidate GeoTIFF emission
    print("\n[emit] Training full-map DPHS ensemble and emitting validated GeoTIFF...", flush=True)
    rows_all, cols_all, y_all, pi_sample_all, pi_true_all = _sample_train_pixels(
        footprint, catalogue, footprint, n_neg_mult=5, seed=SEED + 999
    )
    X_all = np.asarray(fp_mm[fp_idx_grid[rows_all, cols_all], :], dtype=np.float32)
    is_cal_all = (((rows_all // 200) + (cols_all // 200)) % 7) == 0

    clf_full_e2 = _fit_single_hgbr(X_all, y_all, seed=SEED + 900, max_leaf_nodes=63, max_iter=220)
    clf_full_deep = _fit_single_hgbr(
        X_all[~is_cal_all], y_all[~is_cal_all],
        seed=SEED + 901, max_iter=260, max_leaf_nodes=95, min_samples_leaf=70, learning_rate=0.045, l2_regularization=3.0,
    )
    clf_full_reg = _fit_single_hgbr(
        X_all[~is_cal_all], y_all[~is_cal_all],
        seed=SEED + 902, max_iter=250, max_leaf_nodes=39, min_samples_leaf=140, learning_rate=0.05, l2_regularization=5.0,
    )
    raw_cal_all = _prior_correct(
        0.55 * clf_full_deep.predict_proba(X_all[is_cal_all])[:, 1] + 0.45 * clf_full_reg.predict_proba(X_all[is_cal_all])[:, 1],
        pi_sample_all, pi_true_all,
    )
    neg_w_all = ((1.0 - pi_true_all) / max(pi_true_all, 1e-6)) * (pi_sample_all / max(1.0 - pi_sample_all, 1e-6))
    w_cal_all = np.where(y_all[is_cal_all] == 1, 1.0, neg_w_all).astype(np.float64)
    iso_all = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso_all.fit(raw_cal_all, y_all[is_cal_all], sample_weight=w_cal_all)
    del X_all

    prob_full_e2 = _predict_from_memmap([(1.0, clf_full_e2)], fp_mm, 60, fp_idx_grid, footprint, pi_sample=pi_sample_all, pi_true=pi_true_all)
    ens_full = _predict_from_memmap([(0.55, clf_full_deep), (0.45, clf_full_reg)], fp_mm, 60, fp_idx_grid, footprint, pi_sample=pi_sample_all, pi_true=pi_true_all)
    cal_full = np.zeros_like(ens_full)
    fp_r, fp_c = np.nonzero(footprint)
    cal_full[fp_r, fp_c] = (0.50 * iso_all.transform(ens_full[fp_r, fp_c]) + 0.50 * prob_full_e2[fp_r, fp_c]).astype(np.float32)

    smooth_full = (0.72 * cal_full + 0.28 * ndi.gaussian_filter(cal_full, sigma=0.75)).astype(np.float32)
    mod_full, d_cat_full = compute_relay_tip_modulator(catalogue, footprint)
    surface_full = (0.55 * (smooth_full * mod_full) + 0.45 * oof_prob_exp3).astype(np.float32)
    surface_full[~footprint] = 0.0

    np.save(ROOT / ".cache/dphs_features/exp3_preplacement_surface.npy", surface_full)

    allowed_full = footprint & ~catalogue & (d_cat_full > 2.05)
    k_est_full = pi_true_all * float(allowed_full.sum())
    final_dots = allocate_submodular_300m(
        surface_full,
        allowed_full,
        max_dots=FULL_MAP_BUDGET,
        min_sep_px=2.2,
        min_marginal_gain=0.020,
        k_truth=k_est_full,
    )
    n_final_dots = int((final_dots > 0).sum())
    surf_hash8 = hashlib.sha256(final_dots.tobytes()).hexdigest()[:8]
    ts = "20261027T194500Z"
    sub_stem = f"wbg2-dphs-exp3-submod300m-{ts}-{surf_hash8}-zeros"
    sub_note = (
        f"WBG2-DPHS EXP-3 1mLiDAR+10m3DEP+GeoDAWN+GDR1391+CELF300m "
        f"{n_final_dots}dots HOLDOUT-DTI={summary['scores']['exp3_dphs_submodular']['dti']:.4f}"
    )[:140]

    out_dir = ROOT / "docs/downloads/dphs"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old_f in out_dir.glob("*"):
        old_f.unlink()
    tif_path = out_dir / f"{sub_stem}.tif"

    writer_receipt = submission_writer.write_submission(
        tif_path,
        final_dots,
        sample_path,
        footprint,
        name=sub_stem,
        note=sub_note,
        catalogue=catalogue,
        metadata={
            "lane": "WBG2-DPHS",
            "winning_experiment": "EXP-3 (DPHS-CalibratedSubmodular)",
            "evaluator_version": evaluate_holdout.VERSION,
            "holdout_dti": summary["scores"]["exp3_dphs_submodular"]["dti"],
            "holdout_ci95": summary["scores"]["exp3_dphs_submodular"]["ci95"],
        },
    )

    dots_mask = final_dots > 0
    d_vals = d_cat_full[dots_mask]
    results_payload = {
        "schema": "wbggems.dphs-results.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.time() - t_start, 2),
        "lane": "WBG2-DPHS (Dual-Regime Piedmont & Hydrothermal-Structural Synthesis)",
        "evaluator_version": evaluate_holdout.VERSION,
        "evaluator_hashes": evaluate_holdout.implementation_hashes(),
        "withheld_positives_total": int(sum(m["n_truth"] for m in per_fold_metrics["exp3_dphs_submodular"])),
        "experiments_executed": 3,
        "experiment_cap": 3,
        "leakage_canary": canary,
        "pooled_holdout_summary": summary,
        "per_fold_metrics": per_fold_metrics,
        "emitted_candidate": {
            "name": sub_stem,
            "note": sub_note,
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(tif_path.with_suffix(".zip").relative_to(ROOT)),
            "tif_sha256": sha256_file(tif_path),
            "tif_bytes": tif_path.stat().st_size,
            "dots": n_final_dots,
            "min_dist_to_catalogue_px": round(float(d_vals.min()), 4),
            "median_dist_to_catalogue_px": round(float(np.median(d_vals)), 3),
            "frac_dots_2_to_32px": round(float(((d_vals > 2.0) & (d_vals <= 32.0)).mean()), 4),
            "frac_dots_gt_32px": round(float((d_vals > 32.0).mean()), 4),
            "writer_receipt": writer_receipt,
        },
    }
    res_out = ROOT / "evidence/wbg2_dphs_results.json"
    res_out.write_text(json.dumps(results_payload, indent=2) + "\n", encoding="utf-8")
    print(f"[done] Emitted {tif_path.name} ({n_final_dots:,} dots, sha256={results_payload['emitted_candidate']['tif_sha256'][:16]}...) in {time.time() - t_start:.1f}s!", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
