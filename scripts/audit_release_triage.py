#!/usr/bin/env python3
"""Recheck existing research TIFFs against a hash-pinned duplicate witness.

This is a forensic audit, not a geological experiment or a submission selector.
It never emits or changes a TIFF. One duplicate witness is sufficient to stop;
this small pinned registry cannot establish uniqueness. Reference and witness
are owner mirrors, not authenticated DrivenData inputs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.novelty import coverage, overlap_fraction
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import SMALL, fetch_blob, verified

# Exact bytes as recorded in the earlier independent reviews. These are already
# generated artifacts, not candidate methods authorized to run this session.
ARTIFACTS = (
    ("DZ-16", "docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif", "a9c46823cd6ef367726c1446581f0ccfc3d92456f8a242e521358ae84bd27912"),
    ("H3-PACK", "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif", "5b32ad6190957ac43b3d9069f99dc0742c776cd0b2f89af63666dd43672d4ac2"),
    ("MSPTCD", "docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif", "fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614"),
    ("STEPXASYM", "docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif", "592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33"),
    ("CONDUIT", "downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif", "95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad"),
)


def _ensure(path: Path, repo: str, blob: str, size: int, digest: str, fetch: bool) -> None:
    if verified(path, size, sha256=digest, blob=blob):
        return
    # Never replace mismatched data, including a dangling symlink: it may be an
    # authenticated organizer copy or a user's work, not our public mirror.
    if path.exists() or path.is_symlink():
        raise ValueError(f"Existing file failed pinned hash; refusing to replace {path}")
    if not fetch:
        raise FileNotFoundError(f"Missing pinned input {path}; use --fetch")
    fetch_blob(repo, blob, size, path, sha256=digest)
    if not verified(path, size, sha256=digest, blob=blob):
        raise ValueError(f"Fetched input failed verification: {path}")


def audit_one(path: Path, expected_sha: str, reference: Path, footprint: np.ndarray,
              witness_coverage: np.ndarray) -> dict:
    """Inspect exact saved bytes; stop on the binary lattice, not a soft prior."""
    if not path.is_file() or sha256(path) != expected_sha:
        raise ValueError(f"Artifact missing or hash mismatch: {path}")
    inspection = inspect_tif(path, reference, strict_all_finite=False)
    if not inspection["grid_match_reference"]:
        raise ValueError(f"Cannot compare non-matching grid: {path}")
    with rasterio.open(path) as dataset:
        values = dataset.read(1)
    positive = footprint & np.isfinite(values) & (values > 0)
    if not positive.any():
        raise ValueError(f"Cannot compare empty prediction: {path}")
    fraction = overlap_fraction(positive, witness_coverage)
    return {
        "sha256": expected_sha,
        "positive_footprint_cells": int(positive.sum()),
        "local_mirror_format": inspection,
        "preplacement_surface_rank_correlation": None,
        "preplacement_check": "NOT REPLAYED: the original surface and its ordering are not independently available",
        "final_dot_overlap_3px_vs_13GEMSDOE": fraction,
        "duplicate_witness": "13GEMSDOE" if fraction > 0.70 else None,
        "literal_witness_result": "duplicate-stop" if fraction > 0.70 else "no-witness-in-scope",
        "registry_complete": False,
        "ok_to_submit": False,
    }


def run(root: Path = ROOT, *, fetch: bool = False) -> dict:
    reference = root / "data/reference_grid_mirror.tif"
    blob, size, digest = SMALL["reference_grid_mirror.tif"]
    _ensure(reference, "buffedlizard55-lab/GEMSDOE", blob, size, digest, fetch)
    manifest = json.loads((root / "config/registry_inputs.json").read_text())
    witnesses = [item for item in manifest["inputs"] if item["id"] == "13GEMSDOE"]
    if len(witnesses) != 1:
        raise ValueError("Expected exactly one pinned 13GEMSDOE witness")
    item = witnesses[0]
    lattice = root / "data/registry/13GEMSDOE.tif"
    _ensure(lattice, item["repo"], item["git_blob"], item["bytes"], item["sha256"], fetch)
    with rasterio.open(reference) as dataset:
        footprint = np.isfinite(dataset.read(1)) & (dataset.read_masks(1) > 0)
        grid = (dataset.shape, dataset.crs, dataset.transform)
    with rasterio.open(lattice) as dataset:
        if (dataset.shape, dataset.crs, dataset.transform) != grid or dataset.count != 1:
            raise ValueError("Lattice must be a single band on the reference grid")
        if np.any(dataset.read_masks(1)[footprint] == 0):
            raise ValueError("Lattice has masked cells inside the reference footprint")
        values = dataset.read(1)
    inside = values[footprint]
    if not np.isfinite(inside).all() or not np.all((inside == 0) | (inside == 1)):
        raise ValueError("Lattice must be a finite binary witness on the footprint")
    witness_coverage = coverage(footprint & (values > 0), 3.0)
    records = []
    for name, relative_path, expected in ARTIFACTS:
        row = audit_one(root / relative_path, expected, reference, footprint, witness_coverage)
        row.update(name=name, path=relative_path)
        records.append(row)
    return {
        "schema": "wbggems.release-triage.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "LOCAL-BYTE-AND-WITNESS-MEASUREMENT",
        "reference": {"sha256": digest, "authenticated_organizer_copy": False,
                      "footprint_cells": int(footprint.sum())},
        "witness": {"id": item["id"], "sha256": item["sha256"], "source": item["url"],
                    "within_3px_footprint_cells": int((witness_coverage & footprint).sum()),
                    "distance": "Euclidean pixel centers, <= 3 pixels", "threshold": 0.70},
        "scope": "One pinned binary witness; no claim of complete or current registry coverage.",
        "records": records,
        "experiments_run_this_review": 0,
        "weekly_slots_used_this_review": 0,
        "approved_submission_file": None,
        "ok_to_submit": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="fetch missing pinned mirrors; never replace a mismatched file")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/release_triage_20261027.json")
    args = parser.parse_args()
    try:
        result = run(fetch=args.fetch)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
        # Do not present a partial result on error; replace only after all checks.
        temporary = args.output.with_suffix(args.output.suffix + ".partial")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(args.output)
        for row in result["records"]:
            print(f"{row['name']}: {row['literal_witness_result']}; lattice overlap={row['final_dot_overlap_3px_vs_13GEMSDOE']:.6f}; local format={row['local_mirror_format']['format_valid_against_reference']}; DO NOT SUBMIT")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Audit stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
