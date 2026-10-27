"""Read-back GeoTIFF inspection; format validity is NOT submission approval."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import numpy as np
import rasterio


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_tif(path, reference, *, strict_all_finite=False):
    """Validate against an explicit reference grid and its finite footprint.

    Reference authenticity must be assessed separately. No clipping or repair.
    NaN outside the footprint is permitted unless strict_all_finite is enabled.
    """
    failures = []
    path, reference = Path(path), Path(reference)
    with rasterio.open(reference) as ref, rasterio.open(path) as src:
        if ref.count != 1:
            raise ValueError("reference must have one band")
        if ref.crs is None or ref.crs.to_epsg() != 32611:
            raise ValueError("reference must use EPSG:32611")
        if not (math.isclose(math.hypot(ref.transform.a, ref.transform.d), 100.0, abs_tol=1e-6)
                and math.isclose(math.hypot(ref.transform.b, ref.transform.e), 100.0, abs_tol=1e-6)):
            raise ValueError("reference pixel size must be 100 m")
        fp = np.isfinite(ref.read(1)) & (ref.read_masks(1) > 0)
        if not fp.any():
            raise ValueError("reference footprint is empty")
        grid_match = (src.shape == ref.shape and src.crs == ref.crs and src.transform == ref.transform)
        if not grid_match:
            failures.append("CRS, shape or transform does not match reference")
        if src.count != 1:
            failures.append("expected exactly one band")
        if src.dtypes[0] != "float32":
            failures.append("expected float32")
        if src.shape != fp.shape:
            # Avoid broadcasting or reading the wrong footprint after a grid failure.
            values = None
        else:
            values = src.read(1)
        report = {"path": str(path), "sha256": sha256(path), "grid_match_reference": grid_match,
                  "crs": str(src.crs), "shape": list(src.shape), "transform": list(src.transform)[:6],
                  "bands": src.count, "dtype": src.dtypes[0], "nodata": None if src.nodata is None else str(src.nodata),
                  "strict_all_finite_requested": strict_all_finite,
                  "reference_sha256": sha256(reference),
                  "organizer_acceptance": "unknown", "submission_approval": False}
        if values is not None:
            inside = values[fp]
            masked_inside = int((src.read_masks(1)[fp] == 0).sum())
            if masked_inside:
                failures.append("reference-footprint cells are marked nodata/masked")
            finite_inside = np.isfinite(inside)
            bad_inside = (~finite_inside) | (inside < 0) | (inside > 1)
            if bad_inside.any():
                failures.append("nonfinite or outside [0,1] inside footprint")
            finite_all = np.isfinite(values)
            if strict_all_finite and ((~finite_all) | (values < 0) | (values > 1)).any():
                failures.append("strict whole-array finite [0,1] check failed")
            # Infinities or finite values outside [0,1] are invalid everywhere.
            if np.isinf(values).any() or np.any(finite_all & ((values < 0) | (values > 1))):
                failures.append("infinite or out-of-range value anywhere")
            if np.any((~fp) & finite_all & (values > 0)):
                failures.append("positive value outside reference footprint")
            # Preserve raw-value and mask diagnostics separately. In particular,
            # finite zero tagged as NoData is not a valid in-footprint prediction.
            # Counts are for band 1; an additional band is already a hard failure.
            nan = np.isnan(values)
            inf = np.isinf(values)
            below = finite_all & (values < 0)
            above = finite_all & (values > 1)
            report.update(footprint_cells=int(fp.sum()), nonfinite_inside=int((~finite_inside).sum()),
                          masked_inside=masked_inside,
                          nan_total=int(nan.sum()), inf_total=int(inf.sum()),
                          nan_inside=int((nan & fp).sum()), nan_outside=int((nan & ~fp).sum()),
                          inf_inside=int((inf & fp).sum()), inf_outside=int((inf & ~fp).sum()),
                          below_zero_inside=int((below & fp).sum()), below_zero_outside=int((below & ~fp).sum()),
                          above_one_inside=int((above & fp).sum()), above_one_outside=int((above & ~fp).sum()),
                          positive_outside=int((finite_all & (values > 0) & ~fp).sum()),
                          diagnostics_band=1, all_finite=bool(finite_all.all()),
                          minimum_inside=float(inside[finite_inside].min()) if finite_inside.any() else None,
                          maximum_inside=float(inside[finite_inside].max()) if finite_inside.any() else None,
                          nonzero_inside=int((finite_inside & (inside > 0)).sum()))
        report["failures"] = failures
        report["format_valid_against_reference"] = not failures
        return report
