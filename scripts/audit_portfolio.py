#!/usr/bin/env python3
"""Reopen pinned historical files, calculate pairwise novelty and a literal STOP.

Analysis of existing submissions only; never synthesizes a candidate or spends a
weekly slot. Single witness is enough to disprove uniqueness, not enough to claim
an exhaustive, current all-registry scan. Requires the owner-mirrored sample grid.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

from prepare_data import ROOT, TEMPLATE, digest, fetch_checked, restore_template

CACHE = ROOT / ".cache" / "priority-audit"


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    return x*x + y*y <= radius*radius


def same_grid(ds, sample) -> bool:
    return (ds.count == 1 and ds.shape == sample.shape and ds.crs == sample.crs
            and ds.transform == sample.transform)


def load_pinned(row, fetch):
    name = row.get("site", row["sha256"][:16]) + ".tif"
    path = CACHE / name
    if fetch:
        fetch_checked(row["repository"], row["ref"], row["path"], path, row["sha256"])
    if not path.is_file() or digest(path) != row["sha256"]:
        raise FileNotFoundError(f"Missing or hash-mismatched historical input {path}; use --fetch")
    return path


def portfolio() -> tuple[dict, dict]:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--output", default="docs/data/portfolio.json")
    args = ap.parse_args()
    manifest = json.loads((ROOT / "registry/focus_sites.json").read_text())
    witnesses = json.loads((ROOT / "registry/witnesses.json").read_text())
    lattice_record = witnesses["lattice"]
    dense_record = witnesses["dense_probability"]
    sample_path = ROOT / "data/official/sample_submission.tif"
    labels_path = ROOT / "data/official/existing_faults.tif"
    if not sample_path.is_file() or not labels_path.is_file():
        raise FileNotFoundError("Pinned sample and fault files absent; run scripts/prepare_data.py --fetch first")
    # Verify reference bytes rather than trusting a filename or local cache.
    if digest(sample_path) != "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc":
        raise ValueError("sample mirror hash mismatch")
    if digest(labels_path) != "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093":
        raise ValueError("label mirror hash mismatch")
    records = manifest["sites"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda x: load_pinned(x, args.fetch), records + [lattice_record, dense_record]))
    paths_by_site = {r["site"]: p for r, p in zip(records, paths)}
    lattice_path, dense_path = paths[-2:]

    with rasterio.open(sample_path) as sample:
        footprint = np.isfinite(sample.read(1))
        with rasterio.open(labels_path) as ds:
            if not same_grid(ds, sample):
                raise ValueError("Catalogue grid mismatch")
            cat = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & footprint
        masks = {}
        rows = []
        for r in records:
            pth = paths_by_site[r["site"]]
            with rasterio.open(pth) as ds:
                if not same_grid(ds, sample):
                    raise ValueError(f"Grid mismatch: {r['site']}")
                a = ds.read(1)
                finite = np.isfinite(a)
                valid = footprint & finite
                if not np.all(finite[footprint]) or not np.all((a[valid] >= 0) & (a[valid] <= 1)):
                    raise ValueError(f"Inside-footprint values invalid: {r['site']}")
                canonical = np.where(valid, a, 0).astype("<f4", copy=False)
                values_hash = hashlib.sha256(canonical.tobytes()).hexdigest()
                positive = canonical > 0
                masks[r["site"]] = positive
                row = dict(r)
                row.update(
                    decoded_prediction_sha256=values_hash,
                    positive_pixels=int(positive.sum()),
                    binary_in_footprint=bool(np.all((canonical == 0) | (canonical == 1))),
                    dtype=ds.dtypes[0], grid_matches_mirror=True,
                    finite_inside_footprint=int(finite[footprint].sum()),
                    nan_outside_footprint=int((~finite & ~footprint).sum()),
                    evidence_class="HISTORICAL-MIRROR-MEASUREMENT + USER-REPORTED",
                    is_new_candidate=False, eligible_for_submission=False,
                    estimated_leaderboard_score=None,
                )
                rows.append(row)
                del a, canonical
        with rasterio.open(lattice_path) as ds:
            if not same_grid(ds, sample):
                raise ValueError("Lattice witness grid mismatch")
            a = ds.read(1)
            lattice = np.isfinite(a) & (a > 0) & footprint
    # Cache dilated supports one by one, not all nine 12-million-cell arrays.
    n = len(rows)
    matrix = np.empty((n, n), dtype=float)
    structure = disk(3)
    for j, prior in enumerate(rows):
        near = ndi.binary_dilation(masks[prior["site"]], structure=structure)
        for i, candidate in enumerate(rows):
            support = masks[candidate["site"]]
            total = int(support.sum())
            matrix[i, j] = float((support & near).sum()) / total if total else 0.0
        del near
    for i, row in enumerate(rows):
        other_indices = [j for j in range(n) if i != j]
        j = max(other_indices, key=lambda x: matrix[i, x])
        row["max_3px_overlap_vs_other_focus"] = float(matrix[i, j])
        row["max_overlap_witness_site"] = rows[j]["site"]
        row["literal_focus_overlap_pass"] = bool(matrix[i, j] <= 0.70)
        row["decoded_exact_matches_in_focus"] = [
            r["site"] for r in rows
            if r["site"] != row["site"] and r["decoded_prediction_sha256"] == row["decoded_prediction_sha256"]
        ]
        # None of the historical inputs is an eligible new submission. A final
        # support audit cannot establish the required pre-placement surface gate.
        row["surface_uniqueness"] = "not replayed"

    lattice_near = ndi.binary_dilation(lattice, structure=structure)
    n_footprint = int(footprint.sum())
    n_uncovered = int((footprint & ~lattice_near).sum())
    n_covered = n_footprint - n_uncovered
    budget = 37654
    # Pigeonhole bound: distinct positive cells within the footprint, maximum one
    # pixel per location. Applies to this budget, not to every possible raster.
    lower_bound = max(0, budget - n_uncovered) / budget
    b2 = masks["GEMSDOE32"]
    d28 = masks["GEMSDOE25"]
    cat_distance = ndi.distance_transform_edt(~cat)
    expected_b2 = d28 & (cat_distance > 2)
    nested = {
        "d28_pixels": int(d28.sum()), "b2_pixels": int(b2.sum()),
        "b2_pixels_not_in_d28": int((b2 & ~d28).sum()),
        "d28_pixels_removed": int((d28 & ~b2).sum()),
        "b2_equals_d28_excluding_cat_distance_lte_2_pixels": bool(np.array_equal(b2, expected_b2)),
        "cat_distance_definition": "Euclidean pixel-center distance to positive owner-mirrored catalogue pixels",
    }
    witness = {
        "evidence_class": "MEASURED-REGISTRY-COUNTEREXAMPLE",
        "source": lattice_record["source"], "registry_evidence": lattice_record["registry_evidence"],
        "lattice_sha256": lattice_record["sha256"], "sample_sha256": digest(sample_path),
        "footprint_pixels": n_footprint, "lattice_positive_pixels": int(lattice.sum()),
        "within_3px_pixels": n_covered, "outside_3px_pixels": n_uncovered,
        "within_3px_fraction": n_covered / n_footprint,
        "example_budget_distinct_dots": budget,
        "minimum_possible_overlap_at_example_budget": lower_bound,
        "threshold": 0.70, "example_budget_necessarily_fails": lower_bound > 0.70,
        "qualification": "Valid for distinct in-footprint dots at this budget; not a proof about all nonempty rasters. No surface was produced.",
        "registered_b2_overlap": float((b2 & lattice_near).sum() / b2.sum()),
    }
    # Reuse the pinned shared template's literal finite-positive support rule.
    # For a continuous prior, whether these pixels should be called "dots" is an
    # unresolved policy ambiguity; do not quietly exempt it.
    restore_template(False)
    sys.path.insert(0, str(TEMPLATE / "src"))
    from gems57.uniqueness import saturation_certificate
    with rasterio.open(sample_path) as sample:
        dense = saturation_certificate(dense_path, footprint,
                                        expected_grid=(sample.shape, sample.crs, sample.transform))
    dense["witness_file"] = str(dense_path.relative_to(ROOT))
    dense.update(source=dense_record["source"], registry_evidence=dense_record["registry_evidence"],
                 definition_caveat="Continuous prior: shared literal implementation defines finite >0 as support; no exemption applied.")
    result = {
        "schema_version": 1, "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "evidence_class": "HISTORICAL-MIRROR-MEASUREMENT + USER-REPORTED",
        "score_evidence": "User-reported claims, no organizer submission-page receipts",
        "score_forecast": "Unavailable: no verified cross-family leaderboard calibration",
        "current_candidate": None, "new_submission_ok": False,
        "audited_scope": "Nine pinned historical rasters, a registered lattice and a registered continuous prior; not a current exhaustive registry scan",
        "preplacement_surfaces_replayed": False,
        "pairwise_definition": "fraction of this row's positive footprint pixels within Euclidean <=3 pixels of the other raster's positive pixels",
        "sites": rows,
        "pairwise_overlap": {r["site"]: {t["site"]: float(matrix[i,j]) for j,t in enumerate(rows)} for i,r in enumerate(rows)},
        "champion_lineage": nested, "literal_registry_witness": witness,
        "dense_probability_witness": dense,
    }
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result, witness


if __name__ == "__main__":
    result, witness = portfolio()
    print(f"[audit] {len(result['sites'])} historical rasters; no new candidate generated")
    print(f"[audit] lattice footprint={witness['footprint_pixels']}, uncovered={witness['outside_3px_pixels']}; "
          f"minimum overlap at {witness['example_budget_distinct_dots']} dots={witness['minimum_possible_overlap_at_example_budget']:.6f}")
    print(f"[audit] champion lineage: {result['champion_lineage']}")
