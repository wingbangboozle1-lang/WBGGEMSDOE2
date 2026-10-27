#!/usr/bin/env python3
"""Independently re-open existing research TIFFs; never generate or approve one.

This is a forensic audit of files already in the checkout, NOT a candidate
experiment or an original surface preflight. One verified duplicate witness is
sufficient to reject a file; an incomplete witness inventory cannot certify a
pass. No reference, including a lattice or a continuous prior, is exempted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.novelty import coverage, overlap_fraction
from wbggems.release import research_inventory
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import SMALL, verified


SCHEMA = "wbggems.release-audit.v1"


def owned_tifs(root: Path) -> list[Path]:
    return [root / rel for rel in sorted(research_inventory(root, (".tif", ".tiff")))]


def run(root: Path = ROOT, data_dir: Path | None = None) -> dict:
    root = Path(root).resolve()
    data_dir = Path(data_dir) if data_dir else root / "data"
    manifest_path = root / "config/registry_inputs.json"
    manifest = json.loads(manifest_path.read_text())
    sample = data_dir / "reference_grid_mirror.tif"
    blob, size, expected = SMALL[sample.name]
    if not verified(sample, size, blob=blob, sha256=expected):
        raise ValueError("Missing/hash-mismatched owner-mirror reference; run audit_registry.py --fetch")
    with rasterio.open(sample) as ds:
        fp = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    if not fp.any():
        raise ValueError("Empty reference footprint")

    # Independent of former approvals, hashes are measured from the bytes now.
    by_hash: dict[str, dict] = {}
    for p in owned_tifs(root):
        if p.is_symlink():
            raise ValueError(f"Research artifact must not be a symlink: {p}")
        digest = sha256(p)
        if digest in by_hash:
            by_hash[digest]["aliases"].append(p.relative_to(root).as_posix())
            continue
        local = inspect_tif(p, sample)
        strict = inspect_tif(p, sample, strict_all_finite=True)
        with rasterio.open(p) as ds:
            if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != grid:
                raise ValueError(f"Cannot compare an artifact on a different grid: {p}")
            a = ds.read(1)
        support = fp & np.isfinite(a) & (a > 0)
        if not support.any():
            raise ValueError(f"Empty research artifact: {p}")
        by_hash[digest] = {
            "research_name": p.stem, "path": p.relative_to(root).as_posix(),
            "aliases": [p.relative_to(root).as_posix()], "sha256": digest,
            "bytes": p.stat().st_size, "positive_support_cells": int(support.sum()),
            "binary_inside_footprint": bool(np.isin(a[fp], [0., 1.]).all()),
            "validator": local, "strict_all_finite_validator": strict,
            "comparisons": [], "original_surface_preflight": "NOT REPLAYED; original continuous surfaces unavailable",
            "surface_rank_correlation": None, "final_rank_correlation": None,
            "rank_status": "Not needed for rejection: a decisive final-support overlap witness is sufficient",
            "leaderboard_score_estimate": None, "organizer_receipt": None,
            "ok_to_download_for_research": True, "ok_to_submit": False,
            "verdict": "negative", "_support": support,
        }

    if not by_hash:
        raise ValueError("No existing research TIFFs to audit")
    witnessed = set()
    for entry in manifest["inputs"]:
        p = data_dir / "registry" / (entry["id"] + ".tif")
        if not verified(p, entry["bytes"], blob=entry["git_blob"], sha256=entry["sha256"]):
            raise ValueError(f"Missing/hash-mismatched registry witness: {entry['id']}")
        with rasterio.open(p) as ds:
            if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != grid:
                raise ValueError(f"Registry grid mismatch: {entry['id']}")
            values = ds.read(1)
            if np.any(ds.read_masks(1)[fp] == 0):
                raise ValueError(f"Masked interior registry cells: {entry['id']}")
        if not np.isfinite(values[fp]).all() or np.any((values[fp] < 0) | (values[fp] > 1)):
            raise ValueError(f"Invalid in-footprint registry values: {entry['id']}")
        sup = fp & (values > 0)
        near = coverage(sup, 3.)
        for row in by_hash.values():
            fraction = overlap_fraction(row["_support"], near)
            row["comparisons"].append({
                "registry_id": entry["id"], "sha256": entry["sha256"],
                "support_type": entry.get("support_type", "binary_dots"),
                "source": entry["url"], "overlap_3px": fraction,
                "duplicate_stop": fraction > .70,
                "is_focus_champion": entry["user_reported_claim"] is not None,
                "exact_file_hash_match": row["sha256"] == entry["sha256"],
            })
        witnessed.add(entry["id"])
    if not {"13GEMSDOE", "17GEMSDOE_dense_prior"} <= witnessed:
        raise ValueError("Required literal-rule witnesses missing from inventory")

    rows = []
    for row in by_hash.values():
        del row["_support"]
        fails = [r for r in row["comparisons"] if r["duplicate_stop"]]
        if not fails:
            # A future different raster must not inherit this static negative narrative.
            raise ValueError("No decisive overlap witness; investigate without claiming a registry pass")
        row["duplicate_witnesses"] = [r["registry_id"] for r in fails]
        row["maximum_overlap_3px"] = max(r["overlap_3px"] for r in row["comparisons"])
        row["focus_maximum_overlap_3px"] = max(r["overlap_3px"] for r in row["comparisons"] if r["is_focus_champion"])
        row["lattice_overlap_3px"] = next(r["overlap_3px"] for r in row["comparisons"] if r["registry_id"] == "13GEMSDOE")
        row["reasons"] = ["Literal >70% overlap duplicate stop", "Original surface preflight not replayed",
                          "Current exhaustive registry not established", "Explicit method lane unassigned",
                          "Organizer reference authentication absent", "No separate slot-selector authorization"]
        for report_key in ("validator", "strict_all_finite_validator"):
            # Relative paths make the saved receipt portable and auditable in CI.
            row[report_key]["path"] = row["path"]
        rows.append(row)

    zip_rows = []
    for p in (root / rel for rel in sorted(research_inventory(root, (".zip",)))):
        if p.is_symlink():
            raise ValueError(f"Research ZIP must not be a symlink: {p}")
        with zipfile.ZipFile(p) as z:
            members = z.infolist()
            if len(members) != 1 or members[0].is_dir() or Path(members[0].filename).name != members[0].filename:
                raise ValueError(f"ZIP must contain exactly one plain TIFF filename: {p}")
            import hashlib
            name = members[0].filename
            digest = hashlib.sha256(z.read(name)).hexdigest()
            if Path(name).suffix.lower() not in (".tif", ".tiff") or digest not in by_hash:
                raise ValueError(f"ZIP member is not an audited TIFF: {p}")
            zip_rows.append({"path": p.relative_to(root).as_posix(), "sha256": sha256(p),
                             "member": name, "member_sha256": digest, "ok_to_submit": False})

    return {
        "schema": SCHEMA, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "BYTE-LEVEL-FORENSIC-MEASUREMENT; NOT A CANDIDATE EXPERIMENT",
        "reference": {"sha256": expected, "provenance": "hash-pinned owner mirror; not organizer-authenticated",
                      "footprint_cells": int(fp.sum()), "grid": {"shape": list(grid[0]), "crs": str(grid[1]), "transform": list(grid[2])[:6]}},
        "policy": {"radius_px": 3, "overlap_stop_strictly_greater_than": .70,
                   "absolute_rank_stop_strictly_greater_than": .90, "witness_exemptions": [],
                   "continuous_prior_caveat": "Literal finite-positive support is enforced; whether a continuous prior should count as dots remains unresolved, not exempted."},
        "scope": {"registry_rasters_opened": len(witnessed), "all_current_registry_rasters_checked": False,
                  "registry_manifest_sha256": sha256(manifest_path), "owned_tif_paths": len(owned_tifs(root)),
                  "distinct_tif_sha256": len(rows), "new_candidate_experiments": 0, "weekly_slots_used": 0,
                  "note": "Already-existing artifacts only. Continued forensic comparisons after a witness do not constitute candidate placement or promotion."},
        "artifacts": rows, "zip_archives": zip_rows,
        "approved_submission": None, "leaderboard_score_estimate": None,
        "ok_to_submit": False, "verdict": "negative",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "evidence/release_audit.json")
    args = p.parse_args()
    try:
        result = run()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_suffix(".partial")
        temp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        temp.replace(args.output)
        print(json.dumps({"output": str(args.output), "scope": result["scope"],
                          "artifacts": [{"name": a["research_name"], "lattice_overlap": a["lattice_overlap_3px"],
                                         "strict_range_format_ok": a["strict_all_finite_validator"]["format_valid_against_reference"],
                                         "ok_to_submit": False} for a in result["artifacts"]]}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError, zipfile.BadZipFile) as exc:
        print(f"Release audit STOP: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
