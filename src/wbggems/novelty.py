"""Literal, fail-closed novelty checks. A partial inventory can prove FAIL, not PASS.

A prospective surface must be checked before emitting final dots. This module
never creates or alters predictions and cannot certify an incomplete registry.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata


@dataclass(frozen=True)
class Capacity:
    footprint_cells: int
    covered_cells: int
    uncovered_cells: int
    budget: int
    minimum_overlap: float
    feasible_under_limit: bool


def _mask(a, name):
    a = np.asarray(a)
    if a.ndim != 2 or a.dtype != np.bool_:
        raise ValueError(f"{name} must be a two-dimensional boolean mask")
    return a


def coverage(reference, radius_px=3.0):
    """Closed Euclidean disk, including distance exactly equal to the radius."""
    reference = _mask(reference, "reference")
    if not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError("radius must be finite and nonnegative")
    if not reference.any():
        raise ValueError("empty registry raster has undefined proximity")
    return distance_transform_edt(~reference) <= radius_px


def overlap_fraction(dots, covered):
    dots, covered = _mask(dots, "dots"), _mask(covered, "covered")
    if dots.shape != covered.shape or not dots.any():
        raise ValueError("dots must be nonempty and match the reference grid")
    return float(np.count_nonzero(dots & covered) / np.count_nonzero(dots))


def capacity_bound(footprint, covered, budget, limit=0.70):
    """Best possible overlap for any *distinct* dots in the given footprint.

    This is a counting bound, not an algorithm or a geological prediction.
    """
    footprint, covered = _mask(footprint, "footprint"), _mask(covered, "covered")
    if footprint.shape != covered.shape:
        raise ValueError("footprint/coverage shape mismatch")
    if not isinstance(budget, int) or isinstance(budget, bool) or not 0 < budget <= int(footprint.sum()):
        raise ValueError("budget must be a positive integer no larger than the footprint")
    if not np.isfinite(limit) or not 0 <= limit <= 1:
        raise ValueError("limit must be between zero and one")
    n = int(footprint.sum())
    k = int((footprint & covered).sum())
    u = n - k
    minimum = max(0, budget - u) / budget
    return Capacity(n, k, u, budget, minimum, minimum <= limit)


def spearman_footprint(left, right, footprint):
    """Exact tie-aware Spearman correlation on all in-footprint cells.

    Undefined correlations, nonfinite input and shape differences fail closed.
    """
    footprint = _mask(footprint, "footprint")
    a, b = np.asarray(left), np.asarray(right)
    if a.shape != footprint.shape or b.shape != footprint.shape or footprint.sum() < 2:
        raise ValueError("surface grids must match a nontrivial footprint")
    x, y = a[footprint], b[footprint]
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("nonfinite values inside footprint")
    rx = rankdata(x, method="average")
    ry = rankdata(y, method="average")
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.linalg.norm(rx) * np.linalg.norm(ry)
    if not np.isfinite(denom) or denom == 0:
        raise ValueError("rank correlation undefined for a constant surface")
    return float(np.dot(rx, ry) / denom)


def check_against_one(surface, dots, reference, footprint, *, correlation_limit=0.90, overlap_limit=0.70):
    """Check one surface/preview OR final stage against one registry raster.

    Returns an explicit witness; this is never enough to certify a full registry.
    """
    footprint = _mask(footprint, "footprint")
    dots = _mask(dots, "dots")
    reference = np.asarray(reference)
    if dots.shape != footprint.shape or reference.shape != footprint.shape:
        raise ValueError("grid shape mismatch")
    if np.any(dots & ~footprint):
        raise ValueError("dots outside footprint")
    if not np.isfinite(reference[footprint]).all():
        raise ValueError("nonfinite registry predictions inside footprint")
    if np.any((reference[footprint] < 0) | (reference[footprint] > 1)):
        raise ValueError("registry predictions outside [0,1]")
    rho = spearman_footprint(surface, reference, footprint)
    overlap = overlap_fraction(dots, coverage((reference > 0) & footprint))
    return {"spearman": rho, "abs_spearman": abs(rho), "overlap_3px": overlap,
            "duplicate": bool(abs(rho) > correlation_limit or overlap > overlap_limit)}


def single_feature_auc(values, positives, selected):
    """Tie-aware feature-alone AUC on an explicitly supplied holdout selection.

    The caller must construct each feature fold-locally. Passing the canary is
    necessary, not proof that catalogue leakage is absent.
    """
    positives, selected = _mask(positives, "positives"), _mask(selected, "selected")
    values = np.asarray(values)
    if positives.shape != selected.shape or values.shape != selected.shape:
        raise ValueError("feature/canary masks must share the same grid")
    x, truth = values[selected], positives[selected]
    if not np.isfinite(x).all():
        raise ValueError("canary features must be finite inside the evaluation selection")
    npos, nneg = int(truth.sum()), int((~truth).sum())
    if npos == 0 or nneg == 0:
        raise ValueError("AUC requires both positive and negative holdout examples")
    ranks = rankdata(x, method="average")
    auc = float((ranks[truth].sum() - npos * (npos + 1) / 2) / (npos * nneg))
    return {"auc": auc, "two_sided_auc": max(auc, 1.0 - auc),
            "withheld_positives": npos, "negative_examples": nneg,
            "canary_pass": max(auc, 1.0 - auc) <= 0.90}
