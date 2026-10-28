#!/usr/bin/env python3
"""Metric-aware emitter: greedy surface-weighted maximum coverage.

Why this objective
------------------
The organizer's DTI is ``T / (T + 0.2 F + 0.8 (N - T))`` with
``T = sum_truth max_kernel p k``.  For a binary dot field, the only thing a dot can
buy is *new* kernel-weighted truth mass; every dot also pays ``0.2`` of false-positive
price.  So the marginal value of a dot is the kernel-weighted surface mass inside its
300 m disc that no other dot already claims, and the right emission is the set that
maximises ``sum_x w(x) * covered(x)`` for a fixed number of dots -- a monotone
submodular problem, solved here by lazy greedy with a 1 - 1/e guarantee.

``w`` is the calibrated fault-probability surface.  Two emissions are produced so the
decision is visible rather than asserted:

* ``--mode surface``  greedy on ``w`` (value x novelty)
* ``--mode uniform``  greedy on a constant field (pure geometric coverage ceiling)

Both are written as float32 GeoTIFFs on the organizer grid with 0 outside the
footprint and NaN outside the raster footprint, and both are scored with the exact
DTI code on the fold holdout before anything is published.

Usage
-----
    python scripts/gemsdoe_maxcov.py --surface data/work/consensus_surface.npy \
        --mass 38000 --out submissions/<name>.tif
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
R = 3
DISC = [(dy, dx) for dy in range(-R, R + 1) for dx in range(-R, R + 1)
        if dy * dy + dx * dx <= R * R]
DISC_K = np.array([1.0 - np.hypot(dy, dx) / R for dy, dx in DISC], dtype="float32")


def coverage_field(dots: np.ndarray) -> np.ndarray:
    """max_kernel coverage of every cell: k(distance to the nearest dot)."""
    d = ndi.distance_transform_edt(~dots)
    return np.maximum(1.0 - d / R, 0.0).astype("float32")


def greedy(w: np.ndarray, footprint: np.ndarray, mass: int, candidates: int,
           seed: int = 20261028) -> tuple[np.ndarray, list[float]]:
    """Lazy-greedy surface-weighted max coverage.  Returns (dot mask, gain trace).

    True lazy greedy: a candidate is only accepted when its *recomputed* marginal
    gain still beats every other heap key, so the result is the standard greedy
    sequence for the monotone submodular objective (1 - 1/e guarantee).
    """
    import heapq

    h, wd = w.shape
    wf = np.where(footprint, w, 0.0).astype("float32")
    flat = wf.ravel()
    n_fp = int(footprint.sum())
    k_surf = min(candidates, n_fp // 2)
    top = np.argpartition(flat, -k_surf)[-k_surf:]
    rng = np.random.default_rng(seed)
    supp = rng.choice(np.flatnonzero(flat > 0), size=min(candidates // 2, int((flat > 0).sum())),
                      replace=False)
    idx = np.unique(np.concatenate([top, supp]))
    ys, xs = np.unravel_index(idx, (h, wd))
    gain = np.zeros(len(idx), dtype="float32")
    for (dy, dx), kv in zip(DISC, DISC_K):
        gain += kv * wf[np.clip(ys + dy, 0, h - 1), np.clip(xs + dx, 0, wd - 1)]
    heap = [(-float(g), int(i)) for i, g in enumerate(gain)]
    heapq.heapify(heap)
    covered = np.zeros((h, wd), dtype=bool)
    dots = np.zeros((h, wd), dtype=bool)
    trace: list[float] = []
    while len(trace) < mass and heap:
        neg, i = heapq.heappop(heap)
        y, x = int(ys[i]), int(xs[i])
        y0, y1 = max(0, y - R), min(h, y + R + 1)
        x0, x1 = max(0, x - R), min(wd, x + R + 1)
        sub = ~covered[y0:y1, x0:x1]
        if not sub.any():
            continue
        dy = np.arange(y0, y1)[:, None] - y
        dx = np.arange(x0, x1)[None, :] - x
        kv = np.maximum(1.0 - np.hypot(dy, dx) / R, 0.0).astype("float32")
        g = float((wf[y0:y1, x0:x1] * kv * sub).sum())
        if heap and g < -heap[0][0] - 1e-9:
            heapq.heappush(heap, (-g, i))       # stale key: let a better cell win
            continue
        if g <= 0:
            break
        dots[y, x] = True
        covered[y0:y1, x0:x1] |= kv > 0
        trace.append(g)
    return dots, trace


def write_tif(dots: np.ndarray, footprint: np.ndarray, out: Path,
              zero_outside: bool = False) -> dict:
    """Write the organizer-format single-band float32 GeoTIFF."""
    arr = np.where(footprint, dots.astype("float32"), 0.0 if zero_outside else np.nan)
    profile = {"driver": "GTiff", "height": arr.shape[0], "width": arr.shape[1],
               "count": 1, "dtype": "float32", "crs": "EPSG:32611",
               "transform": rasterio.transform.from_origin(243350.0, 4508550.0, 100.0, 100.0),
               "nodata": None if zero_outside else float("nan"),
               "compress": "deflate", "predictor": 3, "tiled": True,
               "blockxsize": 256, "blockysize": 256}
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(arr, 1)
    return {"path": str(out.relative_to(ROOT)) if str(out).startswith(str(ROOT)) else str(out),
            "bytes": int(out.stat().st_size), "cells": int(dots.sum()),
            "nan_outside_footprint": not zero_outside}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", default=str(WORK / "consensus_surface.npy"))
    ap.add_argument("--mode", default="surface", choices=["surface", "uniform"])
    ap.add_argument("--mass", type=int, default=38000)
    ap.add_argument("--candidates", type=int, default=300000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default=str(WORK / "maxcov.json"))
    args = ap.parse_args()

    fp = np.load(WORK / "footprint.npy").astype(bool)
    surf = np.load(args.surface).astype("float32")
    surf = np.nan_to_num(surf, nan=0.0, posinf=0.0, neginf=0.0)
    if surf.shape != fp.shape:
        raise SystemExit(f"surface shape {surf.shape} != {fp.shape}")
    s = (surf - surf[fp].min()) / max(float(np.ptp(surf[fp])), 1e-9)
    w = np.where(fp, s ** 2, 0.0).astype("float32") if args.mode == "surface" else fp.astype("float32")
    if args.mode == "uniform":
        # pad the candidate pool for the uniform case (every cell is a candidate)
        w = np.where(fp, 1.0, 0.0).astype("float32")

    dots, trace = greedy(w, fp, args.mass, args.candidates)
    cov = coverage_field(dots)
    total_w = float(w.sum())
    js = float((w * cov).sum())
    reach = float((cov > 0)[fp].mean())
    info = {"surface": args.surface, "mode": args.mode, "requested_mass": args.mass,
            "cells": int(dots.sum()), "reach_frac_footprint": reach,
            "surface_weighted_coverage": js / total_w,
            "gain_trace_head": [round(g, 5) for g in trace[:3]],
            "gain_trace_tail": [round(g, 7) for g in trace[-3:]],
            "dots_per_1000km2": float(dots.sum() / (fp.sum() * 0.01) * 1000)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    info.update(write_tif(dots, fp, Path(args.out)))
    Path(args.report).write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
