"""Fail-closed format validation of a GEMS submission against the official sample.

Checks, in order, and reports every failure instead of repairing the file:

1.  single band, float32
2.  same height/width, same transform, same CRS as the reference sample
3.  every pixel (inside AND outside footprint) finite and inside [0, 1]
    (DrivenData evaluates ``((pred >= 0) & (pred <= 1)).all()`` across the full
    3730x3292 array, matching ``unet-mc-cv-reference-solution.ipynb`` Cell 16;
    any outside-footprint NaN triggers ``"Predicted values must be in range [0, 1]"``)
4.  out-of-footprint cells equal 0.0 and nodata tag is None (no internal mask hiding 0s)
5.  the file opens through rasterio and the mask is readable

This is a local format check.  It is not an organizer receipt, not a
uniqueness proof and not a score.
"""
from __future__ import annotations

import numpy as np
import rasterio


def validate_submission(path, reference) -> dict:
    failures: list[str] = []
    report: dict = {"file": str(path), "reference": str(reference)}

    with rasterio.open(reference) as ref:
        ref_shape, ref_crs = ref.shape, ref.crs
        ref_transform = tuple(ref.transform)[:6]
        ref_footprint = np.isfinite(ref.read(1))
    report["reference_footprint_cells"] = int(ref_footprint.sum())

    with rasterio.open(path) as ds:
        mask_arr = ds.dataset_mask()
        report.update(
            shape=list(ds.shape), bands=int(ds.count), dtype=ds.dtypes[0],
            crs=str(ds.crs), transform=[round(v, 6) for v in tuple(ds.transform)[:6]],
            nodata=None if ds.nodata is None else (float("nan") if np.isnan(ds.nodata) else float(ds.nodata)),
        )
        if tuple(ds.shape) != tuple(ref_shape):
            failures.append(f"shape {ds.shape} != reference {ref_shape}")
        if ds.count != 1:
            failures.append(f"band count {ds.count} != 1")
        if ds.dtypes[0] != "float32":
            failures.append(f"dtype {ds.dtypes[0]} != float32")
        if ds.crs != ref_crs:
            failures.append(f"crs {ds.crs} != reference {ref_crs}")
        if tuple(ds.transform)[:6] != ref_transform:
            failures.append("transform differs from the reference")
        if ds.nodata is not None:
            failures.append(f"nodata={ds.nodata!r} must be None for portal-safe all-finite [0, 1] GeoTIFF")
        a = ds.read(1)

    finite = np.isfinite(a)
    missing_inside = ref_footprint & ~finite
    nan_outside = (~ref_footprint) & (~finite)
    finite_outside = int(((~ref_footprint) & finite).sum())
    nonzero_outside = int(((~ref_footprint) & finite & (a != 0.0)).sum())
    masked_inside = int((ref_footprint & (mask_arr == 0)).sum()) if mask_arr.shape == ref_footprint.shape else None
    report.update(
        finite_cells=int(finite.sum()),
        nan_cells=int((~finite).sum()),
        inf_cells=int(np.isinf(a).sum()),
        nonfinite_inside_footprint=int(missing_inside.sum()),
        nan_outside_footprint=int(nan_outside.sum()),
        finite_outside_footprint=finite_outside,
        nonzero_outside_footprint=nonzero_outside,
        masked_inside_footprint=masked_inside,
        outside_footprint_cells=int((~ref_footprint).sum()),
    )
    if missing_inside.any():
        failures.append("non-finite values inside the reference footprint")
    if nan_outside.any():
        failures.append(
            f"{int(nan_outside.sum())} non-finite (NaN/Inf) cells outside footprint "
            "(triggers DrivenData 'Predicted values must be in range [0, 1]'; write 0.0 outside footprint)"
        )
    if nonzero_outside:
        failures.append(f"{nonzero_outside} non-zero finite values outside the reference footprint")
    if masked_inside:
        failures.append(f"{masked_inside} masked/nodata cells inside the reference footprint")

    vals = a[ref_footprint & finite]
    report.update(
        min_inside=float(vals.min()) if vals.size else None,
        max_inside=float(vals.max()) if vals.size else None,
        distinct_values=int(np.unique(vals).size) if vals.size else 0,
        positive_cells=int((vals > 0).sum()) if vals.size else 0,
        mass=float(vals.sum()) if vals.size else 0.0,
    )
    if vals.size and (vals.min() < 0.0):
        failures.append("values below 0 inside the footprint")
    if vals.size and (vals.max() > 1.0):
        failures.append("values above 1 inside the footprint")
    if finite.any():
        gmin, gmax = float(a[finite].min()), float(a[finite].max())
        report["min_all"], report["max_all"] = gmin, gmax
        if gmin < 0.0 or gmax > 1.0:
            failures.append("finite values outside [0, 1]")

    report["failures"] = failures
    report["ok"] = not failures
    report["nodata_encoding"] = (
        "all-finite 0.0 outside footprint (nodata=None)"
        if report["nan_cells"] == 0 and nonzero_outside == 0 and report["nodata"] is None
        else ("NaN outside the data footprint (PORTAL-REJECTED)" if report["nan_outside_footprint"] > 0 else "mixed")
    )
    return report
