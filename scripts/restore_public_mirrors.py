#!/usr/bin/env python3
"""Restore and hash-check the public owner mirror; no credentials are stored.

The mirror is NOT an authenticated DrivenData download.  See research/sources.md.
Large data are deliberately kept out of git.  Requires the GitHub CLI (gh).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = "buffedlizard55-lab/GEMSDOE"
MIRROR_COMMIT = "c0c06ac82178f26b94fce3397036ef8f12a2f3a0"
FEATURE_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
FEATURE_SIZE = 418_912_844
PARTS = [
    ("f34e5143d5e7c10014b5cfe01c85d01bcede4c0a", 94_371_840),
    ("4bd98099ae505f63cc6c3733954f259974efd290", 94_371_840),
    ("d6f883ba8822207ac2765445737ecd2ecdfd2914", 94_371_840),
    ("976977b4ac84c4c9b6fec72495c4e512341de872", 94_371_840),
    ("41a7bb7b7603c1e7669d8cc8405cfeb5efb5cf0c", 41_425_484),
]
SMALL = {
    "reference_grid_mirror.tif": ("7d865a9921a40ed2ea4c742a6a25b1fa2f357c5a", 1_599_597,
                                  "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "existing_faults_mirror.tif": ("4ad3c1f3f19823e40924589bee7e51e44ae3a2e7", 425_830,
                                    "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
}
CHUNK = 1 << 20


def file_hash(path: Path, algorithm: str = "sha256", *, git_blob: bool = False) -> str:
    h = hashlib.new(algorithm)
    if git_blob:
        h.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def verified(path: Path, size: int, *, sha256: str | None = None, blob: str | None = None) -> bool:
    if not path.is_file() or path.stat().st_size != size:
        return False
    return ((sha256 is None or file_hash(path) == sha256)
            and (blob is None or file_hash(path, "sha1", git_blob=True) == blob))


def fetch_blob(repo: str, blob: str, size: int, target: Path, *, sha256: str | None = None) -> None:
    if verified(target, size, sha256=sha256, blob=blob):
        print(f"Verified cached {target}", flush=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".partial")
    temporary.unlink(missing_ok=True)
    print(f"Fetching {repo} blob {blob} ({size:,} bytes)", flush=True)
    try:
        with temporary.open("wb") as out:
            subprocess.run(["gh", "api", f"repos/{repo}/git/blobs/{blob}",
                            "-H", "Accept: application/vnd.github.raw+json"],
                           stdout=out, check=True)
        if not verified(temporary, size, sha256=sha256, blob=blob):
            raise ValueError(f"Size or cryptographic hash mismatch: {temporary}")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def restore(destination: Path, *, small_only: bool = False) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, (blob, size, sha256) in SMALL.items():
        fetch_blob(REPO, blob, size, destination / name, sha256=sha256)
    if small_only:
        return
    output = destination / "training_features_mirror.tif"
    if verified(output, FEATURE_SIZE, sha256=FEATURE_SHA256):
        print(f"Verified cached {output}", flush=True)
        return
    parts_dir = destination / ".parts"
    parts_dir.mkdir(exist_ok=True)
    paths = []
    for i, (blob, size) in enumerate(PARTS):
        p = parts_dir / f"features.part-{i:03d}"
        fetch_blob(REPO, blob, size, p)
        paths.append(p)
    temp = destination / "training_features_mirror.tif.partial"
    try:
        with temp.open("wb") as out:
            for path in paths:
                with path.open("rb") as part:
                    while chunk := part.read(CHUNK):
                        out.write(chunk)
        if not verified(temp, FEATURE_SIZE, sha256=FEATURE_SHA256):
            raise ValueError("Assembled feature mirror did not match the published size and SHA-256")
        os.replace(temp, output)
    finally:
        temp.unlink(missing_ok=True)
    # Parts are reproducible and take as much space as the assembled raster.
    for path in paths:
        path.unlink()
    parts_dir.rmdir()
    print(f"Restored {output}; SHA-256 {FEATURE_SHA256}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("data"))
    parser.add_argument("--small-only", action="store_true", help="restore grid and catalogue only")
    args = parser.parse_args()
    try:
        restore(args.destination, small_only=args.small_only)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1
    print("Mirror integrity verified; organizer-origin/rights still require confirmation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
