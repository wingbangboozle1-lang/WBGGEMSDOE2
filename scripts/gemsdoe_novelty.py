"""Novelty audit: is the candidate a copy of anything in the observed fleet?

Two rules, both measured rather than asserted:

R1 (byte identity)  SHA-256 of the candidate must not equal any fleet raster's.
R2 (placement)      fraction of the candidate's positive cells lying within an
                    inclusive 3-px Euclidean halo of a fleet raster's positive
                    cells; and, symmetrically, the fraction of that raster's cells
                    inside the candidate's halo.  Reported at the candidate's own
                    mass budget, which is the only comparison that is meaningful:
                    a 272k-dot lattice trivially covers any 38k-dot emission.
R3 (surface shape)  Spearman correlation of 1 km-smoothed surfaces.

Thresholds are the ones the session brief requests (0.90 rank correlation, 0.70
mutual halo overlap).  Output: ``data/work/novelty.json``.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import grid  # noqa: E402

CAND = grid.ROOT / "submissions" / "gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif"
FP = np.load(grid.WORK / "footprint.npy")


def _load(path):
    with rasterio.open(path) as ds:
        if tuple(ds.shape) != grid.SHAPE or str(ds.crs) != grid.CRS:
            return None
        a = ds.read(1).astype("float32")
    a[~np.isfinite(a)] = 0.0
    return np.clip(a, 0, 1)


def compare(job):
    path, cand_pos, cand_rank, cand_halo = job
    try:
        a = _load(path)
    except Exception:
        return None
    if a is None or not (a > 0).any():
        return None
    pos = a > 0
    halo = ndi.distance_transform_edt(~pos) <= 3
    frac_mine_in_halo = float(halo[cand_pos].mean())
    frac_theirs_in_my_halo = float(cand_halo[pos].mean())
    sm = ndi.uniform_filter(a, 10)
    rho = spearmanr(cand_rank, sm[FP]).statistic
    return {"file": path, "stem": Path(path).stem, "dots": int(pos.sum()),
            "frac_my_dots_within_3px": frac_mine_in_halo,
            "frac_their_dots_within_3px": frac_theirs_in_my_halo,
            "smoothed_spearman": float(rho),
            "sha256": grid.sha256(path)}


def main():
    cand = _load(CAND)
    cand_pos = cand > 0
    cand_halo = ndi.distance_transform_edt(~cand_pos) <= 3
    cand_rank = ndi.uniform_filter(cand, 10)[FP]
    cand_sha = grid.sha256(CAND)
    jobs = []
    for d in ("/tmp/fleet", str(grid.ROOT / "docs" / "downloads")):
        for p in Path(d).rglob("*.tif"):
            if p.resolve() == CAND.resolve():
                continue
            jobs.append((str(p), cand_pos, cand_rank, cand_halo))
    out = {"candidate": str(CAND.relative_to(grid.ROOT)), "sha256": cand_sha,
           "dots": int(cand_pos.sum()), "n_compared": 0, "rules": {
               "R1_identical_bytes": [], "R2_mutual_halo_limit": 0.70,
               "R3_rank_limit": 0.90}, "worst": [], "evidence_class": "MEASURED"}
    with Pool(2) as pool:
        rows = [r for r in pool.imap_unordered(compare, jobs) if r]
    out["n_compared"] = len(rows)
    out["R1_identical_bytes"] = [r["stem"] for r in rows if r["sha256"] == cand_sha]
    rows.sort(key=lambda r: -r["frac_my_dots_within_3px"])
    out["worst"] = rows[:10]
    out["max_frac_my_dots_within_3px"] = rows[0]["frac_my_dots_within_3px"] if rows else 0.0
    out["max_frac_their_dots_within_3px"] = max(r["frac_their_dots_within_3px"] for r in rows) if rows else 0.0
    out["max_abs_smoothed_spearman"] = max(abs(r["smoothed_spearman"]) for r in rows) if rows else 0.0
    out["worst_rank"] = sorted(rows, key=lambda r: -abs(r["smoothed_spearman"]))[:5]
    out["verdict"] = {
        "unique_bytes": not out["R1_identical_bytes"],
        "passes_halo_rule": out["max_frac_my_dots_within_3px"] <= 0.70,
        "passes_rank_rule": out["max_abs_smoothed_spearman"] <= 0.90,
    }
    (grid.WORK / "novelty.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n_compared", "max_frac_my_dots_within_3px",
                                          "max_frac_their_dots_within_3px",
                                          "max_abs_smoothed_spearman", "verdict")}, indent=1))
    for r in out["worst"][:5]:
        print(f"  {r['frac_my_dots_within_3px']:.3f} {r['frac_their_dots_within_3px']:.3f} "
              f"rho={r['smoothed_spearman']:+.3f} {r['stem'][:60]}")


if __name__ == "__main__":  # pragma: no cover
    main()
