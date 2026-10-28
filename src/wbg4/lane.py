"""WBG4 lane: grid I/O, hide-and-recover folds, feature bank, model, emission.

Every function is deterministic and dependency-light (numpy/scipy/rasterio/
scikit-learn).  Nothing here reads another competitor's prediction raster.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CONFIG = ROOT / "config" / "wbg4_lane.json"

HEIGHT, WIDTH = 3730, 3292
TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
CRS_EPSG = 32611


# --------------------------------------------------------------------------- #
# official grids
# --------------------------------------------------------------------------- #
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config() -> dict:
    return json.loads(CONFIG.read_text())


def open_official(path: Path):
    ds = rasterio.open(path)
    if ds.shape != (HEIGHT, WIDTH):
        raise ValueError(f"{path} shape {ds.shape} != {(HEIGHT, WIDTH)}")
    if tuple(ds.transform)[:6] != TRANSFORM:
        raise ValueError(f"{path} transform differs from the official grid")
    if ds.crs.to_epsg() != CRS_EPSG:
        raise ValueError(f"{path} CRS {ds.crs} != EPSG:{CRS_EPSG}")
    return ds


def load_footprint() -> np.ndarray:
    """Cells that participate in scoring: finite values in the official sample."""
    with open_official(DATA / "sample_submission.tif") as ds:
        sample = ds.read(1)
    return np.isfinite(sample)


def load_labels() -> np.ndarray:
    with open_official(DATA / "labels.tif") as ds:
        lab = ds.read(1)
    return (lab == 1)


def verify_pins(cfg: dict | None = None) -> dict:
    """Verify the SHA-256 of every configured input; fail closed on mismatch."""
    cfg = cfg or load_config()
    out = {}
    entries = dict(cfg["inputs"]["official"])
    entries.update(cfg["inputs"]["external"])
    for key, spec in entries.items():
        path = ROOT / spec["path"]
        if not path.exists():
            out[key] = {"path": spec["path"], "present": False}
            continue
        got = sha256(path)
        out[key] = {
            "path": spec["path"],
            "present": True,
            "sha256": got,
            "matches_config": got == spec["sha256"],
        }
    out["all_match"] = all(v.get("matches_config", False) for v in out.values())
    return out


# --------------------------------------------------------------------------- #
# whole-component spatial folds
# --------------------------------------------------------------------------- #
def fault_components(labels: np.ndarray, footprint: np.ndarray):
    """8-connected components of the catalogue; drops specks < 2 px."""
    comp, n = ndi.label(labels, structure=np.ones((3, 3), dtype=bool))
    if n == 0:
        raise ValueError("no fault components")
    sizes = np.bincount(comp.ravel())
    keep = sizes >= 2
    keep[0] = False
    remap = np.zeros(n + 1, dtype=np.int32)
    remap[keep] = np.arange(1, int(keep.sum()) + 1, dtype=np.int32)
    comp = remap[comp]
    return comp, int(keep.sum())


def fold_ids(comp: np.ndarray, footprint: np.ndarray, folds: int = 4) -> np.ndarray:
    """Assign every component to the quadrant that holds most of its pixels."""
    n = int(comp.max())
    rows, cols = np.nonzero(comp)
    ids = comp[rows, cols]
    fr, fc = np.nonzero(footprint)
    rmid = (fr.min() + fr.max()) // 2
    cmid = (fc.min() + fc.max()) // 2
    quad = (rows > rmid).astype(np.int64) * 2 + (cols > cmid).astype(np.int64)
    counts = np.zeros((n + 1, 4), dtype=np.int64)
    np.add.at(counts, (ids, quad), 1)
    assign = counts[1:].argmax(axis=1).astype(np.int8) + 1
    if len(np.unique(assign)) < folds:
        raise ValueError("folds did not populate; check footprint/quadrants")
    return assign


def fold_masks(comp: np.ndarray, ids: np.ndarray, fold: int, buffer_px: int = 3):
    """Masks for one hide-and-recover fold.

    Returns ``(hidden, hidden_buf, visible_feat, visible_exact)``.

    * ``hidden``        — the withheld fault pixels; these are the evaluation positives.
    * ``hidden_buf``    — ``hidden`` dilated by ``buffer_px``; catalogue-derived
      features may not see inside it.
    * ``visible_feat``  — faults a feature builder is allowed to see (buffer removed).
    * ``visible_exact`` — faults that the scorer masks pixel-exactly; the active
      region is the footprint minus exactly these pixels, so withheld faults stay
      active and can be credited.
    """
    sel = np.isin(comp, np.nonzero(ids == (fold + 1))[0] + 1)
    hidden = sel
    if buffer_px > 0:
        hidden_buf = ndi.binary_dilation(hidden, ndi.generate_binary_structure(2, 1),
                                         iterations=buffer_px)
    else:
        hidden_buf = hidden.copy()
    visible_exact = (comp > 0) & ~hidden
    visible_feat = (comp > 0) & ~hidden_buf
    return hidden, hidden_buf, visible_feat, visible_exact


# --------------------------------------------------------------------------- #
# point layers
# --------------------------------------------------------------------------- #
def _point_grid(rows, cols, weights=None, sigma: float = 6.0) -> np.ndarray:
    grid = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    r = np.clip(np.asarray(rows, dtype=np.int64), 0, HEIGHT - 1)
    c = np.clip(np.asarray(cols, dtype=np.int64), 0, WIDTH - 1)
    if weights is None:
        np.add.at(grid, (r, c), 1.0)
    else:
        np.add.at(grid, (r, c), np.asarray(weights, dtype=np.float32))
    return ndi.gaussian_filter(grid, sigma=sigma, mode="constant")


def spring_layers(cfg: dict) -> dict:
    """Density of all springs/wells, of hot springs, and of high geothermometry."""
    path = ROOT / cfg["inputs"]["external"]["gdr_wellspring"]["path"]
    rows, cols, hot, therm = [], [], [], []
    with open(path, newline="") as fh:
        for rec in csv.DictReader(fh):
            try:
                r, c = int(float(rec["row"])), int(float(rec["col"]))
            except (TypeError, ValueError):
                continue
            rows.append(r); cols.append(c)
            hot.append(1.0 if (rec.get("thermalclass") or "").strip() == "Hot" else 0.0)
            try:
                therm.append(max(float(rec.get("geothermcat_c") or 0.0), 0.0) / 200.0)
            except ValueError:
                therm.append(0.0)
    return {
        "spring_dens": _point_grid(rows, cols, None, sigma=6.0),
        "hotspring_dens": _point_grid(rows, cols, hot, sigma=6.0),
        "geotherm_dens": _point_grid(rows, cols, therm, sigma=6.0),
    }


# --------------------------------------------------------------------------- #
# feature bank
# --------------------------------------------------------------------------- #
def _struct_tensor(band: np.ndarray, sigma: float = 4.0):
    g = ndi.gaussian_filter(band, sigma=sigma, mode="nearest")
    gy, gx = np.gradient(g)
    jxx = ndi.gaussian_filter(gx * gx, sigma=sigma, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, sigma=sigma, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, sigma=sigma, mode="nearest")
    tr = jxx + jyy
    coh = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2) / (tr + 1e-6)
    ori = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)          # gradient orientation
    return coh.astype(np.float32), ori.astype(np.float32)


_ANG = {
    0: (0.0, 1.0), 30: (-0.5, 0.866), 60: (-0.866, 0.5), 90: (-1.0, 0.0),
    120: (-0.866, -0.5), 150: (-0.5, -0.866),  -30: (0.5, 0.866),
    -60: (0.866, 0.5),
}


def along_strike(mask: np.ndarray, L: int = 40, step: int = 5) -> np.ndarray:
    """Directional distance to the nearest visible fault, best over 8 strikes.

    Returns a score in [0,1]: 1 - (directional distance)/(L+step), i.e. how
    strongly a fault trace continues through this cell along some strike.
    """
    best = np.zeros(mask.shape, dtype=np.float32)
    for dr, dc in _ANG.values():
        ext = np.full(mask.shape, np.inf, dtype=np.float32)
        for t in range(step, L + step, step):
            for sgn in (1.0, -1.0):
                sh = np.zeros_like(mask)
                dy = int(round(sgn * dr * t)); dx = int(round(sgn * dc * t))
                ys0, ys1 = max(0, dy), min(mask.shape[0], mask.shape[0] + dy)
                xs0, xs1 = max(0, dx), min(mask.shape[1], mask.shape[1] + dx)
                if ys0 >= ys1 or xs0 >= xs1:
                    continue
                sh[ys0:ys1, xs0:xs1] = mask[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
                ext = np.where(sh & (ext == np.inf), np.float32(t), ext)
        score = 1.0 - np.clip(ext, 0.0, L + step) / (L + step)
        np.maximum(best, score, out=best)
    return best


@dataclass
class Window:
    row0: int
    nrows: int
    halo: int


class FeatureBank:
    """Builds the feature matrix for arbitrary row windows.

    Catalogue-derived features are rebuilt for each fold from ``visible`` only;
    everything else is a public layer and is identical across folds.
    """

    LIDAR = ["ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
             "downface_max", "upface_max", "cross_max", "relief", "coh100",
             "strike", "valid"]
    RAD = ["K", "Th", "U", "TC"]
    EXT = ["ThK", "UK", "UTh", "TMI_up150"]

    def __init__(self, cfg: dict, spring: dict):
        self.cfg = cfg
        self.spring = spring
        self._cache: dict[str, np.ndarray] = {}
        self._files = {
            "lidar": ROOT / cfg["inputs"]["external"]["lidar_scarp_features"]["path"],
            "rad": ROOT / cfg["inputs"]["external"]["geodawn_rad"]["path"],
            "ext": ROOT / cfg["inputs"]["external"]["geodawn_extensions"]["path"],
            "sgmc": ROOT / cfg["inputs"]["external"]["sgmc_faults"]["path"],
        }
        self._ds = {k: rasterio.open(v) for k, v in self._files.items()}
        # static whole-grid layers
        sgmc = self._ds["sgmc"].read(1) > 0
        self.dist_sgmc = ndi.distance_transform_edt(~sgmc).astype(np.float32)
        self.sgmc = sgmc
        self.visible: np.ndarray | None = None
        self.dist_vis: np.ndarray | None = None

    def close(self):
        for ds in self._ds.values():
            ds.close()

    def set_visible(self, visible: np.ndarray):
        self.visible = visible
        self.dist_vis = ndi.distance_transform_edt(~visible).astype(np.float32)

    # -- window reads -------------------------------------------------------
    def _read(self, key: str, row0: int, nrows: int, halo: int) -> np.ndarray:
        ds = self._ds[key]
        a = max(0, row0 - halo)
        b = min(HEIGHT, row0 + nrows + halo)
        arr = ds.read(window=rasterio.windows.Window(0, a, WIDTH, b - a))
        return arr  # uint8 (bands, rows, cols)

    def _pad(self, arr: np.ndarray, row0: int, nrows: int, halo: int) -> np.ndarray:
        a = max(0, row0 - halo)
        off = row0 - a
        return arr[:, off:off + nrows]

    def features(self, row0: int, nrows: int, halo: int = 48):
        """Return (names, arrays) for rows ``row0 .. row0+nrows`` of the grid."""
        a = max(0, row0 - halo)
        b = min(HEIGHT, row0 + nrows + halo)
        off0 = row0 - a
        off1 = off0 + nrows
        names: list[str] = []
        bands: list[np.ndarray] = []

        def add(nm, arr):
            names.append(nm)
            bands.append(np.ascontiguousarray(arr[off0:off1], dtype=np.float32))

        win = lambda ds: ds.read(window=rasterio.windows.Window(0, a, WIDTH, b - a))
        lid = win(self._ds["lidar"]).astype(np.float32)
        rad = win(self._ds["rad"]).astype(np.float32)
        ext = win(self._ds["ext"]).astype(np.float32)

        for i, nm in enumerate(self.LIDAR[:11]):
            add(f"L_{nm}", lid[i])
        add("L_valid", (lid[11] > 0).astype(np.float32))
        add("L_polarity", lid[5] - lid[6])
        for nm, i in (("ex_max", 0), ("step_max", 2), ("lapneg_max", 3),
                      ("downface_max", 5), ("coh100", 9)):
            add(f"L_{nm}_s8", ndi.gaussian_filter(lid[i], 8.0, mode="nearest"))
        for nm, i in (("ex_max", 0), ("step_max", 2)):
            gy, gx = np.gradient(ndi.gaussian_filter(lid[i], 2.0, mode="nearest"))
            add(f"L_{nm}_grad2", np.hypot(gx, gy))

        for i, nm in enumerate(self.RAD):
            add(f"R_{nm}", rad[i])
        for i, nm in enumerate(self.EXT):
            add(f"X_{nm}", ext[i])
        for key, src, i in (("TC", rad, 3), ("TMI", ext, 3)):
            add(f"{key}_s8", ndi.gaussian_filter(src[i], 8.0, mode="nearest"))
            gy, gx = np.gradient(ndi.gaussian_filter(src[i], 2.0, mode="nearest"))
            add(f"{key}_grad2", np.hypot(gx, gy))

        coh, ori = _struct_tensor(lid[0], 4.0)
        add("ST_coh", coh)
        add("ST_cos2", np.cos(2.0 * ori))
        add("ST_sin2", np.sin(2.0 * ori))

        add("D_sgmc_log", np.log1p(np.minimum(self.dist_sgmc[a:b], 200.0)))
        add("SGMC_mask", self.sgmc[a:b].astype(np.float32))
        for nm, arr in self.spring.items():
            add(nm, arr[a:b])

        if self.visible is not None:
            vis = self.visible[a:b]
            add("D_vis_log", np.log1p(np.minimum(self.dist_vis[a:b], 200.0)))
            vf = vis.astype(np.float32)
            for s in (5.0, 15.0, 40.0):
                add(f"dens_vis_{int(s)}", ndi.gaussian_filter(vf, s, mode="constant"))
            cont = along_strike(vis, L=40, step=5)
            add("cont_max", cont)
            # separate cardinal directions (regional grain diagnostics)
            for nm, ang in (("cont_ns", 90), ("cont_ne", 30)):
                dr, dc = _ANG[ang]
                ext_d = np.full(vis.shape, np.inf, dtype=np.float32)
                for t in range(5, 45, 5):
                    for sgn in (1.0, -1.0):
                        dy = int(round(sgn * dr * t)); dx = int(round(sgn * dc * t))
                        ys0, ys1 = max(0, dy), min(vis.shape[0], vis.shape[0] + dy)
                        xs0, xs1 = max(0, dx), min(vis.shape[1], vis.shape[1] + dx)
                        if ys0 >= ys1 or xs0 >= xs1:
                            continue
                        sh = np.zeros_like(vis)
                        sh[ys0:ys1, xs0:xs1] = vis[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
                        ext_d = np.where(sh & (ext_d == np.inf), np.float32(t), ext_d)
                add(nm, 1.0 - np.clip(ext_d, 0.0, 45.0) / 45.0)

        return names, bands


# --------------------------------------------------------------------------- #
# metric wrapper (reuse the pinned official implementation)
# --------------------------------------------------------------------------- #
def dti(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """Official DTI; dispatches to the exact binary path for {0,1} predictions."""
    from wbg3.metric import dti_binary, dti_probabilistic
    vals = np.unique(np.asarray(pred)[np.asarray(active)])
    if vals.size <= 2 and np.all(np.isin(vals, (0.0, 1.0))):
        return dti_binary(pred, truth, active)
    return dti_probabilistic(pred, truth, active)


def pooled(parts: list[dict]) -> dict:
    from wbg3.metric import pooled as _pooled
    return _pooled(parts)
