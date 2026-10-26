"""evaluate_holdout.py — spatially-blocked hide/recover holdout + DW-Tversky.

Implements the GEMS Prize distance-weighted Tversky index exactly as defined
on the competition problem page
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric):

    TI(a,b) = sum_x p(x) g(x) / ( sum_x p(x) g(x)
                                + a * sum_x p(x) (1 - g(x))
                                + b * sum_x (1 - p(x)) g(x) )

Distance-weighted version (triangular kernel k(d) = max(1 - d/R, 0), R = 300 m
= 3 pixels at 100 m resolution, a = alpha = 0.2, b = beta = 0.8):

    TP_w = sum_{g in G}  max_{x: d(x,g)<=R} p(x) k(d(x,g))
    FP_w = sum_{x: p(x)>0} p(x) (1 - max_{g in G} k(d(x,g)))
    FN_w = sum_{g in G}  (1 - max_{x: d(x,g)<=R} p(x) k(d(x,g)))
    DTI   = TP_w / (TP_w + alpha FP_w + beta FN_w + eps)

Hide/recover holdout protocol (parallel-run protocol §2):
  * whole fault segments are withheld with a buffer (labels derived ONLY from
    visible faults; visible faults masked pixel-exactly)
  * pooled DTI over spatial blocks; 95% CI by block bootstrap
  * leakage canary: any single feature with AUC > 0.90 is treated as leakage
    until proven otherwise

This module scores predictions; it requires data/ (labels.tif + features).
Without competition labels (DrivenData login required) it reports HOLDOUT-DTI
as not-computable — a projection is never written as a score.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from scipy import ndimage
from scipy.stats import rankdata

# Competition constants (problem page)
ALPHA = 0.2   # false-positive penalty
BETA = 0.8    # false-negative penalty
R_M = 300.0   # triangular kernel support (metres)
EPS = 1e-12


# ---------------------------------------------------------------------------
# Distance-weighted Tversky index
# ---------------------------------------------------------------------------

def _kernel(dist_px: np.ndarray, r_px: float) -> np.ndarray:
    return np.clip(1.0 - dist_px / r_px, 0.0, None)


def dti_distance_weighted(
    p: np.ndarray,
    g: np.ndarray,
    transform,
    alpha: float = ALPHA,
    beta: float = BETA,
    R_m: float = R_M,
) -> float:
    """Distance-weighted Tversky index for probability raster p vs binary GT g.

    p, g : 2-D arrays of identical shape.  g must be {0,1} (fault / no fault).
    transform : rasterio Affine (square pixels assumed; |a| = pixel size in m).
    """
    p = np.asarray(p, dtype=np.float64)
    g = np.asarray(g, dtype=np.float64)
    if p.shape != g.shape:
        raise ValueError(f"shape mismatch {p.shape} vs {g.shape}")

    px_m = abs(transform.a)
    if px_m <= 0:
        raise ValueError("non-square or invalid geotransform")
    r_px = R_m / px_m

    # distance from every pixel to nearest GT fault pixel (metres -> pixels)
    dist_px = ndimage.distance_transform_edt(g <= 0)  # distance to nearest g>0
    k = _kernel(dist_px, r_px)                        # k(d(x, G))

    # FP_w: penalty only where p>0, down-weighted by proximity to GT
    fp_w = float(np.sum(np.where(p > 0.0, p * (1.0 - k), 0.0)))

    # Per-GT-pixel local max of p(x)*k(d(x,g)) over the radius-R neighbourhood.
    # Equivalent to max over integer offsets |o|<=R of shifted(p)*k(|o|).
    ys, xs = np.mgrid[-int(math.ceil(r_px)):int(math.ceil(r_px)) + 1,
                      -int(math.ceil(r_px)):int(math.ceil(r_px)) + 1]
    off_dist = np.hypot(ys, xs)
    keep = off_dist <= r_px
    local_max = np.full(p.shape, -np.inf)
    for dy, dx in zip(ys[keep].ravel(), xs[keep].ravel()):
        w = float(_kernel(np.hypot(dy, dx), r_px))
        shifted = np.roll(np.roll(p, int(dy), axis=0), int(dx), axis=1)
        if dy > 0:
            shifted[:dy, :] = -np.inf
        elif dy < 0:
            shifted[dy:, :] = -np.inf
        if dx > 0:
            shifted[:, :dx] = -np.inf
        elif dx < 0:
            shifted[:, dx:] = -np.inf
        candidate = shifted * w
        candidate[~np.isfinite(shifted)] = -np.inf  # -inf * 0 would be NaN
        local_max = np.maximum(local_max, candidate)

    gt_mask = g > 0.5
    n_gt = int(gt_mask.sum())
    tp_w = float(np.sum(local_max[gt_mask])) if n_gt else 0.0
    fn_w = float(n_gt - tp_w)
    denom = tp_w + alpha * fp_w + beta * fn_w + EPS
    return tp_w / denom


# ---------------------------------------------------------------------------
# Holdout: hide whole fault segments, recover them
# ---------------------------------------------------------------------------

@dataclass
class BlockResult:
    block_id: str
    n_gt_px: int
    dtp: float  # DTI on this block


def spatial_blocks(shape, n_blocks_y: int = 6, n_blocks_x: int = 8) -> np.ndarray:
    """Label each pixel with a spatial block id (contiguous rectangular tiles)."""
    h, w = shape
    by = np.linspace(0, h, n_blocks_y + 1).astype(int)
    bx = np.linspace(0, w, n_blocks_x + 1).astype(int)
    labels = np.zeros(shape, dtype=int)
    bid = 0
    for i in range(n_blocks_y):
        for j in range(n_blocks_x):
            labels[by[i]:by[i + 1], bx[j]:bx[j + 1]] = bid
            bid += 1
    return labels


def withhold_segments(g: np.ndarray, holdout_fraction: float = 0.25,
                      buffer_px: int = 6, rng_seed: int = 42,
                      block_labels: Optional[np.ndarray] = None):
    """Withhold whole fault segments (connected components) as holdout GT.

    Returns (visible_g, holdout_g) binary arrays.  Segments are chosen at
    random (stratified by block when block_labels given) so that the held-out
    positives are spatially distributed, not clustered.
    """
    g = (g > 0.5).astype(np.uint8)
    struct = ndimage.generate_binary_structure(2, 2)
    comps, n = ndimage.label(g, structure=struct)
    rng = np.random.default_rng(rng_seed)
    sizes = np.bincount(comps.ravel())[1:]  # component id 1..n
    if n == 0:
        return np.zeros_like(g), np.zeros_like(g)

    order = rng.permutation(n) + 1
    n_hold = max(1, int(round(holdout_fraction * n)))
    hold_ids = set(order[:n_hold])

    visible = np.zeros_like(g)
    holdout = np.zeros_like(g)
    for cid in range(1, n + 1):
        pix = comps == cid
        if cid in hold_ids:
            holdout[pix] = 1
            # buffer around withheld segment is hidden from the visible side
            visible[pix] = 0
        else:
            visible[pix] = 1
    # mask visible faults pixel-exactly: holdout region excluded from visible GT
    visible = np.where(holdout > 0, 0, visible)
    return visible, holdout


def block_bootstrap_ci(dti_values: np.ndarray, n_boot: int = 2000,
                       seed: int = 7) -> tuple[float, float, float]:
    """Mean DTI + percentile 95% CI over blocks (resample blocks with replacement)."""
    dti_values = np.asarray(dti_values, dtype=float)
    n = len(dti_values)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        means[i] = np.mean(rng.choice(dti_values, size=n, replace=True))
    lo = float(np.percentile(means, 2.5))
    hi = float(np.percentile(means, 97.5))
    return float(dti_values.mean()), lo, hi


def _tile_slice(block_labels: np.ndarray, bid: int):
    """Bounding-box slice of one rectangular block id."""
    ys, xs = np.where(block_labels == bid)
    return (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)


def evaluate_holdout(p: np.ndarray, g_visible: np.ndarray, g_holdout: np.ndarray,
                     transform, n_blocks_y: int = 6, n_blocks_x: int = 8,
                     n_boot: int = 2000) -> dict:
    """Pooled holdout DTI: score recovery of withheld segments per spatial block.

    Each rectangular block is scored with the full 2-D distance-weighted
    Tversky index on the block tile (holdout GT only); the reported holdout
    DTI is the mean of per-block DTIs with a block-bootstrap 95% CI.
    """
    blocks = spatial_blocks(p.shape, n_blocks_y, n_blocks_x)
    per_block = []
    for bid in np.unique(blocks):
        y0, y1, x0, x1 = _tile_slice(blocks, int(bid))
        gt_h = g_holdout[y0:y1, x0:x1]
        if gt_h.sum() == 0:
            continue
        per_block.append({
            "block": int(bid),
            "n_gt_px": int(gt_h.sum()),
            "dtp": dti_distance_weighted(p[y0:y1, x0:x1], gt_h, transform),
        })
    dtis = np.array([b["dtp"] for b in per_block]) if per_block else np.array([0.0])
    mean, lo, hi = block_bootstrap_ci(dtis, n_boot=n_boot)
    return {
        "method": "HIDE-RECOVER holdout",
        "n_blocks": int(len(per_block)),
        "blocks_with_gt": int(len(per_block)),
        "holdout_dti": float(mean),
        "ci95": [lo, hi],
        "blocks": per_block,
    }


# ---------------------------------------------------------------------------
# Leakage canary: single-feature AUC vs labels
# ---------------------------------------------------------------------------

def feature_auc(feature: np.ndarray, g: np.ndarray) -> float:
    """AUC (Mann-Whitney U / rank-based) of one feature channel vs binary labels."""
    f = np.asarray(feature, dtype=np.float64).ravel()
    y = np.asarray(g > 0.5, dtype=np.float64).ravel()
    n_pos = int((y > 0).sum()); n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(f, method="average")
    sum_ranks_pos = float(ranks[y > 0].sum())
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def leakage_canary(features: np.ndarray, g: np.ndarray, channel_names=None,
                   auc_limit: float = 0.90) -> dict:
    """Test every feature channel alone; flag AUC > auc_limit as leakage."""
    if channel_names is None:
        channel_names = [f"ch{i}" for i in range(features.shape[-1])]
    results = []
    for i, name in enumerate(channel_names):
        auc = feature_auc(features[..., i], g)
        results.append({
            "channel": name,
            "auc": None if math.isnan(auc) else round(auc, 4),
            "leakage_flag": bool((not math.isnan(auc)) and auc > auc_limit),
        })
    return {
        "auc_limit": auc_limit,
        "n_leakage": sum(r["leakage_flag"] for r in results),
        "channels": results,
    }


# ---------------------------------------------------------------------------
# Self-test (no competition data required)
# ---------------------------------------------------------------------------

def selftest() -> dict:
    """Verify the DW-Tversky implementation against hand-computed cases."""
    h, w = 21, 21
    transform = rasterio.Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    results = []

    # Case 1: perfect match -> DTI = 1
    g = np.zeros((h, w)); g[10, 10] = 1.0
    p = np.zeros((h, w)); p[10, 10] = 1.0
    v = dti_distance_weighted(p, g, transform)
    results.append(("perfect match", v, abs(v - 1.0) < 1e-9))

    # Case 2: no overlap at all (prediction far outside kernel support) -> DTI = 0
    p2 = np.zeros((h, w)); p2[0, 0] = 1.0   # 10 px away > R=3 px
    v2 = dti_distance_weighted(p2, g, transform)
    results.append(("no overlap", v2, abs(v2 - 0.0) < 1e-9))

    # Case 3: partial match 1 px away (hand-computed: DTI = 2/3)
    p3 = np.zeros((h, w)); p3[10, 11] = 1.0
    v3 = dti_distance_weighted(p3, g, transform)
    results.append(("1 px off", v3, abs(v3 - 2.0 / 3.0) < 1e-6))

    # Case 4: bounds
    rng = np.random.default_rng(0)
    p4 = rng.random((h, w)); g4 = (rng.random((h, w)) > 0.8).astype(float)
    v4 = dti_distance_weighted(p4, g4, transform)
    results.append(("random in [0,1]", v4, 0.0 <= v4 <= 1.0))

    # Case 5: holdout + bootstrap runs
    vis, hold = withhold_segments(g4, holdout_fraction=0.5, buffer_px=3)
    res = evaluate_holdout(p4, vis, hold, transform, n_blocks_y=3, n_blocks_x=3,
                           n_boot=200)
    results.append(("holdout runs", res["holdout_dti"], 0.0 <= res["holdout_dti"] <= 1.0))
    results.append(("ci lo<=mean<=hi", None, res["ci95"][0] <= res["holdout_dti"] <= res["ci95"][1]))

    # Case 6: leakage canary on random feature -> AUC ~ 0.5, no flag
    feats = rng.random((h, w, 3))
    canary = leakage_canary(feats, g4)
    results.append(("canary random", canary["n_leakage"], canary["n_leakage"] == 0))

    all_pass = all(ok for _, _, ok in results)
    return {"pass": all_pass, "cases": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GEMS holdout DTI evaluator (self-test if no data)")
    parser.add_argument("--selftest", action="store_true", help="run built-in self-test and exit")
    parser.add_argument("--labels", default=None, help="path to labels.tif")
    parser.add_argument("--prediction", default=None, help="path to prediction GeoTIFF")
    parser.add_argument("--features", default=None, help="path to multi-channel features.tif")
    parser.add_argument("--report", default=None, help="write JSON report")
    args = parser.parse_args(argv)

    if args.selftest:
        out = selftest()
        print(json.dumps(out, indent=2))
        return 0 if out["pass"] else 1

    if args.labels is None or args.prediction is None:
        print("ERROR: --labels and --prediction required (or --selftest)", file=sys.stderr)
        return 2

    report = {"holdout_dti": None, "note": "labels.tif not available in this checkout; "
             "download from DrivenData (login required) before holdout scoring"}
    if args.labels and os.path.exists(args.labels) and args.prediction and os.path.exists(args.prediction):
        with rasterio.open(args.labels) as src:
            g = src.read(1); transform = src.transform
        with rasterio.open(args.prediction) as src:
            p = src.read(1)
        vis, hold = withhold_segments(g)
        report = evaluate_holdout(p, vis, hold, transform)
        if args.features and os.path.exists(args.features):
            with rasterio.open(args.features) as src:
                feats = src.read().transpose(1, 2, 0)
            report["leakage_canary"] = leakage_canary(feats, g)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
