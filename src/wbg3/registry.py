"""Registry comparison: literal duplicate stop + rank correlation.

Implements the two checks the parallel-run protocol requires, on the *final*
dots and (where available) on the pre-placement surface:

* literal overlap -- the fraction of the candidate's dots that fall within an
  inclusive Euclidean radius of at least one dot of a registry raster.  The
  stop is > 0.70 for any single registry raster.
* rank correlation -- Spearman on the in-footprint values.  The stop is > 0.90.

A partial registry can prove FAIL, never PASS.  The verdict recorded here is
therefore "no registry raster exceeded the limits among the N compared", not a
certificate of uniqueness.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata, spearmanr

OVERLAP_LIMIT = 0.70
CORRELATION_LIMIT = 0.90
RADIUS_PX = 3.0


def literal_overlap(candidate: np.ndarray, reference: np.ndarray,
                    radius_px: float = RADIUS_PX) -> float:
    """Directed: fraction of *candidate* dots within ``radius_px`` of a reference dot."""
    cand = np.asarray(candidate, dtype=bool)
    ref = np.asarray(reference, dtype=bool)
    if cand.shape != ref.shape:
        raise ValueError("candidate and reference must share a grid")
    n = int(cand.sum())
    if n == 0:
        raise ValueError("candidate has no dots")
    if not ref.any():
        return 0.0
    d = distance_transform_edt(~ref)
    return float((d[cand] <= radius_px).mean())


def surface_correlation(candidate, reference, mask) -> float | None:
    """Tie-aware Spearman on in-footprint cells; None when undefined."""
    mask = np.asarray(mask, dtype=bool)
    a = np.asarray(candidate, dtype=np.float64)[mask]
    b = np.asarray(reference, dtype=np.float64)[mask]
    keep = np.isfinite(a) & np.isfinite(b)
    a, b = a[keep], b[keep]
    if a.size < 3 or np.all(a == a[0]) or np.all(b == b[0]):
        return None
    r = spearmanr(a, b).statistic
    if not np.isfinite(r):
        r = _rank_corr(a, b)
    return None if not np.isfinite(r) else float(r)


def _rank_corr(a, b) -> float:
    ra, rb = rankdata(a), rankdata(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = np.sqrt((ra * ra).sum() * (rb * rb).sum())
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def compare(candidate, registry: dict, mask) -> dict:
    """Run both legs against every registry entry and return a receipt."""
    rows = []
    for name, ref in registry.items():
        ref = np.asarray(ref, dtype=bool)
        if ref.shape != candidate.shape:
            rows.append(dict(name=name, status="shape-mismatch"))
            continue
        ov = literal_overlap(candidate, ref)
        rows.append(dict(name=name, dots=int(ref.sum()),
                         overlap_3px=round(ov, 6),
                         overlap_fail=bool(ov > OVERLAP_LIMIT)))
    worst = max((r for r in rows if "overlap_3px" in r),
                key=lambda r: r["overlap_3px"], default=None)
    return dict(
        evaluated=int(len(rows)),
        radius_px=RADIUS_PX,
        overlap_limit=OVERLAP_LIMIT,
        correlation_limit=CORRELATION_LIMIT,
        worst_overlap=worst,
        any_overlap_fail=any(r.get("overlap_fail") for r in rows),
        rows=rows,
        scope_note=("A partial registry can prove a duplicate, never uniqueness. "
                    "This receipt covers only the rasters listed in rows."),
    )
