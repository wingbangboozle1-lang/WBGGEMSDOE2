#!/usr/bin/env python3
"""Restore immutable, publicly mirrored inputs and reference rasters via gh.

The bridge is hash-pinned but is NOT an organizer-authenticated data source.
No credentials are requested or stored.  Data stay in .cache/, not in Git.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "data"
BRIDGE_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
# All pins are byte hashes copied from existing, explicitly unofficial mirror receipts.
CORE = [
    ("buffedlizard55-lab/GEMSDOE24", BRIDGE_REF, "data/bridge/labels.tif", "labels.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    ("buffedlizard55-lab/GEMSDOE24", BRIDGE_REF, "data/bridge/sample_submission.tif", "sample_submission.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    ("buffedlizard55-lab/GEMSDOE24", BRIDGE_REF, "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"),
]


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def blob_digest(path: Path) -> str:
    h = hashlib.sha1()
    h.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, source: str, dest: Path, expected: str, kind="sha256") -> dict:
    check = digest if kind == "sha256" else blob_digest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or check(dest) != expected:
        temp = dest.with_name(dest.name + ".partial")
        try:
            with temp.open("wb") as out:
                proc = subprocess.run(["gh", "api", f"repos/{repo}/contents/{source}?ref={ref}",
                                       "-H", "Accept: application/vnd.github.raw+json"],
                                      stdout=out, stderr=subprocess.PIPE, timeout=180)
            if proc.returncode:
                raise RuntimeError(f"fetch failed for {repo}/{source}: {proc.stderr.decode(errors='replace')[:400]}")
            if check(temp) != expected:
                raise ValueError(f"pin mismatch for {repo}/{source}; refusing unverified bytes")
            os.replace(temp, dest)
        finally:
            temp.unlink(missing_ok=True)
    return {"source_repo": repo, "ref": ref, "source_path": source,
            "local": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size,
            "sha256": digest(dest), "git_blob_sha1": blob_digest(dest)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true")
    args = parser.parse_args()
    rows = [(r, ref, path, CACHE / name, sha, "sha256") for r, ref, path, name, sha in CORE]
    rows.append(("buffedlizard55-lab/17GEMSDOE", "6fc71d19d49dca4960d5434bd81b6dd06fcc030a",
                 "docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
                 CACHE / "17gems-e-proba.tif", "374c88b1da2b803e2ed160de467fd71ae114010d", "blob"))
    if not args.core_only:
        data = json.loads((ROOT / "data/focus_sources.json").read_text())
        for s in data["sites"]:
            rows.append((f"{data['owner']}/{s['site']}", s["ref"], s["path"],
                         ROOT / ".cache/portfolio" / f"{s['site']}.tif", s["blob_sha"], "blob"))
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts = list(pool.map(lambda row: fetch(*row), rows))
    except (ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"INPUT RESTORE FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"provenance": "owner-hosted mirror; not an organizer receipt", "files": receipts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
