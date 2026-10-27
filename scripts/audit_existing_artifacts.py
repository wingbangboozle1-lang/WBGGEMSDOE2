#!/usr/bin/env python3
"""Recheck archived local TIFFs against two hash-pinned registry witnesses.

This is an investigative, stop-only audit. It does not create a prediction, use
an experiment slot, replay a pre-placement surface, prove uniqueness, or select
a submission. The reference grid is a third-party mirror, not authenticated
organizer data. Restore the small mirror and registry inputs with:

  python scripts/audit_registry.py --fetch --data-dir data/official_mirror
  python scripts/audit_existing_artifacts.py
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import SMALL, verified

ARTIFACTS = (
    ("DZ-16", "docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif", "a9c46823cd6ef367726c1446581f0ccfc3d92456f8a242e521358ae84bd27912"),
    ("H3-PACK", "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif", "5b32ad6190957ac43b3d9069f99dc0742c776cd0b2f89af63666dd43672d4ac2"),
    ("MSPTCD", "docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif", "fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614"),
    ("STEPXASYM", "docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif", "592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33"),
    ("CONDUIT", "downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif", "95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad"),
)
WITNESSES = ("13GEMSDOE", "17GEMSDOE_dense_prior")


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return x * x + y * y <= radius * radius


def fraction_near(support: np.ndarray, covered: np.ndarray) -> float:
    """Directed fraction of candidate positive cells within the witness halo."""
    if support.shape != covered.shape or not support.any():
        raise ValueError("candidate support must be nonempty and on the reference grid")
    return float(np.count_nonzero(support & covered) / np.count_nonzero(support))


def run(data_dir: Path, manifest_path: Path) -> dict:
    reference = data_dir / "reference_grid_mirror.tif"
    blob, size, expected = SMALL["reference_grid_mirror.tif"]
    if not verified(reference, size, blob=blob, sha256=expected):
        raise ValueError("reference grid mirror missing or hash-mismatched")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in manifest["inputs"]}
    with rasterio.open(reference) as ds:
        footprint = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    if not footprint.any():
        raise ValueError("empty reference footprint")
    covered = {}
    witness_info = {}
    for name in WITNESSES:
        e = entries[name]
        path = data_dir / "registry" / (name + ".tif")
        if not verified(path, e["bytes"], blob=e["git_blob"], sha256=e["sha256"]):
            raise ValueError(f"witness {name} missing or hash-mismatched")
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                raise ValueError(f"witness {name} grid mismatch")
            a = ds.read(1)
            support = footprint & np.isfinite(a) & (a > 0)
            if not support.any():
                raise ValueError(f"witness {name} has empty support")
            if name == "13GEMSDOE" and not np.all((a[footprint] == 0) | (a[footprint] == 1)):
                raise ValueError("lattice witness must be binary")
        covered[name] = ndi.binary_dilation(support, structure=disk(3))
        witness_info[name] = {
            "sha256": e["sha256"], "source": e["url"],
            "support_type": e.get("support_type", "binary_dots"),
            "positive_footprint_cells": int(support.sum()),
        }
    rows = []
    for name, relpath, expected_hash in ARTIFACTS:
        path = ROOT / relpath
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"archived artifact {name} missing or hash-mismatched")
        normal = inspect_tif(path, reference, strict_all_finite=False)
        strict = inspect_tif(path, reference, strict_all_finite=True)
        if not normal["grid_match_reference"] or normal["bands"] != 1:
            raise ValueError(f"archived artifact {name} grid/band mismatch; no overlap measured")
        normal["path"] = relpath  # portable audit receipt, never a host-specific absolute path
        with rasterio.open(path) as ds:
            a = ds.read(1)
        support = footprint & np.isfinite(a) & (a > 0)
        overlaps = {key: fraction_near(support, value) for key, value in covered.items()}
        rows.append({
            "name": name, "path": relpath, "sha256": expected_hash,
            "positive_footprint_cells": int(support.sum()),
            "format": normal, "strict_all_finite_format": strict["format_valid_against_reference"],
            "final_overlap_3px": overlaps,
            "literal_stop_witnesses": [key for key, value in overlaps.items() if value > 0.70],
            "preplacement_surface_checked": False,
            "final_spearman_checked": False,
            "complete_registry_checked": False,
            "ok_to_submit": False,
            "reason": "No pre-placement or complete-registry pass; stop on any literal witness above 70%. Local format is not organizer acceptance.",
        })
    return {
        "schema": "wbggems.archived-artifact-audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "MEASURED; owner-mirror research only, not an organizer receipt",
        "reference_sha256": expected,
        "reference_authenticated_by_organizer": False,
        "footprint_cells": int(footprint.sum()), "radius_px": 3, "overlap_limit": 0.70,
        "distance_rule": "Euclidean distance <= 3 pixels; candidate positive pixels are the denominator",
        "scope": "Two pinned witnesses only; useful to disprove uniqueness, never to certify a complete registry.",
        "continuous_prior_caveat": "A finite positive continuous probability field is counted as support by the shared literal tool; whether it should count as dots is unresolved and not exempted.",
        "witnesses": witness_info,
        "preplacement_surfaces_replayed": False,
        "artifacts": rows,
        "experiment_count": 0, "weekly_slots_used": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data/official_mirror")
    p.add_argument("--manifest", type=Path, default=ROOT / "config/registry_inputs.json")
    p.add_argument("--output", type=Path, default=ROOT / "evidence/local_artifact_audit_20261027.json")
    args = p.parse_args()
    try:
        report = run(args.data_dir, args.manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        for row in report["artifacts"]:
            print(f"{row['name']}: DO NOT SUBMIT; lattice={row['final_overlap_3px']['13GEMSDOE']:.6f}; "
                  f"dense={row['final_overlap_3px']['17GEMSDOE_dense_prior']:.6f}; "
                  f"masked_inside={row['format']['masked_inside']}")
        return 0
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        print(f"Audit failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
