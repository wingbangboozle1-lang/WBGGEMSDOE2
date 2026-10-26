"""submission_writer.py — strict GEMS submission GeoTIFF validator/writer.

Implements the submission-format contract of the DOE GEMS Prize Challenge
(see https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format):

  * single-band GeoTIFF, 32-bit float (float32)
  * CRS: EPSG:32611 (UTM zone 11N), 100 m resolution
  * identical bounds / geotransform as the training grid
  * pixel values in [0, 1] (confidence/probability of fault presence)
  * no NaN anywhere in the submitted array; cells outside the survey
    footprint are written as 0 (the "zeros" convention used by valid entries)

This module is intentionally dependency-lean: numpy + rasterio only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio.transform import Affine

# Canonical competition grid (verified from the GEMSDOE reference submissions
# on the same grid: EPSG:32611, 100 m pixels, origin (243350, 4508550),
# 3730 rows x 3292 columns).  The writer always matches the *provided*
# reference raster; these constants are only fallback documentation values.
CANONICAL_CRS = "EPSG:32611"
CANONICAL_SHAPE = (3730, 3292)
CANONICAL_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str]
    checks: dict
    shape: tuple[int, int]
    dtype: str
    crs: str
    transform: str
    value_min: Optional[float]
    value_max: Optional[float]
    nan_count: int
    outside_zero_fraction: Optional[float]
    sha256: Optional[str] = None


def reference_grid(reference_path: str | Path) -> dict:
    """Read CRS/transform/shape/dtype from a reference raster (sample
    submission, training features, or any validated competition-format TIF)."""
    with rasterio.open(reference_path) as src:
        return {
            "crs": src.crs,
            "transform": src.transform,
            "height": src.height,
            "width": src.width,
            "count": src.count,
            "dtype": src.dtypes[0],
            "bounds": src.bounds,
        }


def footprint_mask(reference_path: str | Path) -> np.ndarray:
    """Boolean True = inside survey footprint.

    Derived from a "-nan" reference raster (NaN = outside footprint).  Falls
    back to all-True with a warning if the reference has no NaN cells.
    """
    with rasterio.open(reference_path) as src:
        arr = src.read(1)
    mask = ~np.isnan(arr) if np.issubdtype(arr.dtype, np.floating) else np.ones(arr.shape, bool)
    if not mask.any():
        mask = np.ones(arr.shape, bool)
    return mask


def validate_array(
    arr: np.ndarray,
    reference_path: str | Path,
    footprint: Optional[np.ndarray] = None,
) -> ValidationReport:
    """Validate an in-memory prediction array against the reference grid.
    Does NOT modify the array.  Returns a report; ok=False on any failure."""
    errors: list[str] = []
    grid = reference_grid(reference_path)
    if footprint is None:
        footprint = footprint_mask(reference_path)

    checks = {
        "single_band": arr.ndim == 2,
        "shape_match": arr.shape == (grid["height"], grid["width"]),
        "dtype_float32": arr.dtype == np.float32,
        "values_in_01": bool(np.all((arr >= 0.0) & (arr <= 1.0))),
        "no_nan": bool(~np.isnan(arr).any()),
        "crs_match": True,  # set at write time from reference
        "transform_match": True,
    }

    if arr.ndim != 2:
        errors.append(f"expected 2-D array, got {arr.ndim}-D")
    else:
        if not checks["shape_match"]:
            errors.append(
                f"shape {arr.shape} != reference {grid['height']}x{grid['width']}"
            )
        if arr.dtype != np.float32:
            errors.append(f"dtype {arr.dtype} != float32")
        if not checks["values_in_01"]:
            mn = float(np.nanmin(arr)) if arr.size else None
            mx = float(np.nanmax(arr)) if arr.size else None
            errors.append(f"values outside [0, 1]: min={mn} max={mx}")
        if not checks["no_nan"]:
            errors.append(f"array contains {int(np.isnan(arr).sum())} NaN cells")

    sha = None
    vmin = vmax = None
    n_nan = int(np.isnan(arr).sum()) if arr.size else 0
    if arr.size:
        vmin = float(np.nanmin(arr)); vmax = float(np.nanmax(arr))
        with rasterio.open(reference_path, "r") as src:
            pass  # placeholder, sha computed by caller on file bytes

    outside_frac = None
    if footprint is not None and arr.shape == footprint.shape:
        outside = arr[~footprint]
        outside_frac = float((outside == 0.0).mean()) if outside.size else None

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        checks=checks,
        shape=arr.shape if arr.ndim == 2 else None,  # type: ignore[arg-type]
        dtype=str(arr.dtype),
        crs=str(grid["crs"]),
        transform=str(grid["transform"]),
        value_min=vmin,
        value_max=vmax,
        nan_count=n_nan,
        outside_zero_fraction=outside_frac,
    )


def write_submission(
    arr: np.ndarray,
    out_path: str | Path,
    reference_path: str | Path,
    footprint: Optional[np.ndarray] = None,
    compress: str = "deflate",
) -> ValidationReport:
    """Write a validated GEMS submission GeoTIFF.

    Raises ValueError if validation fails (nothing is written).
    """
    if footprint is None:
        footprint = footprint_mask(reference_path)
    report = validate_array(arr, reference_path, footprint)
    if not report.ok:
        raise ValueError("submission validation failed:\n  - " + "\n  - ".join(report.errors))

    grid = reference_grid(reference_path)
    a = np.asarray(arr, dtype=np.float32)
    # Enforce the zeros convention outside the footprint (format-compatible,
    # keeps every cell finite and inside [0, 1]).
    a = np.where(footprint, a, 0.0)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": grid["height"],
        "width": grid["width"],
        "crs": grid["crs"],
        "transform": grid["transform"],
        "compress": compress,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(a, 1)
        try:
            dst.set_band_description(1, "FAULT_PROBABILITY: 0=no_fault, 1=fault")
        except Exception:
            pass

    # Re-read back and verify the saved bytes (ground-truth the file, not RAM).
    report2 = validate_file(str(out_path), reference_path, footprint)
    # sha256 of saved bytes
    h = __import__("hashlib").sha256(out_path.read_bytes()).hexdigest()
    report2.sha256 = h
    return report2


def validate_file(
    path: str | Path,
    reference_path: str | Path,
    footprint: Optional[np.ndarray] = None,
) -> ValidationReport:
    """Validate an already-written GeoTIFF file."""
    if footprint is None:
        footprint = footprint_mask(reference_path)
    grid = reference_grid(reference_path)
    errors: list[str] = []
    with rasterio.open(path) as src:
        arr = src.read(1)
        crs = src.crs
        transform = src.transform
        shape = (src.height, src.width)
        dtype = src.dtypes[0]
        dtype_np = np.dtype(dtype)

    checks = {
        "single_band": True,  # read(1) of a single-band file
        "shape_match": shape == (grid["height"], grid["width"]),
        "dtype_float32": dtype_np == np.float32,
        "crs_match": str(crs) == str(grid["crs"]),
        "transform_match": str(transform) == str(grid["transform"]),
        "values_in_01": bool(np.all((arr >= 0.0) & (arr <= 1.0))),
        "no_nan": bool(~np.isnan(arr).any()),
    }
    if not checks["shape_match"]:
        errors.append(f"shape {shape} != reference {grid['height']}x{grid['width']}")
    if not checks["dtype_float32"]:
        errors.append(f"dtype {dtype} != float32")
    if not checks["crs_match"]:
        errors.append(f"CRS {crs} != {grid['crs']}")
    if not checks["transform_match"]:
        errors.append(f"transform {transform} != {grid['transform']}")
    if not checks["values_in_01"]:
        errors.append(f"values outside [0,1]: min={float(np.nanmin(arr))} max={float(np.nanmax(arr))}")
    if not checks["no_nan"]:
        errors.append(f"{int(np.isnan(arr).sum())} NaN cells in saved file")

    outside_frac = None
    if footprint is not None and arr.shape == footprint.shape:
        outside = arr[~footprint]
        outside_frac = float((outside == 0.0).mean()) if outside.size else None

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        checks=checks,
        shape=shape,
        dtype=str(dtype),
        crs=str(crs),
        transform=str(transform),
        value_min=float(np.nanmin(arr)),
        value_max=float(np.nanmax(arr)),
        nan_count=int(np.isnan(arr).sum()),
        outside_zero_fraction=outside_frac,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate/check a GEMS submission GeoTIFF")
    parser.add_argument("--check", required=True, help="GeoTIFF file to validate")
    parser.add_argument(
        "--reference",
        default=None,
        help="Reference raster defining CRS/shape/transform (default: a GEMSDOE32 "
        "registry TIF bundled under registry/, else canonical grid constants)",
    )
    parser.add_argument("--report", default=None, help="write JSON report to this path")
    args = parser.parse_args(argv)

    reference_path = args.reference
    if reference_path is None:
        # fall back to any registry TIF next to this repo, else canonical constants
        candidates = [
            Path("registry/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
            Path("/tmp/registry_ref/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
        ]
        reference_path = next((c for c in candidates if c.exists()), None)
        if reference_path is None:
            print("ERROR: no reference raster available; pass --reference", file=sys.stderr)
            return 2

    report = validate_file(args.check, reference_path, footprint_mask(reference_path))
    print(json.dumps(asdict(report), indent=2))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
