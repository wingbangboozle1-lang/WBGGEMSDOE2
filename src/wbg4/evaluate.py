"""Shared fold evaluation for any prediction raster (candidate or registry).

The expensive per-fold products (hidden-truth distance transforms, active masks)
are computed once and reused, so a 60-raster registry sweep is affordable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import wbg4.lane as L  # noqa: E402

ALPHA, BETA, RADIUS = 0.2, 0.8, 3.0


def kernel(d):
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / RADIUS, 0.0)


def build_caches(folds=(0, 1, 2, 3), buffer_px: int = 3):
    fp = L.load_footprint()
    lab = L.load_labels()
    comp, _ = L.fault_components(lab, fp)
    ids = L.fold_ids(comp, fp)
    caches = []
    for f in folds:
        hidden, _hbuf, _vis_feat, vis_exact = L.fold_masks(comp, ids, f, buffer_px=buffer_px)
        active = fp & ~vis_exact
        d_truth = ndi.distance_transform_edt(~hidden).astype(np.float32)
        caches.append({
            "fold": f,
            "bbox": _bbox(hidden),
            "hidden": hidden,
            "active": active,
            "d_truth": d_truth,
            "n_truth": int(hidden.sum()),
        })
    return caches


def _bbox(mask: np.ndarray, pad: int = 6):
    rows = np.nonzero(mask.any(axis=1))[0]
    cols = np.nonzero(mask.any(axis=0))[0]
    return (max(0, rows.min() - pad), min(mask.shape[0], rows.max() + pad + 1),
            max(0, cols.min() - pad), min(mask.shape[1], cols.max() + pad + 1))


def score_binary(pred_bin: np.ndarray, caches) -> dict:
    """Exact pooled DTI, evaluated inside the withheld-fault bounding box.

    Predictions outside the padded bounding box of the withheld faults are farther
    than the 3 px kernel radius from every truth cell, so each contributes exactly
    one unit of ``FP_w``; they are counted rather than distance-transformed.
    """
    parts = []
    for c in caches:
        p = pred_bin & c["active"]
        n = int(p.sum())
        if n == 0:
            parts.append({"tp": 0.0, "fp": 0.0, "fn": float(c["n_truth"]),
                          "n_truth": c["n_truth"], "n_pred": 0})
            continue
        r0, r1, c0, c1 = c["bbox"]
        sub = p[r0:r1, c0:c1]
        n_out = n - int(sub.sum())
        d_pred = ndi.distance_transform_edt(~sub)
        tp = float(kernel(d_pred[c["hidden"][r0:r1, c0:c1]]).sum())
        fp = float((1.0 - kernel(c["d_truth"][r0:r1, c0:c1][sub])).sum()) + n_out
        fn = float(c["n_truth"]) - tp
        parts.append({"tp": tp, "fp": fp, "fn": fn, "n_truth": c["n_truth"],
                      "n_pred": n})
    tp = sum(p["tp"] for p in parts)
    fp = sum(p["fp"] for p in parts)
    fn = sum(p["fn"] for p in parts)
    nt = sum(p["n_truth"] for p in parts)
    return {
        "tp": tp, "fp": fp, "fn": fn, "n_truth": nt,
        "mass": int(sum(p["n_pred"] for p in parts)),
        "coverage": tp / nt if nt else None,
        "dti": tp / (tp + ALPHA * fp + BETA * fn + 1e-12),
        "per_fold": parts,
    }


def score_raster(path: Path, caches, threshold: float = 0.0) -> dict:
    with rasterio.open(path) as ds:
        if ds.shape != (L.HEIGHT, L.WIDTH):
            raise ValueError(f"{path} shape {ds.shape} is not the official grid")
        arr = ds.read(1)
    pred = np.isfinite(arr) & (arr > threshold)
    out = score_binary(pred, caches)
    out["file"] = Path(path).name
    out["positive_pixels_total"] = int(np.isfinite(arr).sum() and (np.isfinite(arr) & (arr > threshold)).sum())
    return out


def load_registry_index(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text())
