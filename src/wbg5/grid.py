"""Grid, mask and layer loading for the WBG5 campaign (all cached under /tmp)."""
from __future__ import annotations

import csv
from dataclasses import dataclass

import numpy as np
import rasterio
from scipy import ndimage as ndi

from . import paths

SENTINEL = -3.4028234663852886e38
SHAPE = (3730, 3292)
TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
CRS = "EPSG:32611"


@dataclass(frozen=True)
class Masks:
    footprint: np.ndarray
    catalogue: np.ndarray

    @property
    def outside(self) -> np.ndarray:
        return ~self.footprint


def load_masks() -> Masks:
    fp_p, cat_p = paths.WORK / "footprint.npy", paths.WORK / "catalogue.npy"
    if fp_p.exists() and cat_p.exists():
        return Masks(np.load(fp_p), np.load(cat_p))
    with rasterio.open(paths.LABELS) as d:
        lab = d.read(1)
    assert (d.height, d.width) == SHAPE
    m = Masks(lab != -1, lab == 1)
    paths.ensure_work()
    np.save(fp_p, m.footprint)
    np.save(cat_p, m.catalogue)
    return m


def _read_tif(path, sentinel: float | None = SENTINEL) -> np.ndarray:
    with rasterio.open(path) as d:
        a = d.read().astype("float32")
    if sentinel is not None:
        a[~np.isfinite(a) | (a < -1e37)] = np.nan
    return a


def feature_stack() -> np.ndarray:
    """19-band organizer feature stack, sentinel converted to NaN."""
    p = paths.WORK / "X.npy"
    if p.exists():
        return np.load(p, mmap_mode="r")
    X = _read_tif(paths.FEATURES)
    paths.ensure_work()
    np.save(p, X)
    return np.load(p, mmap_mode="r")


FEATURE_NAMES = [
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
    "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15",
    "iso_grav_anom_vg", "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf",
    "ieq_n100a15", "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
]
LIDAR_NAMES = [
    "ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max", "downface_max",
    "upface_max", "cross_max", "relief", "coh100", "strike", "valid",
]


def lidar_stack() -> np.ndarray:
    p = paths.WORK / "lidar.npy"
    if p.exists():
        return np.load(p, mmap_mode="r")
    L = _read_tif(paths.LIDAR, sentinel=None)
    np.save(p, L)
    return np.load(p, mmap_mode="r")


def rad_stack() -> np.ndarray:
    p = paths.WORK / "rad8.npy"
    if p.exists():
        return np.load(p, mmap_mode="r")
    R = np.concatenate([_read_tif(paths.RAD, None), _read_tif(paths.RAD_EXT, None)], 0)
    np.save(p, R)
    return np.load(p, mmap_mode="r")


RAD_NAMES = ["K", "Th", "U", "TC", "ThK", "UK", "UTh", "TMI_up150"]


def sgmc_offcatalogue(masks: Masks, buffer_px: float = 3.0) -> np.ndarray:
    """Independent state-map faults, restricted to >buffer from the public catalogue."""
    with rasterio.open(paths.SGMC) as d:
        sg = d.read(1) > 0
    d_cat = ndi.distance_transform_edt(~masks.catalogue)
    return sg & masks.footprint & (d_cat > buffer_px)


def point_distance(csv_path, masks: Masks, use: str = "rowcol", max_cells: int = 4000) -> np.ndarray:
    """Euclidean pixel distance from every cell to the nearest CSV point."""
    pts = []
    with open(csv_path, newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                if use == "rowcol":
                    r, c = int(row["row"]), int(row["col"])
                    if 0 <= r < SHAPE[0] and 0 <= c < SHAPE[1]:
                        pts.append((r, c))
            except (KeyError, TypeError, ValueError):
                continue
    seed = np.ones(SHAPE, dtype=bool)
    for r, c in pts:
        seed[r, c] = False
    return ndi.distance_transform_edt(seed).astype("float32")


def percentile_field(values: np.ndarray, domain: np.ndarray, fill: float = 0.0) -> np.ndarray:
    """Percentile rank in [0,1] computed inside ``domain``; ``fill`` elsewhere."""
    out = np.full(values.shape, fill, dtype="float32")
    v = np.asarray(values, dtype="float32")[domain]
    ok = np.isfinite(v)
    if not ok.any():
        return out
    ranks = np.full(len(v), np.nan, dtype="float32")
    ranks[ok] = np.argsort(np.argsort(v[ok])).astype("float32") / max(int(ok.sum()) - 1, 1)
    full = np.full(values.shape, np.nan, dtype="float32")
    full[domain] = ranks
    out = np.where(np.isfinite(full), full, fill).astype("float32")
    return out
