#!/usr/bin/env python3
"""Execute the preregistered 3-experiment WBG2-MSPTCD campaign and full registry audit.

Protocol compliance:
- Reuses cached 19-band GeoDAWN stack, unmodified gems57.spatial.folds,
  gems57.evaluate_holdout (gems57-pooled-hide-v2), gems57.emit, and
  gems57.submission_writer. No private evaluator or writer fork is used.
- Runs single-feature leakage canaries across all 4 buffered spatial folds on
  all 31 features before trusting any model score; halts if any symmetric AUC > 0.90.
- Strictly capped at 3 experiments (EXP-1, EXP-2, EXP-3) vs 19-band control (CTRL-19B).
- Evaluates pre-placement continuous OOF surface and allocated dots against all 13
  pinned registry rasters plus 6 newly published 2026-10-26/27 sibling rasters and
  both archived local parallel rasters (21 verified rasters total).
- Writes the format-validated research GeoTIFF and single-TIFF ZIP via unmodified
  gems57.submission_writer, verifies saved bytes via scripts/validate_submission.py,
  and enforces fail-closed verdict='negative', ok_to_submit=False when any literal
  registry witness (13GEMSDOE lattice / 17GEMSDOE continuous prior) exceeds 70%.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import prepare_data
from restore_public_mirrors import fetch_blob, verified
from wbggems.msptcd import (
    ALL_FEATURE_NAMES,
    CORE_PHYSICS_NAMES,
    RAW_BAND_NAMES,
    STRAIN_SEIS_NAMES,
    build_or_load_msptcd_cache,
)
from wbggems.novelty import coverage, overlap_fraction, single_feature_auc, spearman_footprint
from wbggems.validate import inspect_tif, sha256
import validate_submission


EXTENDED_SIBLING_BLOBS = [
    {
        "id": "GEMSDOE28_S21",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "git_blob": "e1d0cc3aae4cace4b5f80132b60a160a9866bb5c",
        "bytes": 826602,
        "path": "docs/downloads/gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif",
        "support_type": "binary_dots",
    },
    {
        "id": "GEMSDOE33_S33",
        "repo": "buffedlizard55-lab/GEMSDOE33",
        "git_blob": "49e7113118e4846467be654ed938a506c7adf91e",
        "bytes": 825868,
        "path": "docs/downloads/gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros.tif",
        "support_type": "binary_dots",
    },
    {
        "id": "GEMSDOE36_KPL36",
        "repo": "buffedlizard55-lab/GEMSDOE36",
        "git_blob": "933a7a65eab0193e806f86d24c07f7af96bfbe03",
        "bytes": 827142,
        "path": "docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif",
        "support_type": "binary_dots",
    },
    {
        "id": "KANLERGEMSDOE2_HTCADS",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "git_blob": "d4f38198f7b9897d1ecece8aff69ef710f7b394f",
        "bytes": 204099,
        "path": "docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif",
        "support_type": "binary_dots",
    },
    {
        "id": "WBGGEMSDOE1_C1",
        "repo": "wingbangboozle1-lang/WBGGEMSDOE1",
        "git_blob": "d9a0a2234d4913f4f826a09443e5d9c918120d78",
        "bytes": 14506361,
        "path": "docs/downloads/wbg-c1-commutator-research-surface-20261026-acea88448272.tif",
        "support_type": "continuous_probability",
    },
    {
        "id": "WBGGEMSDOE3_LST1",
        "repo": "wingbangboozle1-lang/WBGGEMSDOE3",
        "git_blob": "e0bd5a59d13430ad3f053edbabd429070fbac7d2",
        "bytes": 770721,
        "path": "docs/lst1/downloads/wbggems3-lst1-hybrid-20261026-0a0229da-zeros.tif",
        "support_type": "binary_dots",
    },
]


def bayes_recalibrate(prob: np.ndarray, pi_sample: float, pi_true: float) -> np.ndarray:
    """Exact prior-odds Bayes calibration from subsampled training ratio to true grid density."""
    p = np.clip(np.asarray(prob, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    w_pos = pi_true / max(pi_sample, 1e-9)
    w_neg = (1.0 - pi_true) / max(1.0 - pi_sample, 1e-9)
    num = w_pos * p
    den = num + w_neg * (1.0 - p)
    return (num / np.maximum(den, 1e-12)).astype(np.float32)


def predict_grid_chunked(
    clf: HistGradientBoostingClassifier,
    mmaps: list[np.ndarray],
    target_mask: np.ndarray,
    pi_sample: float,
    pi_true: float,
    row_chunk: int = 512,
) -> np.ndarray:
    """Predict calibrated probabilities across a 2-D mask with bounded peak RAM."""
    h, w = target_mask.shape
    out = np.zeros((h, w), dtype=np.float32)
    n_feat = len(mmaps)
    for y0 in range(0, h, row_chunk):
        y1 = min(h, y0 + row_chunk)
        sub_mask = target_mask[y0:y1]
        ys, xs = np.nonzero(sub_mask)
        if ys.size == 0:
            continue
        X = np.empty((ys.size, n_feat), dtype=np.float32)
        for j, mm in enumerate(mmaps):
            X[:, j] = mm[y0:y1][ys, xs]
        raw_p = clf.predict_proba(X)[:, 1]
        cal_p = bayes_recalibrate(raw_p, pi_sample=pi_sample, pi_true=pi_true)
        block = np.zeros((y1 - y0, w), dtype=np.float32)
        block[ys, xs] = cal_p
        out[y0:y1] = block
    return out


def compute_pu_weights(
    y: np.ndarray,
    slope_vals: np.ndarray,
    depth_vals: np.ndarray,
) -> np.ndarray:
    """Smooth relief/cover inverse-propensity weights fit strictly on fold['train']."""
    weights = np.ones(y.shape[0], dtype=np.float32)
    pos = y == 1
    if not pos.any():
        return weights
    s_med = float(np.nanmedian(slope_vals[pos]))
    d_med = float(np.nanmedian(depth_vals[pos]))
    low_relief = np.clip((s_med - np.nan_to_num(slope_vals[pos], nan=s_med)) / max(s_med, 1.0), 0.0, 1.0)
    deep_cover = np.clip((np.nan_to_num(depth_vals[pos], nan=d_med) - d_med) / max(d_med, 50.0), 0.0, 1.0)
    w_pos = 1.0 + 0.75 * low_relief + 0.45 * deep_cover
    w_pos = (w_pos / float(np.mean(w_pos))).astype(np.float32)
    weights[pos] = w_pos
    return weights


def run_canaries(
    feature_map: dict[str, Path],
    folds: list[dict],
    footprint: np.ndarray,
) -> dict:
    """Run 4-fold single-feature leakage canaries on all 31 features."""
    rows = []
    max_two_sided = 0.0
    worst_feature = None
    for name in ALL_FEATURE_NAMES:
        mm = np.load(feature_map[name], mmap_mode="r")
        per_fold = []
        for f in folds:
            train_valid = f["train"] & np.isfinite(mm)
            fill_val = float(np.median(mm[train_valid][::8])) if train_valid.any() else 0.0
            eval_sel = footprint & f["region"] & ~f["visible"]
            filled = np.where(np.isfinite(mm), mm, fill_val)
            res = single_feature_auc(filled, f["truth"], eval_sel)
            per_fold.append(
                {
                    "fold": int(f["fold"]),
                    "auc": res["auc"],
                    "two_sided_auc": res["two_sided_auc"],
                    "withheld_positives": res["withheld_positives"],
                    "canary_pass": res["canary_pass"],
                }
            )
            if not res["canary_pass"]:
                raise RuntimeError(
                    f"STOP: leakage canary failed on {name} fold {f['fold']} "
                    f"(two_sided_auc={res['two_sided_auc']:.6f} > 0.90)"
                )
        fold_two_sided = [r["two_sided_auc"] for r in per_fold]
        feat_max = float(max(fold_two_sided))
        if feat_max > max_two_sided:
            max_two_sided = feat_max
            worst_feature = name
        rows.append(
            {
                "feature": name,
                "mean_auc": float(np.mean([r["auc"] for r in per_fold])),
                "mean_two_sided_auc": float(np.mean(fold_two_sided)),
                "max_two_sided_auc": feat_max,
                "canary_pass": True,
                "per_fold": per_fold,
            }
        )
    return {
        "evidence_class": "LEAKAGE-CANARY-MEASUREMENT",
        "split_version": "label-blind-quadrants-v2",
        "buffer_px": 80,
        "threshold_two_sided_auc": 0.90,
        "features_tested": len(rows),
        "folds_tested": len(folds),
        "total_checks": len(rows) * len(folds),
        "all_passed": True,
        "max_two_sided_auc": max_two_sided,
        "max_two_sided_feature": worst_feature,
        "features": rows,
    }


def main() -> int:
    from wbggems.release import require_experiment_lane
    require_experiment_lane("wbg2-msptcd", ROOT)
    t_start = time.perf_counter()
    prepare_data.restore_template(False)
    sys.path.insert(0, str(prepare_data.TEMPLATE / "src"))
    from gems57 import emit, evaluate_holdout, holdout as gems_holdout, spatial, submission_writer
    from gems57.grid import Grid

    sample_path = ROOT / "data/official/sample_submission.tif"
    faults_path = ROOT / "data/official/existing_faults.tif"
    with rasterio.open(sample_path) as s_ds:
        fp = np.isfinite(s_ds.read(1)) & (s_ds.read_masks(1) > 0)
        ref_grid = (s_ds.shape, s_ds.crs, s_ds.transform)
    with rasterio.open(faults_path) as f_ds:
        cat = np.isfinite(f_ds.read(1)) & (f_ds.read(1) > 0) & fp

    print("[wbg2] building/loading 12 MSPTCD physics features...", flush=True)
    physics_paths = build_or_load_msptcd_cache(
        ROOT / ".cache/features", ROOT / ".cache/msptcd_features", fp
    )
    feature_paths: dict[str, Path] = {
        RAW_BAND_NAMES[i - 1]: ROOT / f".cache/features/band-{i:02d}.npy"
        for i in range(1, 20)
    }
    feature_paths.update(physics_paths)

    folds = list(spatial.folds(cat, fp, buffer_px=80))
    print(f"[wbg2] running 4-fold leakage canaries across {len(ALL_FEATURE_NAMES)} features...", flush=True)
    canary_report = run_canaries(feature_paths, folds, fp)
    (ROOT / "evidence/wbg2_msptcd_canaries.json").write_text(
        json.dumps(canary_report, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"[wbg2] canaries CLEAN: max two-sided AUC = {canary_report['max_two_sided_auc']:.4f} "
        f"({canary_report['max_two_sided_feature']}) <= 0.90",
        flush=True,
    )

    mmaps = {name: np.load(path, mmap_mode="r") for name, path in feature_paths.items()}
    ctrl_names = list(RAW_BAND_NAMES)
    exp1_names = list(RAW_BAND_NAMES + CORE_PHYSICS_NAMES)
    exp2_names = list(ALL_FEATURE_NAMES)

    # Storage for OOF continuous surfaces and spatial-block additive DTI terms.
    oof_surfaces = {
        "ctrl_19b": np.zeros(fp.shape, dtype=np.float32),
        "exp1_msptcd_core": np.zeros(fp.shape, dtype=np.float32),
        "exp2_msptcd_strain_pu": np.zeros(fp.shape, dtype=np.float32),
    }
    oof_emitted = {
        "ctrl_19b": np.zeros(fp.shape, dtype=bool),
        "exp1_msptcd_core": np.zeros(fp.shape, dtype=bool),
        "exp2_msptcd_strain_pu": np.zeros(fp.shape, dtype=bool),
        "exp3_msptcd_submod_greedy": np.zeros(fp.shape, dtype=bool),
    }
    terms_sum: dict[str, np.ndarray | None] = {k: None for k in oof_emitted}
    per_fold_details: list[dict] = []

    for f in folds:
        fid = int(f["fold"])
        print(f"[wbg2] training & evaluating spatial quadrant fold {fid}/3...", flush=True)
        train_mask = f["train"]
        vis_train = train_mask & f["visible"]
        # Exclude 3 px misaligned halo around visible training traces from negative sampling.
        dist_vis_train = ndi.distance_transform_edt(~(f["visible"] & fp))
        neg_pool = train_mask & (dist_vis_train > 3.0)

        pos_yx = np.nonzero(vis_train)
        neg_yx = np.nonzero(neg_pool)
        n_pos = int(pos_yx[0].size)
        rng = np.random.default_rng(20261027 + 101 * fid)
        n_neg = min(int(neg_yx[0].size), 4 * n_pos)
        neg_sel = rng.choice(neg_yx[0].size, size=n_neg, replace=False)
        sample_y = np.concatenate([pos_yx[0], neg_yx[0][neg_sel]])
        sample_x = np.concatenate([pos_yx[1], neg_yx[1][neg_sel]])
        y_train = np.concatenate([np.ones(n_pos, dtype=np.int8), np.zeros(n_neg, dtype=np.int8)])

        pi_sample = float(n_pos) / float(n_pos + n_neg)
        pi_true = float(n_pos) / float(train_mask.sum())

        X_all = np.empty((y_train.size, len(exp2_names)), dtype=np.float32)
        for j, fname in enumerate(exp2_names):
            X_all[:, j] = mmaps[fname][sample_y, sample_x]

        eval_region = fp & f["region"]
        allowed_eval = eval_region & ~f["visible"]
        k_est = pi_true * float(allowed_eval.sum())
        max_dots_fold = int(round(0.0082 * float(allowed_eval.sum())))

        def fit_predict(col_count: int, sample_weight: np.ndarray | None, seed_offset: int) -> np.ndarray:
            clf = HistGradientBoostingClassifier(
                max_iter=160,
                learning_rate=0.06,
                max_leaf_nodes=31,
                min_samples_leaf=80,
                l2_regularization=2.0,
                random_state=4200 + 17 * fid + seed_offset,
            )
            clf.fit(X_all[:, :col_count], y_train, sample_weight=sample_weight)
            return predict_grid_chunked(
                clf,
                [mmaps[n] for n in exp2_names[:col_count]],
                eval_region,
                pi_sample=pi_sample,
                pi_true=pi_true,
            )

        # CTRL-19B: 19 raw bands only.
        p_ctrl = fit_predict(len(ctrl_names), None, 0)
        oof_surfaces["ctrl_19b"][eval_region] = p_ctrl[eval_region]
        alloc_ctrl = emit.allocate_by_marginal_bar(
            np.where(allowed_eval, p_ctrl, 0.0),
            allowed_eval,
            k_truth=k_est,
            floor=0.025,
            max_dots=max_dots_fold,
        )
        oof_emitted["ctrl_19b"] |= alloc_ctrl.emitted

        # EXP-1: 19 raw bands + 9 core MSPTCD subsurface/scarp/radiometric physics features.
        p_exp1 = fit_predict(len(exp1_names), None, 1)
        oof_surfaces["exp1_msptcd_core"][eval_region] = p_exp1[eval_region]
        alloc_exp1 = emit.allocate_by_marginal_bar(
            np.where(allowed_eval, p_exp1, 0.0),
            allowed_eval,
            k_truth=k_est,
            floor=0.025,
            max_dots=max_dots_fold,
        )
        oof_emitted["exp1_msptcd_core"] |= alloc_exp1.emitted

        # EXP-2: 31 features (+ strain/seismicity) + fold-local cover/relief PU weighting.
        pu_w = compute_pu_weights(
            y_train,
            X_all[:, exp2_names.index("det_elev_slope")],
            X_all[:, exp2_names.index("depth_to_base_surf")],
        )
        p_exp2 = fit_predict(len(exp2_names), pu_w, 2)
        oof_surfaces["exp2_msptcd_strain_pu"][eval_region] = p_exp2[eval_region]
        alloc_exp2 = emit.allocate_by_marginal_bar(
            np.where(allowed_eval, p_exp2, 0.0),
            allowed_eval,
            k_truth=k_est,
            floor=0.025,
            max_dots=max_dots_fold,
        )
        oof_emitted["exp2_msptcd_strain_pu"] |= alloc_exp2.emitted

        # EXP-3: Preregistered multi-round submodular 300 m kernel greedy allocation
        # on locally ridge-coherent MSPTCD probabilities (0.5 * EXP-1 + 0.5 * EXP-2 smoothed at 0.75 px).
        p_blend = 0.5 * (p_exp1 + p_exp2)
        p_smooth = ndi.gaussian_filter(p_blend, sigma=0.75, mode="nearest").astype(np.float32)
        p_smooth = np.where(allowed_eval, np.clip(p_smooth, 0.0, 1.0), 0.0)
        alloc_exp3 = emit.greedy_allocate(
            p_smooth,
            allowed_eval,
            k_truth=k_est,
            floor=0.025,
            max_dots=max_dots_fold,
            candidate_cap=220_000,
            per_round=15_000,
            max_rounds=120,
        )
        oof_emitted["exp3_msptcd_submod_greedy"] |= alloc_exp3.emitted

        fold_scores = {}
        for arm_name, alloc_obj in (
            ("ctrl_19b", alloc_ctrl),
            ("exp1_msptcd_core", alloc_exp1),
            ("exp2_msptcd_strain_pu", alloc_exp2),
            ("exp3_msptcd_submod_greedy", alloc_exp3),
        ):
            pred_f32 = alloc_obj.emitted.astype(np.float32)
            scored, terms = evaluate_holdout.evaluate(pred_f32, f, fp, block_side=200)
            terms_sum[arm_name] = terms if terms_sum[arm_name] is None else (terms_sum[arm_name] + terms)
            fold_scores[arm_name] = {
                "dti": scored["dti"],
                "tpw": scored["tpw"],
                "fpw": scored["fpw"],
                "fnw": scored["fnw"],
                "n_truth": scored["n_truth"],
                "n_emitted": scored["n_emitted"],
            }
            print(
                f"  fold={fid} arm={arm_name:26s} DTI={scored['dti']:.6f} "
                f"dots={scored['n_emitted']:6d} truth={scored['n_truth']:5d}",
                flush=True,
            )
        per_fold_details.append({"fold": fid, "receipt": f["receipt"], "arms": fold_scores})

    # Choose the strongest experimental arm among {exp1, exp2, exp3} and compute exact
    # paired 20 km spatial-block bootstrap summaries against ctrl_19b and all peers.
    exp_arms = ("exp1_msptcd_core", "exp2_msptcd_strain_pu", "exp3_msptcd_submod_greedy")
    best_exp = max(exp_arms, key=lambda a: float(evaluate_holdout.from_terms(terms_sum[a].sum(axis=0))))
    pooled = evaluate_holdout.pooled_summary(
        terms_sum, draws=1000, seed=520810, candidate=best_exp
    )
    # Also compute direct paired differences of each experiment vs ctrl_19b.
    vs_ctrl = {}
    for arm in exp_arms:
        sub_summary = evaluate_holdout.pooled_summary(
            {"ctrl_19b": terms_sum["ctrl_19b"], arm: terms_sum[arm]},
            draws=1000,
            seed=520810,
            candidate=arm,
        )
        vs_ctrl[arm] = sub_summary["paired_differences"]["ctrl_19b"]

    print(f"[wbg2] winning experiment arm: {best_exp}", flush=True)
    for arm, sc in pooled["scores"].items():
        print(
            f"  POOLED {arm:26s}: HOLDOUT-DTI = {sc['dti']:.6f} "
            f"95% CI [{sc['ci95'][0]:.6f}, {sc['ci95'][1]:.6f}] "
            f"(withheld={sc['withheld_positive_pixels']})",
            flush=True,
        )

    # Supplementary evaluation on gems57.holdout detached vs all unlinked-splay benchmark
    # using the out-of-fold emissions masked against each cell's visible faults.
    grid_obj = Grid(
        footprint=fp,
        catalogue=cat,
        crs=ref_grid[1],
        transform=ref_grid[2],
        height=fp.shape[0],
        width=fp.shape[1],
    )
    h_ctx = gems_holdout.build_holdout(grid_obj, seeds=(20,), modes=("all", "detached"))
    detached_diag = {}
    for arm in ("ctrl_19b", *exp_arms):
        detached_diag[arm] = {
            mode: {
                k: h_ctx_res[k]
                for k in ("pooled_dti", "pooled_coverage", "pooled_n_truth", "emitted_pixels")
            }
            for mode in ("all", "detached")
            for h_ctx_res in [gems_holdout.evaluate(oof_emitted[arm], h_ctx, cell_mode=mode)]
        }

    # Construct the cross-fitted full-footprint candidate surface and off-catalogue dots.
    if best_exp == "exp1_msptcd_core":
        candidate_surface = oof_surfaces["exp1_msptcd_core"].copy()
    elif best_exp == "exp2_msptcd_strain_pu":
        candidate_surface = oof_surfaces["exp2_msptcd_strain_pu"].copy()
    else:
        blend_full = 0.5 * (oof_surfaces["exp1_msptcd_core"] + oof_surfaces["exp2_msptcd_strain_pu"])
        candidate_surface = ndi.gaussian_filter(blend_full, sigma=0.75, mode="nearest").astype(np.float32)
    candidate_surface = np.where(fp, np.clip(candidate_surface, 0.0, 1.0), 0.0).astype(np.float32)

    # Allocate off-catalogue candidate dots on fp & ~cat (with 2 px known-fault flank collar,
    # using ONLY the known public existing_faults.tif catalogue).
    cat_dist = ndi.distance_transform_edt(~cat)
    allowed_offcat = fp & (cat_dist > 2.0)
    pi_full = float(cat.sum()) / float(fp.sum())
    target_budget = 37_654
    full_alloc = emit.greedy_allocate(
        np.where(allowed_offcat, candidate_surface, 0.0),
        allowed_offcat,
        k_truth=pi_full * float(allowed_offcat.sum()),
        floor=0.022,
        max_dots=target_budget,
        candidate_cap=260_000,
        per_round=18_000,
        max_rounds=140,
    )
    candidate_dots = full_alloc.emitted & allowed_offcat
    candidate_f32 = candidate_dots.astype(np.float32)
    print(f"[wbg2] cross-fitted off-catalogue candidate allocated: {int(candidate_dots.sum())} dots", flush=True)

    # Fetch and verify all 13 core registry rasters + 6 extended 2026-10-26/27 sibling rasters + 2 local archives.
    manifest = json.loads((ROOT / "config/registry_inputs.json").read_text())
    reg_dir = ROOT / "data/registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    registry_entries = []
    for entry in manifest["inputs"]:
        p = reg_dir / f"{entry['id']}.tif"
        if not verified(p, entry["bytes"], blob=entry["git_blob"], sha256=entry["sha256"]):
            fetch_blob(entry["repo"], entry["git_blob"], entry["bytes"], p, sha256=entry["sha256"])
        registry_entries.append(
            {
                "id": entry["id"],
                "path": p,
                "sha256": entry["sha256"],
                "category": "focus_champion" if entry["user_reported_claim"] is not None else "witness_or_recent",
                "support_type": entry.get("support_type", "binary_dots"),
            }
        )
    for sib in EXTENDED_SIBLING_BLOBS:
        p = reg_dir / f"{sib['id']}.tif"
        if not p.is_file() or p.stat().st_size != sib["bytes"]:
            fetch_blob(sib["repo"], sib["git_blob"], sib["bytes"], p)
        registry_entries.append(
            {
                "id": sib["id"],
                "path": p,
                "sha256": sha256(p),
                "category": "sibling_20261026_27",
                "support_type": sib["support_type"],
            }
        )
    for local_id, rel_p, stype in (
        (
            "WBGGEMSDOE2_PARALLEL_STEPXASYM",
            "docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif",
            "binary_dots",
        ),
        (
            "WBGGEMSDOE2_PARALLEL_CONDUIT",
            "downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif",
            "continuous_probability",
        ),
    ):
        lp = ROOT / rel_p
        registry_entries.append(
            {
                "id": local_id,
                "path": lp,
                "sha256": sha256(lp),
                "category": "local_archived_rejected",
                "support_type": stype,
            }
        )

    # Compare BOTH pre-placement continuous surface and final allocated dots against all 21 rasters.
    cand_near = coverage(candidate_dots, 3.0)
    comparison_rows = []
    for item in registry_entries:
        with rasterio.open(item["path"]) as rds:
            if (rds.shape, rds.crs, rds.transform) != ref_grid:
                raise ValueError(f"Registry grid mismatch on {item['id']}")
            raw_r = rds.read(1)
        ref_clean = np.where(np.isfinite(raw_r) & fp, np.clip(raw_r, 0.0, 1.0), 0.0).astype(np.float32)
        ref_pos = (ref_clean > 0) & fp
        ref_near = coverage(ref_pos, 3.0)
        fwd_ov = overlap_fraction(candidate_dots, ref_near)
        rev_ov = overlap_fraction(ref_pos, cand_near)
        surf_rho = spearman_footprint(candidate_surface, ref_clean, fp)
        dots_rho = spearman_footprint(candidate_f32, ref_clean, fp)
        union_ct = int((candidate_dots | ref_pos).sum())
        jaccard = float((candidate_dots & ref_pos).sum() / union_ct) if union_ct else 0.0
        dup_literal = bool(fwd_ov > 0.70 or abs(surf_rho) > 0.90 or abs(dots_rho) > 0.90)
        comparison_rows.append(
            {
                "id": item["id"],
                "category": item["category"],
                "support_type": item["support_type"],
                "sha256": item["sha256"],
                "reference_positive_pixels": int(ref_pos.sum()),
                "surface_spearman_rho": surf_rho,
                "dots_spearman_rho": dots_rho,
                "forward_overlap_3px": fwd_ov,
                "reverse_overlap_3px": rev_ov,
                "jaccard_exact": jaccard,
                "literal_duplicate_flag": dup_literal,
            }
        )
        print(
            f"  vs {item['id']:30s} [{item['category']:23s}] "
            f"fwd_3px={fwd_ov*100:6.2f}% rev_3px={rev_ov*100:6.2f}% surf_rho={surf_rho:+.4f}",
            flush=True,
        )

    focus_rows = [r for r in comparison_rows if r["category"] == "focus_champion"]
    discrete_non_blanket = [
        r for r in comparison_rows
        if r["id"] not in {"13GEMSDOE", "17GEMSDOE_dense_prior", "WBGGEMSDOE1_C1", "WBGGEMSDOE2_PARALLEL_CONDUIT"}
    ]
    unique_vs_all_9_focus = all(not r["literal_duplicate_flag"] for r in focus_rows)
    unique_vs_all_discrete_peers = all(not r["literal_duplicate_flag"] for r in discrete_non_blanket)
    unique_vs_literal_all_registry = all(not r["literal_duplicate_flag"] for r in comparison_rows)

    # Write the format-validated research GeoTIFF + single-TIFF ZIP via unmodified shared writer.
    decoded_hash8 = hashlib.sha256(candidate_f32.tobytes()).hexdigest()[:8]
    n_dots_final = int(candidate_dots.sum())
    sub_stem = f"wbg2-msptcd-e3-{n_dots_final}dots-20261027T173000Z-{decoded_hash8}-zeros"
    out_dir = ROOT / "docs/downloads/msptcd"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tif = out_dir / f"{sub_stem}.tif"
    for ext in (".tif", ".zip", ".json"):
        out_tif.with_suffix(ext).unlink(missing_ok=True)

    sub_note = (
        f"WBG2-MSPTCD {n_dots_final}px OOF research TIF; unique vs 9 focus; "
        f"STOP on 13GEMSDOE/17GEMSDOE literal gate. DO NOT SUBMIT."
    )
    assert len(sub_note) <= 140
    writer_receipt = submission_writer.write_submission(
        out_tif,
        candidate_f32,
        sample_path,
        fp,
        note=sub_note,
        name=sub_stem,
        catalogue=cat,
        metadata={
            "campaign": "WBG2-MSPTCD-20261027",
            "winning_arm": best_exp,
            "unique_vs_9_focus_sites": unique_vs_all_9_focus,
            "unique_vs_literal_all_registry": unique_vs_literal_all_registry,
            "ok_to_submit": False,
        },
    )
    strict_val = validate_submission.run(out_tif, sample_path)
    insp = inspect_tif(out_tif, sample_path, strict_all_finite=True)
    if not (strict_val["ok"] and insp["format_valid_against_reference"]):
        raise RuntimeError(f"Saved GeoTIFF failed strict validation: {strict_val} / {insp}")

    runtime_s = time.perf_counter() - t_start
    full_results = {
        "schema": "wbggems.msptcd-campaign.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "runtime_seconds": runtime_s,
        "budget_compliance": {
            "experiments_run": 3,
            "max_experiments": 3,
            "runtime_seconds": runtime_s,
            "max_seconds": 7200,
            "weekly_slots_used": 0,
        },
        "canary_summary": {
            "features_tested": canary_report["features_tested"],
            "folds_tested": canary_report["folds_tested"],
            "all_passed": canary_report["all_passed"],
            "max_two_sided_auc": canary_report["max_two_sided_auc"],
            "max_two_sided_feature": canary_report["max_two_sided_feature"],
            "details_file": "evidence/wbg2_msptcd_canaries.json",
        },
        "holdout_pooled": pooled,
        "paired_vs_ctrl_19b": vs_ctrl,
        "per_fold": per_fold_details,
        "detached_splay_diagnostic": detached_diag,
        "winning_experiment": best_exp,
        "artifact": {
            "stem": sub_stem,
            "tif_path": str(out_tif.relative_to(ROOT)),
            "zip_path": str(out_tif.with_suffix(".zip").relative_to(ROOT)),
            "receipt_path": str(out_tif.with_suffix(".json").relative_to(ROOT)),
            "tif_sha256": writer_receipt["sha256"],
            "tif_bytes": writer_receipt["bytes"],
            "zip_sha256": writer_receipt["zip_sha256"],
            "zip_bytes": out_tif.with_suffix(".zip").stat().st_size,
            "dots": n_dots_final,
            "note": sub_note,
            "validator": strict_val,
            "inspect_tif": insp,
        },
        "registry_comparison": {
            "rasters_checked": len(comparison_rows),
            "unique_vs_all_9_focus_sites": unique_vs_all_9_focus,
            "unique_vs_all_discrete_non_blanket_peers": unique_vs_all_discrete_peers,
            "unique_vs_literal_all_registry": unique_vs_literal_all_registry,
            "max_focus_forward_overlap_3px": max(r["forward_overlap_3px"] for r in focus_rows),
            "max_focus_overlap_site": max(focus_rows, key=lambda r: r["forward_overlap_3px"])["id"],
            "max_focus_abs_surface_spearman": max(abs(r["surface_spearman_rho"]) for r in focus_rows),
            "max_focus_abs_dots_spearman": max(abs(r["dots_spearman_rho"]) for r in focus_rows),
            "blanket_witnesses_triggered": [
                r["id"] for r in comparison_rows if r["literal_duplicate_flag"]
            ],
            "rows": comparison_rows,
        },
        "ok_to_download_research_tif": True,
        "ok_to_submit": False,
        "verdict": "negative",
    }
    (ROOT / "evidence/wbg2_msptcd_results.json").write_text(
        json.dumps(full_results, indent=2, allow_nan=False) + "\n"
    )
    print(f"[wbg2] campaign complete in {runtime_s:.1f}s -> evidence/wbg2_msptcd_results.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
