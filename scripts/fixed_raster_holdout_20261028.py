#!/usr/bin/env python3
"""Score fixed submission rasters on the SHARED hide-and-recover folds (no fork).

Purpose: test the claim that the local HOLDOUT-DTI proxy ranks the top leaderboard
file (GEMSDOE32 / B2, user-reported 0.2778) near zero. Everything used is shared:

* folds:     gems57.spatial.folds(catalogue, footprint, buffer_px=80)
* evaluator: gems57.evaluate_holdout.evaluate / pooled_summary (VERSION gems57-pooled-hide-v2)
* catalogue: data/official/existing_faults.tif == 1 (the visible USGS/INGENIOUS catalogue)
* footprint: data/official/sample_submission.tif finite & valid cells (5,167,373)

Caveat (carried into the evidence file): a fixed raster is evaluated on each fold
without regenerating it from fold-visible features. This is the same protocol the
repo used for its fixed-raster checks; it is NOT a hide-and-recover regeneration.

Also measures, for each raster, how many dots lie within 2 px / 3 px of the
catalogue. Writes evidence/fixed_raster_holdout_20261028.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_SRC = ROOT / ".cache" / "shared-template" / "src"
sys.path.insert(0, str(TEMPLATE_SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import spatial, evaluate_holdout as E  # noqa: E402
from prepare_data import restore_template  # noqa: E402  (verifies pinned upstream bytes)
from recheck_nine_site_20261028 import fetch_sites, sha256  # noqa: E402

SAMPLE = ROOT / "data/official/sample_submission.tif"
CATALOGUE = ROOT / "data/official/existing_faults.tif"
OUT = ROOT / "evidence/fixed_raster_holdout_20261028.json"
CANDIDATES = {
    "triphysics_zerooutside": ROOT / "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2-zerooutside.tif",
    "distal2_zeros": ROOT / "docs/downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif",
}
RANDOM_SEEDS = (1, 2, 3)


def read_positive(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
    return np.clip(np.where(np.isfinite(a), a, 0.0), 0.0, 1.0)


def main() -> int:
    restore_template(False)
    with rasterio.open(SAMPLE) as ds:
        fp = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
    with rasterio.open(CATALOGUE) as ds:
        cat = ds.read(1) == 1
    dcat = ndi.distance_transform_edt(~cat)
    folds = list(spatial.folds(cat, fp, buffer_px=80))

    def score(pred: np.ndarray, label: str) -> dict:
        acc, per_fold = None, []
        for fo in folds:
            r, t = E.evaluate(pred, fo, fp, global_shape=fp.shape)
            per_fold.append(round(float(r["dti"]), 6))
            acc = t if acc is None else acc + t
        summ = E.pooled_summary({"candidate": acc}, draws=1000, seed=520810, candidate="candidate")
        s = summ["scores"]["candidate"]
        d = (pred > 0)
        return {
            "label": label,
            "dots": int(d.sum()),
            "dots_inside_footprint": int((d & fp).sum()),
            "frac_dots_within_2px_of_catalogue": round(float((dcat[d] <= 2).mean()), 4),
            "frac_dots_within_3px_of_catalogue": round(float((dcat[d] <= 3).mean()), 4),
            "per_fold_dti": per_fold,
            "pooled_dti_HOLDOUT_DTI": round(s["dti"], 6),
            "ci95_spatial_cluster_bootstrap": [round(x, 6) for x in s["ci95"]],
            "withheld_positive_pixels": s["withheld_positive_pixels"],
            "evaluator_version": s["evaluator_version"],
        }

    rows = []
    sites = fetch_sites()
    b2 = read_positive(sites["GEMSDOE32"])
    rows.append({"raster": "GEMSDOE32 (user-reported 0.2778)", "sha256": sha256(sites["GEMSDOE32"]),
                 **score(b2, "GEMSDOE32 (user-reported 0.2778)")})
    for name, path in CANDIDATES.items():
        p = read_positive(path)
        rows.append({"raster": name, "sha256": sha256(path), **score(p, name)})
    budget = int((b2 > 0).sum())
    idx = np.flatnonzero(fp)
    for seed in RANDOM_SEEDS:
        sel = np.random.default_rng(seed).choice(idx, budget, replace=False)
        p = np.zeros(fp.shape, dtype="float64")
        p.flat[sel] = 1.0
        label = f"uniform random {budget} dots (seed {seed}) - control"
        rows.append({"raster": label, "sha256": None, **score(p, label)})

    report = {
        "schema": "wbggems.fixed-raster-holdout.v1",
        "evidence_class": "HOLDOUT-DTI (shared evaluator, fixed raster; not a leaderboard score)",
        "evaluator_version": E.VERSION,
        "evaluator_implementation_sha256": E.implementation_hashes(),
        "folds": "gems57.spatial.folds(catalogue, footprint, buffer_px=80)",
        "catalogue_cells": int(cat.sum()),
        "footprint_cells": int(fp.sum()),
        "caveat": ("Fixed rasters evaluated on each fold without regeneration from fold-visible "
                   "features; the 0.2778 raster was derived from the full catalogue, so this is "
                   "a placement test, not a hide-and-recover generalisation test."),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=1, allow_nan=False) + "\n")
    for r in rows:
        print(f"{r['label']:<48} DTI={r['pooled_dti_HOLDOUT_DTI']:.4f} "
              f"CI={r['ci95_spatial_cluster_bootstrap']} "
              f"near-cat2px={r['frac_dots_within_2px_of_catalogue']:.3f}")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
