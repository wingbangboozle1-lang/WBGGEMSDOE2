#!/usr/bin/env python3
"""Byte-check with the pinned shared gate AND an independent mask check; never authorize a slot.

This cannot establish novelty, a holdout win, or portal acceptance. All-finite
outside-footprint encoding is a local range precaution and may not match the
literal public specification's null/NaN wording; organizer acceptance is unknown.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from prepare_data import ROOT, TEMPLATE, digest, restore_template

SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"


def run(path: Path, sample: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"No such raster: {path}")
    if not sample.is_file() or digest(sample) != SAMPLE_SHA:
        raise ValueError("The owner-mirrored sample is absent or hash-mismatched")
    # Verify each cached upstream file before importing; no evaluator/writer fork.
    restore_template(False)
    sys.path.insert(0, str(TEMPLATE / "src"))
    from gems57.gates import format_report
    with rasterio.open(sample) as ds:
        footprint = np.isfinite(ds.read(1))
    result = format_report(path, sample, footprint=footprint)
    # The pinned shared version reports mask presence but can accept finite
    # NoData=0 pixels within the footprint. Until that is fixed upstream, an
    # additional independent read-back is a STOP only, never a private fork.
    sys.path.insert(0, str(ROOT / "src"))
    from wbggems.validate import inspect_tif
    supplemental = inspect_tif(path, sample, strict_all_finite=True)
    shared_ok = bool(result["ok"])
    supplemental_ok = bool(supplemental["format_valid_against_reference"])
    result["shared_format_ok"] = shared_ok
    result["supplemental_mask_and_format_ok"] = supplemental_ok
    result["masked_inside_footprint"] = supplemental.get("masked_inside")
    result["supplemental_failures"] = supplemental["failures"]
    result["ok"] = shared_ok and supplemental_ok
    result.update(
        evidence_class="LOCAL-FORMAT-MEASUREMENT",
        reference_provenance="Hash-pinned third-party mirror; not organizer authenticated",
        sample_sha256=SAMPLE_SHA,
        no_nan_inside_footprint=None,
        organizer_acceptance="unknown",
        official_outside_footprint_nodata_compliance="not established by all-finite check",
        scientific_holdout="not checked by this command",
        registry_surface_and_final="not checked by this command",
        ok_to_submit=False,
        verdict="research-only; local format is not promotion or slot selection",
    )
    with rasterio.open(path) as ds:
        a = ds.read(1)
    if a.shape == footprint.shape:
        values = a[footprint]
        result["no_nan_inside_footprint"] = bool(np.isfinite(values).all())
        result["inside_values_in_0_1"] = bool(np.isfinite(values).all() and
                                               (values >= 0).all() and (values <= 1).all())
    else:
        result["inside_values_in_0_1"] = False
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raster", type=Path)
    p.add_argument("--sample", type=Path, default=ROOT / "data/official/sample_submission.tif")
    p.add_argument("--output", type=Path, help="optional JSON receipt (never overwrites an existing file)")
    args = p.parse_args()
    try:
        report = run(args.raster, args.sample)
        text = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
        print(text, end="")
        return 0 if report["ok"] else 1
    except (OSError, ValueError, RuntimeError) as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
