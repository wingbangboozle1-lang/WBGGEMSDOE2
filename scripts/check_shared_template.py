#!/usr/bin/env python3
"""Demonstrate a pinned upstream novelty-grid defect on synthetic data only.

Imports the shared file byte-for-byte; does not maintain a private fork or change it.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from audit_registry import restore, sha256

ROOT = Path(__file__).resolve().parents[1]
ITEM = {
    "url": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/src/gems/novelty.py",
    "sha256": "0bfd40199fb00041446eb70368dbb7023f681a260073b41478629cbdc23d26c9",
    "local": "upstream/novelty.py",
}


def diagnose(module_path: Path) -> dict:
    if sha256(module_path) != ITEM["sha256"]:
        raise ValueError("Shared source hash does not match the pin")
    spec = importlib.util.spec_from_file_location("shared_novelty", module_path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load pinned source")
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    footprint = np.ones((6, 6), bool)
    pixels = np.zeros((6, 6), np.float32)
    pixels[1, 1] = 1
    surface = np.arange(36, dtype=np.float32).reshape(6, 6)
    with tempfile.TemporaryDirectory(prefix="gems-grid-test-") as directory:
        directory = Path(directory)
        path = directory / "misaligned.tif"
        with rasterio.open(path, "w", driver="GTiff", height=6, width=6, count=1,
                           dtype="float32", crs="EPSG:4326", transform=from_origin(1, 1, 1, 1)) as ds:
            ds.write(pixels, 1)
        content = hashlib.sha256(np.asarray(pixels[footprint], dtype="<f4").tobytes()).hexdigest()
        result = shared.compare_registry(surface, footprint,
            [{"id": "wrong-grid", "file": path.name, "cache_path": path.name, "footprint_sha256": content}], directory)
    return {
        "schema": "wbggems.shared-template-diagnostic.v1",
        "source": ITEM["url"], "source_sha256": ITEM["sha256"],
        "comparison_grid": "Synthetic 6x6 array intended to represent an EPSG:32611 template",
        "registry_grid": "EPSG:4326 with an unrelated transform; same shape and value hash",
        "upstream_reported_passed": result["passed"],
        "finding": "The shared comparison accepts this misaligned raster instead of failing closed." if result["passed"] else "The synthetic test did not reproduce the expected defect; inspect upstream behavior.",
        "issue": "https://github.com/buffedlizard55-lab/GEMSDOE24/issues/59",
        "scope": "Synthetic test of pinned novelty.py only; not a candidate or full template audit.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--cache", type=Path, default=ROOT / ".work")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path = restore(ITEM, args.cache) if args.restore else args.cache / ITEM["local"]
    result = diagnose(path)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
