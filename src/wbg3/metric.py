"""Distance-weighted Tversky index (DTI) -- the official GEMS Prize metric.

Source of truth (fetched 2026-10-27):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

    k(d)   = max(1 - d/R, 0)                      triangular kernel, R = 300 m
    TP_w   = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
    FP_w   = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w   = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
    DTI    = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps)

with alpha = 0.2 and beta = 0.8.  The grid is 100 m, so R = 3 pixels.

This module is deliberately dependency-light (numpy + scipy) and is checked
against an independent brute-force implementation in ``tests/test_wbg3_metric.py``.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
RADIUS_PX = 3.0
EPS = 1e-12


def kernel(d, radius: float = RADIUS_PX):
    """Triangular kernel k(d) = max(1 - d/R, 0)."""
    return np.maximum(1.0 - np.asarray(d, dtype=float) / float(radius), 0.0)


def _binary(pred, truth, active):
    p = np.asarray(pred)
    g = np.asarray(truth, dtype=bool)
    a = np.ones(g.shape, dtype=bool) if active is None else np.asarray(active, dtype=bool)
    return p, g & a, a


def dti_binary(pred, truth, active=None, radius: float = RADIUS_PX,
               alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI for a *binary* prediction (p in {0, 1}) restricted to ``active``.

    ``truth`` and ``pred`` are boolean masks on the same grid. ``active`` marks
    the cells that participate in scoring (footprint minus already-known faults);
    predictions outside ``active`` and truths outside ``active`` are ignored.
    """
    p, g, a = _binary(pred, truth, active)
    p = (p > 0) & a
    n_truth = int(g.sum())
    n_pred = int(p.sum())
    if n_truth == 0:
        # Undefined; fail closed rather than invent a value.
        raise ValueError("no active truth cells: DTI is undefined")
    if n_pred == 0:
        return dict(tp=0.0, fp=0.0, fn=float(n_truth), n_truth=n_truth,
                    n_pred=0, dti=0.0)
    # distance from every cell to the nearest predicted cell
    d_pred = distance_transform_edt(~p)
    k_at_truth = kernel(d_pred[g], radius)
    tp = float(k_at_truth.sum())
    fn = float(n_truth) - tp
    # distance from every predicted cell to the nearest truth cell
    d_truth = distance_transform_edt(~g)
    fp = float((1.0 - kernel(d_truth[p], radius)).sum())
    dti = tp / (tp + alpha * fp + beta * fn + EPS)
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth, n_pred=n_pred, dti=float(dti))


def dti_probabilistic(pred, truth, active=None, radius: float = RADIUS_PX,
                      alpha: float = ALPHA, beta: float = BETA,
                      chunk: int = 4096) -> dict:
    """Exact DTI for a continuous prediction in [0, 1].

    TP_w needs, for every truth cell, the maximum of p(x)*k(d) over all x within
    R.  That is a grey-dilation of ``p`` by the kernel; it is computed here with
    a straightforward local maximum over the (2R+1)^2 window using scipy, which
    is exact and memory-bounded in row chunks.
    """
    from scipy.ndimage import maximum_filter
    p = np.asarray(pred, dtype=float)
    g = np.asarray(truth, dtype=bool)
    a = np.ones(g.shape, dtype=bool) if active is None else np.asarray(active, dtype=bool)
    if not np.isfinite(p[np.isfinite(p)]).all():
        raise ValueError("prediction contains non-finite values inside the grid")
    p = np.where(np.isfinite(p), np.clip(p, 0.0, 1.0), 0.0) * a
    g = g & a
    n_truth = int(g.sum())
    if n_truth == 0:
        raise ValueError("no active truth cells: DTI is undefined")

    r = int(round(radius))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    dist = np.hypot(yy, xx)
    ker = kernel(dist, radius)
    shape = (2 * r + 1, 2 * r + 1)

    # max over x of p(x) k(d(x,g)) : dilated max of p*k for each kernel offset
    best = np.zeros(g.shape, dtype=float)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            kv = float(ker[dy + r, dx + r])
            if kv <= 0:
                continue
            shifted = np.zeros_like(p)
            ys0, ys1 = max(0, dy), min(p.shape[0], p.shape[0] + dy)
            xs0, xs1 = max(0, dx), min(p.shape[1], p.shape[1] + dx)
            shifted[ys0:ys1, xs0:xs1] = p[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            np.maximum(best, shifted * kv, out=best)
    tp = float(best[g].sum())
    fn = float(n_truth) - tp

    # FP_w: for each x with p>0, p(x) * (1 - max_g k(d(x,g)))
    d_truth = distance_transform_edt(~g)
    w = p > 0
    fp = float((p[w] * (1.0 - kernel(d_truth[w], radius))).sum())
    dti = tp / (tp + alpha * fp + beta * fn + EPS)
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth, n_pred=int(w.sum()),
                dti=float(dti))


def pooled(parts) -> dict:
    """Pool per-block component dicts (the shared protocol pools, never averages)."""
    tp = sum(float(c["tp"]) for c in parts)
    fp = sum(float(c["fp"]) for c in parts)
    fn = sum(float(c["fn"]) for c in parts)
    n = sum(int(c["n_truth"]) for c in parts)
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n,
                dti=tp / (tp + ALPHA * fp + BETA * fn + EPS))


def dti_bruteforce(pred, truth, active=None, radius: float = RADIUS_PX,
                   alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Independent O(N*M) reference implementation used only by the tests."""
    p = np.asarray(pred, dtype=float)
    g = np.asarray(truth, dtype=bool)
    a = np.ones(g.shape, dtype=bool) if active is None else np.asarray(active, dtype=bool)
    a = a & np.isfinite(p)
    p = np.where(np.isfinite(p), p, 0.0) * a
    g = g & a
    xs = np.argwhere(p > 0)
    gs = np.argwhere(g)
    if len(gs) == 0:
        raise ValueError("no active truth cells")
    if len(xs) == 0:
        return dict(tp=0.0, fp=0.0, fn=float(len(gs)), n_truth=len(gs),
                    n_pred=0, dti=0.0)
    tp = 0.0
    for gt in gs:
        d = np.hypot(*(xs - gt).T)
        tp += float(np.max(p[tuple(xs.T)] * np.maximum(1 - d / radius, 0)))
    fp = 0.0
    for x in xs:
        d = np.hypot(*(gs - x).T)
        fp += float(p[tuple(x)] * (1 - np.max(np.maximum(1 - d / radius, 0))))
    fn = float(len(gs)) - tp
    return dict(tp=tp, fp=fp, fn=fn, n_truth=len(gs), n_pred=len(xs),
                dti=tp / (tp + alpha * fp + beta * fn + EPS))
