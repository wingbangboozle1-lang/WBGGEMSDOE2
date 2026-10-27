#!/usr/bin/env python3
"""Build the shared-template uint8 feature bank from the hash-verified mirror.

This reuses the *definitions* of the pinned shared builder
``data/shared_template/scripts/prep_feature_stack.py`` (``q`` = global quantile
rank inside the footprint, ``z`` = 9x9 local standardised contrast then global
quantile rank, 255 = nodata) but replaces two implementation details that do not
scale to this sandbox (2 CPU / 3 GB RAM):

* ``_rank_u8``'s tie loop is O(#distinct values) in Python.  ``rank_u8_fast``
  below computes the *same* average-rank transform with ``np.unique`` and is
  verified equal to the shared implementation on random arrays with heavy ties
  (``tests/test_feature_bank.py``).
* The shared script's catalogue-derived ``geo_f32``/``dtip_f32`` caches use the
  **full** catalogue.  Parallel-run protocol rule 2 forbids reusing them inside a
  hide-and-recover fold, so this script deliberately does **not** build them.
  Fold-local, visible-faults-only equivalents are built in
  ``scripts/lane_blind_propensity.py``.

Output (gitignored): ``data/features/bank_u8.npy`` (38, 3730, 3292) uint8.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PREP = ROOT / "data" / "shared_template" / "scripts" / "prep_feature_stack.py"
FEATURES_TIF = ROOT / "data" / "training_features_mirror.tif"
SAMPLE_TIF = ROOT / "data" / "bridge" / "sample_submission.tif"
OUT_DIR = ROOT / "data" / "features"
FEATURE_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def _load_shared_constants():
    """Import the pinned shared builder for its constants only (no execution)."""
    spec = importlib.util.spec_from_file_location("shared_prep_feature_stack", TEMPLATE_PREP)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned shared builder: {TEMPLATE_PREP}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHARED = _load_shared_constants()
NODATA = SHARED.NODATA
RANK_MAX = SHARED.RANK_MAX
NODATA_U8 = SHARED.NODATA_U8
shared_rank_u8 = SHARED._rank_u8


def rank_u8_fast(values: np.ndarray) -> np.ndarray:
    """Average-rank of ``values`` scaled to 0..RANK_MAX; ties share a rank.

    Algebraically identical to the shared ``_rank_u8``: a tie group occupying
    sorted positions ``[s, s+c-1]`` receives average position ``s+(c-1)/2``,
    which is ``0.5*(i+j)`` in the shared loop's indexing.
    """
    v = np.asarray(values, np.float64).ravel()
    uniq, inverse, counts = np.unique(v, return_inverse=True, return_counts=True)
    starts = np.zeros(counts.size, np.float64)
    np.cumsum(counts[:-1], out=starts[1:])
    avg = starts + (counts - 1) / 2.0
    r = avg[inverse.reshape(-1)]
    if v.size > 1:
        r = r * (RANK_MAX / (v.size - 1))
    return np.clip(np.rint(r), 0, RANK_MAX).astype(np.uint8)


def build(out_dir: Path = OUT_DIR, *, verbose: bool = True) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(SAMPLE_TIF) as src:
        sample = src.read(1)
        mask = src.read_masks(1)
    footprint = np.isfinite(sample) & (mask > 0)
    del sample, mask

    with rasterio.open(FEATURES_TIF) as src:
        nb = src.count
        names = [src.descriptions[i].split(" - ")[0] for i in range(nb)]
        height, width = src.height, src.width
        bank_path = out_dir / "bank_u8.npy"
        bank = np.lib.format.open_memmap(bank_path, mode="w+", dtype=np.uint8,
                                         shape=(2 * nb, height, width))
        per_band = []
        for i in range(nb):
            a = src.read(i + 1).astype(np.float32)
            bad = (~np.isfinite(a)) | (a <= NODATA / 10.0)
            good = (~bad) & footprint
            idx = np.flatnonzero(good.ravel())
            q = np.full(a.shape, NODATA_U8, np.uint8)
            z = np.full(a.shape, NODATA_U8, np.uint8)
            if int(good.sum()) > 100:
                q.reshape(-1)[idx] = rank_u8_fast(a[good])
                median = float(np.median(a[good]))
                b = np.where(bad, median, a)
                m1 = ndi.uniform_filter(b, size=9, mode="nearest")
                m2 = ndi.uniform_filter(b * b, size=9, mode="nearest")
                sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0)) + 1e-6
                zz = (b - m1) / sd
                z.reshape(-1)[idx] = rank_u8_fast(zz[good])
                del b, m1, m2, sd, zz
            bank[2 * i] = q
            bank[2 * i + 1] = z
            per_band.append(dict(band=i + 1, name=names[i],
                                 nodata_cells=int(bad.sum()),
                                 nodata_in_footprint=int((bad & footprint).sum()),
                                 median=float(np.median(a[good])) if int(good.sum()) else None,
                                 q_min=int(q[good].min()) if int(good.sum()) else None,
                                 z_min=int(z[good].min()) if int(good.sum()) else None))
            del a, bad, good, q, z
            if verbose:
                print(f"banked {i + 1:2d}/{nb} {names[i]}", flush=True)
        bank.flush()
        del bank

    receipt = dict(schema="gems57.feature-bank.v1",
                   definition_source=str(TEMPLATE_PREP.relative_to(ROOT)),
                   source_raster=str(FEATURES_TIF.relative_to(ROOT)),
                   source_sha256=FEATURE_SHA256,
                   bank_path=str(bank_path.relative_to(ROOT)),
                   bank_shape=[2 * nb, height, width],
                   band_names=names, footprint_cells=int(footprint.sum()),
                   rank_max=int(RANK_MAX), nodata_code=int(NODATA_U8),
                   rank_implementation="rank_u8_fast (np.unique average rank), "
                                       "verified equal to shared _rank_u8",
                   catalogue_features="NOT BUILT HERE: must be fold-local and "
                                      "visible-faults-only (protocol rule 2)",
                   per_band=per_band)
    (ROOT / "evidence" / "feature_bank.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    receipt = build(args.out, verbose=not args.quiet)
    print(json.dumps({k: v for k, v in receipt.items() if k != "per_band"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
