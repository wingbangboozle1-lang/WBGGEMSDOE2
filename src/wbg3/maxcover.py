"""Exact greedy max-coverage over the official triangular kernel.

Objective.  For a binary prediction with ``D`` predicted cells and ``N`` truth
cells the official metric is

    DTI = TP / (0.2*FP + 0.8*N + 0.2*TP)

because ``FN = N - TP`` always.  Note ``FP`` is *not* ``D - TP``: a single dot
can earn credit on several truth cells and a single truth cell can be served by
several dots, so ``FP <= D`` with equality only when no dot lies within the
kernel of any truth cell (verified in ``tests/test_wbg3_metric.py``).  ``TP`` is
still the dominant lever at fixed ``D`` -- it is the only term that placement can
raise without bound -- and ``TP = sum_cells prior(c) * max_dot k``, so maximising
that sum is a weighted max-coverage problem.  This module solves it *exactly per
greedy step* (not with a clipped-convolution surrogate): the marginal gain of a
candidate dot is recomputed against the accumulated kernel cover, and candidates
are re-seeded from a freshly computed exact gain map when the heap empties.

DTI is strictly increasing in ``TP`` and strictly decreasing in ``FP``, so
maximising the coverage sum is the correct objective at a fixed budget.  The
full marginal-gain sequence is returned so a caller can inspect the TP(D) curve
instead of guessing a budget.
"""
from __future__ import annotations

import heapq

import numpy as np


def kernel_offsets(radius: float = 3.0):
    r = int(np.ceil(radius))
    off = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            k = max(1.0 - d / radius, 0.0)
            if k > 0:
                off.append((dy, dx, k))
    return off


def exact_gain_map(prior: np.ndarray, acc: np.ndarray, offsets) -> np.ndarray:
    """gain(x) = sum_offsets prior(x+o) * max(k_o - acc(x+o), 0)."""
    h, w = prior.shape
    gain = np.zeros_like(prior, dtype=np.float32)
    for dy, dx, k in offsets:
        # a dot at (y, x) reads the cell (y+dy, x+dx); keep only valid sources
        ys0, ys1 = max(0, -dy), min(h, h - dy)
        xs0, xs1 = max(0, -dx), min(w, w - dx)
        if ys0 >= ys1 or xs0 >= xs1:
            continue
        src_prior = prior[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        src_acc = acc[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        gain[ys0:ys1, xs0:xs1] += np.maximum(k - src_acc, 0.0) * src_prior
    return gain


def greedy(prior, allowed, budget, min_sep=5.0, radius=3.0, chunk=300000,
           log_every=5000):
    """Greedy max coverage with an exact per-step gain and Poisson-disk spacing."""
    h, w = prior.shape
    offs = kernel_offsets(radius)
    acc = np.zeros((h, w), dtype=np.float32)
    dots = np.zeros((h, w), dtype=bool)
    r = int(np.ceil(min_sep))
    margins = []
    chosen = []
    start = 0

    while len(chosen) < budget:
        gain = exact_gain_map(prior, acc, offs)
        gain[~allowed] = -np.inf
        gain[dots] = -np.inf
        flat = gain.ravel()
        # Poisson-disk: exclude cells within min_sep of an existing dot
        from scipy.ndimage import binary_dilation
        blocked = binary_dilation(dots, iterations=r)
        flat[blocked.ravel()] = -np.inf
        cand = np.flatnonzero(np.isfinite(flat))
        if cand.size == 0:
            break
        take = min(chunk, cand.size)
        part = cand[np.argpartition(-flat[cand], take - 1)[:take]]
        part = part[np.argsort(-flat[part])]
        heap = [(-float(flat[i]), int(i)) for i in part]
        heapq.heapify(heap)
        progressed = False
        while heap and len(chosen) < budget:
            negg, idx = heapq.heappop(heap)
            y, x = divmod(idx, w)
            if dots[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].any():
                continue
            g = 0.0
            upd = []
            for dy, dx, k in offs:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w:
                    pv = float(prior[yy, xx])
                    if pv > 0.0:
                        old = float(acc[yy, xx])
                        if k > old:
                            g += pv * (k - old)
                            upd.append((yy, xx, k))
            if g <= 0.0:
                continue
            # lazy check: cached gain must not exceed the recomputed gain by much
            if g < -negg - 1e-6 * max(1.0, -negg):
                heapq.heappush(heap, (-g, idx))
                continue
            dots[y, x] = True
            chosen.append(idx)
            margins.append(g)
            for yy, xx, kk in upd:
                acc[yy, xx] = kk
            progressed = True
            if log_every and len(chosen) % log_every == 0:
                print(f"    [greedy] {len(chosen)} dots, cumulative TP={sum(margins):.0f}",
                      flush=True)
        start += 1
        if not progressed:
            break
        if start > 40:
            break
    return dots, np.asarray(margins), np.asarray(chosen)
