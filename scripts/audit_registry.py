#!/usr/bin/env python3
"""Reproduce the pinned nine-site raster audit and literal-registry preflight.

This is a geometry/identity audit, not a model, metric, or submission writer.
It never creates a candidate TIFF, trains a model, or uploads to the competition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "focus-inputs.json"
GRID = {"shape": (3730, 3292), "crs": "EPSG:32611", "transform": (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)}
PLANNED_DOTS = 37_654


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def api_url(url: str) -> str:
    """Only immutable public GitHub content URLs are eligible for restoration."""
    parts = urllib.parse.urlparse(url)
    if parts.scheme != "https" or parts.netloc != "github.com" or parts.query or parts.fragment:
        raise ValueError("Expected an immutable GitHub blob URL")
    m = re.fullmatch(r"/([^/]+)/([^/]+)/blob/([a-f0-9]{40})/(.+)", parts.path)
    if not m or any(p in ("", ".", "..") for p in m.group(4).split("/")):
        raise ValueError("Expected an immutable 40-hex commit and a safe repository path")
    owner, repo, ref, path = m.groups()
    quoted = urllib.parse.quote(path, safe="/")
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{quoted}?ref={ref}"


def cache_path(cache: Path, name: str) -> Path:
    path = (cache / name).resolve()
    if not path.is_relative_to(cache.resolve()) or path == cache.resolve():
        raise ValueError("Cache path must stay inside cache directory")
    return path


def restore(item: dict, cache: Path) -> Path:
    path = cache_path(cache, item["local"])
    if path.is_file() and sha256(path) == item["sha256"]:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Accept": "application/vnd.github.raw", "User-Agent": "WBGGEMSDOE2-audit/1.0"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(api_url(item["url"]), headers=headers)
    # Download to the same filesystem; a failed/truncated response never replaces good bytes.
    fd, tmp = tempfile.mkstemp(prefix=".fetch-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as dest, urllib.request.urlopen(request, timeout=90) as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                dest.write(block)
        if sha256(Path(tmp)) != item["sha256"]:
            raise ValueError(f"SHA-256 mismatch while restoring {item['local']}")
        Path(tmp).replace(path)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return path


def verify_input(item: dict, cache: Path) -> Path:
    path = cache_path(cache, item["local"])
    if not path.is_file() or sha256(path) != item["sha256"]:
        raise ValueError(f"Missing or hash-mismatched input: {item['local']}; use --restore")
    return path


def overlap_bound(n_footprint: int, covered: int, dots: int, threshold: Fraction = Fraction(7, 10)) -> dict:
    """Exact pigeonhole lower bound; equality to the threshold is not failure."""
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (n_footprint, covered, dots)):
        raise ValueError("Counts must be integers")
    if not 0 <= covered <= n_footprint or not 1 <= dots <= n_footprint:
        raise ValueError("Counts must describe a non-empty footprint subset")
    if not isinstance(threshold, Fraction) or not 0 <= threshold < 1:
        raise ValueError("Threshold must be a Fraction in [0, 1)")
    uncovered = n_footprint - covered
    forced = max(0, dots - uncovered)
    bound = Fraction(forced, dots)
    first = int(Fraction(uncovered, 1) / (1 - threshold)) + 1
    return {
        "footprint_pixels": n_footprint,
        "covered_pixels": covered,
        "uncovered_pixels": uncovered,
        "candidate_distinct_dots": dots,
        "minimum_overlapping_dots": forced,
        "minimum_overlap_fraction": float(bound),
        "threshold_fraction": float(threshold),
        "guaranteed_duplicate": bound > threshold,
        "first_dot_count_forced_over_threshold": first if first <= n_footprint else None,
    }


def coverage(dots: np.ndarray, radius: int = 3) -> np.ndarray:
    if dots.ndim != 2 or dots.dtype != np.bool_ or radius < 0:
        raise ValueError("Expected a two-dimensional Boolean mask and nonnegative radius")
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return binary_dilation(dots, structure=(x * x + y * y <= radius * radius))


def read_aligned(path: Path, grid: dict) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        if (ds.count != 1 or ds.shape != grid["shape"] or str(ds.crs) != grid["crs"]
                or tuple(ds.transform)[:6] != grid["transform"]):
            raise ValueError(f"Grid/CRS/transform/band mismatch: {path}")
        arr = ds.read(1)
        return arr, {"dtype": ds.dtypes[0], "nodata": str(ds.nodata)}


def analyze(manifest: dict, cache: Path, *, budget: int = PLANNED_DOTS) -> dict:
    core = {key: verify_input(item, cache) for key, item in manifest["core"].items()}
    focus = [(item, verify_input(item, cache)) for item in manifest["focus_sites"]]
    template, meta = read_aligned(core["template"], GRID)
    if meta["dtype"] != "float32":
        raise ValueError("Template must be float32")
    footprint = np.isfinite(template)
    if not footprint.any() or np.any((template[footprint] < 0) | (template[footprint] > 1)):
        raise ValueError("Template footprint/range invalid")
    labels, _ = read_aligned(core["catalogue"], GRID)
    known = (labels > 0) & footprint
    lattice, _ = read_aligned(core["lattice"], GRID)
    if not np.isfinite(lattice[footprint]).all() or np.any((lattice[footprint] < 0) | (lattice[footprint] > 1)):
        raise ValueError("Registered lattice has invalid values in footprint")
    content_sha = hashlib.sha256(np.asarray(lattice[footprint], dtype="<f4").tobytes()).hexdigest()
    registry = json.loads(core["registry"].read_text())
    entries = [r for r in registry["unique_rasters"] if r.get("sha256") == manifest["core"]["lattice"]["sha256"]]
    if len(entries) != 1 or entries[0].get("footprint_sha256") != content_sha:
        raise ValueError("The pinned witness is absent or its footprint content does not match the registry")
    ref_dots = footprint & (lattice > 0)
    covered = coverage(ref_dots)
    bound = overlap_bound(int(footprint.sum()), int((footprint & covered).sum()), budget)
    arrays, rows = {}, []
    for item, path in focus:
        arr, pmeta = read_aligned(path, GRID)
        inside = arr[footprint]
        if not np.isfinite(inside).all() or np.any((inside < 0) | (inside > 1)):
            raise ValueError(f"Invalid historical values inside footprint: {item['site']}")
        value_hash = hashlib.sha256(np.asarray(inside, dtype="<f4").tobytes()).hexdigest()
        if value_hash != item["footprint_sha256"]:
            raise ValueError(f"Footprint SHA-256 mismatch: {item['site']}")
        dots = footprint & (arr > 0)
        arrays[item["site"]] = dots
        rows.append({"site": item["site"], "file_sha256": item["sha256"], "footprint_sha256": value_hash,
                     "positive_pixels": int(dots.sum()), "inside_finite": True,
                     "single_band_grid_match": True, "dtype": pmeta["dtype"],
                     "outside_nan_pixels": int(np.isnan(arr[~footprint]).sum()),
                     "total_outside_pixels": int((~footprint).sum())})
    if len(arrays) != len(focus) or not arrays:
        raise ValueError("Focus site IDs must be unique and nonempty")
    for ref_site, ref in arrays.items():
        near = coverage(ref)
        for row in rows:
            candidate = arrays[row["site"]]
            if row["site"] == ref_site:
                continue
            count = int(candidate.sum())
            if not count:
                raise ValueError(f"Cannot compare an empty historical raster: {row['site']}")
            row.setdefault("overlap_within_3px", {})[ref_site] = int((candidate & near).sum()) / count
    for row in rows:
        nearest, fraction = max(row["overlap_within_3px"].items(), key=lambda pair: pair[1])
        row["max_peer_overlap"] = fraction
        row["max_peer_site"] = nearest
        row["other_focus_exact_value_matches"] = [other["site"] for other in rows
            if other["site"] != row["site"] and other["footprint_sha256"] == row["footprint_sha256"]]
        row["literal_peer_duplicate"] = fraction > 0.70
    d28, r1, b2, geothermal = (arrays[s] for s in ("GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE36"))
    near1, near2 = coverage(known, 1), coverage(known, 2)
    lineage = {
        "b2_dots_not_in_r1": int((b2 & ~r1).sum()),
        "r1_dots_not_in_d28": int((r1 & ~d28).sum()),
        "d28_dots_removed_to_r1": int((d28 & ~r1).sum()),
        "d28_removed_within_1px_catalogue": int((d28 & ~r1 & near1).sum()),
        "r1_dots_removed_to_b2": int((r1 & ~b2).sum()),
        "r1_removed_within_2px_catalogue": int((r1 & ~b2 & near2).sum()),
        "b2_not_in_geothermal": int((b2 & ~geothermal).sum()),
        "geothermal_additions_to_b2": int((geothermal & ~b2).sum()),
        "interpretation": "Set relationship on pinned owner mirrors; it does not authenticate scores or prove hidden-label causation.",
    }
    return {
        "schema": "wbggems.focus-audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_scope": "Nine hash-pinned owner-mirror artifacts plus one pinned registry witness; no organizer score receipt, no original candidate surfaces, no full-registry novelty pass.",
        "grid": {"shape_rows_columns": list(GRID["shape"]), "crs": GRID["crs"], "transform": list(GRID["transform"]),
                 "template_sha256": manifest["core"]["template"]["sha256"],
                 "template_provenance": "owner mirror; original organizer bytes not authenticated",
                 "footprint_pixels": int(footprint.sum()), "catalogue_positive_pixels": int(known.sum()),
                 "sample_positive_pixels": int(((template > 0) & footprint).sum()),
                 "sample_positives_equal_catalogue": bool(np.array_equal((template > 0) & footprint, known))},
        "preflight": {"registry_id": entries[0]["id"], "registry_sha256": manifest["core"]["registry"]["sha256"],
                      "lattice_file_sha256": manifest["core"]["lattice"]["sha256"],
                      "lattice_footprint_sha256": content_sha, "lattice_positive_pixels": int(ref_dots.sum()),
                      "radius_pixels": 3, "bound": bound,
                      "status": "STOP_GUARANTEED_DUPLICATE" if bound["guaranteed_duplicate"] else "NOT_A_PASS_MORE_CHECKS_REQUIRED"},
        "historical_focus": rows, "lineage": lineage,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="Restore missing/hash-mismatched immutable inputs from GitHub")
    parser.add_argument("--cache", type=Path, default=ROOT / ".work")
    parser.add_argument("--output", type=Path, help="Write evidence JSON here; always prints to stdout")
    args = parser.parse_args()
    try:
        manifest = json.loads(MANIFEST.read_text())
        if args.restore:
            for item in list(manifest["core"].values()) + manifest["focus_sites"]:
                restore(item, args.cache)
        result = analyze(manifest, args.cache)
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        print(text, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Audit failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
