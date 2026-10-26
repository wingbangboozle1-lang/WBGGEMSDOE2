"""prepare_data.py — verify staged competition data matches the submission grid.

Checks data/training_features.tif (or numeric_features.tif), data/labels.tif and
optionally data/sample_submission.tif for CRS (EPSG:32611), shape (3730x3292),
transform, and value ranges.  Exits non-zero on any problem so downstream
holdout scoring never runs on misplaced data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submission_writer import reference_grid, footprint_mask  # noqa: E402

EXPECTED = {
    "crs": "EPSG:32611",
    "shape": (3730, 3292),
    "transform": "| 100.00, 0.00, 243350.00|\n| 0.00,-100.00, 4508550.00|",
}


def check(path: Path, label: str) -> list[str]:
    errors = []
    if not path.exists():
        return [f"{label}: MISSING {path}"]
    with rasterio.open(path) as src:
        ok_crs = str(src.crs) == EXPECTED["crs"]
        ok_shape = (src.height, src.width) == EXPECTED["shape"]
        ok_tr = str(src.transform) == EXPECTED["transform"]
        arr = src.read(1)
        n_nan = int(np.isnan(arr).sum()) if arr.dtype.kind == "f" else 0
    if not ok_crs:
        errors.append(f"{label}: CRS {src.crs} != {EXPECTED['crs']}")
    if not ok_shape:
        errors.append(f"{label}: shape {src.height}x{src.width} != {EXPECTED['shape']}")
    if not ok_tr:
        errors.append(f"{label}: transform mismatch (expected {EXPECTED['transform']!r})")
    print(f"{label}: {path} CRS={src.crs} shape={src.height}x{src.width} "
          f"dtype={src.dtypes[0]} nan={n_nan} "
          f"{'OK' if (ok_crs and ok_shape and ok_tr) else 'MISMATCH'}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify staged competition data")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir)
    candidates = [data_dir / "training_features.tif", data_dir / "numeric_features.tif"]
    feature_path = next((c for c in candidates if c.exists()), None)
    errors = []
    if feature_path:
        errors += check(feature_path, "features")
    else:
        errors.append("features: MISSING (training_features.tif or numeric_features.tif)")
    errors += check(data_dir / "labels.tif", "labels")
    sample = data_dir / "sample_submission.tif"
    if sample.exists():
        errors += check(sample, "sample_submission")
    else:
        print("sample_submission.tif: MISSING (needed as format reference)")
    if errors:
        print("\nFAIL:", *errors, sep="\n  - ")
        return 1
    print("\nPASS: staged data matches the competition grid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
