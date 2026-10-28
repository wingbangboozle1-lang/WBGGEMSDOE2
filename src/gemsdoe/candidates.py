"""Candidate emissions for the GEMS submission, built to a stated mass budget.

Every candidate here is a *deterministic* function of organizer-provided layers
(the 19-band stack) plus, optionally, a dispersed hedge term.  Nothing is copied
from another team's raster and nothing reads the truth set.

Physics used by the consensus (each category contributes one vote, so no single
survey can dominate):

* magnetic  -- ``rtp``, ``tmi_hg``, ``tmi_vg``, ``tc``  (magnetisation contrasts
  across fault blocks; ``tc`` is itself an edge/curvature detector)
* gravity   -- ``iso_grav_anom_hg``, ``iso_grav_anom_vg``, ``iso_grav_anom_slope``
  (density contrasts at basement steps)
* topographic -- ``det_elev_slope``, ``det_elev`` (fault scarps and range fronts)
* strain    -- ``geod_shearrate``, ``geod_2ndinv`` (active deformation fabric)
* seismic   -- ``ieq_n100a15`` (earthquake density along active structures)

The response for a band is the absolute band-pass (Laplacian-of-Gaussian) at the
300 m scale already stored in the shared feature bank, robustly normalised inside
the footprint.  Faults are *curvilinear* features, so the consensus is thinned to
a one-pixel skeleton before placement: width is what the alpha=0.2/beta=0.8 metric
punishes, not length.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import features, grid

CATEGORIES = {
    "magnetic": ["rtp", "tmi_hg", "tmi_vg", "tc"],
    "gravity": ["iso_grav_anom_hg", "iso_grav_anom_vg", "iso_grav_anom_slope"],
    "topographic": ["det_elev_slope", "det_elev"],
    "strain": ["geod_shearrate", "geod_2ndinv"],
    "seismic": ["ieq_n100a15"],
}


def _layer_index(name: str, kind: str = "log_s3") -> int:
    names = features.layer_names()
    return names.index(f"{name}__{kind}")


def consensus_surface(fp: np.ndarray, kind: str = "log_s3", scale_clip: float = 4.0) -> np.ndarray:
    bank = features.load()
    votes = []
    for cat, bands in CATEGORIES.items():
        acc = np.zeros(grid.SHAPE, dtype="float32")
        used = 0
        for b in bands:
            try:
                li = _layer_index(b, kind)
            except ValueError:
                continue
            a = np.asarray(bank[li], dtype="float32")
            a = np.abs(np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0))
            v = a[fp]
            hi = float(np.percentile(v, 99.5)) or 1.0
            a = np.clip(a / hi, 0.0, scale_clip)
            acc += a
            used += 1
        if used:
            votes.append(acc / used)
    surf = np.mean(votes, axis=0).astype("float32")
    surf = ndi.gaussian_filter(surf, 1.0)
    surf[~fp] = 0.0
    return surf


def _skeleton(surface: np.ndarray, threshold: float) -> np.ndarray:
    from skimage.morphology import skeletonize
    return skeletonize(surface >= threshold)


def _skeleton_for_budget(surface: np.ndarray, fp: np.ndarray, budget: int) -> np.ndarray:
    """Binary-search the threshold whose skeleton holds about ``budget`` cells."""
    lo, hi = float(np.quantile(surface[fp], 0.50)), float(surface[fp].max())
    v = surface[fp]
    best = None
    for _ in range(7):
        mid = 0.5 * (lo + hi)
        skel = _skeleton(surface, mid)
        n = int(skel.sum())
        if best is None or abs(n - budget) < abs(int(best[0].sum()) - budget):
            best = (skel, mid)
        if n < budget:
            hi = mid
        else:
            lo = mid
    return best[0]


def ridge_emission(surface: np.ndarray, fp: np.ndarray, budget: int,
                   threshold: float | None = None, flank_value: float = 0.0) -> np.ndarray:
    """Place ``budget`` unit-mass cells on the strongest skeleton cells."""
    skel = _skeleton(surface, threshold) if threshold is not None else \
        _skeleton_for_budget(surface, fp, budget)
    vals = surface[skel]
    if vals.size == 0:
        raise ValueError("empty skeleton: threshold too high")
    order = np.argsort(-vals)
    take = min(budget, vals.size)
    keep = order[:take]
    r, c = np.nonzero(skel)
    out = np.zeros(grid.SHAPE, dtype="float32")
    out[r[keep], c[keep]] = 1.0
    if flank_value > 0:
        ring = ndi.binary_dilation(out > 0, iterations=1) & ~(out > 0)
        out[ring] = float(flank_value)
    return out


def dispersed_emission(fp: np.ndarray, budget: int, seed: int = 20261028) -> np.ndarray:
    """Deterministic, spatially dispersed hedge placement (quasi-random)."""
    rng = np.random.default_rng(seed)
    r, c = np.nonzero(fp)
    sel = rng.choice(r.size, size=min(budget, r.size), replace=False)
    out = np.zeros(grid.SHAPE, dtype="float32")
    out[r[sel], c[sel]] = 1.0
    return out


def hybrid_emission(surface: np.ndarray, fp: np.ndarray, budget: int,
                    ridge_fraction: float = 0.75, seed: int = 20261028) -> np.ndarray:
    n_ridge = int(round(budget * ridge_fraction))
    out = ridge_emission(surface, fp, n_ridge)
    hedge = dispersed_emission(fp, budget - n_ridge, seed=seed)
    out = np.maximum(out, hedge)
    return out
