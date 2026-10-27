"""Fail-closed format validation of a GEMS submission against the official sample.

Checks, in order, and reports every failure instead of repairing the file:

1.  single band, float32
2.  same height/width, same transform, same CRS as the reference sample
3.  every in-footprint cell finite and inside [0, 1]
4.  no negative / greater-than-one values anywhere
5.  out-of-footprint cells are NaN or null (the specification allows either)
6.  the file opens through rasterio and the mask is readable

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
        report.update(
            shape=list(ds.shape), bands=int(ds.count), dtype=ds.dtypes[0],
            crs=str(ds.crs), transform=[round(v, 6) for v in tuple(ds.transform)[:6]],
            nodata=None if ds.nodata is None else float(ds.nodata),
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
        a = ds.read(1)

    finite = np.isfinite(a)
    missing_inside = ref_footprint & ~finite          # must be zero
    nan_outside = (~ref_footprint) & (~finite)        # permitted by the spec
    report.update(
        finite_cells=int(finite.sum()),
        nan_cells=int((~finite).sum()),
        nonfinite_inside_footprint=int(missing_inside.sum()),
        nan_outside_footprint=int(nan_outside.sum()),
        outside_footprint_cells=int((~ref_footprint).sum()),
    )
    if missing_inside.any():
        failures.append("non-finite values inside the reference footprint")
    finite_outside = int(((~ref_footprint) & finite).sum())
    report["finite_outside_footprint"] = finite_outside
    if finite_outside:
        failures.append("finite values outside the reference footprint "
                        "(the specification requires null/NaN there)")

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
    if np.isfinite(a).any():
        gmin, gmax = float(np.nanmin(a)), float(np.nanmax(a))
        report["min_all"], report["max_all"] = gmin, gmax
        if gmin < 0.0 or gmax > 1.0:
            failures.append("finite values outside [0, 1]")

    report["failures"] = failures
    report["ok"] = not failures
    report["nodata_encoding"] = ("NaN outside the data footprint"
                                 if report["nan_outside_footprint"] == report["outside_footprint_cells"]
                                 else "mixed")
    return report
