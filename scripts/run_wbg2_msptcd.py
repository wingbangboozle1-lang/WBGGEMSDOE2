#!/usr/bin/env python3
"""Historical MSPTCD utility functions; the campaign entry point is retired.

The old campaign placed dots before checking the registry and continued writing
a research artifact after detecting duplicates. The original source is archived
for audit; it must not be rerun as a protocol-compliant experiment.
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
    raise RuntimeError("STOP: historical MSPTCD campaign exhausted its three experiments and failed the literal duplicate gate; see evidence/retired_20261027.")


if __name__ == "__main__":
    raise SystemExit("STOP: historical MSPTCD campaign exhausted its three experiments and failed the literal duplicate gate; see evidence/retired_20261027.")
