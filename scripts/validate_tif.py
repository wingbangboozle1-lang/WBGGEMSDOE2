#!/usr/bin/env python3
"""Inspect a TIFF against a local reference; never authorizes an upload."""
import argparse
import json
import sys
import rasterio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wbggems.validate import inspect_tif


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", type=Path)
    p.add_argument("--reference", type=Path, default=Path("data/reference_grid_mirror.tif"))
    p.add_argument("--strict-all-finite", action="store_true")
    args = p.parse_args()
    try:
        result = inspect_tif(args.candidate, args.reference, strict_all_finite=args.strict_all_finite)
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(json.dumps({"format_valid_against_reference": False, "error": str(exc),
                          "submission_approval": False}, indent=2))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["format_valid_against_reference"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
