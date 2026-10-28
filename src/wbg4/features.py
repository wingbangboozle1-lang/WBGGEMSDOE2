"""Design matrix for the WBG4 lane.

Provenance (every input is a hash-pinned public artifact; see
``evidence/wbg4_inputs.json`` and ``docs/EDTI_EXECUTIVE_SUMMARY.md``):

===================================  =========================================  ========
file                                  content                                     source
===================================  =========================================  ========
``scratch/bridge/sample_submission``  official 3730x3292 float32 template,        organizer
                                      EPSG:32611, 100 m, NaN outside footprint     (bridged)
``scratch/bridge/labels.tif``         int8, -1 outside / 0 / 1, 60,988 positives  organizer
``lidar_scarp_features_u8.tif``       12 u8 bands of 1 m LiDAR scarp morphometry  USDA/USGS
``geodawn_rad_u8.tif``                4 u8 bands K, Th, U, TC                     DOE GeoDAWN
``geodawn_extensions_u8.tif``         4 u8 bands ThK, UK, UTh, TMI_up150          DOE GeoDAWN
===================================  =========================================  ========

**Catalogue-derived layers are deliberately excluded.**  In particular
``derived_sgmc_faults_100m_u8.tif`` (a rasterised state-geological-map fault
layer) is *not* used, so a withheld-fault holdout built from the label raster is
not circular: no feature can encode the location of the fault it is asked to
recover.
"""
from __future__ import annotations

import json
import os

import numpy as np
import rasterio

LIDAR_BANDS = ("ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
               "downface_max", "upface_max", "cross_max", "relief", "coh100",
               "strike", "valid")
RAD_BANDS = ("K", "Th", "U", "TC")
EXT_BANDS = ("ThK", "UK", "UTh", "TMI_up150")

# Layers that would leak the catalogue into a catalogue-derived holdout.
FORBIDDEN_LAYERS = ("derived_sgmc_faults_100m_u8.tif", "gdr_qfaults_traces.csv",
                    "gdr_volcanic_vents_in_footprint.csv", "gdr_wellspring_in_footprint.csv")


def _read(path: str) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read().astype(np.float32), ds


def load_grid(paths: dict) -> dict:
    """Load template, labels, footprint and the 20 catalogue-free feature bands."""
    for p in paths.values():
        base = os.path.basename(p)
        if base in FORBIDDEN_LAYERS:
            raise ValueError(f"forbidden catalogue-derived layer requested: {base}")

    lidar, ds = _read(paths["lidar"])
    if lidar.shape[0] != len(LIDAR_BANDS):
        raise ValueError(f"lidar band count {lidar.shape[0]} != {len(LIDAR_BANDS)}")
    rad, ds_r = _read(paths["rad"])
    ext, _ = _read(paths["ext"])
    names = list(LIDAR_BANDS) + list(RAD_BANDS) + list(EXT_BANDS)
    stack = np.concatenate([lidar, rad, ext], axis=0)
    assert stack.shape[0] == len(names) == 20, stack.shape

    with rasterio.open(paths["template"]) as t:
        tmpl = t.read(1).astype(np.float32)
        ref = dict(shape=t.shape, crs=str(t.crs), transform=tuple(t.transform),
                   width=t.width, height=t.height)
    with rasterio.open(paths["labels"]) as L:
        lab = L.read(1)
        assert L.shape == ref["shape"], (L.shape, ref["shape"])
    footprint = np.isfinite(tmpl)
    truth = (lab > 0) & footprint
    for d in (ds, ds_r):
        assert d.shape == ref["shape"] and d.crs == ref["crs"], "feature grid mismatch"
        assert tuple(d.transform) == ref["transform"], "feature transform mismatch"
    census = dict(footprint=int(footprint.sum()),
                  cells_with_all_bands=int((footprint & ~(stack <= 0).any(axis=0)).sum()),
                  per_band_valid={n: int((stack[i] > 0).sum()) for i, n in enumerate(names)})
    return dict(features=stack, names=names, footprint=footprint, truth=truth,
                template=tmpl, ref=ref, census=census,
                prevalence=float(truth.sum()) / float(footprint.sum()))


def design_matrix(grid: dict, valid_only: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(X, y, cell_index)`` restricted to the scoring footprint.

    The 0..255 quantiser in the source products writes ``0`` for "no
    observation" (``q = 1 + round(254 * t(x))``), so ``0`` is converted to
    ``NaN`` rather than imputed: a value that was never measured must not be
    presented to the model as a measurement.  ``HistGradientBoostingClassifier``
    handles ``NaN`` natively.

    ``valid_only=True`` instead *drops* cells with any missing band, which is the
    stricter variant used to quantify how much of the footprint radiometric
    coverage actually supports.  Never silent: the kept/dropped counts are in
    ``grid['census']``.
    """
    f = grid["features"]
    fp = grid["footprint"]
    n_band = f.shape[0]
    nodata_any = (f <= 0).any(axis=0)
    keep = fp & (~nodata_any if valid_only else True)
    idx = np.flatnonzero(keep.ravel())
    X = f.reshape(n_band, -1)[:, idx].T.copy()
    X[X <= 0] = np.nan
    y = grid["truth"].ravel()[idx].astype(np.int8)
    return X, y, idx


def summary(grid: dict) -> dict:
    return dict(shape=list(grid["ref"]["shape"]), crs=grid["ref"]["crs"],
                transform=list(grid["ref"]["transform"]),
                footprint_pixels=int(grid["footprint"].sum()),
                label_positives=int(grid["truth"].sum()),
                prevalence=grid["prevalence"],
                n_features=len(grid["names"]), feature_names=grid["names"])


def write_provenance(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(payload, open(path, "w"), indent=1, sort_keys=True)
