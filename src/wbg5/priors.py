"""Geologically motivated prior surfaces on the competition grid.

Each prior is a percentile field in [0,1] built only from layers that do **not**
encode the public fault catalogue, except ``catalogue_continuity`` which is
explicitly labelled and recomputed from visible faults in holdout runs.
"""
from __future__ import annotations

import numpy as np

from . import grid


def _mean(fields):
    out = np.zeros_like(fields[0], dtype="float32")
    n = 0
    for f in fields:
        out += np.nan_to_num(f, nan=0.0)
        n += 1
    return out / max(n, 1)


def scarp(masks) -> np.ndarray:
    """Lidar scarp morphometry (USGS 3DEP 1 m DEM, 100 m aggregation)."""
    L = grid.lidar_stack()
    valid = L[11] > 0
    dom = masks.footprint & valid
    idx = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    return _mean([grid.percentile_field(L[i], dom) for i in idx])


def geophysical_edge(masks) -> np.ndarray:
    """Coincident magnetic / gravity gradient highs (edge detection)."""
    X = grid.feature_stack()
    dom = masks.footprint
    idx = [2, 4, 8, 10, 17]  # tmi_hg, grav slope, tmi_vg, grav vg, grav hg
    return _mean([grid.percentile_field(np.abs(X[i]), dom) for i in idx])


def strain(masks) -> np.ndarray:
    X = grid.feature_stack()
    dom = masks.footprint
    return _mean([grid.percentile_field(np.abs(X[i]), dom) for i in (3, 6, 7)])


def topography(masks) -> np.ndarray:
    X = grid.feature_stack()
    dom = masks.footprint
    return _mean([grid.percentile_field(np.abs(X[i]), dom) for i in (11, 18)])


def thermal(masks) -> np.ndarray:
    """Hydrothermal / geothermal occurrence proximity plus K-U radiometric enrichment."""
    d_ws = grid.point_distance(grid.paths.WELLSPRING, masks)
    d_ve = grid.point_distance(grid.paths.VENTS, masks)
    dom = masks.footprint
    prox = _mean([
        grid.percentile_field(-d_ws, dom),
        grid.percentile_field(-d_ve, dom),
    ])
    R = grid.rad_stack()
    rad = _mean([grid.percentile_field(R[0], dom), grid.percentile_field(R[2], dom),
                 grid.percentile_field(R[4], dom)])
    return 0.7 * prox + 0.3 * rad


def catalogue_continuity(masks, visible: np.ndarray | None = None,
                         reach_px: float = 12.0) -> np.ndarray:
    """Inverse distance to mapped fault pixels (truncated at ``reach_px``)."""
    from scipy import ndimage as ndi
    src = masks.catalogue if visible is None else visible
    d = ndi.distance_transform_edt(~src).astype("float32")
    v = np.clip(1.0 - d / reach_px, 0.0, 1.0)
    v[~masks.footprint] = 0.0
    return v


def catalogue_halo(masks, visible: np.ndarray | None = None, inner=2.0, outer=6.0) -> np.ndarray:
    """Ring around mapped faults: the organizer says new geometry may continue them."""
    from scipy import ndimage as ndi
    src = masks.catalogue if visible is None else visible
    d = ndi.distance_transform_edt(~src).astype("float32")
    v = np.clip(1.0 - np.abs(d - 0.5 * (inner + outer)) / (0.5 * (outer - inner)), 0.0, 1.0)
    v[~masks.footprint] = 0.0
    return v
