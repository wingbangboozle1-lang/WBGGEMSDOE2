"""Budgeted dot selection and exact DTI scoring (shared metric implementation)."""
from __future__ import annotations

import numpy as np

from src.gemsdoe.fastdti import ALPHA, BETA, RADIUS_PX, fast_dti, pool


def poisson_disk(score: np.ndarray, n: int, domain: np.ndarray, min_dist: float = 3.0,
                 seed: int = 0) -> np.ndarray:
    """Greedy score-ordered Poisson-disk selection; returns a boolean mask.

    Ties are broken reproducibly by adding a tiny deterministic jitter derived
    from the cell index (seed controls nothing else).
    """
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(domain & np.isfinite(score))
    vals = score.ravel()[idx].astype("float64")
    # ULP-scale jitter breaks exact ties without changing the ordering meaningfully
    jitter = rng.random(len(vals)) * 1e-9
    order = np.argsort(-(vals + jitter), kind="stable")
    h, w = score.shape
    occ = np.zeros((h, w), dtype=bool)
    r = int(np.ceil(min_dist))
    out = np.zeros((h, w), dtype=bool)
    count = 0
    rr = min_dist * min_dist
    for flat in idx[order]:
        if np.any(score.ravel()[flat] < -np.inf):  # pragma: no cover - defensive
            continue
        y, x = divmod(int(flat), w)
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        if occ[y0:y1, x0:x1].any():
            sub = occ[y0:y1, x0:x1]
            ys, xs = np.nonzero(sub)
            if np.any((ys + y0 - y) ** 2 + (xs + x0 - x) ** 2 < rr):
                continue
        occ[y, x] = True
        out[y, x] = True
        count += 1
        if count >= n:
            break
    return out


def dti(positive: np.ndarray, truth: np.ndarray, active: np.ndarray | None = None) -> dict:
    p = np.asarray(positive, dtype="float32")
    return fast_dti(p, truth, active)


def density_curve(score, n_list, domain, truth, active=None, min_dist=3.0):
    rows = []
    for n in n_list:
        pos = poisson_disk(score, n, domain, min_dist=min_dist)
        r = dti(pos, truth, active)
        r["requested"] = n
        r["emitted"] = int(pos.sum())
        rows.append(r)
    return rows


def cluster_bootstrap_ci(positive, truth, active=None, n_boot=400, seed=0):
    """Paired cluster bootstrap over connected truth components (label-block)."""
    from scipy import ndimage as ndi
    lab, ncomp = ndi.label(truth, structure=np.ones((3, 3), bool))
    rng = np.random.default_rng(seed)
    idx = np.arange(1, ncomp + 1)
    weights = np.bincount(lab.ravel(), minlength=ncomp + 1)[1:]
    vals = []
    base = fast_dti(positive.astype("float32"), truth, active)
    # per-component contributions approximated by resampling whole components
    comp_map = {c: lab == c for c in idx if weights[c - 1] > 0}
    for _ in range(n_boot):
        choice = rng.choice(idx, size=ncomp, replace=True, p=weights / weights.sum())
        sel = np.isin(lab, choice) & truth
        if sel.sum() == 0:
            continue
        r = fast_dti(positive.astype("float32"), sel, active)
        vals.append(r["dti"])
    lo, hi = np.percentile(vals, [2.5, 97.5]) if vals else (np.nan, np.nan)
    return {"dti": base["dti"], "ci95": [float(lo), float(hi)], "n_bootstrap": len(vals)}
