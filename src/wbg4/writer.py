"""Submission writer and independent format validator for the WBG4 lane.

The format contract is taken from the official submission text and from the
organizer template's actual bytes (``scratch/bridge/sample_submission.tif``):

* one band, ``float32``
* ``EPSG:32611`` (UTM 11N), 100 m pixels, shape ``(3730, 3292)``
* geotransform exactly ``(100, 0, 243350, 0, -100, 4508550)``
* every value in ``[0, 1]`` inside the scoring footprint, no ``NaN`` inside it
* outside the footprint: ``NaN`` *or* ``0`` are both accepted by the official
  text.  Zeros are written here because the requester reported that the portal
  answered a NaN-filled upload with *"Predicted values must be in range [0, 1]"*,
  and ``12GEMSDOE`` owner reports that NaN-outside and zeros-outside variants of
  the same predictions scored identically (0.1294).  A ``-nan`` twin is written
  alongside so the choice is auditable rather than asserted.
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import rasterio
from rasterio.transform import Affine

EXPECTED_SHAPE = (3730, 3292)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


def write_submission(footprint: np.ndarray, dots: np.ndarray, path: str,
                     outside: str = "zero", template: str | None = None) -> dict:
    """Write a validated single-band GeoTIFF and return its receipt."""
    if footprint.shape != EXPECTED_SHAPE or dots.shape != EXPECTED_SHAPE:
        raise ValueError(f"shape {dots.shape} != {EXPECTED_SHAPE}")
    if outside not in ("zero", "nan"):
        raise ValueError("outside must be 'zero' or 'nan'")
    out = np.full(dots.shape, 0.0 if outside == "zero" else np.nan, np.float32)
    out[footprint] = 0.0
    out[footprint & dots] = 1.0
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=EXPECTED_SHAPE[0],
                       width=EXPECTED_SHAPE[1], count=1, dtype="float32",
                       crs=EXPECTED_CRS, transform=Affine(*EXPECTED_TRANSFORM),
                       nodata=None if outside == "zero" else np.nan,
                       compress="deflate", predictor=3, tiled=False) as ds:
        ds.write(out, 1)
    return validate_submission(path, template=template)


def validate_submission(path: str, template: str | None = None) -> dict:
    """Reopen the written bytes and check every clause of the format contract."""
    with rasterio.open(path) as ds:
        a = ds.read(1)
        meta = dict(shape=ds.shape, count=ds.count, dtype=ds.dtypes[0], crs=str(ds.crs),
                    transform=tuple(ds.transform), nodata=ds.nodata,
                    width=ds.width, height=ds.height)
    with rasterio.open(template) as t:
        base = t.read(1)
        tmeta = dict(shape=t.shape, crs=str(t.crs), transform=tuple(t.transform))
    fp = np.isfinite(base)
    inside = a[fp]
    outside_vals = a[~fp]
    checks = dict(
        shape_matches=meta["shape"] == EXPECTED_SHAPE == tmeta["shape"],
        count_is_one=meta["count"] == 1,
        dtype_is_float32=meta["dtype"] == "float32",
        crs_matches=meta["crs"] == EXPECTED_CRS == tmeta["crs"],
        transform_matches=tuple(round(v, 6) for v in meta["transform"][:6])
        == EXPECTED_TRANSFORM == tuple(round(v, 6) for v in tmeta["transform"][:6]),
        no_nan_inside_footprint=bool(np.isfinite(inside).all()),
        values_in_0_1_inside_footprint=bool(
            np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0),
        no_inf_anywhere=bool(~np.isinf(a).any()),
        positives_inside=int((inside > 0).sum()),
        outside_all_zero=bool((outside_vals == 0).all()) if outside_vals.size else True,
        outside_all_nan=bool(np.isnan(outside_vals).all()) if outside_vals.size else True,
    )
    checks["all_format_checks_pass"] = bool(
        checks["shape_matches"] and checks["count_is_one"] and checks["dtype_is_float32"]
        and checks["crs_matches"] and checks["transform_matches"]
        and checks["no_nan_inside_footprint"] and checks["values_in_0_1_inside_footprint"]
        and checks["no_inf_anywhere"]
        and (checks["outside_all_zero"] or checks["outside_all_nan"]))
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return dict(path=path, sha256=h, bytes=os.path.getsize(path),
                meta=meta, checks=checks,
                format_valid=checks["all_format_checks_pass"])
