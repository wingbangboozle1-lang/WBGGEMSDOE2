#!/usr/bin/env python3
"""WBG5: build, validate, hash and audit the campaign submission raster.

Method (single lane, no private forks):

1.  Prior surface P = 0.6 * SGMC-fault-likeness + 0.4 * topography percentile.
    * The SGMC model is a HistGradientBoosting classifier trained only on the
      independent USGS State Geologic Map Compilation fault raster (NV/CA
      structure layers, public domain), with negatives >300 m from any SGMC
      fault.  It never sees the competition labels.
    * The topography term is the mean percentile of ``det_elev`` and
      ``det_elev_slope`` from the organizer feature stack.
2.  Dots = score-ordered Poisson-disk sample (minimum spacing 3 px = 300 m) of
    P inside the footprint and outside the mapped catalogue.
3.  Output = float32 single band, 1.0 on dots, 0.0 elsewhere (all finite).

The number of dots is a calibrated budget, not a guess: see
``evidence/wbg5_prior_experiment.json`` for the independent-fault-map density
curve (20k-300k dots) that selected it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.gemsdoe.fastdti import fast_dti  # noqa: E402
from src.wbg5 import evaluate, grid, paths, priors  # noqa: E402

EXPECTED = {
    "training_features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "labels.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs() -> dict:
    out = {}
    for name, want in EXPECTED.items():
        if name == "training_features.tif":
            got = sha256(paths.FEATURES)
        else:
            got = sha256(paths.LABELS if name == "labels.tif" else paths.SAMPLE)
        out[name] = {"sha256": got, "expected": want, "match": got == want}
        if got != want:
            raise SystemExit(f"hash mismatch for {name}: {got} != {want}")
    return out


def build_features(masks, X, L, R):
    valid = L[11] > 0
    d_cat = ndi.distance_transform_edt(~masks.catalogue).astype("float32")
    d_ws = grid.point_distance(paths.WELLSPRING, masks)
    d_ve = grid.point_distance(paths.VENTS, masks)
    feats = [(f"X{i}", X[i]) for i in range(19)]
    feats += [(f"L{i}", np.where(valid, L[i], 0)) for i in range(11)]
    feats += [(f"R{i}", R[i]) for i in range(8)]
    feats += [("d_cat", d_cat), ("d_ws", d_ws), ("d_ve", d_ve)]
    return feats


def train_sgmc_prior(masks, feats, seed: int = 0):
    from sklearn.ensemble import HistGradientBoostingClassifier

    with rasterio.open(paths.SGMC) as d:
        sg = d.read(1) > 0
    d_sg = ndi.distance_transform_edt(~sg)
    pos = np.flatnonzero(sg & masks.footprint)
    neg_pool = np.flatnonzero(masks.footprint & (d_sg > 3))
    rng = np.random.default_rng(seed)
    neg = rng.choice(neg_pool, min(250_000, len(neg_pool)), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    F = np.stack([np.asarray(v).ravel()[idx] for _, v in feats], axis=1).astype("float32")
    clf = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.06, max_leaf_nodes=31,
        l2_regularization=1.0, random_state=seed,
    )
    clf.fit(F, y)
    h, w = masks.footprint.shape
    out = np.zeros((h, w), "float32")
    rows = np.flatnonzero(masks.footprint.any(axis=1))
    for r0 in range(rows.min(), rows.max() + 1, 250):
        r1 = min(r0 + 250, rows.max() + 1)
        G = np.stack([np.asarray(v)[r0:r1].ravel() for _, v in feats], axis=1).astype("float32")
        out[r0:r1] = clf.predict_proba(G)[:, 1].reshape(r1 - r0, w).astype("float32")
    out[~masks.footprint] = 0.0
    return out, {"n_positive": int(len(pos)), "n_negative": int(len(neg)),
                 "n_features": int(F.shape[1])}


def write_tif(path: Path, dots: np.ndarray, template: Path) -> None:
    with rasterio.open(template) as t:
        prof = t.profile.copy()
    prof.update(driver="GTiff", count=1, dtype="float32", nodata=None, compress="deflate")
    arr = dots.astype("float32")
    with rasterio.open(path, "w", **prof) as d:
        d.write(arr, 1)
        d.set_band_description(1, "fault probability")



EXPECTED_GRID = {"crs": "EPSG:32611", "shape": (3730, 3292),
                 "transform": (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)}


def verify_standalone(path: Path) -> dict:
    """Re-check saved bytes without the 419 MB organizer stack or any /tmp cache."""
    checks = []
    with rasterio.open(path) as d:
        a = d.read(1)
        checks.append(("crs", str(d.crs) == EXPECTED_GRID["crs"], str(d.crs)))
        checks.append(("shape", (d.height, d.width) == EXPECTED_GRID["shape"], f"{d.height}x{d.width}"))
        checks.append(("transform", tuple(d.transform)[:6] == EXPECTED_GRID["transform"],
                       str(tuple(d.transform)[:6])))
        checks.append(("band_count", d.count == 1, str(d.count)))
        checks.append(("dtype", d.dtypes[0] == "float32", d.dtypes[0]))
        checks.append(("all_finite", bool(np.isfinite(a).all()), f"nan={int((~np.isfinite(a)).sum())}"))
        checks.append(("range", bool(a.min() >= 0.0 and a.max() <= 1.0), f"[{a.min()},{a.max()}]"))
        checks.append(("values_binary", bool(np.isin(a, [0.0, 1.0]).all()), f"n_pos={int((a > 0).sum())}"))
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size,
            "checks": [{"name": n, "passed": bool(v), "detail": d} for n, v, d in checks],
            "all_passed": all(v for _, v, _ in checks)}


def validate(path: Path) -> dict:
    checks = []
    with rasterio.open(path) as d, rasterio.open(paths.SAMPLE) as t:
        a = d.read(1)
        checks.append(("crs", d.crs == t.crs == "EPSG:32611", str(d.crs)))
        checks.append(("shape", (d.height, d.width) == (t.height, t.width), f"{d.height}x{d.width}"))
        checks.append(("transform", d.transform == t.transform, str(tuple(d.transform)[:6])))
        checks.append(("band_count", d.count == 1, str(d.count)))
        checks.append(("dtype", d.dtypes[0] == "float32", d.dtypes[0]))
        checks.append(("all_finite", bool(np.isfinite(a).all()), f"nan={int((~np.isfinite(a)).sum())}"))
        checks.append(("range", bool(a.min() >= 0.0 and a.max() <= 1.0), f"[{a.min()},{a.max()}]"))
        checks.append(("values_binary", bool(np.isin(a, [0.0, 1.0]).all()), f"n_pos={int((a > 0).sum())}"))
    return {"checks": [{"name": n, "passed": bool(p), "detail": s} for n, p, s in checks],
            "all_passed": all(p for _, p, _ in checks)}


def overlap_audit(dots: np.ndarray, max_files: int = 40) -> dict:
    """Dot-halo and smoothed-surface agreement against every local registry raster."""
    from scipy.ndimage import gaussian_filter, distance_transform_edt
    from scipy.stats import spearmanr

    d_dots = distance_transform_edt(~dots)
    smooth = gaussian_filter(dots.astype("float32"), 10.0)
    rows = []
    files = list((REPO / "docs/downloads").rglob("*.tif")) + list((REPO / "downloads").rglob("*.tif"))
    files += list((REPO / "submissions").rglob("*.tif")) + list((REPO / "candidate").rglob("*.tif"))
    seen = set()
    for p in files[:max_files]:
        if p.name in seen:
            continue
        seen.add(p.name)
        try:
            with rasterio.open(p) as d:
                b = d.read(1)
        except Exception:
            continue
        if b.shape != dots.shape:
            continue
        b = np.where(np.isfinite(b), b, 0.0)
        q = b > 0
        if not q.any():
            continue
        frac = float((d_dots[q] <= 3).mean()) if q.sum() <= 5_000_000 else None
        frac_mine = float((distance_transform_edt(~q)[dots] <= 3).mean())
        rho = float(spearmanr(smooth.ravel(), gaussian_filter(b.astype("float32"), 10.0).ravel()).statistic)
        rows.append({"file": p.name, "other_dots": int(q.sum()),
                     "frac_my_dots_within_3px_of_other": frac_mine,
                     "frac_other_dots_within_3px_of_mine": frac,
                     "smoothed_spearman": rho})
    rows.sort(key=lambda r: -r["frac_my_dots_within_3px_of_other"])
    return {"measured_files": len(rows), "top10": rows[:10],
            "max_frac_my_dots_within_3px": rows[0]["frac_my_dots_within_3px_of_other"] if rows else None,
            "max_smoothed_spearman": max((r["smoothed_spearman"] for r in rows), default=None)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dots", type=int, default=150_000)
    ap.add_argument("--min-dist", type=float, default=3.0)
    ap.add_argument("--out", default="submissions/wbg5-sgmc-topo-poisson150k-20261031-zeros.tif")
    ap.add_argument("--verify", metavar="TIF", default=None,
                    help="re-check saved bytes only; needs no organizer stack or /tmp cache")
    args = ap.parse_args()

    if args.verify:
        report = verify_standalone(Path(args.verify))
        print(json.dumps(report, indent=2))
        return 0 if report["all_passed"] else 1

    if not Path(paths.FEATURES).exists():
        print(json.dumps({
            "status": "INPUTS_UNAVAILABLE",
            "needed": {"training_features": str(paths.FEATURES),
                       "sample_submission": str(paths.SAMPLE),
                       "feature_arrays": "/tmp/wbg/{X,lidar,rad,footprint,catalogue}.npy"},
            "why": "The organizer stack is an authenticated 419 MB download and is not committed. "
                   "Use --verify submissions/wbg5-sgmc-topo-poisson150k-20261031-zeros.tif to re-check the "
                   "saved deliverable without rebuilding it.",
            "rebuild_docs": "research/wbg5_findings.md section 9"}, indent=2))
        return 3

    masks = grid.load_masks()
    X = grid.feature_stack()
    L = grid.lidar_stack()
    R = grid.rad_stack()
    feats = build_features(masks, X, L, R)
    model, model_info = train_sgmc_prior(masks, feats)
    topo = priors.topography(masks)
    prior = 0.6 * model + 0.4 * topo
    domain = masks.footprint & ~masks.catalogue
    dots = evaluate.poisson_disk(prior, args.dots, domain, args.min_dist)

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    write_tif(out, dots, paths.SAMPLE)
    val = validate(out)
    audit = overlap_audit(dots)

    # Independent-fault-map evidence (SGMC faults >300 m from the catalogue)
    truth = grid.sgmc_offcatalogue(masks)
    active = masks.footprint & ~masks.catalogue
    res = fast_dti(dots.astype("float32"), truth, active)
    evidence = {
        "schema": "wbg5.run-card.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "WBG5-SGMC-TOPO-POISSON",
        "hypothesis": ("Unmapped faults express as topographic lineaments (detrended-elevation slope) "
                       "and as structures that an independent state geologic map already records; a "
                       "fault-likeness classifier trained only on that independent map, blended with "
                       "topography, places a 300 m-spaced dot lattice on unmapped fault habitat."),
        "mechanism": ("0.6 * HistGradientBoosting P(fault|19 organizer bands, 11 lidar scarp bands, 8 "
                      "radiometric bands, distances) trained on USGS SGMC state-map faults + 0.4 * "
                      "detrended-elevation percentile, Poisson-disk sampled at 3 px."),
        "named_non_fault_mimic": ("Fluvial terrace risers, landslide headwalls, lake shorelines, "
                                  "road cuts and lithologic contacts produce the same topographic steps."),
        "inputs_verified": verify_inputs() if Path(paths.FEATURES).exists() else "not re-checked",
        "model": model_info,
        "dots": int(dots.sum()),
        "min_spacing_px": args.min_dist,
        "sgmc_proxy": {"evidence_class": "SGMC-PROXY-DTI (independent fault map, NOT a leaderboard score)",
                       "truth_px": int(truth.sum()), **{k: res[k] for k in ("tp", "fp", "fn", "dti")}},
        "validator": val,
        "overlap_audit": audit,
        "raster": {"path": str(out.relative_to(REPO)), "sha256": sha256(out), "bytes": out.stat().st_size},
        "verdict": "EMIT_ONLY_SEE_CURATED_RUN_CARD" if val["all_passed"] else "NEGATIVE",
    }
    ev = REPO / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "wbg5_emit_card.json").write_text(json.dumps(evidence, indent=2))
    print(json.dumps({k: evidence[k] for k in ("dots", "sgmc_proxy", "raster", "verdict")}, indent=2))
    print("validator:", val["all_passed"], "worst overlap:",
          audit["top10"][0] if audit["top10"] else None)
    return 0 if val["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
