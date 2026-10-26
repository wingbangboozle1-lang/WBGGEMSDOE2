#!/usr/bin/env python3
"""Restore the owner's pinned mirror and invoke the unmodified shared cache builder.

The live organizer download requires DrivenData authentication. These public GitHub
mirror bytes are hash-verified against an owner-published manifest, NOT authenticated
as organizer downloads. This script does not spend a competition submission slot.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".cache" / "template"
PINS = ROOT / "registry" / "template_pins.json"
PREPARE_SHA = "73c743e8ab7238b44ce82b9a8d4f9c7a17312fc023ee894ebd0e3788a456d7d6"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_checked(repo: str, ref: str, remote: str, path: Path, expected: str) -> None:
    if path.is_file() and digest(path) == expected:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    try:
        with partial.open("wb") as out:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{remote}?ref={ref}",
                 "-H", "Accept: application/vnd.github.raw+json"],
                stdout=out, stderr=subprocess.PIPE, timeout=180, check=False,
            )
        if result.returncode:
            raise RuntimeError(f"GitHub fetch failed for {remote}: "
                               f"{result.stderr.decode(errors='replace')[:300]}")
        actual = digest(partial)
        if actual != expected:
            raise ValueError(f"Hash mismatch for {remote}: {actual} != {expected}")
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)


def restore_template(fetch: bool) -> Path:
    """Fetch unchanged upstream files to an ignored cache, never a private fork."""
    pins = json.loads(PINS.read_text())
    repo, ref = pins["repository"], pins["ref"]
    if (repo, ref) != ("buffedlizard55-lab/57GEMSDOE",
                        "822a0ce5546c7b6749cdd82eb145b6b3e616603d"):
        raise ValueError("Unexpected shared template identity")
    rows = [(r["upstream_path"], TEMPLATE / r["upstream_path"], r["sha256"])
            for r in pins["files"] if r["upstream_path"].startswith("src/gems57/")]
    rows.append(("scripts/prepare_data.py", TEMPLATE / "scripts/prepare_data.py", PREPARE_SHA))
    # Verify every entry, including files previously cached. Network access is optional
    # after the first restore, and failures cannot silently change the pinned bytes.
    def one(row):
        remote, path, expected = row
        if fetch:
            fetch_checked(repo, ref, remote, path, expected)
        elif not path.is_file() or digest(path) != expected:
            raise FileNotFoundError(f"Missing or changed template file: {path}; use --fetch")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(one, rows))
    return TEMPLATE / "scripts/prepare_data.py"


def load_builder(path: Path):
    spec = importlib.util.spec_from_file_location("pinned_shared_prepare", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load pinned shared preparation code")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="fetch pinned template and mirror files")
    parser.add_argument("--cache-bands", action="store_true", help="run upstream band cache builder")
    args = parser.parse_args()
    try:
        prepare = load_builder(restore_template(args.fetch))
        file_sources = {
            "labels.tif": "existing_faults.tif",
            "existing_faults.tif": "existing_faults.tif",
            "sample_submission.tif": "example_submission.tif",
        }
        root = ROOT / "data" / "official"
        root.mkdir(parents=True, exist_ok=True)
        for dest, src in file_sources.items():
            path = root / dest
            expected = prepare.PIN[f"data/official/{dest}"]
            if args.fetch:
                prepare.fetch_raw(prepare.BRIDGE_REPO, f"data/bridge/{src}",
                                  prepare.BRIDGE_COMMIT, path, expected)
            if not path.is_file() or digest(path) != expected:
                raise FileNotFoundError(f"Missing or changed mirror file: {path}; use --fetch")
            print(f"[data] verified {path.relative_to(ROOT)}", flush=True)
        feature = root / "training_features.tif"
        expected_feature = prepare.PIN["data/official/training_features.tif"]
        if not feature.is_file() or digest(feature) != expected_feature:
            if not args.fetch:
                raise FileNotFoundError("Feature stack missing or changed; use --fetch")
            print("[data] restoring five pinned feature-stack parts", flush=True)
            prepare.assemble_features(ROOT)
        if digest(feature) != expected_feature:
            raise ValueError("Feature stack hash mismatch")
        print(f"[data] verified {feature.relative_to(ROOT)}", flush=True)
        if args.cache_bands:
            print("[data] invoking upstream cache_bands, label-derived geometry excluded", flush=True)
            report = prepare.cache_bands(ROOT)
            print(f"[data] cached {report['count']} feature bands", flush=True)
        receipt = {
            "evidence_class": "DATA-MEASUREMENT",
            "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "origin": "Owner-published mirror; not an authenticated DrivenData download",
            "template_repository": "buffedlizard55-lab/57GEMSDOE",
            "template_commit": "822a0ce5546c7b6749cdd82eb145b6b3e616603d",
            "files": [
                {"path": f"data/official/{name}", "sha256": digest(root / name),
                 "bytes": (root / name).stat().st_size}
                for name in ["labels.tif", "existing_faults.tif", "sample_submission.tif", "training_features.tif"]
            ],
            "band_cache_built": args.cache_bands,
            "authenticated_organizer_copy": False,
        }
        (ROOT / "evidence").mkdir(exist_ok=True)
        (ROOT / "evidence" / "data_preparation.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"[data] STOP: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
