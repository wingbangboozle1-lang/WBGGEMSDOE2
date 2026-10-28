"""Write and validate the WBG4 submission raster.

Rules enforced here, straight from the organizer's submission format
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):

* one band, ``float32``, EPSG:32611, 100 m, shape (3730, 3292),
* geotransform identical to the official sample submission,
* values in [0, 1] for every cell, no NaN anywhere,
* outside the organizer footprint the file is filled with 0.0 (the variant the
  organizer portal accepted for the reported 0.2778 submission), never NaN.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parents[1]
HEIGHT, WIDTH = 3730, 3292
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
CRS = "EPSG:32611"


def write_submission(values: np.ndarray, dest: Path, dtype: str = "float32") -> Path:
    values = np.asarray(values)
    if values.shape != (HEIGHT, WIDTH):
        raise ValueError(f"refusing to write {values.shape}; official grid is {(HEIGHT, WIDTH)}")
    if not np.isfinite(values).all():
        raise ValueError("refusing to write non-finite values")
    if values.min() < 0.0 or values.max() > 1.0:
        raise ValueError("refusing to write values outside [0, 1]")
    dest.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": HEIGHT, "width": WIDTH, "count": 1,
        "dtype": dtype, "crs": CRS, "transform": TRANSFORM,
        "nodata": None, "compress": "deflate", "tiled": False,
    }
    tmp = dest.with_suffix(dest.suffix + ".part")
    with rasterio.open(tmp, "w", **profile) as ds:
        ds.write(values.astype(dtype), 1)
    tmp.rename(dest)
    return dest


def package_zip(tif: Path) -> Path:
    zpath = tif.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tif, arcname=tif.name)
    return zpath


def validate(tif: Path, footprint: np.ndarray, reference: Path | None = None) -> dict:
    """Read the written bytes back and check every format rule independently."""
    out: dict = {"path": str(tif), "ok": True, "checks": {}, "notes": []}
    with rasterio.open(tif) as ds:
        arr = ds.read(1)
        out["checks"]["single_band"] = ds.count == 1
        out["checks"]["float32"] = ds.dtypes[0] == "float32"
        out["checks"]["shape"] = ds.shape == (HEIGHT, WIDTH)
        out["checks"]["epsg32611"] = ds.crs.to_epsg() == 32611
        out["checks"]["transform_matches"] = tuple(ds.transform)[:6] == tuple(TRANSFORM)[:6]
        out["checks"]["no_nan"] = bool(np.isfinite(arr).all())
        out["checks"]["values_in_0_1"] = bool(arr.min() >= 0.0 and arr.max() <= 1.0)
        out["checks"]["zero_outside_footprint"] = bool(np.all(arr[~footprint] == 0.0))
        out["checks"]["positive_inside_footprint"] = int(((arr > 0) & footprint).sum())
        out["positive_pixels"] = int((arr > 0).sum())
        out["positive_inside_footprint"] = int(((arr > 0) & footprint).sum())
        out["unique_values"] = [round(float(v), 4) for v in np.unique(arr)[:6]]
        out["dtype"] = ds.dtypes[0]
        out["crs"] = str(ds.crs)
        out["transform"] = list(tuple(ds.transform)[:6])
        out["shape"] = list(ds.shape)
        if reference is not None:
            with rasterio.open(reference) as ref:
                out["checks"]["grid_matches_reference"] = (
                    ref.shape == ds.shape and tuple(ref.transform)[:6] == tuple(ds.transform)[:6]
                    and ref.crs.to_epsg() == ds.crs.to_epsg())
        if out["positive_inside_footprint"] == 0:
            out["notes"].append("no positive cells inside the footprint: prediction is empty")
    out["ok"] = all(out["checks"].values())
    return out


def sha256_of(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def summarise(tif: Path, footprint: np.ndarray, reference: Path) -> dict:
    v = validate(tif, footprint, reference)
    v["sha256"] = sha256_of(tif)
    v["bytes"] = tif.stat().st_size
    v["zip"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha256_of(p)}
                for p in [tif.with_suffix(".zip")] if p.exists()}
    return v
