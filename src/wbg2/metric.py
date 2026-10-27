"""Distance-weighted Tversky index (DTI) exactly as specified by the organizers.

Source (official problem description, "Performance metric" section):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
retrieved 2026-10-27.

The organizers define, for prediction p(x) in [0,1] and ground truth g(x) in {0,1},
with kernel k(d) = max(1 - d/R, 0), R = 300 m = 3 px at 100 m resolution:

    TI(alpha, beta) = sum_x p(x) g(x)
                      / ( sum_x p(x) g(x)
                          + alpha * sum_x p(x) (1 - g(x))
                          + beta  * sum_x (1 - p(x)) g(x) )

    TP_w = sum_{g in G} max_{x: d(x,g) <= R} p(x) k(d(x,g))
    FP_w = sum_{x: p(x) > 0} p(x) [ 1 - max_{g in G} k(d(x,g)) ]
    FN_w = sum_{g in G} [ 1 - max_{x: d(x,g) <= R} p(x) k(d(x,g)) ]

    DTI(alpha, beta) = TP_w / (TP_w + alpha * FP_w + beta * FN_w + eps)

with alpha = 0.2 (false-positive weight) and beta = 0.8 (false-negative weight).

Consequences that are used elsewhere in this repository and are derived, not
assumed (see ``tests/test_metric.py`` for the checks):

* ``FN_w == |G| - TP_w`` exactly, because every ground-truth pixel contributes
  ``max(...)`` to TP_w and ``1 - max(...)`` to FN_w.
* A pixel predicted with value 1 exactly on a ground-truth pixel adds 1 to TP_w
  and 0 to FP_w (``1 - k(0) == 0``). Prediction mass only accrues false-positive
  cost when it is *not* on a ground-truth pixel.
* ``k`` is 1, 2/3, 1/3, 0 for d = 0, 1, 2, 3 px.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

ALPHA = 0.2
BETA = 0.8
RADIUS_PX = 3


def triangular_kernel(d: np.ndarray | float, radius: float = RADIUS_PX) -> np.ndarray:
    """k(d) = max(1 - d/R, 0) with R = 300 m = 3 px."""
    d = np.asarray(d, dtype=np.float64)
    return np.maximum(1.0 - d / float(radius), 0.0)


def _max_plus_kernel(pred: np.ndarray, radius: int) -> np.ndarray:
    """For every pixel g: max over x within ``radius`` of pred(x) * k(d(x,g)).

    Max-plus convolution with the triangular kernel. Implemented with explicit
    shifts so it is exact for any (non-separable) kernel, and cheap for R=3.
    """
    out = np.zeros(pred.shape, dtype=np.float64)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = float(np.hypot(dy, dx))
            w = 1.0 - d / radius
            if w <= 0.0:
                continue
            shifted = _shift(pred, dy, dx, fill=0.0) * w
            np.maximum(out, shifted, out=out)
    return out


def _shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """Return b with b[y, x] = a[y - dy, x - dx], filled with ``fill`` outside."""
    h, w = a.shape
    pad = ((max(dy, 0), max(-dy, 0)), (max(dx, 0), max(-dx, 0)))
    ap = np.pad(np.asarray(a, dtype=np.float64), pad, constant_values=fill)
    top, left = max(-dy, 0), max(-dx, 0)
    return ap[top:top + h, left:left + w]


def weighted_components(pred: np.ndarray, gt: np.ndarray, radius: int = RADIUS_PX):
    """Return (TP_w, FP_w, FN_w, n_truth) exactly as the organizers define them."""
    pred = np.asarray(pred, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.float64)
    if pred.shape != gt.shape:
        raise ValueError(f"shape mismatch {pred.shape} vs {gt.shape}")
    if not np.isfinite(pred).all():
        raise ValueError("prediction contains NaN/Inf; the organizers require values in [0,1]")
    if pred.min() < 0.0 or pred.max() > 1.0:
        raise ValueError("prediction values must lie in [0,1]")

    gt_bool = gt > 0.5
    n_truth = int(gt_bool.sum())

    # TP_w: per-truth-pixel max of pred * kernel over the R-neighbourhood.
    cover = _max_plus_kernel(pred, radius)
    tp = float(cover[gt_bool].sum()) if n_truth else 0.0

    # FN_w follows from the identity FN_w = |G| - TP_w.
    fn = float(n_truth) - tp

    # FP_w: per predicted pixel, cost p(x) * (1 - nearest-truth kernel weight).
    support = pred > 0.0
    if support.any():
        if n_truth:
            # Euclidean distance (px) to the nearest truth pixel, R-capped.
            dist = ndi.distance_transform_edt(~gt_bool)
            k = triangular_kernel(np.minimum(dist, radius), radius)
        else:
            k = np.zeros_like(pred)
        fp = float((pred[support] * (1.0 - k[support])).sum())
    else:
        fp = 0.0
    return tp, fp, fn, n_truth


def dti(pred: np.ndarray, gt: np.ndarray, alpha: float = ALPHA, beta: float = BETA,
        radius: int = RADIUS_PX, eps: float = 0.0) -> float:
    """Distance-weighted Tversky index (the competition metric)."""
    tp, fp, fn, _ = weighted_components(pred, gt, radius)
    denom = tp + alpha * fp + beta * fn + eps
    return float(tp / denom) if denom > 0 else 0.0


def dti_bruteforce(pred: np.ndarray, gt: np.ndarray, alpha: float = ALPHA,
                   beta: float = BETA, radius: int = RADIUS_PX) -> float:
    """Literal, loop-based transcription of the organizers' formulas.

    Deliberately slow and independent of :func:`weighted_components`; used only
    to cross-check the fast implementation in tests.
    """
    pred = np.asarray(pred, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.float64)
    h, w = pred.shape
    rows, cols = np.nonzero(gt > 0.5)
    gt_pts = list(zip(rows.tolist(), cols.tolist()))
    pred_pts = list(zip(*np.nonzero(pred > 0.0)))
    tp = 0.0
    for (gyv, gxv) in gt_pts:
        best = 0.0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                y, x = gyv + dy, gxv + dx
                if 0 <= y < h and 0 <= x < w:
                    d = float(np.hypot(dy, dx))
                    if d <= radius:
                        best = max(best, float(pred[y, x]) * (1.0 - d / radius))
        tp += best
    fp = 0.0
    for (y, x) in pred_pts:
        p = float(pred[y, x])
        if p <= 0.0:
            continue
        best_k = 0.0
        for (gyv, gxv) in gt_pts:
            d = float(np.hypot(y - gyv, x - gxv))
            best_k = max(best_k, max(1.0 - d / radius, 0.0))
        fp += p * (1.0 - best_k)
    fn = 0.0
    for (gyv, gxv) in gt_pts:
        best = 0.0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                y, x = gyv + dy, gxv + dx
                if 0 <= y < h and 0 <= x < w:
                    d = float(np.hypot(dy, dx))
                    if d <= radius:
                        best = max(best, float(pred[y, x]) * (1.0 - d / radius))
        fn += 1.0 - best
    denom = tp + alpha * fp + beta * fn
    return float(tp / denom) if denom > 0 else 0.0


# ---------------------------------------------------------------------------
# Backward-compatible helpers (pre-existing API kept so earlier tests and
# scripts keep working). They are thin wrappers over the verified core above.
# ---------------------------------------------------------------------------
EPS = 1e-12


def kernel(d, radius: float = RADIUS_PX):
    """Alias of :func:`triangular_kernel` (kept for the earlier API)."""
    return triangular_kernel(d, radius)


def dti_binary(pred_bool, truth, valid=None, known=None):
    """Binary-prediction DTI with optional valid/known masks.

    ``known`` pixels are excluded from both prediction and truth (they are the
    catalogue pixels drawn from the visible data); ``valid`` restricts the
    domain. Returns a dict for pooled aggregation across folds.
    """
    p0 = np.asarray(pred_bool, bool)
    g0 = np.asarray(truth, bool)
    valid_ = np.ones(p0.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(p0.shape, bool) if known is None else np.asarray(known, bool)
    active = valid_ & ~known_
    p, g = p0 & active, g0 & active
    n = int(g.sum())
    if n == 0:
        return dict(tp=0.0, fp=float(p.sum()), fn=0.0, n_truth=0, dti=0.0)
    tp, fp, fn, n_truth = weighted_components(p.astype(np.float64), g.astype(np.float64))
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth,
                dti=float(tp / (tp + ALPHA * fp + BETA * fn + EPS)))


def pooled_dti(fold_components):
    """Pool TP/FP/FN across folds before forming the ratio."""
    tp = sum(c["tp"] for c in fold_components)
    fp = sum(c["fp"] for c in fold_components)
    fn = sum(c["fn"] for c in fold_components)
    n = sum(c["n_truth"] for c in fold_components)
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n,
                dti=float(tp / (tp + ALPHA * fp + BETA * fn + EPS)))
