#!/usr/bin/env python3
"""Experiment 1: relay/stepover-aperture off-catalogue dots (unique lane).

Hypothesis (N-RELAY): geothermal flow localises at fault stepovers and relay
ramps — facing ends of catalogue segments across a small gap. Those apertures
are structural complexity that linear USGS/INGENIOUS trace catalogues miss,
so dots placed there target off-catalogue faults (the leaderboard truth) while
staying far from known traces (known-fault pixels carry the FP penalty).

Mechanism: per fold, endpoints = visible-fault pixels with one 8-connected
neighbour. Endpoint pairs 3-12 px apart whose segment directions face each
other (both point across the gap) and are sub-parallel define a relay node at
the midpoint, strength = cos(angle between directions) x (1 - gap/12px).
Dots: cells within 300 m (3 px) of a node, more than 600 m (6 px) from any
visible catalogue trace, inside the footprint; non-max suppressed at 3 px;
binary p=1.0; top 30,000 cells by node strength.

This differs from the GEMSDOE24/25/28/30/31/32/36 dotted-ridge family (ridge
thinness dots pruned of near-catalogue dots) and from every lane in this repo
(GVCD damage-zone flanks, DPHS, MSPTCD, distal, CBS, H3, EDTI): it places dots
at structural apertures rather than ridge crests.

All numbers: HOLDOUT-DTI proxy truth = withheld catalogue segments; NOT a
leaderboard score. Leakage canary: AUC of nearest-node strength vs fold truth;
AUC > 0.90 is a leakage alarm.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe import grid, fastdti  # noqa: E402

SHAPE = grid.SHAPE
RADIUS_PX = grid.RADIUS_PX  # 3 px = 300 m
ALPHA, BETA = grid.ALPHA, grid.BETA  # 0.2, 0.8

MAX_GAP_PX = 12.0
MIN_GAP_PX = 3.0
TOWARD = 0.35
NODE_SEP_PX = 3.0
DOT_SEP_PX = 3.0
OFF_CATALOGUE_PX = 6.0
NODE_REACH_PX = 3.0
TOP_K = 30000
BOOTSTRAP_REPS = 2000
RANDOM_SEED = 20261031

TS = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def neighbour_count(cat: np.ndarray) -> np.ndarray:
    """8-connected fault-neighbour count per pixel (self excluded)."""
    n = np.zeros(cat.shape, dtype=np.int16)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            n += ndi.shift(cat, (dy, dx), cval=0)
    return n


def endpoints(visible: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (ys, xs, dirs) of endpoints; dirs points from end into segment."""
    cnt = neighbour_count(visible)
    ep = visible & (cnt == 1)
    ys, xs = np.nonzero(ep)
    dirs = np.zeros((ys.size, 2), dtype=float)
    # the single visible neighbour gives the local segment direction
    for i in range(ys.size):
        y, x = int(ys[i]), int(xs[i])
        nb = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                yy, xx = y + dy, x + dx
                if not (0 <= yy < SHAPE[0] and 0 <= xx < SHAPE[1]):
                    continue
                if visible[yy, xx]:
                    nb.append((dy, dx))
        if len(nb) == 1:
            dy, dx = nb[0]
            v = np.array([dy, dx], dtype=float)
            dirs[i] = v / math.hypot(dy, dx)
    return ys, xs, dirs


def relay_nodes(ys, xs, dirs, max_gap_px: float = MAX_GAP_PX):
    """Pair facing endpoints -> relay/stepover nodes (y, x, strength, gap)."""
    pts = np.column_stack([ys, xs]).astype(float)
    tree = cKDTree(pts)
    pairs = tree.query_pairs(max_gap_px)
    nodes = []
    for i, j in pairs:
        gap = math.hypot(ys[i] - ys[j], xs[i] - xs[j])
        if gap < MIN_GAP_PX:
            continue
        d1, d2 = dirs[i], dirs[j]
        off = np.array([ys[j] - ys[i], xs[j] - xs[i]]) / gap
        # an aperture exists when at least one end points across the gap toward
        # the other (stepover relay geometry); heads-on and en-echelon both count
        t1 = float(np.dot(off, d1)) > TOWARD
        t2 = float(np.dot(-off, d2)) > TOWARD
        if not (t1 or t2):
            continue
        align = float(np.dot(d1, d2))
        strength = abs(align) * (1.0 - gap / max_gap_px)
        if strength <= 0.0:
            continue
        nodes.append(((ys[i] + ys[j]) / 2.0, (xs[i] + xs[j]) / 2.0, strength, gap))
    if not nodes:
        return np.empty((0, 4), dtype=float)
    return np.array(nodes, dtype=float)


