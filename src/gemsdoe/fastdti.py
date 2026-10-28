"""Exact distance-weighted Tversky index (DTI), fast form, plus set-coverage tools.

Definition (organizer problem description, page 967):

    k(d)  = max(1 - d/R, 0), R = 300 m = 3 px
    TP_w  = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
    FP_w  = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w  = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
    DTI   = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)

``fast_dti`` is algebraically identical to :func:`src.wbg3.metric.dti_probabilistic`
but avoids materialising 49 full-grid shifted arrays: the max over the kernel
window is evaluated only at ground-truth cells, and the FP term uses one EDT.
Equality with the shared implementation is asserted in ``tests/test_gemsdoe_dti.py``.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

RADIUS_PX = 3.0
ALPHA = 0.2
BETA = 0.8
EPS = 1e-12


def kernel(d, radius: float = RADIUS_PX):
    return np.maximum(1.0 - np.asarray(d, dtype=float) / float(radius), 0.0)


def _window_weights(radius: int = 3):
    offs = []
    r = int(radius)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            kv = max(1.0 - d / RADIUS_PX, 0.0)
            if kv > 0:
                offs.append((dy, dx, kv))
    return offs


OFFSETS = _window_weights(3)


def fast_dti(pred, truth, active=None, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI for a continuous prediction p in [0,1] against boolean truth."""
    p = np.asarray(pred, dtype="float32")
    g = np.asarray(truth, dtype=bool)
    if active is not None:
        a = np.asarray(active, dtype=bool)
        g = g & a
        pp = np.where(a, p, 0.0).astype("float32")
    else:
        pp = np.where(np.isfinite(p), p, 0.0).astype("float32")
    pp = np.where(np.isfinite(pp), pp, 0.0)
    n_truth = int(g.sum())
    if n_truth == 0:
        raise ValueError("no active truth cells: DTI is undefined")

    ys, xs = np.nonzero(g)
    h, w = pp.shape
    best = np.zeros(n_truth, dtype="float32")
    for dy, dx, kv in OFFSETS:
        y2 = ys + dy
        x2 = xs + dx
        ok = (y2 >= 0) & (y2 < h) & (x2 >= 0) & (x2 < w)
        vals = np.zeros(n_truth, dtype="float32")
        vals[ok] = pp[y2[ok], x2[ok]] * kv
        np.maximum(best, vals, out=best)
    tp = float(best.sum())
    fn = float(n_truth) - tp

    d_truth = distance_transform_edt(~g)
    pos = pp > 0
    fp = float((pp[pos] * (1.0 - kernel(d_truth[pos]))).sum())
    dti = tp / (tp + alpha * fp + beta * fn + EPS)
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": n_truth,
            "n_pred": int(pos.sum()), "mass": float(pp.sum()), "dti": float(dti)}


def pool(parts) -> dict:
    tp = sum(float(c["tp"]) for c in parts)
    fp = sum(float(c["fp"]) for c in parts)
    fn = sum(float(c["fn"]) for c in parts)
    n = sum(int(c["n_truth"]) for c in parts)
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": n,
            "dti": tp / (tp + ALPHA * fp + BETA * fn + EPS)}


def marginal_rule(dti_now: float, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Break-even: one unit of TP mass justifies how much FP mass?

    From DTI = T / ((1-beta) T + alpha F + beta N), dDTI/dT > 0 and dDTI/dF < 0, so
    a change is an improvement iff  (1 - (1-beta) s) dT > alpha s dF.
    """
    lhs = 1.0 - (1.0 - beta) * dti_now
    rhs = alpha * dti_now
    return {"dti_now": dti_now, "tp_gain_coeff": lhs, "fp_cost_coeff": rhs,
            "max_fp_per_unit_tp": float(lhs / rhs) if rhs else None}


def coverage_counts(pred_positive, truth, radius_px: float = RADIUS_PX) -> dict:
    """Fraction of truth pixels covered within the kernel and precision of positives."""
    p = np.asarray(pred_positive, dtype=bool)
    g = np.asarray(truth, dtype=bool)
    d_pred = distance_transform_edt(~p)
    d_truth = distance_transform_edt(~g)
    covered = d_pred[g] <= radius_px
    near = d_truth[p] <= radius_px
    return {
        "n_truth": int(g.sum()),
        "n_pred": int(p.sum()),
        "frac_truth_covered": float(covered.mean()) if g.any() else None,
        "precision_within_3px": float(near.mean()) if p.any() else None,
        "median_px_to_truth": float(np.median(d_truth[p])) if p.any() else None,
    }
