#!/usr/bin/env python3
"""Fail-closed local GeoTIFF format check for DOE GEMS submissions.

This checks only the organizer's file-format/grid constraints against a local
reference raster. A PASS is not a holdout result, uniqueness result, or upload
approval. Registry and scientific gates are intentionally not inferred here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

VALIDATOR_VERSION = "wbg-gems-tif-format-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(candidate_path: Path, reference_path: Path) -> dict[str, Any]:
    """Validate candidate bytes against a reference grid and return a receipt."""
    checks: dict[str, Any] = {}
    errors: list[str] = []

    with rasterio.open(reference_path) as reference, rasterio.open(candidate_path) as candidate:
        reference_footprint = reference.dataset_mask() != 0
        values = candidate.read(1, masked=False) if candidate.count >= 1 else np.empty((0, 0))

        checks["readable"] = True
        checks["geotiff"] = candidate.driver == "GTiff" and candidate_path.suffix.lower() in {".tif", ".tiff"}
        checks["single_band"] = candidate.count == 1
        checks["float32"] = candidate.count == 1 and candidate.dtypes[0] == "float32"
        checks["crs_match"] = reference.crs is not None and candidate.crs == reference.crs
        checks["shape_match"] = (candidate.height, candidate.width) == (reference.height, reference.width)
        checks["transform_match"] = tuple(candidate.transform) == tuple(reference.transform)
        same_shape = values.shape == reference_footprint.shape
        checks["reference_footprint_available"] = bool(reference_footprint.any())
        checks["reference_footprint_shape_match"] = same_shape

        if same_shape and values.size:
            inside_values = values[reference_footprint]
            all_finite = bool(np.isfinite(values).all())
            inside_finite = bool(np.isfinite(inside_values).all())
            all_in_range = bool(all_finite and np.all((values >= 0.0) & (values <= 1.0)))
            inside_in_range = bool(inside_finite and np.all((inside_values >= 0.0) & (inside_values <= 1.0)))
            checks["finite_all_pixels"] = all_finite
            checks["finite_inside_footprint"] = inside_finite
            checks["range_0_1_all_pixels"] = all_in_range
            checks["range_0_1_inside_footprint"] = inside_in_range
            checks["array_shape"] = list(values.shape)
            checks["footprint_pixels"] = int(reference_footprint.sum())
            if all_finite:
                checks["minimum"] = float(values.min())
                checks["maximum"] = float(values.max())
            else:
                checks["minimum"] = None
                checks["maximum"] = None
        else:
            checks["finite_all_pixels"] = False
            checks["finite_inside_footprint"] = False
            checks["range_0_1_all_pixels"] = False
            checks["range_0_1_inside_footprint"] = False
            checks["array_shape"] = list(values.shape)
            checks["footprint_pixels"] = int(reference_footprint.sum())
            checks["minimum"] = None
            checks["maximum"] = None

        if checks["geotiff"] is False:
            errors.append("candidate must be a GeoTIFF with a .tif or .tiff extension")
        if checks["single_band"] is False:
            errors.append("candidate must contain exactly one band")
        if checks["float32"] is False:
            errors.append("candidate band must be 32-bit float")
        if checks["crs_match"] is False:
            errors.append("candidate CRS does not match reference CRS")
        if checks["shape_match"] is False:
            errors.append("candidate raster shape does not match reference shape")
        if checks["transform_match"] is False:
            errors.append("candidate geotransform does not exactly match reference geotransform")
        if checks["reference_footprint_available"] is False:
            errors.append("reference raster has no valid footprint")
        if checks["reference_footprint_shape_match"] is False:
            errors.append("candidate array shape does not match reference footprint")
        if checks["finite_all_pixels"] is False:
            errors.append("candidate contains NaN or infinity; all cells are checked to guard against range-validator errors")
        if checks["finite_inside_footprint"] is False:
            errors.append("candidate contains NaN or infinity inside the reference footprint")
        if checks["range_0_1_all_pixels"] is False:
            errors.append("candidate values are not all within [0, 1]")

    passed = not errors
    return {
        "validator": VALIDATOR_VERSION,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate_path.name,
        "candidate_sha256": sha256_file(candidate_path),
        "reference": reference_path.name,
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "errors": errors,
        "submission_authorized": False,
        "authorization_note": "Format validation alone cannot establish holdout performance, leakage safety, registry uniqueness, organizer acceptance, or selector approval.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path, help="candidate single-band GeoTIFF")
    parser.add_argument("--reference", required=True, type=Path, help="official sample/reference GeoTIFF defining the required grid")
    parser.add_argument("--json-out", type=Path, help="optional path for a machine-readable receipt")
    args = parser.parse_args(argv)

    for path in (args.candidate, args.reference):
        if not path.is_file():
            parser.error(f"file does not exist: {path}")

    try:
        receipt = validate(args.candidate, args.reference)
    except Exception as exc:  # readable fail-closed diagnostic for GDAL/raster errors
        receipt = {
            "validator": VALIDATOR_VERSION,
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "candidate": args.candidate.name,
            "reference": args.reference.name,
            "status": "FAIL",
            "checks": {"readable": False},
            "errors": [f"could not read/validate rasters: {type(exc).__name__}: {exc}"],
            "submission_authorized": False,
            "authorization_note": "Format validation alone cannot establish holdout performance, leakage safety, registry uniqueness, organizer acceptance, or selector approval.",
        }

    rendered = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
