#!/usr/bin/env python3
"""Evaluate a probability surface, or any binary fleet raster, against HOLDOUT truth.

For a fold ``k`` the truth is that fold's withheld catalogue segments, restricted to
pixels at least ``known_dilation`` px away from the fold-visible catalogue, and the
scoring mask is the footprint minus the dilated visible catalogue (the organizer's
"known faults are masked out" rule).

Reported quantities per threshold:

* ``mass``, ``n_pred`` — cost of the emission;
* ``reach`` — share of the whole footprint within 3 px of a predicted cell;
* ``cover`` — share of *hidden truth* within 3 px of a predicted cell;
* ``enrich`` = cover / reach — 1.0 means the surface is blind (a uniform random
  field would score 1.0 by construction);
* ``dti`` — the organizer's distance-weighted Tversky index.

Usage
-----
    python scripts/gemsdoe_v2_eval.py --surface data/work/surface_fold0.npy --fold 0
    python scripts/gemsdoe_v2_eval.py --raster /tmp/fleet/GEMSDOE32_downloads/....tif
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
R = 3.0


def load_raster(path: Path, shape=(3730, 3292)) -> np.ndarray:
    with rasterio.open(path) as d:
        a = d.read(1)
        if a.shape != shape:
            raise SystemExit(f"{path}: shape {a.shape} != {shape}")
    return np.nan_to_num(a.astype("float32"), nan=0.0, posinf=0.0, neginf=0.0)


def masks(fold: int, known_dilation: int = 1):
    fp = np.load(WORK / "footprint.npy")
    vis = np.load(WORK / f"fold{fold}_visible.npy").astype(bool)
    tru = np.load(WORK / f"fold{fold}_truth.npy").astype(bool)
    vd = ndi.binary_dilation(vis, iterations=known_dilation) if known_dilation else vis
    return fp & ~vd, tru


def dti_fast(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """Exact organizer DTI, evaluated only where it can differ from zero."""
    g = truth & active
    p = np.where(active, pred, 0.0)
    ys, xs = np.nonzero(g)
    best = np.zeros(len(ys), dtype="float32")
    h, w = p.shape
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            kv = 1.0 - float(np.hypot(dy, dx)) / R
            if kv <= 0:
                continue
            y2, x2 = ys + dy, xs + dx
            ok = (y2 >= 0) & (y2 < h) & (x2 >= 0) & (x2 < w)
            v = np.zeros(len(ys), dtype="float32")
            v[ok] = p[y2[ok], x2[ok]] * kv
            np.maximum(best, v, out=best)
    tp = float(best.sum())
    fn = float(len(ys)) - tp
    d_g = ndi.distance_transform_edt(~g)
    pos = p > 0
    fp = float((p[pos] * np.maximum(1.0 - d_g[pos] / R, 0.0).__rsub__(1.0) * 0 + 1.0).sum() * 0)
    fp = float((p[pos] * (1.0 - np.maximum(1.0 - d_g[pos] / R, 0.0))).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * fn + 1e-12)
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": int(len(ys)), "dti": float(dti)}


def describe(pred: np.ndarray, truth: np.ndarray, active: np.ndarray,
             footprint: np.ndarray) -> dict:
    pos = pred > 0
    d_pred = ndi.distance_transform_edt(~pos) if pos.any() else None
    reach = float((d_pred <= R)[footprint].mean()) if pos.any() else 0.0
    cover = float((d_pred[truth] <= R).mean()) if pos.any() else 0.0
    row = dti_fast(pred, truth, active)
    row.update({"mass": float(pred.sum()), "n_pred": int(pos.sum()),
                "reach": reach, "cover": cover,
                "enrich": (cover / reach) if reach else None})
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface")
    ap.add_argument("--raster")
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--thresholds", default="auto")
    args = ap.parse_args()

    active, truth = masks(args.fold)
    footprint = np.load(WORK / "footprint.npy")
    truth_active = truth & active
    print(f"fold {args.fold}: hidden truth {int(truth.sum()):,} px, "
          f"active {int(active.sum()):,}, active truth {int(truth_active.sum()):,}")

    if args.raster:
        pred = load_raster(Path(args.raster))
        row = describe(pred, truth, active, footprint)
        print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v)
                          for k, v in row.items()}, indent=1))
        return 0

    surf = np.load(args.surface).astype("float32")
    surf = np.where(footprint, surf, 0.0)
    qs = [0.90, 0.95, 0.97, 0.98, 0.99, 0.995, 0.999, 1.0] if args.thresholds == "auto" else None
    rows = []
    if qs:
        cuts = np.unique(np.quantile(surf[footprint], qs))
    else:
        cuts = np.unique(np.quantile(surf[footprint], [float(t) for t in args.thresholds.split(",")]))
    for t in cuts:
        binp = (surf >= t).astype("float32")
        r = describe(binp, truth, active, footprint)
        r["threshold"] = float(t)
        rows.append(r)
        print(f"t={t:.5f} mass={r['mass']:>10,.0f} reach={r['reach']:.4f} "
              f"cover={r['cover']:.4f} enrich={r['enrich']:.2f} DTI={r['dti']:.4f}")
    out = ROOT / "data" / "work" / "v2_eval.json"
    out.write_text(json.dumps({"fold": args.fold, "surface": args.surface, "rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
