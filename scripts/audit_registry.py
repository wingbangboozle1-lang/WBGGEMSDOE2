#!/usr/bin/env python3
"""Reproduce the pinned historical-byte, lattice and lineage audit.

This finite witness inventory is intentionally incomplete. It can disprove
uniqueness, but it can never prove a prospective candidate globally unique.
No geological candidate, holdout score or TIFF is produced by this script.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.novelty import capacity_bound, coverage, overlap_fraction
from wbggems.validate import inspect_tif
from restore_public_mirrors import fetch_blob, verified, SMALL


def run(manifest_path, data_dir, fetch=False, budget=37_654):
    manifest = json.loads(Path(manifest_path).read_text())
    ref = data_dir / "reference_grid_mirror.tif"
    faults = data_dir / "existing_faults_mirror.tif"
    for name, path in (("reference_grid_mirror.tif", ref), ("existing_faults_mirror.tif", faults)):
        blob, size, digest = SMALL[name]
        if not verified(path, size, blob=blob, sha256=digest):
            if not fetch:
                raise FileNotFoundError(f"Missing/invalid {path}; run restore_public_mirrors.py --small-only")
            fetch_blob("buffedlizard55-lab/GEMSDOE", blob, size, path, sha256=digest)
    with rasterio.open(ref) as src:
        sample = src.read(1)
        fp = np.isfinite(sample) & (src.read_masks(1) > 0)
        sample_positive = fp & (sample > 0)
        ref_grid = (src.shape, src.crs, src.transform)
    with rasterio.open(faults) as src:
        if (src.shape, src.crs, src.transform) != ref_grid:
            raise ValueError("fault mirror does not match the reference mirror")
        catalogue = fp & (src.read(1) == 1)
    cat_distance = distance_transform_edt(~catalogue)
    masks, per_item = {}, {}
    registry_dir = data_dir / "registry"
    for entry in manifest["inputs"]:
        target = registry_dir / (entry["id"] + ".tif")
        if not verified(target, entry["bytes"], blob=entry["git_blob"], sha256=entry["sha256"]):
            if not fetch:
                raise FileNotFoundError(f"Missing/invalid {target}; rerun with --fetch")
            fetch_blob(entry["repo"], entry["git_blob"], entry["bytes"], target, sha256=entry["sha256"])
        info = inspect_tif(target, ref)
        if not info["format_valid_against_reference"]:
            raise ValueError(f"Cannot audit invalid reference raster {entry['id']}: {info['failures']}")
        with rasterio.open(target) as src:
            a = src.read(1)
            inside = a[fp]
            binary = bool(np.all((inside == 0) | (inside == 1)))
            support_type = entry.get("support_type", "binary_dots")
            if support_type not in {"binary_dots", "continuous_probability"}:
                raise ValueError(f"Unknown support type for {entry['id']}")
            if support_type == "binary_dots" and not binary:
                raise ValueError(f"{entry['id']} is not binary; positive support is not a set of dots")
            dots = np.isfinite(a) & (a > 0) & fp
        if not dots.any():
            raise ValueError(f"{entry['id']} has no dots")
        masks[entry["id"]] = dots
        per_item[entry["id"]] = {
            "sha256": entry["sha256"], "source": entry["url"],
            "dots": int(dots.sum()) if support_type == "binary_dots" else None,
            "positive_support_cells": int(dots.sum()), "support_type": support_type, "binary_in_footprint": binary,
            "format_valid_against_mirror": info["format_valid_against_reference"],
            "all_finite": info["all_finite"], "catalogue_exact_overlap": int((dots & catalogue).sum()),
            "within_2px_catalogue": int((dots & (cat_distance <= 2)).sum()),
            "user_reported_claim": entry["user_reported_claim"],
            "claim_evidence": entry["claim_evidence"],
        }
    lattice = masks["13GEMSDOE"]
    covered = coverage(lattice, 3)
    uncovered = fp & ~covered
    cap = capacity_bound(fp, covered, budget)
    for key, dots in masks.items():
        if key != "13GEMSDOE":
            per_item[key]["fraction_within_3px_of_lattice"] = overlap_fraction(dots, covered)
            per_item[key]["literal_lattice_duplicate"] = per_item[key]["fraction_within_3px_of_lattice"] > 0.70
    # Pairwise comparison of the nine named files only, directed candidate -> peer.
    focus = [entry["id"] for entry in manifest["inputs"] if entry["user_reported_claim"] is not None]
    for key in focus:
        per_item[key]["max_focus_peer_overlap_3px"] = {"peer": None, "fraction": 0.0}
    for ref_id in focus:
        peers_covered = coverage(masks[ref_id], 3)
        for cand_id in focus:
            if cand_id == ref_id:
                continue
            overlap = overlap_fraction(masks[cand_id], peers_covered)
            if overlap > per_item[cand_id]["max_focus_peer_overlap_3px"]["fraction"]:
                per_item[cand_id]["max_focus_peer_overlap_3px"] = {"peer": ref_id, "fraction": overlap}
    edge_distance = distance_transform_edt(fp)
    max_edge_distance = float(edge_distance[uncovered].max()) if uncovered.any() else 0.0
    uncovered_near_edge = int((uncovered & (edge_distance <= 3)).sum())
    result = {
        "schema": "wbggems.registry-audit.v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": manifest["scope"] + " A failed witness is conclusive for this rule; no comprehensive uniqueness pass is claimed.",
        "radius_px": 3, "distance_rule": "Euclidean distance <= 3 pixels", "overlap_limit": 0.70,
        "reference_is_authenticated_organizer_file": False,
        "reference_sample_equals_catalogue_positives": bool(np.array_equal(sample_positive, catalogue)),
        "catalogue_positives": int(catalogue.sum()),
        "lattice_capacity": {**asdict(cap), "fraction_footprint_covered": cap.covered_cells / cap.footprint_cells,
                             "max_uncovered_distance_to_footprint_exterior_px": max_edge_distance,
                             "uncovered_within_3px_of_footprint_exterior": uncovered_near_edge,
                             "largest_budget_with_possible_overlap_at_most_limit": (cap.uncovered_cells * 10) // 3},
        "lineage": {
            "GEMSDOE25_and_30_identical_in_footprint": bool(np.array_equal(masks["GEMSDOE25"], masks["GEMSDOE30"])),
            "GEMSDOE32_equals_GEMSDOE25_pruned_at_2px": bool(np.array_equal(masks["GEMSDOE32"], masks["GEMSDOE25"] & (cat_distance > 2))),
            "GEMSDOE36_additions_to_32": int((masks["GEMSDOE36"] & ~masks["GEMSDOE32"]).sum()),
            "GEMSDOE36_removals_from_32": int((masks["GEMSDOE32"] & ~masks["GEMSDOE36"]).sum()),
        },
        "dense_probability_prior": {
            "id": "17GEMSDOE_dense_prior", "positive_footprint_cells": int((masks["17GEMSDOE_dense_prior"] & fp).sum()),
            "footprint_cells": int(fp.sum()),
            "full_footprint_positive": bool(np.array_equal(masks["17GEMSDOE_dense_prior"], fp)),
            "definition": "The shared literal gate treats every finite value > 0 as support; this is a continuous prior, not a dotted submission.",
            "implication": "If that definition applies to continuous registry rasters, every nonempty candidate overlaps this prior by 100%; whether it should count as dots requires policy clarification.",
        },
        "surface_rank_correlation": "not evaluated: the original pre-placement surfaces are unavailable",
        "items": per_item,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/registry_inputs.json")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--fetch", action="store_true", help="download and hash-check missing public research rasters with gh")
    parser.add_argument("--budget", type=int, default=37_654)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/registry_audit.json")
    args = parser.parse_args()
    try:
        result = run(args.manifest, args.data_dir, args.fetch, args.budget)
    except (OSError, ValueError) as exc:
        print(f"Audit failed closed: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "lattice_capacity": result["lattice_capacity"],
                      "lineage": result["lineage"], "sample_equals_catalogue": result["reference_sample_equals_catalogue_positives"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
