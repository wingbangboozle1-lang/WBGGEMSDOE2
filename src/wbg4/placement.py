"""Dot placement algorithms for the WBG4 lane.

Three selectors are compared on identical folds:

``nms_threshold``
    Sort cells by hazard and take the top ``budget`` after 3x3 non-maximum
    suppression.  This is the naive "threshold a probability map" approach.

``maxcover``
    Lazy-greedy submodular **max-cover** of the hazard mass: maximise
    ``P(S) = sum_x h(x) * max_{s in S} k(d(x,s))`` with no false-positive term.
    This is the selector used by the historical ``wbg2``/``wbg3`` campaigns
    (CELF / submodular maximisation over a hazard surface).

``edti``
    Lazy-greedy maximisation of the **metric itself**.  With
    ``Den = P + alpha*F + beta*N`` and ``P = sum_x h(x) * max_{s} k``,

        adding c improves DTI  <=>  dP > lambda * dF,
        lambda = alpha*P / (alpha*F + beta*N) = P / (F + 4N)      (alpha=0.2, beta=0.8)

    so the greedy step is an exact penalised-cover step with a Lagrange
    multiplier ``lambda`` that is **monotonically increasing** across accepted
    steps (proved in ``tests/test_wbg4_algebra.py``).  ``lambda = 0`` recovers
    ``maxcover`` exactly, so EDTI is a strict generalisation: the same machinery
    with the false-positive price switched on.  Greedy stops on its own when no
    remaining candidate satisfies ``dP > lambda*dF``, which yields an optimal dot
    count instead of a hand-tuned one.

Expected false-positive cost of a dot at ``s``
    ``dF(s) = 1 - E[max_g k(d(s,g))]``, approximated by ``1 - sum_x h(x) k(d(s,x))``
    over the 3-px window.  When ``sum h k >= 1`` the dot is expected to sit on
    more than one truth pixel, so its marginal false-positive cost is zero and
    the term is clipped at 0.  This is the correct behaviour, not a fudge: it is
    what makes dense emission inside an already-hit fault *free* and emission
    into empty ground *expensive*.
"""
from __future__ import annotations

import heapq

import numpy as np

ALPHA, BETA, RADIUS = 0.2, 0.8, 3.0


def kernel_offsets(radius: float = RADIUS):
    """Integer offsets and triangular kernel weights with ``k > 0``."""
    r = int(np.ceil(radius))
    offs, ks = [], []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            k = max(1.0 - d / radius, 0.0)
            if k > 0.0:
                offs.append((dy, dx))
                ks.append(k)
    return np.asarray(offs, np.int64), np.asarray(ks, np.float32)


def _neighbours(flat: np.ndarray, dy: int, dx: int, shape) -> tuple[np.ndarray, np.ndarray]:
    H, W = shape
    y = flat // W + dy
    x = flat % W + dx
    ok = (y >= 0) & (y < H) & (x >= 0) & (x < W)
    return np.where(ok, y * W + x, 0), ok


def _gains(h_flat: np.ndarray, flat: np.ndarray, cover: np.ndarray,
           offs: np.ndarray, ks: np.ndarray, shape) -> np.ndarray:
    """Exact ``dP`` for each candidate given the current cover field."""
    acc = np.zeros(flat.shape[0], np.float32)
    cf = cover
    for (dy, dx), k in zip(offs, ks):
        nbr, ok = _neighbours(flat, int(dy), int(dx), shape)
        g = k - cf[nbr]
        np.maximum(g, 0.0, out=g)
        np.multiply(h_flat[nbr], g, out=g)
        acc += np.where(ok, g, 0.0)
    return acc


def _static(h_flat: np.ndarray, flat: np.ndarray, offs: np.ndarray,
            ks: np.ndarray, shape) -> tuple[np.ndarray, np.ndarray]:
    """``(u0, fcost)`` per candidate: uncovered mass, and expected FP cost."""
    u0 = np.zeros(flat.shape[0], np.float32)
    for (dy, dx), k in zip(offs, ks):
        nbr, ok = _neighbours(flat, int(dy), int(dx), shape)
        u0 += np.where(ok, h_flat[nbr] * k, 0.0)
    return u0, np.maximum(0.0, 1.0 - u0)


def _candidates(h_flat: np.ndarray, footprint: np.ndarray, n_cand: int) -> np.ndarray:
    """Top-``n_cand`` footprint cells by hazard."""
    hf = np.where(footprint.ravel(), h_flat, -np.inf)
    n = int(footprint.sum())
    n_cand = int(min(n_cand, n))
    if n_cand <= 0:
        raise ValueError("no footprint cells to place into")
    part = np.argpartition(-hf, n_cand - 1)[:n_cand]
    return part.astype(np.int64)


