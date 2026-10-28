"""Authoritative grid/inputs for the GEMS Prize submission lane.

Everything here is measured from the organizer rasters (mirrored through the
hash-pinned transport in ``data/raw``); nothing is assumed.

Pinned identities (SHA-256), verified at load time by ``scripts/gemsdoe_prepare.py``:

* ``training_features.tif``  4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
* ``labels.tif``             7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093
* ``sample_submission.tif``  2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc

Grid: EPSG:32611, 100 m, 3730 x 3292, origin (243350, 4508550) -> bounds
(243350, 4135550, 572550, 4508550).  Valid (in-footprint) cells: 5,167,373.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
WORK = ROOT / "data" / "work"

PINS = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "labels.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}

CRS = "EPSG:32611"
SHAPE = (3730, 3292)
TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
PIXEL_M = 100.0
RADIUS_PX = 3.0
ALPHA = 0.2
BETA = 0.8

NODATA = -3.4028234663852886e38


def sha256(path, chunk=1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def verify_pins(strict: bool = True) -> dict:
    out = {}
    for name, want in PINS.items():
        p = RAW / name
        if not p.exists():
            out[name] = {"present": False, "ok": False}
            continue
        got = sha256(p)
        out[name] = {"present": True, "sha256": got, "expected": want, "ok": got == want}
    if strict and not all(v["ok"] for v in out.values()):
        bad = {k: v for k, v in out.items() if not v["ok"]}
        raise RuntimeError(f"pinned inputs missing or altered: {bad}")
    return out


def read_labels() -> np.ndarray:
    """int8 catalogue: 1 = mapped fault, 0 = in-footprint background, -1 = outside."""
    with rasterio.open(RAW / "labels.tif") as ds:
        return ds.read(1)


def footprint() -> np.ndarray:
    """Boolean mask of cells the organizer scores (finite in sample_submission)."""
    with rasterio.open(RAW / "sample_submission.tif") as ds:
        a = ds.read(1)
    return np.isfinite(a)


def catalogue_mask() -> np.ndarray:
    return read_labels() == 1


def feature_band_names() -> list[str]:
    with rasterio.open(RAW / "training_features.tif") as ds:
        names = [ds.tags(i).get("band_name", f"b{i}") for i in range(1, ds.count + 1)]
    return names


def read_band(index: int) -> np.ndarray:
    """1-based band read, sentinel -> NaN, float32."""
    with rasterio.open(RAW / "training_features.tif") as ds:
        a = ds.read(index).astype("float32")
    a[a <= NODATA / 2] = np.nan
    return a


def write_submission(path, values: np.ndarray, outside="nan") -> dict:
    """Write a single-band float32 GeoTIFF on the organizer grid.

    ``values`` must already be 0..1 inside the footprint.  ``outside`` chooses the
    encoding for out-of-footprint cells: ``"nan"`` (exactly what the organizer's
    own sample raster uses) or ``"zero"``.
    """
    values = np.asarray(values, dtype="float32")
    if values.shape != SHAPE:
        raise ValueError(f"shape {values.shape} != organizer grid {SHAPE}")
    fp = footprint()
    arr = np.array(values, dtype="float32", copy=True)
    if outside == "nan":
        arr[~fp] = np.nan
    elif outside == "zero":
        arr[~fp] = 0.0
    else:
        raise ValueError("outside must be 'nan' or 'zero'")
    inside = arr[fp]
    if not np.isfinite(inside).all():
        raise ValueError("non-finite value inside the footprint")
    if inside.min() < 0.0 or inside.max() > 1.0:
        raise ValueError("value outside [0,1] inside the footprint")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", height=SHAPE[0], width=SHAPE[1], count=1,
                   dtype="float32", crs=CRS, transform=rasterio.Affine(*TRANSFORM),
                   nodata=float("nan") if outside == "nan" else None,
                   compress="deflate", predictor=2, tiled=True,
                   blockxsize=256, blockysize=256)
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(arr, 1)
        ds.set_band_description(1, "GEMS fault probability")
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def summary() -> dict:
    lab = read_labels()
    fp = footprint()
    cat = lab == 1
    return {
        "grid": {"shape": list(SHAPE), "crs": CRS, "transform": list(TRANSFORM)},
        "footprint_cells": int(fp.sum()),
        "outside_footprint_cells": int((~fp).sum()),
        "catalogue_positive_cells": int(cat.sum()),
        "catalogue_frac_of_footprint": float(cat.sum() / fp.sum()),
        "label_sentinel_cells": int((lab == -1).sum()),
        "pins": verify_pins(strict=False),
    }


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True)


def ensure_work() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    return WORK


if __name__ == "__main__":  # pragma: no cover
    print(dumps(summary()))
