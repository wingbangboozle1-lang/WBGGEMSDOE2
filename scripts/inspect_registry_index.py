#!/usr/bin/env python3
"""Inspect a pinned upstream registry *index*, not its raster bytes.

This documents how much larger the shared public inventory is than our witness
set. It never certifies uniqueness or treats the old index as exhaustive/current.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from prepare_data import ROOT, digest
from restore_public_mirrors import fetch_blob

REPO = "buffedlizard55-lab/57GEMSDOE"
COMMIT = "822a0ce5546c7b6749cdd82eb145b6b3e616603d"
PATH = "evidence/registry_refreshed.json"
BLOB = "866aeddbf9fe94beafa892fb5418024f4cca2181"
SHA256 = "846eddb9459f0e5b67f33da519bbd62c966bf5f539545ba3dad262fbfbc308c2"
SIZE = 339283
URL = f"https://github.com/{REPO}/blob/{COMMIT}/{PATH}"
DEFAULT_INDEX = ROOT / ".cache/shared-registry-index.json"


def summarize(index: dict, manifest: dict) -> dict:
    rows = index.get("rasters")
    inputs = manifest.get("inputs")
    if not isinstance(rows, list) or not rows or not isinstance(inputs, list) or not inputs:
        raise ValueError("index or witness list is missing")
    hashes = [r.get("sha256") for r in rows if isinstance(r, dict)]
    if len(hashes) != len(rows) or any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes):
        raise ValueError("index contains a missing or invalid raster SHA-256")
    if len(set(hashes)) != len(hashes):
        raise ValueError("upstream index contains duplicate raster SHA-256 rows")
    if index.get("n_unique_grid_rasters") != len(rows):
        raise ValueError("upstream declared raster count disagrees with index rows")
    names = [r.get("id") for r in inputs if isinstance(r, dict)]
    own_hashes = [r.get("sha256") for r in inputs if isinstance(r, dict)]
    if (len(names) != len(inputs) or len(set(names)) != len(names)
            or any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in own_hashes)):
        raise ValueError("invalid local witness manifest")
    known = set(hashes)
    local = set(own_hashes)
    return {
        "schema": "wbggems.shared-registry-index-summary.v1",
        "evidence_class": "PINNED-UPSTREAM-INDEX-METADATA; NOT RASTER VALIDATION",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": URL, "source_commit": COMMIT, "index_sha256": SHA256,
        "upstream_generated_utc": index.get("generated_utc"),
        "upstream_scope": index.get("scope"),
        "upstream_reported_complete_accessible_scan": index.get("complete_accessible_scan"),
        "upstream_reported_repositories": len(index.get("repos_scanned", [])),
        "upstream_reported_errors": len(index.get("errors", [])),
        "indexed_unique_sha256_rows": len(hashes),
        "local_witness_rows": len(inputs),
        "local_witness_ids_present_in_index": [r["id"] for r in inputs if r["sha256"] in known],
        "local_witness_ids_not_in_index": [r["id"] for r in inputs if r["sha256"] not in known],
        "indexed_hashes_absent_from_local_witness_manifest": len(known - local),
        "raster_bytes_opened_for_this_index_summary": 0,
        "current_complete_registry_established": False,
        "note": "Counts describe an old owner-published index only. No additional raster bytes were opened; private, missing, newer, and unlinked files can be absent. A witness can prove a duplicate but this index cannot approve uniqueness."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/registry_inputs.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/shared_registry_index_summary.json")
    args = parser.parse_args()
    try:
        if args.fetch:
            fetch_blob(REPO, BLOB, SIZE, args.index, sha256=SHA256)
        if not args.index.is_file() or args.index.stat().st_size != SIZE or digest(args.index) != SHA256:
            raise ValueError("pinned upstream index is missing or has changed; use --fetch")
        result = summarize(json.loads(args.index.read_text()), json.loads(args.manifest.read_text()))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"Registry-index inspection failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
