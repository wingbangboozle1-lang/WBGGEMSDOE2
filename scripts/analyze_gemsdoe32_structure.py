#!/usr/bin/env python3
"""Measure the structure of the public GEMSDOE32 0.2778 raster against the mapped-fault catalogue.

Read-only diagnostic. It does NOT reproduce the hidden test score, does not use
hidden labels, and never authorises a submission. Inputs:
  * .cache/priority-audit/GEMSDOE32.tif  (fetched from buffedlizard55-lab/GEMSDOE32 @ 45ee207185f72804497f7a7a392ad2c43e168f02)
  * data/official/existing_faults.tif     (owner-mirror; -1 nodata, 0 absent, 1 mapped fault)
  * data/official/sample_submission.tif   (footprint = finite and read-mask > 0)
Output: evidence/gemsdoe32_structure_20261028.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / ".cache/priority-audit/GEMSDOE32.tif"
SUBMISSION_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
FAULTS = ROOT / "data/official/existing_faults.tif"
SAMPLE = ROOT / "data/official/sample_submission.tif"
OUT = ROOT / "evidence/gemsdoe32_structure_20261028.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if not SUBMISSION.is_file():
        raise SystemExit("STOP: fetch GEMSDOE32 raster first (see research note)")
    digest = sha256(SUBMISSION)
    if digest != SUBMISSION_SHA256:
        raise SystemExit(f"STOP: hash mismatch {digest}")
    with rasterio.open(SUBMISSION) as ds:
        p = ds.read(1).astype(np.float64)
        crs, shape, transform = str(ds.crs), ds.shape, ds.transform
    with rasterio.open(FAULTS) as ds:
        faults = ds.read(1)
    with rasterio.open(SAMPLE) as ds:
        footprint = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)

    pos = p > 0
    mapped = faults == 1
    dist_m = ndi.distance_transform_edt(~mapped) * 100.0
    d = dist_m[pos]
    # Cumulative counts with explicit strict/inclusive ends; k(R)=0 at R, so d < 300 m is the credit-bearing set.
    thresholds = [100, 200, 300, 500, 1000, 2000, 5000]
    cumulative_lt = {f"d_lt_{t}m": int((d < t).sum()) for t in thresholds}
    exactly_300 = int(np.isclose(d, 300.0).sum())
    ys, xs = np.nonzero(pos)
    nn = cKDTree(np.c_[xs, ys]).query(np.c_[xs, ys], k=2)[0][:, 1]
    result = {
        "schema": "wbggems.gemsdoe32-structure.v1",
        "evidence_class": "PUBLIC-RASTER STRUCTURE MEASUREMENT; NOT HOLDOUT-DTI, NOT AN ORGANIZER RECEIPT",
        "source": "https://github.com/buffedlizard55-lab/GEMSDOE32/blob/45ee207185f72804497f7a7a392ad2c43e168f02/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "sha256": digest,
        "crs": crs,
        "shape": list(shape),
        "transform": list(transform)[:6],
        "nan_pixels": int(np.isnan(p).sum()),
        "unique_values": [float(v) for v in np.unique(p)],
        "positive_pixels": int(pos.sum()),
        "footprint_pixels": int(footprint.sum()),
        "positives_outside_footprint": int((pos & ~footprint).sum()),
        "mapped_fault_pixels": int(mapped.sum()),
        "positives_on_mapped_faults": int((pos & mapped).sum()),
        "positive_distance_to_mapped_fault_m_cumulative_strict": cumulative_lt,
        "positives_exactly_300m": exactly_300,
        "positives_beyond_5000m": int((d >= 5000).sum()),
        "fraction_positives_with_kernel_credit_d_lt_300m": float((d < 300).mean()),
        "median_positive_distance_to_mapped_fault_m": float(np.median(d)),
        "nearest_neighbour_spacing_cells_p5_p50_p95": [float(x) for x in np.percentile(nn, [5, 50, 95])],
        "nearest_neighbour_min_cells": float(nn.min()),
        "scoring_note": "The official DTI page (drivendata competition 306, page 967) does not mention masking mapped faults; the pinned template docstring cites an organiser thread for that masking, which is NOT verified here. Hidden test labels are unavailable, so the raster score is not recomputed.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
