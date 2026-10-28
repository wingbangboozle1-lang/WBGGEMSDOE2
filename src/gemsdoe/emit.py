"""Metric-aware emission: turn a probability surface into a submission raster.

Why emission matters more than the model
----------------------------------------
With ``alpha = 0.2`` and ``beta = 0.8`` and DTI ``s``, one unit of true-positive
mass is worth ``1 - (1-beta) s`` while one unit of false-positive mass costs
``alpha s``.  At ``s = 0.28`` a wasted positive cell may therefore be traded
against up to 17 hit cells (``marginal_rule`` in ``fastdti``).  Two consequences:

1. **Width is expensive.**  A band ``w`` cells wide along a trace pays ``~0.2 w``
   per cell of length while the kernel already tolerates 300 m of offset.  A
   1-px skeleton plus a fractional flank captures nearly the same truth mass for
   a third of the cost.
2. **Mass is a budget.**  Beyond the point where extra cells stop covering new
   truth, every additional cell strictly lowers DTI.  The emission rule therefore
   optimises *coverage per unit mass*, not area.

The rule is a deterministic function of the surface (threshold, skeletonise,
flank), tuned on the holdout; nothing here peeks at the truth it is scored on.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi


def _thin(mask: np.ndarray) -> np.ndarray:
    from skimage.morphology import skeletonize
    return skeletonize(np.asarray(mask, dtype=bool))


def emit(surface: np.ndarray, threshold: float, thin: bool = False,
         flank_width: int = 0, flank_value: float = 0.0) -> np.ndarray:
    """Build a float32 prediction in [0, 1] from a probability surface."""
    core = np.asarray(surface, dtype="float32") >= float(threshold)
    if thin:
        core = _thin(core)
    out = np.where(core, 1.0, 0.0).astype("float32")
    if flank_width > 0 and flank_value > 0:
        grown = ndi.binary_dilation(core, iterations=int(flank_width))
        ring = grown & ~core
        out[ring] = float(flank_value)
    return out


def budget_sweep(surface: np.ndarray, active: np.ndarray, quantiles):
    """Emission thresholds that spend a target fraction of the scored cells."""
    v = np.asarray(surface, dtype="float32")[active]
    return {q: float(np.quantile(v, 1.0 - q)) for q in quantiles}


def describe(pred: np.ndarray, active: np.ndarray) -> dict:
    p = np.asarray(pred, dtype="float32")
    pos = (p > 0) & active
    return {"cells": int(pos.sum()), "mass": float(p[active].sum()),
            "frac_of_active": float(pos.sum() / max(int(active.sum()), 1))}