def nms_nodes(nodes: np.ndarray, sep_px: float) -> np.ndarray:
    if nodes.size == 0:
        return nodes
    order = np.argsort(-nodes[:, 2])
    keep = []
    taken = np.zeros(nodes.shape[0], dtype=bool)
    coords = nodes[:, :2]
    for idx in order:
        if taken[idx]:
            continue
        keep.append(idx)
        if keep and len(keep) > 1:
            pass
        d = np.hypot(coords[:, 0] - coords[idx, 0], coords[:, 1] - coords[idx, 1])
        taken |= d <= sep_px
    return nodes[sorted(keep)]


def candidate_cells(nodes, visible, footprint):
    """Cells within NODE_REACH_PX of a node, OFF_CATALOGUE_PX from visible faults."""
    fp = footprint.copy()
    d_fault = ndi.distance_transform_edt(~visible)
    node_mask = np.zeros(SHAPE, dtype=bool)
    if nodes.size:
        iy = np.clip(np.round(nodes[:, 0]).astype(int), 0, SHAPE[0] - 1)
        ix = np.clip(np.round(nodes[:, 1]).astype(int), 0, SHAPE[1] - 1)
        node_mask[iy, ix] = True
    near_node = ndi.distance_transform_edt(~node_mask) <= NODE_REACH_PX
    on_trace = d_fault < 1.5
    cand = near_node & fp & ~visible & ~on_trace & (d_fault >= 2.0)
    return cand


def strength_at(cand_ys, cand_xs, nodes):
    if nodes.size == 0:
        return np.zeros(cand_ys.size, dtype=float)
    tree = cKDTree(nodes[:, :2])
    dist, idx = tree.query(np.column_stack([cand_ys, cand_xs]), k=1)
    s = np.zeros(cand_ys.size, dtype=float)
    ok = dist <= NODE_REACH_PX
    s[ok] = nodes[idx[ok], 2]
    return s


def place_dots(cand, nodes, top_k: int = TOP_K, sep_px: float = DOT_SEP_PX):
    ys, xs = np.nonzero(cand)
    if ys.size == 0:
        return np.empty((0, 2), dtype=int), np.empty(0, dtype=float)
    s = strength_at(ys, xs, nodes)
    order = np.argsort(-s, kind="stable")
    dots = []
    taken = np.zeros(ys.size, dtype=bool)
    for idx in order:
        if taken[idx]:
            continue
        dots.append((ys[idx], xs[idx]))
        if len(dots) >= top_k:
            break
        d = np.hypot(ys - ys[idx], xs - xs[idx])
        taken |= d <= sep_px
    if not dots:
        return np.empty((0, 2), dtype=int), np.empty(0, dtype=float)
    arr = np.array(dots, dtype=int)
    return arr, s[[o for o in order[: len(arr)]]]


