"""Fast fleet measurement: pooled HOLDOUT-DTI + shape statistics for scored rasters.

Same protocol as ``gemsdoe_fleet_eval.py`` (4 hidden-segment folds, known catalogue
pixels masked as the organizer does) but the fold masks are cached in memory and
only rasters that carry a published score are measured, which is what the
calibration and the strategy diagnostic actually need.
"""
from __future__ import annotations

import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import grid  # noqa: E402
from gemsdoe.fastdti import fast_dti, pool  # noqa: E402

FP = np.load(grid.WORK / "footprint.npy")
CAT = np.load(grid.WORK / "catalogue.npy")
TRUTH = [np.load(grid.WORK / f"fold{k}_truth.npy") for k in range(4)]
ACT = [FP & ~np.load(grid.WORK / f"fold{k}_visible.npy") for k in range(4)]
D_CAT = ndi.distance_transform_edt(~CAT).astype("float32")
N_FP = int(FP.sum())


def measure(job):
    path, pub, src = job
    try:
        with rasterio.open(path) as ds:
            if tuple(ds.shape) != grid.SHAPE or str(ds.crs) != grid.CRS:
                return {"file": path, "error": "grid mismatch"}
            a = ds.read(1).astype("float32")
    except Exception as exc:
        return {"file": path, "error": f"read: {exc}"}
    a[~np.isfinite(a)] = 0.0
    a = np.clip(a, 0.0, 1.0)
    pos = a > 0
    if not pos.any():
        return {"file": path, "error": "empty"}
    parts = [fast_dti(a, t, act) for t, act in zip(TRUTH, ACT)]
    pooled = pool(parts)
    d_pred = ndi.distance_transform_edt(~pos).astype("float32")
    halo = d_pred <= 3.0
    return {
        "file": path, "stem": Path(path).stem, "sha256": grid.sha256(path),
        "published_score": pub, "published_source": src,
        "mass": float(a[FP].sum()), "dots": int(pos.sum()),
        "holdout_dti": pooled["dti"], "holdout_tp": pooled["tp"],
        "holdout_fp": pooled["fp"], "holdout_truth": pooled["n_truth"],
        "fold_dti": [p["dti"] for p in parts],
        "collar_precision": float((D_CAT[pos] <= 3).mean()),
        "reach": float(halo[FP].sum() / N_FP),
        "catalogue_recall": float(halo[CAT].mean()),
        "catalogue_dti": fast_dti(pos.astype("float32"), CAT, FP)["dti"],
        "binary": bool(np.isin(a[pos], [0.0, 1.0]).all()),
    }


def load_scores(paths):
    out = {}
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        with p.open() as fh:
            for row in csv.DictReader(fh):
                stem = (row.get("submission") or row.get("file_stem") or "").strip()
                val = row.get("score") or row.get("reported_score") or ""
                try:
                    out.setdefault(stem, (float(val), str(p)))
                except (TypeError, ValueError):
                    continue
    return out


def main():
    scores = load_scores([grid.ROOT / "data_public" / "fleet_score_claims.csv",
                          "/tmp/g32/docs/score-ledger.csv"])
    files = set()
    for d in ("/tmp/fleet", str(grid.ROOT / "docs" / "downloads")):
        files |= {str(p) for p in Path(d).rglob("*.tif")}
    jobs = []
    for f in sorted(files):
        stem = Path(f).stem
        hit = scores.get(stem)
        if hit is None:  # fuzzy: scored stem may be a prefix of the file stem
            for k, v in scores.items():
                if k and k in stem:
                    hit = v
                    break
        if hit is not None:
            jobs.append((f, hit[0], hit[1]))
    print(f"{len(jobs)} scored rasters", flush=True)
    with Pool(2) as pool_:
        rows = []
        for i, r in enumerate(pool_.imap_unordered(measure, jobs), 1):
            rows.append(r)
            if i % 20 == 0:
                print(f"[{i}/{len(jobs)}]", flush=True)
    rows = [r for r in rows if "error" not in r]
    seen, uniq = set(), []
    for r in rows:
        if r["sha256"] in seen:
            continue
        seen.add(r["sha256"])
        uniq.append(r)
    uniq.sort(key=lambda r: -r["published_score"])
    out = {"evidence_class": "MEASURED", "n": len(uniq),
           "protocol": "pooled 4-fold withheld-segment DTI, known catalogue pixels masked",
           "rows": uniq}
    (grid.WORK / "fleet_scored.json").write_text(json.dumps(out, indent=1))
    print("wrote", len(uniq), "rows")


if __name__ == "__main__":  # pragma: no cover
    main()
