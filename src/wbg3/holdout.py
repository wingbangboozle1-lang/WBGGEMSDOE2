"""Spatially blocked hide-and-recover holdout for the GEMS fault task.

Design (pre-registered before any candidate is generated):

* The region is cut into square blocks.  A deterministic hash assigns each block
  to one of K folds, so every fold is spatially contiguous but interleaved with
  the others -- this is the same geometry as the organiser's public/private
  "chunked" split described on the problem page.
* For fold k the *visible* faults are the catalogue outside fold k; the
  *withheld* truth is the catalogue inside fold k, eroded by ``boundary_px`` so
  that a fault crossing a block edge cannot be trivially continued from the
  neighbouring block.
* Catalogue-derived features (distance to visible fault) are recomputed from the
  visible set only.  No feature ever sees the withheld truth.
* Predictions are scored with the exact official metric on the whole grid; a
  predicted dot on a visible (not withheld) fault is a false positive, exactly
  as it is in the real competition where the catalogue is *not* the truth.

The instrument measures one thing: can a method recover mapped faults that it
cannot see, from the 19 geophysical/elevation bands alone?  It is *not* the
organiser's hidden truth and never becomes a leaderboard score.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt

from .metric import dti_binary, pooled


def block_folds(shape, n_folds=4, block=256, salt=0):
    """Deterministic interleaved spatial fold map."""
    h, w = shape
    rr, cc = np.mgrid[0:h, 0:w]
    bi, bj = rr // block, cc // block
    key = (bi.astype(np.int64) * 73856093) ^ (bj.astype(np.int64) * 19349663) ^ (salt * 83492791)
    return (key % n_folds).astype(np.int8)


def make_fold(catalogue, footprint, fold_map, k, boundary_px=15):
    """Return (visible, withheld, active) boolean masks for fold ``k``."""
    in_fold = fold_map == k
    withheld = catalogue & in_fold
    # erode the withheld truth away from the block boundary that crosses it
    if boundary_px > 0:
        # a truth cell is kept only if its whole (2b+1) neighbourhood is in-fold
        interior = binary_erosion(in_fold, iterations=boundary_px)
        withheld = withheld & interior
    visible = catalogue & ~in_fold
    active = footprint
    return visible, withheld, active


def distance_to_visible(visible, footprint):
    """Euclidean distance (px) from every cell to the nearest visible fault."""
    d = distance_transform_edt(~visible).astype(np.float32)
    d[~footprint] = np.nan
    return d


def evaluate_dots(dots, withheld, active, visible=None, buffer_visible_px=0):
    """Score a dot raster on the withheld truth.  Mirrors the official metric."""
    dots = np.asarray(dots, dtype=bool)
    if buffer_visible_px and visible is not None:
        keep = distance_transform_edt(~visible) > buffer_visible_px
        dots = dots & keep
    return dti_binary(dots, withheld, active)


def topk_dots(score, mask, k, min_sep=1):
    """Place ``k`` dots at the highest-scoring cells of ``score`` inside ``mask``.

    ``min_sep`` > 1 thins the selection greedily so no two dots are closer than
    ``min_sep`` px (Chebyshev), which spreads a fixed budget over more structure.
    """
    idx = np.flatnonzero(mask.ravel())
    if idx.size == 0 or k <= 0:
        return np.zeros(score.shape, dtype=bool)
    vals = score.ravel()[idx]
    order = np.argsort(-vals, kind="stable")[: min(idx.size, k * (min_sep ** 2) if min_sep > 1 else k)]
    out = np.zeros(score.shape, dtype=bool)
    h, w = score.shape
    taken = 0
    if min_sep <= 1:
        sel = idx[order[:k]]
        out.ravel()[sel] = True
        return out
    flat = out.ravel()
    for j in order:
        r, c = divmod(int(idx[j]), w)
        r0, r1 = max(0, r - min_sep + 1), min(h, r + min_sep)
        c0, c1 = max(0, c - min_sep + 1), min(w, c + min_sep)
        if out[r0:r1, c0:c1].any():
            continue
        flat[idx[j]] = True
        taken += 1
        if taken >= k:
            break
    return out


def poisson_thin(mask, radius, rng, target):
    """Randomly thin ``mask`` to ``target`` cells keeping a Poisson-disk spacing."""
    idx = np.flatnonzero(mask.ravel())
    rng.shuffle(idx)
    h, w = mask.shape
    out = np.zeros(mask.shape, dtype=bool)
    taken = 0
    for j in idx:
        r, c = divmod(int(j), w)
        r0, r1 = max(0, r - radius), min(h, r + radius + 1)
        c0, c1 = max(0, c - radius), min(w, c + radius + 1)
        if out[r0:r1, c0:c1].any():
            continue
        out[r, c] = True
        taken += 1
        if taken >= target:
            break
    return out
