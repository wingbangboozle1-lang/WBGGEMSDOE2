"""Score any prediction raster the way the organizer scores a submission.

Organizer rule (verified at source, 2026-10-28):

* metric = distance-weighted Tversky index, R = 300 m, alpha = 0.2, beta = 0.8
  (problem description, page 967);
* pixels of known USGS/INGENIOUS faults are **masked / excluded** from evaluation
  so they do not contribute to any penalty term (DrivenData staff, forum thread
  11516, 2026-09-16);
* the test truth is a set of expert-labelled faults that are absent from the
  public catalogue.

Locally we can only approximate (3): the held-out catalogue segments of
``gemsdoe.holdout`` stand in for expert-labelled new faults.  Every number that
comes out of this module is therefore labelled HOLDOUT-DTI, never a leaderboard
score.
"""
from __future__ import annotations

import numpy as np

from . import grid
from .fastdti import fast_dti, pool

K_FOLDS = 4


def active_masks(known_dilation: int = 0) -> list[np.ndarray]:
    """Per-fold scoring mask: footprint minus the known (visible) catalogue pixels."""
    from scipy import ndimage as ndi
    fp = np.load(grid.WORK / "footprint.npy")
    out = []
    for k in range(K_FOLDS):
        vis = np.load(grid.WORK / f"fold{k}_visible.npy")
        if known_dilation:
            vis = ndi.binary_dilation(vis, iterations=int(known_dilation))
        out.append(fp & ~vis)
    return out


def truth_masks() -> list[np.ndarray]:
    return [np.load(grid.WORK / f"fold{k}_truth.npy") for k in range(K_FOLDS)]


def holdout_dti(pred: np.ndarray, known_dilation: int = 0) -> dict:
    """Pooled HOLDOUT-DTI over the four folds with the organizer's masked-pixel rule."""
    acts = active_masks(known_dilation)
    truths = truth_masks()
    parts = [fast_dti(pred, t, a) for t, a in zip(truths, acts)]
    res = pool(parts)
    res["fold_dti"] = [p["dti"] for p in parts]
    res["fold_truth"] = [p["n_truth"] for p in parts]
    res["known_dilation_px"] = known_dilation
    res["evidence_class"] = ("HOLDOUT-DTI (proxy truth = withheld catalogue segments; "
                             "not a leaderboard score)")
    return res


def describe(pred: np.ndarray) -> dict:
    fp = np.load(grid.WORK / "footprint.npy")
    inside = np.asarray(pred, dtype="float32")[fp]
    pos = inside > 0
    return {
        "mass_inside_footprint": float(np.nansum(inside)),
        "positive_cells": int(pos.sum()),
        "max": float(np.nanmax(inside)) if inside.size else None,
        "mean": float(np.nanmean(inside)) if inside.size else None,
        "binary": bool(np.all(np.isin(inside[pos], [0.0, 1.0]))) if pos.any() else True,
        "frac_of_footprint": float(pos.sum() / fp.sum()),
    }
