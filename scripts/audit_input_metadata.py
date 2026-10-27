#!/usr/bin/env python3
"""Measure mirror footprint and band-6 NoData; no training or predictions.

The public mirror is not authenticated as the current DrivenData download.
The official page shows a radiometric image but does not, by itself, identify
band 6 in these particular bytes. Positivity alone cannot establish band identity.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.validate import sha256

PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "existing_faults.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
}


def summarize(feature: Path, sample: Path, faults: Path) -> dict:
    for file in (feature, sample, faults):
        expected = PINS.get(file.name)
        if expected is None or not file.is_file() or sha256(file) != expected:
            raise ValueError(f"Missing or mismatched pinned mirror: {file}")
    with rasterio.open(sample) as ds:
        values = ds.read(1)
        footprint = np.isfinite(values) & (ds.read_masks(1) > 0)
        sample_positives = footprint & (values > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    with rasterio.open(faults) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError("Fault mirror does not match sample grid")
        fault_values = ds.read(1)
        catalogue = footprint & (ds.read_masks(1) > 0) & (fault_values == 1)
    with rasterio.open(feature) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 19:
            raise ValueError("19-band feature mirror does not match sample grid")
        raw = ds.read(6)
        valid_mask = ds.read_masks(6) > 0
        valid = footprint & valid_mask & np.isfinite(raw)
        numbers = raw[valid]
        if not numbers.size:
            raise ValueError("Band 6 has no valid values inside the reference footprint")
        quantiles = np.quantile(numbers, [.01, .5, .99])
        result = {
            "feature_sha256": PINS[feature.name],
            "feature_bytes": feature.stat().st_size,
            "feature_bands": ds.count,
            "band_6_description_from_mirror": ds.descriptions[5],
            "band_6_nodata": float(ds.nodata) if ds.nodata is not None else None,
            "reference_footprint_cells": int(footprint.sum()),
            "band_6_masked_inside_reference_footprint": int((footprint & ~valid_mask).sum()),
            "band_6_raw_negative_inside_reference_footprint": int((footprint & (raw < 0)).sum()),
            "band_6_valid_negative_inside_reference_footprint": int((valid & (raw < 0)).sum()),
            "band_6_valid_cells_inside_reference_footprint": int(valid.sum()),
            "band_6_valid_min": float(numbers.min()),
            "band_6_valid_max": float(numbers.max()),
            "band_6_valid_q01_median_q99": [float(x) for x in quantiles],
        }
    result.update(
        sample_sha256=PINS[sample.name],
        catalogue_sha256=PINS[faults.name],
        sample_positive_pixels=int(sample_positives.sum()),
        catalogue_positive_pixels=int(catalogue.sum()),
        sample_positives_equal_catalogue_positives=bool(np.array_equal(sample_positives, catalogue)),
        evidence_class="LOCAL-OWNER-MIRROR-MEASUREMENT",
        authenticated_organizer_copy=False,
        band_6_identity="UNRESOLVED: mirrored metadata says tilt/curvature; valid values and the official radiometric illustration do not independently identify this band",
        sample_warning="Official problem page describes its sample as predicting fault absence; this owner-mirror sample's positive mask equals the mirrored catalogue. Identity with current organizer sample is not verified.",
        experiments_run=0,
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data/official")
    p.add_argument("--output", type=Path, default=ROOT / "evidence/input_metadata_20261027.json")
    args = p.parse_args()
    try:
        report = summarize(args.data_dir / "training_features.tif", args.data_dir / "sample_submission.tif",
                           args.data_dir / "existing_faults.tif")
        report["generated_utc"] = datetime.now(timezone.utc).isoformat()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(args.output.suffix + ".partial")
        tmp.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        tmp.replace(args.output)
        print(f"Wrote {args.output}; band 6 identity remains unresolved; no experiment was run.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Metadata audit stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
