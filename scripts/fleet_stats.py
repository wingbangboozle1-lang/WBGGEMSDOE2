#!/usr/bin/env python3
"""Measure fleet raster geometry and compute the catalogue-proxy DTI.

Every number produced here is labelled:

* ``CATALOGUE-PROXY-DTI`` — the official DTI formula applied with
  ``gt = existing_faults.tif`` (the *visible* catalogue). The competition's
  scoring labels are expert-identified faults that are NOT in that catalogue,
  so this is an in-sample proxy, NOT a competition score and NOT a holdout.
* geometry statistics are direct measurements of the raster bytes.

Inputs (verified hashes in ``data_public/official/SOURCES.json``):
  data_public/official/existing_faults.tif  (byte-identical to labels.tif)
  data_public/official/sample_submission.tif (grid template / footprint)

Output: data_public/fleet_features.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbg2.metric import RADIUS_PX, weighted_components  # noqa: E402

OFFICIAL = ROOT / "data_public" / "official"
RASTERS = ROOT / "data_public" / "rasters"


def load_official():
    with rasterio.open(OFFICIAL / "existing_faults.tif") as src:
        cat = src.read(1)
        cat_meta = {
            "shape": list(src.shape), "crs": str(src.crs), "transform": list(src.transform)[:6],
            "dtype": src.dtypes[0], "nodata": src.nodata,
        }
    with rasterio.open(OFFICIAL / "sample_submission.tif") as src:
        sub = src.read(1)
        sub_meta = {
            "shape": list(src.shape), "crs": str(src.crs), "transform": list(src.transform)[:6],
            "dtype": src.dtypes[0], "nodata": src.nodata, "count": src.count,
        }
        finite = np.isfinite(sub) if sub.dtype.kind == "f" else np.ones(sub.shape, bool)
        footprint = finite if src.nodata is None else (finite & (sub != src.nodata))
    return cat, cat_meta, sub_meta, footprint


def tp_at_truth(pred: np.ndarray, truth: np.ndarray, radius: int = RADIUS_PX) -> float:
    """TP_w = sum over truth pixels of max_{x within R} pred(x) k(d).

    Evaluated only at truth pixels, which is exact for TP_w and cheap because
    the catalogue is sparse.
    """
    rows, cols = np.nonzero(truth)
    if rows.size == 0:
        return 0.0
    ap = np.pad(pred.astype(np.float64), radius, constant_values=0.0)
    best = np.zeros(rows.size, dtype=np.float64)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = float(np.hypot(dy, dx))
            w = 1.0 - d / radius
            if w <= 0.0:
                continue
            vals = ap[rows + dy + radius, cols + dx + radius] * w
            np.maximum(best, vals, out=best)
    return float(best.sum())


def geometry(pred: np.ndarray, footprint: np.ndarray, cat: np.ndarray, buf: np.ndarray) -> dict:
    support = pred > 0.0
    inside = support & footprint
    n_support = int(inside.sum())
    mass = float(np.where(inside, pred, 0.0).sum())

    # distance to the visible catalogue, in px (100 m)
    dist_cat = ndi.distance_transform_edt(cat == 0)
    d_at_support = dist_cat[inside] if n_support else np.array([np.inf])

    # connected components of the support (8-connectivity)
    _, ncomp = ndi.label(inside, structure=np.ones((3, 3), bool))

    # occupied 1 km (10 px) blocks: a spatial-breadth measure
    blocks = buf & footprint
    occupied_blocks = int((blocks.sum()))

    return {
        "support_px": n_support,
        "mass": mass,
        "binary_fraction": float((pred[inside] >= 0.999).mean()) if n_support else 0.0,
        "mean_value_on_support": float(pred[inside].mean()) if n_support else 0.0,
        "footprint_fill_fraction": n_support / float(footprint.sum()),
        "components_8conn": int(ncomp),
        "occupied_1km_blocks": occupied_blocks,
        "frac_within_1px_catalogue": float((d_at_support <= 1).mean()) if n_support else 0.0,
        "frac_within_2px_catalogue": float((d_at_support <= 2).mean()) if n_support else 0.0,
        "frac_within_3px_catalogue": float((d_at_support <= 3).mean()) if n_support else 0.0,
        "median_px_to_catalogue": float(np.median(d_at_support)) if n_support else 0.0,
        "mean_px_to_catalogue": float(np.mean(d_at_support)) if n_support else 0.0,
    }


def main() -> int:
    cat, cat_meta, sub_meta, footprint = load_official()
    truth = cat > 0
    print(f"catalogue positives: {int(truth.sum())}  footprint: {int(footprint.sum())}")

    manifest = json.loads((ROOT / "data_public" / "raster_fetch_manifest.json").read_text())
    # 1 km block occupancy helper grid
    buf = np.zeros(cat.shape, dtype=bool)
    buf[::10, ::10] = True

    out = []
    for row in manifest:
        path = ROOT / row["local"]
        try:
            with rasterio.open(path) as src:
                arr = src.read(1)
                meta_ok = (
                    list(src.shape) == cat_meta["shape"]
                    and str(src.crs) == cat_meta["crs"]
                    and [float(v) for v in list(src.transform)[:6]] == [float(v) for v in cat_meta["transform"]]
                )
                dtype = src.dtypes[0]
                count = src.count
        except Exception as exc:  # pragma: no cover
            print("SKIP", path.name, exc)
            continue
        pred = np.nan_to_num(arr.astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0)
        pred = np.clip(pred, 0.0, 1.0)
        geo = geometry(pred, footprint, cat, buf)
        tp = tp_at_truth(pred, truth)
        n_truth = int(truth.sum())
        support = (pred > 0) & footprint
        dist = ndi.distance_transform_edt(~truth)
        k = np.clip(1.0 - np.minimum(dist, RADIUS_PX) / RADIUS_PX, 0.0, 1.0)
        fp = float((pred[support] * (1.0 - k[support])).sum()) if support.any() else 0.0
        fn = n_truth - tp
        denom = tp + 0.2 * fp + 0.8 * fn
        proxy = float(tp / denom) if denom > 0 else 0.0
        rec = dict(row)
        rec.update(geo)
        rec.update({
            "grid_matches_official": bool(meta_ok), "dtype": dtype, "bands": count,
            "catalogue_proxy_dti": proxy,
            "catalogue_proxy_tp": tp, "catalogue_proxy_fp": fp,
            "metric_label": "CATALOGUE-PROXY-DTI (in-sample; gt=visible catalogue; NOT a competition score)",
        })
        out.append(rec)
        print(f"{row['site']:11s} score={row['reported_score']:.4f} sup={geo['support_px']:6d} "
              f"proxy={proxy:.4f} d3={geo['frac_within_3px_catalogue']:.2f} medpx={geo['median_px_to_catalogue']:.1f}",
              flush=True)
    (ROOT / "data_public" / "fleet_features.json").write_text(json.dumps({
        "evidence_class": "MEASURED. Scores are USER-REPORTED; no organizer receipt exists for them.",
        "official": {"catalogue_meta": cat_meta, "sample_submission_meta": sub_meta,
                     "catalogue_positives": int(truth.sum()),
                     "footprint_cells": int(footprint.sum())},
        "rows": out,
    }, indent=1))
    print(f"\nwrote {len(out)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
