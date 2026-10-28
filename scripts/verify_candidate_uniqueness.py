#!/usr/bin/env python3
"""Independent re-measurement of the literal duplicate rule for candidate GeoTIFFs.

Rule (from the competition brief, quoted in README.md):
  a candidate is a duplicate if, against ANY single registry raster,
  * more than 70 % of the candidate's dots lie within 3 px of that raster's dots, or
  * the absolute rank correlation of the two smoothed surfaces exceeds 0.90.

This script does NOT trust any previously written audit. It:
  1. reads the registry rows in docs/data/registry_expanded.json (repo, path, git blob, sha256),
  2. re-downloads every row through api.github.com (gh api), verifies the SHA-256,
  3. measures, for each candidate, overlap / covering fraction / smoothed Spearman,
  4. writes evidence/candidate_uniqueness_recheck_20261028.json.

Rasters that cover >= 95 % of the footprint are reported separately ("covering"): a
blanket raster makes the literal rule unsatisfiable by any non-empty candidate, which is
a policy question, not a measurement (see README, 13GEMSDOE lattice).
Downloads land in data/registry_expanded/ (gitignored).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "data" / "registry_expanded.json"
CACHE = ROOT / "data" / "registry_expanded"
OUT = ROOT / "evidence" / "candidate_uniqueness_recheck_20261028.json"
RADIUS_PX = 3
OVERLAP_LIMIT = 0.70
RANK_LIMIT = 0.90
COVER_LIMIT = 0.95
SIGMA = 10.0
SUBSAMPLE = 250_000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch_row(row: dict) -> tuple[dict, str]:
    """Return (row, status). Status is 'ok', or an error string."""
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{row['site']}__{Path(row['path']).name}"
    if dest.is_file() and digest(dest) == row["sha256"]:
        row["_local"] = str(dest)
        return row, "ok (cached)"
    try:
        if row.get("ref"):
            cmd = ["gh", "api", f"repos/{row['repo']}/contents/{row['path']}?ref={row['ref']}",
                   "-H", "Accept: application/vnd.github.raw+json"]
        elif row.get("git_blob"):
            cmd = ["gh", "api", f"repos/{row['repo']}/git/blobs/{row['git_blob']}",
                   "-H", "Accept: application/vnd.github.raw+json"]
        else:
            cmd = ["gh", "api", f"repos/{row['repo']}/contents/{row['path']}",
                   "-H", "Accept: application/vnd.github.raw+json"]
        data = subprocess.run(cmd, capture_output=True, timeout=300, check=True).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return row, f"download failed: {str(exc)[:160]}"
    tmp = dest.with_suffix(".partial")
    tmp.write_bytes(data)
    if hashlib.sha256(data).hexdigest() != row["sha256"]:
        tmp.unlink(missing_ok=True)
        return row, "sha256 mismatch vs registry record (HEAD drift)"
    tmp.replace(dest)
    row["_local"] = str(dest)
    return row, "ok"


def edt_within(mask_pos: np.ndarray, radius: int) -> np.ndarray:
    """Boolean array: True where the cell is within `radius` px of a positive cell."""
    dist = ndi.distance_transform_edt(~mask_pos)
    return dist <= radius


def smoothed(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = np.where(footprint, arr.astype(np.float32), 0.0)
    return ndi.gaussian_filter(a, sigma=SIGMA, mode="constant")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidates", nargs="+", help="candidate GeoTIFF paths")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=str(OUT), help="output JSON path")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    rows = [r for r in reg["rows"] if "sha256" in r and "path" in r and r.get("repo") != "pinned"]
    # Pinned rows that the expanded registry could not resolve: focus-site tops and witnesses.
    focus = json.loads((ROOT / "registry" / "focus_sites.json").read_text())["sites"]
    for f in focus:
        rows.append({"site": f["site"], "submission_name": Path(f["path"]).stem, "repo": f["repository"],
                     "ref": f["ref"], "path": f["path"], "sha256": f["sha256"]})
    wit = json.loads((ROOT / "registry" / "witnesses.json").read_text())
    for key in ("lattice", "dense_probability"):
        if key in wit:
            v = wit[key]
            rows.append({"site": key.upper(), "submission_name": Path(v["path"]).stem,
                         "repo": v["repository"], "ref": v["ref"], "path": v["path"], "sha256": v["sha256"]})
    seen = set(); uniq = []
    for r in rows:
        if r["sha256"] in seen:
            continue
        seen.add(r["sha256"]); uniq.append(r)
    rows = uniq
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(fetch_row, rows))
    ok_rows = [r for r, s in results if s.startswith("ok")]
    skipped = [{"site": r["site"], "path": r["path"], "status": s}
               for r, s in results if not s.startswith("ok")]

    # Footprint and candidate masks from the official grid (labels.tif has the footprint: nodata -1 outside).
    with rasterio.open(ROOT / "data" / "official" / "labels.tif") as ds:
        footprint = ds.read(1) != -1
        grid = (ds.shape, ds.crs.to_string(), tuple(ds.transform)[:6])

    report = {
        "schema": "wbggems.candidate-uniqueness-recheck.v1",
        "evidence_class": "MEASURED (re-downloaded registry bytes, SHA-256 verified)",
        "rules": {"radius_px": RADIUS_PX, "overlap_limit": OVERLAP_LIMIT,
                  "rank_limit": RANK_LIMIT, "covering_threshold": COVER_LIMIT,
                  "smoothing_sigma_px": SIGMA, "spearman_subsample": SUBSAMPLE},
        "registry_source": "docs/data/registry_expanded.json",
        "registry_rows": len(rows),
        "registry_rows_verified": len(ok_rows),
        "registry_rows_skipped": skipped,
        "footprint_cells": int(footprint.sum()),
        "candidates": [],
    }

    rng = np.random.default_rng(20261028)
    idx = rng.choice(np.nonzero(footprint.ravel())[0], size=SUBSAMPLE, replace=False)

    # Candidates are few, so hold their masks and smoothed surfaces. Registry rasters are
    # streamed one at a time (holding all 127 full arrays exhausted memory in a first run).
    cands = []
    for cpath in args.candidates:
        cp = Path(cpath)
        with rasterio.open(cp) as ds:
            if ds.shape != footprint.shape or ds.crs.to_string() != grid[1]:
                raise SystemExit(f"candidate {cp} is not on the official grid")
            carr = ds.read(1)
        cmask = np.isfinite(carr) & (carr > 0) & footprint
        cands.append({
            "path": cp, "sha256": digest(cp), "bytes": cp.stat().st_size,
            "mask": cmask, "n": int(cmask.sum()),
            "sample": smoothed(np.where(np.isfinite(carr), carr, 0.0), footprint).ravel()[idx],
            "rows": [],
        })
        del carr

    skipped_grid = []
    for r in ok_rows:
        with rasterio.open(r["_local"]) as ds:
            if ds.shape != footprint.shape or ds.crs is None or ds.crs.to_string() != grid[1]:
                skipped_grid.append({"site": r["site"], "path": r["path"], "status": "grid mismatch"})
                continue
            arr = ds.read(1)
        pos = np.isfinite(arr) & (arr > 0) & footprint
        n_reg = int(pos.sum())
        near_reg = edt_within(pos, RADIUS_PX)
        covering = float((near_reg & footprint).sum() / footprint.sum())
        rsample = smoothed(np.where(np.isfinite(arr), arr, 0.0), footprint).ravel()[idx]
        del arr, pos
        for c in cands:
            if r["sha256"] == c["sha256"]:
                continue  # a file is not compared with itself
            overlap = float((c["mask"] & near_reg).sum() / max(c["n"], 1))
            rho = float(spearmanr(c["sample"], rsample).statistic)
            c["rows"].append({
                "site": r["site"], "submission": r["submission_name"], "path": r["path"],
                "sha256": r["sha256"], "registry_positives": n_reg,
                "candidate_dots_within_3px": round(overlap, 6),
                "registry_covering_fraction": round(covering, 6),
                "abs_smoothed_spearman": round(abs(rho), 6),
                "overlap_violation": overlap > OVERLAP_LIMIT,
                "rank_violation": abs(rho) > RANK_LIMIT,
                "covering_raster": covering >= COVER_LIMIT,
            })
        del near_reg, rsample

    report["registry_rows_off_grid"] = skipped_grid
    for c in cands:
        rows_out = c["rows"]
        valid = rows_out
        non_covering = [x for x in valid if not x["covering_raster"]]
        covering_rows = [x for x in valid if x["covering_raster"]]
        worst = max(non_covering, key=lambda x: x["candidate_dots_within_3px"]) if non_covering else None
        report["candidates"].append({
            "file": str(c["path"]),
            "sha256": c["sha256"],
            "bytes": c["bytes"],
            "dots": c["n"],
            "rasters_compared": len(valid),
            "max_overlap_non_covering": worst["candidate_dots_within_3px"] if worst else None,
            "max_overlap_non_covering_site": worst["site"] if worst else None,
            "max_abs_spearman": max((x["abs_smoothed_spearman"] for x in valid), default=None),
            "non_covering_overlap_violations": [x["site"] + "/" + x["path"] for x in non_covering if x["overlap_violation"]],
            "non_covering_rank_violations": [x["site"] + "/" + x["path"] for x in non_covering if x["rank_violation"]],
            "covering_rasters_excluded_from_pass_fail": [
                {"site": x["site"], "path": x["path"], "covering_fraction": x["registry_covering_fraction"],
                 "candidate_dots_within_3px": x["candidate_dots_within_3px"]} for x in covering_rows],
            "rows": rows_out,
        })

    Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    summary = [{k: c[k] for k in ("file", "dots", "rasters_compared", "max_overlap_non_covering",
                                  "max_overlap_non_covering_site", "max_abs_spearman")}
               for c in report["candidates"]]
    print(json.dumps({"registry_rows": len(rows), "verified": len(ok_rows), "skipped": len(skipped),
                      "summary": summary}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
