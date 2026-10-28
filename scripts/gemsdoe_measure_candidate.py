#!/usr/bin/env python3
"""Measure the published candidate once, with every definition written down.

Two reach numbers circulate in this repository and they are not interchangeable:

* ``reach_in_footprint``  share of the 5,167,373 in-footprint cells whose centre lies
  within 300 m of a predicted cell -- the honest denominator for "how much of the
  scored map is claimed";
* ``reach_all_cells``     the same count divided by all 12,280,360 raster cells,
  including the NaN margin outside the footprint (dots near the boundary cover some of
  it).  This is the number the earlier run card printed as 0.1724.

The structural score curve uses the inverted truth size from
``data_public/gemsdoe_metric_model.json`` so that the estimate is reproducible.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
PUB = ROOT / "data_public"
NAME = "gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2"
R = 3.0


def main() -> int:
    tif = ROOT / "submissions" / f"{NAME}.tif"
    zero = ROOT / "submissions" / f"{NAME}-zerooutside.tif"
    fp = np.load(WORK / "footprint.npy").astype(bool)
    cat = np.load(WORK / "catalogue.npy").astype(bool)
    with rasterio.open(tif) as d:
        a = d.read(1)
        meta = {"height": d.height, "width": d.width, "count": d.count,
                "dtypes": list(d.dtypes), "crs": str(d.crs),
                "transform": [d.transform.a, d.transform.b, d.transform.c,
                              d.transform.d, d.transform.e, d.transform.f],
                "nodata": d.nodata}
    finite = np.isfinite(a)
    pos = finite & (a > 0)
    dist = ndi.distance_transform_edt(~pos)
    cov = np.maximum(1.0 - dist / R, 0.0)
    within = dist <= R                      # "within 300 m", inclusive
    dcat = ndi.distance_transform_edt(~cat)
    model = json.loads((PUB / "gemsdoe_metric_model.json").read_text())
    n_truth = model["n_truth_pixels_solved"]
    mass = float(pos.sum())

    curve = {}
    for f in (0.15, 0.20, 0.25, 0.30, 0.35, 0.409, 0.45, 0.50):
        t = f * n_truth
        curve[f"{f:.3f}"] = t / (t + 0.2 * mass + 0.8 * (n_truth - t))

    out = {
        "schema": "wbggems.candidate-measurements.v1",
        "file": f"submissions/{NAME}.tif",
        "bytes": tif.stat().st_size,
        "sha256": hashlib.sha256(tif.read_bytes()).hexdigest(),
        "raster": meta,
        "cells": int(pos.sum()),
        "mass": mass,
        "binary": bool(np.all(np.isin(a[pos], [0.0, 1.0]))),
        "values_in_0_1_inside_footprint": bool(np.all((a[fp] >= 0) & (a[fp] <= 1))),
        "nan_inside_footprint": int(np.isnan(a[fp]).sum()),
        "reach_in_footprint": float(within[fp].mean()),
        "reach_all_cells": float(within.mean()),
        "kernel_weighted_coverage": float(cov[fp].mean()),
        "reach_definition": ("reach_in_footprint = share of the 5,167,373 in-footprint cells "
                            "whose centre is within 300 m (inclusive) of a predicted cell -- "
                            "this is what the run card's 0.1724 means; "
                            "kernel_weighted_coverage = mean organizer kernel weight over the "
                            "same cells, i.e. the share of a uniformly placed truth pixel that "
                            "would be claimed, which is the quantity DTI actually pays for"),
        "frac_dots_within_px_of_catalogue": {
            "1": float((dcat[pos] <= 1).mean()),
            "2": float((dcat[pos] <= 2).mean()),
            "3": float((dcat[pos] <= 3).mean()),
        },
        "median_px_to_catalogue": float(np.median(dcat[pos])),
        "p90_px_to_catalogue": float(np.percentile(dcat[pos], 90)),
        "structural_score_curve": {"n_truth": n_truth, "mass": mass, "by_coverage": curve},
        "zero_outside_twin": {
            "bytes": zero.stat().st_size,
            "sha256": hashlib.sha256(zero.read_bytes()).hexdigest(),
            "identical_inside_footprint": bool(
                np.array_equal(np.nan_to_num(_read(zero), nan=0.0), np.nan_to_num(a, nan=0.0))),
        },
        "evidence_class": "MEASURED (geometry, format) + STRUCTURAL-ESTIMATE (score curve)",
    }
    def clean(v):
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [clean(x) for x in v]
        if isinstance(v, float) and not np.isfinite(v):
            return None
        return v

    (PUB / "candidate_measurements.json").write_text(json.dumps(clean(out), indent=1))
    print(json.dumps({k: out[k] for k in ("cells", "mass", "reach_in_footprint",
                                         "reach_all_cells", "median_px_to_catalogue")}, indent=1))
    print(json.dumps(curve, indent=1))
    return 0


def _read(path: Path):
    with rasterio.open(path) as d:
        return d.read(1).astype("float32")


if __name__ == "__main__":
    raise SystemExit(main())
