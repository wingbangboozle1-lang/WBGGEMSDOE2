#!/usr/bin/env python3
"""Train the fault-probability model for the submission lane and write OOF surfaces.

Design (measurement, no assumptions):

* Features: the 76 catalogue-independent layers of ``data/work/features.npy``
  (19 organizer bands x {z, grad-magnitude, -LoG, wide smooth}) plus three
  *fold-visible* catalogue-context layers (log distance to a mapped fault, and
  3-px / 8-px fault density).  Catalogue context is legal: the organizer masks
  known-fault pixels out of every scoring term, so a prediction is only rewarded
  where it finds faults the catalogue does not already contain.
* Labels for fold ``k`` are that fold's visible catalogue pixels.  The withheld
  segments never enter fitting, so ``surface_fold{k}.npy`` is a genuine
  out-of-fold prediction on territory the model has not seen.
* Model: gradient boosting on cells (2 cores; no torch in this container).

Outputs
-------
``data/work/surface_fold{k}.npy``     float16 OOF probability surface, k = 0..3
``data/work/surface_final.npy``       float16 surface of the all-catalogue model
``data_public/gemsdoe_v2_train.json`` sampling, timing and held-out AUC per fold
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
PUB = ROOT / "data_public"
SHAPE = (3730, 3292)
BLOCK = 64
SEED = 20261028

_NAMES: list[str] | None = None


def feature_names() -> list[str]:
    global _NAMES
    if _NAMES is None:
        _NAMES = json.loads((WORK / "features.json").read_text())["layers"]
    return _NAMES


def context_layers(visible: np.ndarray) -> list[np.ndarray]:
    d = ndi.distance_transform_edt(~visible).astype("float32")
    return [np.log1p(d).astype("float32"),
            ndi.gaussian_filter(visible.astype("float32"), 3.0),
            ndi.gaussian_filter(visible.astype("float32"), 8.0)]


CONTEXT_NAMES = ["log_dist_visible", "fault_density_s3", "fault_density_s8"]


def block_matrix(feat_mm, context, r0, r1):
    n = len(feature_names())
    X = np.empty((r1 - r0, SHAPE[1], n + len(context)), dtype="float32")
    for i in range(n):
        X[:, :, i] = feat_mm[i, r0:r1, :]
    for j, arr in enumerate(context):
        X[:, :, n + j] = arr[r0:r1]
    return X.reshape(-1, n + len(context))


def sample(footprint, visible, context, per_block_pos, per_block_neg, rng):
    """Stratified block sampling: all fault cells in a block up to a cap, plus background."""
    feat_mm = np.load(WORK / "features.npy", mmap_mode="r")
    Xs, ys = [], []
    for r0 in range(0, SHAPE[0], BLOCK):
        r1 = min(r0 + BLOCK, SHAPE[0])
        vis = visible[r0:r1]
        pos_local = np.argwhere(vis)
        if len(pos_local) > per_block_pos:
            pos_local = pos_local[rng.choice(len(pos_local), per_block_pos, replace=False)]
        bg = np.argwhere(footprint[r0:r1] & ~vis)
        neg_local = bg[rng.choice(len(bg), min(per_block_neg, len(bg)), replace=False)] if len(bg) else bg
        sel = np.vstack([pos_local, neg_local])
        if not len(sel):
            continue
        X = block_matrix(feat_mm, context, r0, r1)[sel[:, 0] * SHAPE[1] + sel[:, 1]]
        y = np.r_[np.ones(len(pos_local), dtype=np.int8), np.zeros(len(neg_local), dtype=np.int8)]
        Xs.append(X)
        ys.append(y)
    del feat_mm
    return np.vstack(Xs), np.concatenate(ys)


def predict_surface(model, context, out_path: Path):
    feat_mm = np.load(WORK / "features.npy", mmap_mode="r")
    out = np.lib.format.open_memmap(out_path, mode="w+", dtype="float16", shape=SHAPE)
    for r0 in range(0, SHAPE[0], BLOCK):
        r1 = min(r0 + BLOCK, SHAPE[0])
        X = block_matrix(feat_mm, context, r0, r1)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        p = model.predict_proba(X)[:, 1]
        out[r0:r1] = p.reshape(r1 - r0, SHAPE[1]).astype("float16")
    out.flush()
    del out, feat_mm


def fit(fold: int | None, n_neg: int, max_iter: int):
    fp = np.load(WORK / "footprint.npy")
    visible = (np.load(WORK / "catalogue.npy") if fold is None
               else np.load(WORK / f"fold{fold}_visible.npy")).astype(bool)
    context = context_layers(visible)
    rng = np.random.default_rng(SEED + (fold if fold is not None else 99))
    n_blocks = int(np.ceil(SHAPE[0] / BLOCK))
    per_block_neg = max(1, n_neg // n_blocks)
    X, y = sample(fp, visible, context, 400, per_block_neg, rng)
    order = rng.permutation(len(y))
    X, y = X[order], y[order]
    cut = int(0.9 * len(y))
    model = HistGradientBoostingClassifier(
        max_iter=max_iter, learning_rate=0.07, max_leaf_nodes=31,
        min_samples_leaf=40, l2_regularization=1.0, max_bins=128,
        early_stopping=False, random_state=SEED)
    sw = np.where(y[:cut] == 1, 1.0, 0.25).astype("float32")
    model.fit(X[:cut], y[:cut], sample_weight=sw)
    auc_hold = float(roc_auc_score(y[cut:], model.predict_proba(X[cut:])[:, 1]))
    info = {"train_rows": int(cut), "holdout_rows": int(len(y) - cut),
            "train_pos": int(y[:cut].sum()), "holdout_auc_sampled": auc_hold,
            "n_features": int(X.shape[1])}
    del X, y
    return model, context, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", nargs="*", type=int, default=[0, 1, 2, 3])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--n-neg", type=int, default=200_000)
    ap.add_argument("--max-iter", type=int, default=260)
    args = ap.parse_args()

    report = {"schema": "wbggems.v2-train.v1", "seed": SEED,
              "features": feature_names() + CONTEXT_NAMES, "folds": {}, "final": {}}
    for k in args.folds:
        t0 = time.time()
        model, context, info = fit(k, args.n_neg, args.max_iter)
        fit_s = round(time.time() - t0, 1)
        predict_surface(model, context, WORK / f"surface_fold{k}.npy")
        info.update({"fit_seconds": fit_s, "total_seconds": round(time.time() - t0, 1)})
        report["folds"][str(k)] = info
        print(f"fold {k}: {info} {info['total_seconds']}s", flush=True)
        del model, context

    if args.final:
        t0 = time.time()
        model, context, info = fit(None, args.n_neg, args.max_iter)
        predict_surface(model, context, WORK / "surface_final.npy")
        info["total_seconds"] = round(time.time() - t0, 1)
        report["final"] = info
        print(f"final: {info}", flush=True)

    PUB.mkdir(exist_ok=True)
    (PUB / "gemsdoe_v2_train.json").write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