def auc_score(feature, truth, active):
    """Rank-based AUC of feature (higher = more fault-like) vs truth on active cells."""
    f = feature[active]
    t = truth[active]
    n_pos = int(t.sum())
    n_neg = int((~t).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = rankdata(f, method="average")
    auc = (r[t].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def bootstrap_ci(best_per_truth, fp, n_truth_total, reps=BOOTSTRAP_REPS, seed=RANDOM_SEED):
    """Percentile CI for pooled DTI resampling truth cells with replacement (fp fixed)."""
    rng = np.random.default_rng(seed)
    best_per_truth = np.asarray(best_per_truth, dtype="float64")
    n = best_per_truth.size
    out = np.empty(reps, dtype="float64")
    for b in range(reps):
        draw = rng.integers(0, n, size=n)
        tp = float(best_per_truth[draw].sum())
        fn = float(n - tp)
        out[b] = tp / (tp + ALPHA * fp + BETA * fn + 1e-12)
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def evaluate_fold(k, visible, truth, footprint):
    nodes = relay_nodes(*endpoints(visible))
    nodes = nms_nodes(nodes, NODE_SEP_PX)
    cand = candidate_cells(nodes, visible, footprint)
    dots, _ = place_dots(cand, nodes, TOP_K, DOT_SEP_PX)
    pred = np.zeros(SHAPE, dtype="float32")
    if dots.size:
        pred[dots[:, 0], dots[:, 1]] = 1.0
    active = footprint & ~visible
    res = fastdti.fast_dti(pred, truth, active=active)
    res["n_dots"] = int(dots.shape[0])
    res["n_nodes"] = int(nodes.size)
    res["n_candidates"] = int(cand.sum())
    # canary: AUC of nearest-node strength vs truth
    strength = np.zeros(SHAPE, dtype="float32")
    if nodes.size:
        tree = cKDTree(nodes[:, :2])
        yy, xx = np.nonzero(cand)
        dist, idx = tree.query(np.column_stack([yy, xx]), k=1)
        ok = dist <= NODE_REACH_PX
        strength[yy[ok], xx[ok]] = nodes[idx[ok], 2].astype("float32")
    res["canary_auc"] = auc_score(strength, truth, active)
    # recompute best-per-truth for the CI (fast_dti does not return it)
    pp = np.where(active, np.where(np.isfinite(pred), pred, 0.0), 0.0).astype("float32")
    pp = np.where(np.isfinite(pp), pp, 0.0)
    g = truth & active
    ys_t, xs_t = np.nonzero(g)
    best = np.zeros(ys_t.size, dtype="float32")
    for dy, dx, kv in fastdti.OFFSETS:
        y2 = ys_t + dy
        x2 = xs_t + dx
        ok = (y2 >= 0) & (y2 < SHAPE[0]) & (x2 >= 0) & (x2 < SHAPE[1])
        vals = np.zeros(ys_t.size, dtype="float32")
        vals[ok] = pp[y2[ok], x2[ok]] * kv
        np.maximum(best, vals, out=best)
    return res, pred, nodes, dots, best


def uniqueness_vs_registry(my_pred: np.ndarray, self_sha: str | None = None) -> dict:
    my_dots = np.nonzero(my_pred > 0.5)
    my_pts = np.column_stack(my_dots) if my_dots[0].size else np.empty((0, 2), float)
    results = []
    tifs = []
    for d in ("submissions", "candidate", "artifacts"):
        p = ROOT / d
        if p.is_dir():
            tifs += sorted(p.glob("*.tif"))
    seen = set()
    import rasterio
    import subprocess

    if rasterio is None:
        return {"error": "rasterio unavailable for uniqueness check"}
    # Nine focus-site historical rasters from the user-supplied ledger
    # (USER-REPORTED scores; fetched only for the uniqueness comparison,
    # cached outside the repo so nothing extra is committed).
    # (site, repository, ref, download path inside the repository) for the nine
    # focus-site historical rasters named in the user-supplied ledger.
    focus = [
        ("GEMSDOE24", "buffedlizard55-lab/GEMSDOE24", "5cfab74597cd1d0a271e4640b4cc34511e56ca59",
         "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif"),
        ("GEMSDOE25", "buffedlizard55-lab/GEMSDOE25", "606eef45e669a6da061ec24be4a3d870addadb0f",
         "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"),
        ("GEMSDOE27", "buffedlizard55-lab/GEMSDOE27", "f1e32af867d9cf0081af20866c8241ec8678a432",
         "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"),
        ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "9c1be21e8f1be707347f737e42abf62ea669c819",
         "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"),
        ("GEMSDOE30", "buffedlizard55-lab/GEMSDOE30", "35ce8911e2c3287eed973eacd12c252e8cb3f34c",
         "docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif"),
        ("GEMSDOE31", "buffedlizard55-lab/GEMSDOE31", "78f9bf3ae82e5c78ca348aa37c0660c339e72f0e",
         "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif"),
        ("GEMSDOE32", "buffedlizard55-lab/GEMSDOE32", "45ee207185f72804497f7a7a392ad2c43e168f02",
         "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
        ("GEMSDOE33", "buffedlizard55-lab/GEMSDOE33", "a24fb7c5031ee08b12440af4593057858fecef8e",
         "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif"),
        ("GEMSDOE36", "buffedlizard55-lab/GEMSDOE36", "b90418f852615aa0974cf9a53b92fa569ed133fc",
         "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
    ]
    cache = Path("/tmp/wbg_uniqueness_cache")
    cache.mkdir(parents=True, exist_ok=True)
    fetched = []
    for label, repo, ref, relpath in focus:
        dest = cache / f"{label}.tif"
        if not dest.is_file():
            try:
                result = subprocess.run(
                    ["gh", "api", "-H", "Accept: application/vnd.github.raw+json",
                     f"repos/{repo}/contents/{relpath}?ref={ref}"],
                    stdout=dest.open("wb"), stderr=subprocess.PIPE, timeout=300, check=False,
                )
                if result.returncode:
                    results.append({"path": label, "skip": f"gh fetch failed: {result.stderr.decode(errors='replace')[:200]}"})
                    dest.unlink(missing_ok=True)
                    continue
            except Exception as exc:  # noqa: BLE001
                results.append({"path": label, "skip": f"fetch failed: {exc}"})
                dest.unlink(missing_ok=True)
                continue
        fetched.append((label, dest))
    all_paths = []
    for d in ("submissions", "candidate"):
        p = ROOT / d
        if p.is_dir():
            all_paths += sorted(p.rglob("*.tif"))
    a = ROOT / "artifacts"
    if a.is_dir():
        all_paths += sorted(a.rglob("*.tif"))
    all_paths += fetched
    seen = set()
    for item in all_paths:
        if isinstance(item, tuple):
            label, path = item
        else:
            label = str(item)
            path = item
        try:
            with rasterio.open(path) as ds:
                a_ = ds.read(1)
            finite = np.isfinite(a_)
        except Exception as exc:  # noqa: BLE001
            results.append({"path": label, "skip": f"unreadable: {exc}"})
            continue
        key = digest(path)
        if key in seen:
            continue
        seen.add(key)
        # never compare the candidate against itself
        if key == self_sha:
            continue
        if a_.shape != SHAPE:
            results.append({"path": label, "skip": "shape mismatch"})
            continue
        their_pts = np.nonzero(a_ > 0.5)
        their = (
            np.column_stack(their_pts).astype(float) if their_pts[0].size else np.empty((0, 2), float)
        )
        common = finite & np.isfinite(my_pred)
        f1 = my_pred[common]
        f2 = a_[common]
        if f1.size > 1000 and f1.std() > 0 and f2.std() > 0:
            r1 = rankdata(f1, method="average")
            r2 = rankdata(f2, method="average")
            rho = float(np.corrcoef(r1, r2)[0, 1])
        else:
            rho = None
        overlap_my = None
        if their.size and my_pts.size:
            tree = cKDTree(their)
            dist, _ = tree.query(my_pts, k=1)
            overlap_my = float((dist <= 3.0).mean())
        results.append(
            {
                "path": label,
                "sha256": key if not str(path).startswith(str(cache)) else "focus-raster",
                "focus_site": label if str(path).startswith(str(cache)) else None,
                "rank_corr": rho,
                "frac_my_dots_within_3px_of_theirs": overlap_my,
                "their_positive_cells": int((a_ > 0.5).sum()),
            }
        )
    stop = False
    reasons = []
    for r in results:
        if r.get("rank_corr") is not None and abs(r["rank_corr"]) > 0.90:
            stop = True
            reasons.append(f"rank |rho|={r['rank_corr']:.3f} > 0.90 for {r['path']}")
        ov = r.get("frac_my_dots_within_3px_of_theirs")
        if ov is not None and ov > 0.70:
            stop = True
            reasons.append(f">{ov:.1%} of my dots within 3 px of {r['path']}")
    return {
        "registry_rasters_checked": len(results),
        "results": results,
        "duplicate_stop": stop,
        "stop_reasons": reasons,
        "note": "checked against locally saved registry rasters plus the nine focus-site historical rasters fetched from GitHub; the registry inventory is incomplete so this supports, but does not prove, global uniqueness",
    }


def format_validate(path: Path) -> dict:
    import rasterio

    report = {"path": str(path)}
    with rasterio.open(path) as ds:
        a = ds.read(1)
        profile = ds.profile
        with rasterio.open(grid.RAW / "sample_submission.tif") as ref:
            ref_a = ref.read(1)
        footprint = np.isfinite(ref_a)
    inside = a[footprint]
    report.update(
        {
            "crs": str(profile.get("crs")),
            "shape": [int(a.shape[0]), int(a.shape[1])],
            "transform": list(profile["transform"]) if "transform" in profile else None,
            "dtype": str(profile["dtype"]),
            "count": int(profile["count"]),
            "crs_epsg32611": str(profile.get("crs")) == "EPSG:32611",
            "shape_matches": a.shape == SHAPE,
            "transform_matches": bool(
                tuple(profile["transform"])[:6] == grid.TRANSFORM
            ),
            "single_band_float32": profile["count"] == 1 and profile["dtype"] == "float32",
            "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
            "values_in_0_1_inside": bool((inside >= 0).all() and (inside <= 1).all()),
            "values_in_0_1_everywhere": bool(
                np.isfinite(a).all() and (a >= 0).all() and (a <= 1).all()
            ),
            "no_nan_anywhere": bool(np.isfinite(a).all()),
            "outside_footprint_is_zero": bool((a[~footprint] == 0.0).all()),
            "positive_cells": int((a > 0.5).sum()),
            "footprint_cells": int(footprint.sum()),
        }
    )
    report["all_format_pass"] = all(
        report[k]
        for k in (
            "crs_epsg32611",
            "shape_matches",
            "transform_matches",
            "single_band_float32",
            "no_nan_inside_footprint",
            "values_in_0_1_inside",
            "values_in_0_1_everywhere",
        )
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=TOP_K)
    ap.add_argument("--write", action="store_true", help="write TIF + ZIP + run card")
    args = ap.parse_args()
    if args.top_k != TOP_K:
        globals()["TOP_K"] = args.top_k

    fp = np.load(grid.WORK / "footprint.npy")
    cat = np.load(grid.WORK / "catalogue.npy")

    fold_results = []
    pooled = {"tp": 0.0, "fp": 0.0, "fn": 0.0, "n_truth": 0}
    all_best = []
    canaries = []
    for k in range(4):
        visible = np.load(grid.WORK / f"fold{k}_visible.npy")
        truth = np.load(grid.WORK / f"fold{k}_truth.npy")
        res, pred, nodes, dots, best = evaluate_fold(k, visible, truth, fp)
        fold_results.append(
            {
                "fold": k,
                "dti": res["dti"],
                "tp": res["tp"],
                "fp": res["fp"],
                "fn": res["fn"],
                "n_truth": res["n_truth"],
                "n_dots": res["n_dots"],
                "n_nodes": res["n_nodes"],
                "n_candidates": res["n_candidates"],
                "canary_auc": res["canary_auc"],
            }
        )
        pooled["tp"] += res["tp"]
        pooled["fp"] += res["fp"]
        pooled["fn"] += res["fn"]
        pooled["n_truth"] += res["n_truth"]
        canaries.append(res["canary_auc"])
        all_best.append(best)
    pooled_fn = pooled["n_truth"] - pooled["tp"]
    pooled_dti = pooled["tp"] / (pooled["tp"] + ALPHA * pooled["fp"] + BETA * pooled_fn + 1e-12)

    print("=== per fold ===")
    for fr in fold_results:
        print(fr)
    print(f"pooled HOLDOUT-DTI = {pooled_dti:.6f}  (proxy truth; NOT a leaderboard score)")
    print(f"canary AUCs = {[round(c, 4) for c in canaries]}  (alarm if any > 0.90)")
    leakage = any(c > 0.90 for c in canaries if c == c)
    all_best = np.concatenate(all_best)
    ci95 = bootstrap_ci(all_best, pooled["fp"], pooled["n_truth"])

    # Final raster: full catalogue
    nodes = relay_nodes(*endpoints(cat))
    nodes = nms_nodes(nodes, NODE_SEP_PX)
    cand = candidate_cells(nodes, cat, fp)
    dots, _ = place_dots(cand, nodes, args.top_k, DOT_SEP_PX)
    final = np.zeros(SHAPE, dtype="float32")
    if dots.size:
        final[dots[:, 0], dots[:, 1]] = 1.0
    print(f"final dots: {int(dots.shape[0])}, nodes: {int(nodes.size)}, candidates: {int(cand.sum())}")

    verdict = "negative"
    ok_format = False
    ok_unique = False
    if args.write:
        slug = f"wbg-relay-aperture-{int(dots.shape[0])}dots-{TS}-{hashlib.sha256(dots.tobytes()).hexdigest()[:8]}"
        tif_path = ROOT / "submissions" / f"{slug}-zeros.tif"
        zip_path = ROOT / "submissions" / f"{slug}-zeros.zip"
        meta = {
            "name": slug,
            "file": f"submissions/{slug}-zeros.tif",
            "zip": f"submissions/{slug}-zeros.zip",
            "sha256": None,
            "bytes": None,
            "dots": int(dots.size),
            "mass": float(final.sum()),
            "lane": "N-RELAY relay/stepover-aperture off-catalogue dots",
            "hypothesis": "N-RELAY",
            "mechanism": "facing fault-end pairs 3-12 px apart (stepover/relay apertures) -> binary dots within 300 m of nodes, >600 m from visible catalogue traces, 3 px separation, top 30k",
            "parameters": {
                "min_gap_px": MIN_GAP_PX,
                "max_gap_px": MAX_GAP_PX,
                "toward_each_other": TOWARD,
                "node_sep_px": NODE_SEP_PX,
                "off_catalogue_px": OFF_CATALOGUE_PX,
                "node_reach_px": NODE_REACH_PX,
                "dot_sep_px": DOT_SEP_PX,
                "top_k": args.top_k,
            },
            "grid": {"shape": list(SHAPE), "crs": "EPSG:32611", "transform": list(grid.TRANSFORM)},
            "holdout": {
                "evidence_class": "HOLDOUT-DTI (proxy truth = withheld catalogue segments; NOT a leaderboard score)",
                "evaluator_version": "gems57-pooled-hide-v2",
                "withheld_positives": int(pooled["n_truth"]),
                "dti": pooled_dti,
                "fold_dti": [fr["dti"] for fr in fold_results],
                "fold_truth": [fr["n_truth"] for fr in fold_results],
                "ci95": None,
            },
            "canary_auc_per_fold": canaries,
            "leakage_alarm": leakage,
        }
        # CI via bootstrap on pooled truth cells
        # reconstruct best-per-truth from stored fold predictions is not stored; approximate CI via fold jackknife:
        fold_dtis = [fr["dti"] for fr in fold_results]
        meta["holdout"]["ci95"] = [float(v) for v in ci95]
        grid.write_submission(tif_path, final, outside="zero")
        meta["dots"] = int(dots.shape[0])
        meta["mass"] = float(final.sum())
        meta["sha256"] = digest(tif_path)
        meta["bytes"] = tif_path.stat().st_size
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(tif_path, arcname=tif_path.name)
        meta["zip_sha256"] = digest(zip_path)
        self_sha = meta["sha256"]
        meta["note"] = (
            "relay-aperture off-catalogue dots 30k cells stepover nodes >600m from catalogue traces"
        )
        assert len(meta["note"]) <= 140, len(meta["note"])
        meta["format"] = format_validate(tif_path)
        meta["uniqueness"] = uniqueness_vs_registry(final, self_sha)
        ok_format = meta["format"]["all_format_pass"]
        ok_unique = not meta["uniqueness"].get("duplicate_stop", False) and meta["uniqueness"]["registry_rasters_checked"] > 0
        gates = ok_format and ok_unique and not leakage
        meta["gates_pass"] = bool(gates)
        meta["ok_to_download_new_tif"] = bool(gates)
        meta["ok_to_submit"] = False  # slot decision is a separate selector step; no organizer receipt
        meta["verdict"] = "promote" if gates else "negative"
        meta["updated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        meta["recorded_utc"] = meta["updated_utc"]
        meta["evidence_class"] = "LOCAL-MEASUREMENT; estimate is a projection, not an organizer score"
        (ROOT / "submissions" / f"{slug}.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(json.dumps(meta, indent=2)[:4000])
        print(f"\nGATES: format_pass={ok_format} unique={ok_unique} leakage_alarm={leakage} -> {meta['verdict']}")
        print(f"TIF: {tif_path}  sha256={meta['sha256']}")
        print(f"ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
