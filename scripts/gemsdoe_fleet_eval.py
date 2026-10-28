"""Measure every available fleet raster on the shared holdout and attach published scores.

Inputs
------
* rasters: ``--dirs`` (defaults to the cloned GEMSDOE* ``docs/downloads`` trees)
* published scores: ``data_public/fleet_score_claims.csv`` plus ``--ledger`` CSVs

Output: ``data/work/fleet_eval.json`` -- one row per distinct SHA-256 identity with
measured geometry-free properties (mass, positive cells), the pooled HOLDOUT-DTI
and, where a published score exists, the user-reported leaderboard value.

Nothing in the output is a leaderboard forecast: published values are
USER-REPORTED, holdout values are HOLDOUT-DTI.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import grid, scoring  # noqa: E402


def load_scores(paths) -> dict:
    """stem -> (score, source) from ledger CSVs and our fleet score claims."""
    out = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        with p.open() as fh:
            for row in csv.DictReader(fh):
                stem = row.get("submission") or row.get("file_stem") or ""
                val = row.get("score") or row.get("reported_score") or ""
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    continue
                out.setdefault(stem.strip(), {"score": v, "source": str(p)})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=["/tmp/fleet", str(grid.ROOT / "docs" / "downloads")])
    ap.add_argument("--ledger", nargs="*", default=[
        str(grid.ROOT / "data_public" / "fleet_score_claims.csv"),
        "/tmp/g32/docs/score-ledger.csv",
    ])
    ap.add_argument("--out", default=str(grid.WORK / "fleet_eval.json"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-score-dilation", type=int, default=0)
    args = ap.parse_args(argv)

    grid.ensure_work()
    scores = load_scores(args.ledger)
    ref_transform = rasterio.Affine(*grid.TRANSFORM)
    tifs = []
    for d in args.dirs:
        tifs += sorted(str(p) for p in Path(d).rglob("*.tif"))
    tifs = sorted(set(tifs))
    if args.limit:
        withs = [t for t in tifs if Path(t).stem in scores]
        others = [t for t in tifs if Path(t).stem not in scores]
        tifs = (withs + others)[: args.limit]

    fp = np.load(grid.WORK / "footprint.npy")
    rows, seen = [], {}
    for i, t in enumerate(tifs):
        try:
            with rasterio.open(t) as ds:
                if tuple(ds.shape) != grid.SHAPE or ds.crs is None or str(ds.crs) != grid.CRS:
                    rows.append({"file": t, "error": f"grid mismatch {ds.shape} {ds.crs}"})
                    continue
                if tuple(ds.transform)[:6] != tuple(ref_transform)[:6]:
                    rows.append({"file": t, "error": "transform mismatch"})
                    continue
                a = ds.read(1).astype("float32")
        except Exception as exc:  # pragma: no cover - corrupt third-party file
            rows.append({"file": t, "error": f"read: {exc}"})
            continue
        a[~np.isfinite(a)] = 0.0
        a = np.clip(a, 0.0, 1.0)
        sha = grid.sha256(t)
        if sha in seen:
            continue
        seen[sha] = t
        d = scoring.describe(a)
        h = scoring.holdout_dti(a, known_dilation=args.min_score_dilation)
        stem = Path(t).stem
        pub = scores.get(stem)
        rows.append({
            "file": t, "stem": stem, "sha256": sha, **d,
            "holdout_dti": h["dti"], "holdout_tp": h["tp"], "holdout_fp": h["fp"],
            "holdout_fn": h["fn"], "holdout_truth": h["n_truth"],
            "fold_dti": h["fold_dti"],
            "published_score": pub["score"] if pub else None,
            "published_source": pub["source"] if pub else None,
        })
        if (i + 1) % 25 == 0:
            print(f"[{i+1}/{len(tifs)}] {stem} holdout={h['dti']:.4f} mass={d['mass_inside_footprint']:.0f}", flush=True)

    Path(args.out).write_text(json.dumps({
        "evidence_class": "MEASURED",
        "note": ("HOLDOUT-DTI = pooled withheld-catalogue DTI with known catalogue pixels masked "
                 "(organizer rule). published_score = USER-REPORTED leaderboard value, unauthenticated."),
        "known_dilation_px": args.min_score_dilation,
        "n_rasters": len(rows), "n_scored": sum(1 for r in rows if r.get("published_score") is not None),
        "rows": rows,
    }, indent=1))
    print("wrote", args.out, len(rows), "rows")


if __name__ == "__main__":  # pragma: no cover
    main()
