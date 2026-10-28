#!/usr/bin/env python3
"""Pairwise 3-px overlap matrix of the nine focus sites' top reported submissions.

Answers, with measured bytes rather than prose: *are the nine sites' best files
actually different methods?*  For a pair (A, B) the number reported is

    overlap(A -> B) = fraction of A's dots within an inclusive Euclidean 3 px
                      of one of B's positive cells

which is exactly the quantity the project brief's 70 % stop rule names.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITES = json.load(open(os.path.join(ROOT, "scratch/nine_site_tops.json")))


def positives(path: str) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.argwhere(np.isfinite(a) & (a > 0))


def main() -> int:
    names, pts = [], {}
    for site in ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]:
        p = os.path.join(ROOT, "scratch/rasters", SITES[site]["sha"][:16] + ".tif")
        names.append(site)
        pts[site] = positives(p)
        print(f"{site:11s} dots={len(pts[site]):7d}", flush=True)
    trees = {s: cKDTree(pts[s]) for s in names}
    M = {}
    for a in names:
        row = {}
        for b in names:
            if a == b:
                row[b] = 1.0
                continue
            d, _ = trees[b].query(pts[a], k=1, distance_upper_bound=4.0)
            row[b] = round(float(np.mean(d <= 3.0)), 4)
        M[a] = row
    off = [(a, b, M[a][b]) for a in names for b in names if a != b]
    summary = dict(
        matrix=M, sites=names,
        dots={s: int(len(pts[s])) for s in names},
        max_offdiag=round(max(v for _, _, v in off), 4),
        n_pairs=int(len(off)),
        n_pairs_over_70=sum(1 for _, _, v in off if v > 0.70),
        n_pairs_over_90=sum(1 for _, _, v in off if v > 0.90),
        definition="overlap(A->B) = share of A's positive cells within inclusive 3 px of a B positive cell",
        source="scratch/rasters/<sha16>.tif, hashes in scratch/nine_site_tops.json")
    out = os.path.join(ROOT, "evidence/wbg4_nine_site_matrix.json")
    json.dump(summary, open(out, "w"), indent=1)
    print("\noverlap(A -> B), rows = A, cols = B")
    print("           " + " ".join(f"{n[-2:]:>6s}" for n in names))
    for a in names:
        print(f"{a:11s}" + " ".join(f"{M[a][b]:6.3f}" for b in names))
    print(f"\nmax off-diagonal overlap: {summary['max_offdiag']}")
    print(f"pairs > 0.70: {summary['n_pairs_over_70']} / {summary['n_pairs']}")
    print(f"pairs > 0.90: {summary['n_pairs_over_90']} / {summary['n_pairs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
