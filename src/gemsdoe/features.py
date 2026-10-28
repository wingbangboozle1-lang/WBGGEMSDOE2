"""Build the catalogue-independent feature bank used by every model in this lane.

Design notes
------------
* Only organizer-provided layers are used, so no external-data licence question
  arises for the modeled features.
* Every layer is stored as float16 in a single memory-mapped ``.npy`` of shape
  ``(n_layers, 3730, 3292)`` so training and full-grid inference can stream it
  inside a 3 GB container.
* Bands are robustly standardised (median / IQR inside the footprint, NaN kept as
  NaN) so that gradient/curvature filters are scale-free.
* Catalogue-dependent layers (distance to visible faults) are deliberately NOT
  stored here: they must be rebuilt per fold from fold-visible faults only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from . import grid

SCALES = (2.0, 3.0, 6.0)  # in pixels = 200 m, 300 m, 600 m


def _robust_scale(a: np.ndarray, fp: np.ndarray) -> tuple[np.ndarray, dict]:
    v = a[fp & np.isfinite(a)]
    med = float(np.median(v))
    q25, q75 = np.percentile(v, [25, 75])
    iqr = float(q75 - q25)
    if not np.isfinite(iqr) or iqr <= 0:
        iqr = float(np.std(v)) or 1.0
    out = (a - med) / iqr
    return out.astype("float32"), {"median": med, "iqr": iqr,
                                   "min": float(v.min()), "max": float(v.max())}


def layer_names() -> list[str]:
    names = []
    for b in grid.feature_band_names():
        names += [f"{b}__z", f"{b}__gradmag_s{SCALES[0]:g}", f"{b}__log_s{SCALES[1]:g}",
                  f"{b}__smooth_s{SCALES[2]:g}"]
    return names


def build(force: bool = False) -> dict:
    grid.ensure_work()
    out = grid.WORK / "features.npy"
    meta_path = grid.WORK / "features.json"
    names = layer_names()
    if out.exists() and meta_path.exists() and not force:
        return json.loads(meta_path.read_text())

    fp = np.load(grid.WORK / "footprint.npy")
    n = len(names)
    arr = np.lib.format.open_memmap(out, mode="w+", dtype="float16", shape=(n,) + grid.SHAPE)
    meta = {"layers": names, "scales_px": list(SCALES), "dtype": "float16",
            "standardisation": "median/IQR inside footprint", "bands": {}}

    i = 0
    for bi in range(1, 20):
        raw = grid.read_band(bi)
        z, st = _robust_scale(raw, fp)
        name = grid.feature_band_names()[bi - 1]
        meta["bands"][name] = st
        filled = np.where(np.isfinite(z), z, 0.0).astype("float32")
        valid = np.isfinite(z)
        arr[i] = np.where(valid, z, np.nan).astype("float16"); i += 1

        g2 = ndi.gaussian_filter(filled, SCALES[0])
        gy, gx = np.gradient(g2)
        gm = np.hypot(gx, gy).astype("float32")
        arr[i] = np.where(valid, gm, np.nan).astype("float16"); i += 1

        lo = (-ndi.gaussian_laplace(filled, SCALES[1])).astype("float32")
        arr[i] = np.where(valid, lo, np.nan).astype("float16"); i += 1

        sm = ndi.gaussian_filter(filled, SCALES[2]).astype("float32")
        arr[i] = np.where(valid, sm, np.nan).astype("float16"); i += 1
        print(f"band {name} done ({i}/{n})", flush=True)

    arr.flush()
    del arr
    meta["n_layers"] = n
    meta["bytes"] = int(Path(out).stat().st_size)
    meta_path.write_text(json.dumps(meta, indent=1))
    return meta


def load(mmap: bool = True):
    return np.load(grid.WORK / "features.npy", mmap_mode="r" if mmap else None)


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(build(), indent=1)[:2000])
