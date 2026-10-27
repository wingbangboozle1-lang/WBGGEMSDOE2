#!/usr/bin/env python3
"""Fail-closed pre-placement and final-dot novelty checks; never approves upload.

Preview dots represent a proposed selection, not a submitted TIFF. A known
witness is enough to STOP. A partial/stale inventory can never establish a
pass, even when no witness is found. This script never generates predictions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.novelty import coverage, overlap_fraction, spearman_footprint
from wbggems.validate import sha256, inspect_tif
from restore_public_mirrors import verified


def _read_grid(path, ref_grid, footprint):
    with rasterio.open(path) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != ref_grid:
            raise ValueError(f"{path} is not a single-band raster on the reference grid")
        data = src.read(1)
        if np.any(src.read_masks(1)[footprint] == 0):
            raise ValueError(f"{path} has masked/nodata cells inside the reference footprint")
        return data


def stage(surface, dots, footprint, registry):
    surface, dots, footprint = np.asarray(surface), np.asarray(dots), np.asarray(footprint)
    if (surface.ndim != 2 or dots.shape != surface.shape or footprint.shape != surface.shape
            or dots.dtype != np.bool_ or footprint.dtype != np.bool_):
        raise ValueError("surface, boolean selection and boolean footprint must share a 2-D grid")
    if np.any(dots & ~footprint) or not dots.any():
        raise ValueError("selection must have nonempty support within the footprint")
    if not np.isfinite(surface[footprint]).all():
        raise ValueError("surface must be finite within the footprint")
    checked = 0
    for ident, reference in registry:
        checked += 1
        inside = reference[footprint]
        if not np.isfinite(inside).all() or np.any((inside < 0) | (inside > 1)):
            raise ValueError(f"invalid registry raster: {ident}")
        mask = np.isfinite(reference) & (reference > 0) & footprint
        overlap = overlap_fraction(dots, coverage(mask, 3))
        # Stop on the first decisive witness; do not continue to placement.
        if overlap > .70:
            return {"status": "duplicate-stop", "witness": ident, "overlap_3px": overlap,
                    "spearman": None, "reason": "overlap exceeds 70%"}
        rho = spearman_footprint(surface, reference, footprint)
        if abs(rho) > .90:
            return {"status": "duplicate-stop", "witness": ident, "overlap_3px": overlap,
                    "spearman": rho, "reason": "absolute rank correlation exceeds 0.90"}
    return {"status": "no-witness-in-scope", "registry_rasters_checked": checked}


def run(surface_path, preview_path, final_path, ref_path, manifest_path, data_dir):
    manifest = json.loads(Path(manifest_path).read_text())
    # Until registry enumeration, hashes, and freshness can be independently
    # established, no caller can override the incomplete-inventory block.
    inventory_complete = False
    with rasterio.open(ref_path) as src:
        if src.count != 1:
            raise ValueError("reference must contain one band")
        ref_grid = (src.shape, src.crs, src.transform)
        footprint = np.isfinite(src.read(1)) & (src.read_masks(1) > 0)
    surface = _read_grid(surface_path, ref_grid, footprint)
    if (not np.isfinite(surface[footprint]).all()
            or np.any((surface[footprint] < 0) | (surface[footprint] > 1))):
        raise ValueError("pre-placement surface must be finite and in [0,1] inside the footprint")
    entries = sorted(manifest["inputs"], key=lambda e: e["id"] != "13GEMSDOE")
    ids = [e["id"] for e in entries]
    if (not ids or any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError("registry IDs must be nonempty, unique, and safe file names")

    def registry():
        # Stream witnesses: a conclusive early STOP does not depend on opening
        # later files, but absence/invalidity can never become a passing result.
        for entry in entries:
            path = Path(data_dir) / "registry" / (entry["id"] + ".tif")
            if not verified(path, entry["bytes"], sha256=entry["sha256"], blob=entry["git_blob"]):
                raise ValueError(f"missing or invalid registered raster {entry['id']}")
            yield entry["id"], _read_grid(path, ref_grid, footprint)

    # The shared literal support definition is finite >0. Compare the actual
    # surface BEFORE opening any preview or final-dot file, not merely a selected
    # subset of the surface. A soft prior can therefore be a universal witness;
    # its interpretation remains an explicit policy ambiguity, not an exemption.
    surface_support = np.isfinite(surface) & (surface > 0) & footprint
    pre = stage(surface, surface_support, footprint, registry())
    pre["phase"] = "surface-before-placement"
    result = {"schema": "wbggems.candidate-check.v2", "surface_sha256": sha256(surface_path),
              "preview_sha256": None, "pre_placement": pre, "preview": {"status": "not-run"},
              "final": {"status": "not-run"}, "inventory_complete": inventory_complete,
              "ok_to_emit": False, "ok_to_submit": False,
              "note": "No local format or novelty check alone authorizes a weekly slot."}
    if pre["status"] == "duplicate-stop":
        return result
    # No witness in a partial list is not a pre-placement pass. Do not open a
    # preview or final file until every registered raster has been accounted for.
    if not inventory_complete:
        result["preview"] = {"status": "blocked-incomplete-registry"}
        result["final"] = {"status": "blocked-incomplete-registry"}
        return result
    preview = _read_grid(preview_path, ref_grid, footprint)
    if not np.isfinite(preview[footprint]).all() or not np.all((preview[footprint] == 0) | (preview[footprint] == 1)):
        raise ValueError("preview must be binary and finite inside the footprint")
    result["preview_sha256"] = sha256(preview_path)
    result["preview"] = stage(surface, np.isfinite(preview) & (preview > 0), footprint, registry())
    if result["preview"]["status"] == "duplicate-stop":
        return result
    if final_path is not None:  # Reserved for a future complete, authenticated inventory.
        validation = inspect_tif(final_path, ref_path, strict_all_finite=True)
        if not validation["format_valid_against_reference"]:
            result["final"] = {"status": "format-fail", "validator": validation}
            return result
        final = _read_grid(final_path, ref_grid, footprint)
        result["final"] = stage(final, np.isfinite(final) & (final > 0), footprint, registry())
        result["final"]["validator"] = validation
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--surface', type=Path, required=True)
    p.add_argument('--preview', type=Path, required=True)
    p.add_argument('--final', type=Path)
    p.add_argument('--reference', type=Path, default=ROOT / 'data/reference_grid_mirror.tif')
    p.add_argument('--manifest', type=Path, default=ROOT / 'config/registry_inputs.json')
    p.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    args = p.parse_args()
    try:
        result = run(args.surface, args.preview, args.final, args.reference, args.manifest, args.data_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {'schema': 'wbggems.candidate-check.v1', 'pre_placement': {'status': 'error', 'message': str(exc)},
                  'final': {'status': 'not-run'}, 'ok_to_emit': False, 'ok_to_submit': False}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if not result['ok_to_emit'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