def place(h: np.ndarray, footprint: np.ndarray, mode: str = "edti",
          budget: int | None = 42000, n_cand: int = 140000,
          N_hat: float | None = None, max_steps: int | None = None,
          batch: int = 512, min_gain: float = 0.0,
          snapshot_budgets: tuple[int, ...] = ()) -> dict:
    """Select dots.  Returns the dot mask, the tracked P/F and a sparse trace.

    Lazy greedy is evaluated in **batches**: pop ``batch`` upper bounds, recompute
    their exact penalised gains in one vectorised call, commit the single best and
    push the rest back with exact keys (which remain valid upper bounds because
    gains only decrease).  This is the standard batch-lazy form of CELF and
    produces the same selection order as one-at-a-time lazy greedy.
    """
    offs, ks = kernel_offsets()
    shape = h.shape
    h_flat = np.ascontiguousarray(h.ravel(), dtype=np.float32)
    flat = _candidates(h_flat, footprint, n_cand)
    u0, fcost = _static(h_flat, flat, offs, ks, shape)
    order = np.argsort(-u0, kind="stable")
    flat, u0, fcost = flat[order], u0[order], fcost[order]

    cover = np.zeros(h_flat.shape[0], np.float32)
    chosen = np.zeros(flat.shape[0], bool)
    dots: list[int] = []
    P = 0.0
    F = 0.0
    lam = 0.0
    if N_hat is None:
        N_hat = float(footprint.sum()) * 0.012
    cap = budget if budget is not None else (max_steps or flat.shape[0])

    heap = [(-float(u0[i]), int(i)) for i in range(flat.shape[0])]
    heapq.heapify(heap)
    trace: list[dict] = []
    while heap and len(dots) < cap:
        popped: list[int] = []
        while heap and len(popped) < batch:
            _, i = heapq.heappop(heap)
            if chosen[i]:
                continue
            popped.append(i)
        if not popped:
            break
        pi = np.asarray(popped, np.int64)
        exact = _gains(h_flat, flat[pi], cover, offs, ks, shape)
        dF = fcost[pi]
        score = exact if mode == "maxcover" else exact - lam * dF
        top_bound = -heap[0][0] if heap else -np.inf
        best = int(np.argmax(score))
        if score[best] < top_bound - 1e-6:
            for j, i in enumerate(popped):
                heapq.heappush(heap, (-float(score[j]), int(i)))
            continue
        if mode != "maxcover" and score[best] <= min_gain:
            break                      # λ only grows; nothing left can qualify
        for j, i in enumerate(popped):
            if j != best:
                heapq.heappush(heap, (-float(score[j]), int(i)))
        i = popped[best]
        chosen[i] = True
        dots.append(int(flat[i]))
        y, x = divmod(int(flat[i]), shape[1])
        for (dy, dx), k in zip(offs, ks):
            yy, xx = y + int(dy), x + int(dx)
            if 0 <= yy < shape[0] and 0 <= xx < shape[1]:
                j = yy * shape[1] + xx
                if k > cover[j]:
                    P += float(h_flat[j]) * (k - cover[j])
                    cover[j] = k
        F += float(dF[best])
        if mode != "maxcover":
            lam = P / (F + 4.0 * N_hat) if (F + 4.0 * N_hat) > 0 else 0.0
        trace.append(dict(step=len(dots), P=round(P, 2), F=round(F, 2), lam=round(lam, 6)))

    mask = np.zeros(h_flat.shape[0], bool)
    mask[np.asarray(dots, np.int64)] = True
    snaps = {}
    if snapshot_budgets:
        take = sorted({int(b) for b in snapshot_budgets if 0 < int(b) <= len(dots)})
        for b in take:
            m = np.zeros(h_flat.shape[0], bool)
            m[np.asarray(dots[:b], np.int64)] = True
            snaps[b] = m.reshape(shape)
    stride = max(1, len(trace) // 12)
    return dict(mask=mask.reshape(shape), dots=len(dots), P=P, F=F, lam=lam,
                N_hat=N_hat, mode=mode, trace=trace[::stride] + trace[-1:],
                snapshots=snaps)


def nms_threshold(h: np.ndarray, footprint: np.ndarray, budget: int,
                  mode: str = "nms") -> dict:
    """Baseline: top-``budget`` hazard cells after optional 3x3 NMS."""
    from scipy import ndimage as ndi
    hh = np.where(footprint, h, -np.inf)
    if mode == "nms":
        mx = ndi.maximum_filter(hh, size=3)
        keep = footprint & (hh >= mx) & (hh > 0)
    else:
        keep = footprint & (hh > 0)
    H, W = h.shape
    idx = np.flatnonzero(keep.ravel())
    if idx.size > budget:
        vals = hh.ravel()[idx]
        sel = np.argpartition(-vals, budget - 1)[:budget]
        idx = idx[sel]
    mask = np.zeros(H * W, bool)
    mask[idx] = True
    return dict(mask=mask.reshape(H, W), dots=int(idx.size), mode=mode)
