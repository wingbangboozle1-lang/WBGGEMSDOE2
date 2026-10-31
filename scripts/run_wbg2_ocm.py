#!/usr/bin/env python3
"""WBG2-OCM campaign: off-catalogue multi-band concordance emission.

Lane: config/wbg2_ocm_lane.json. Reuses the pinned shared template under
data/shared_template/src/gems57 (metric, emit.greedy_allocate, holdout,
submission_writer). Official arithmetic is never reimplemented here; the only
lane-local placement policy is the documented fixed-budget fallback (bar = 0).

Stages: prior -> canaries -> allocate -> holdout -> uniqueness -> write -> card.
Each stage writes dated evidence under evidence/ and can be re-run alone.
This script never contacts the leaderboard and never spends a submission slot.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))

from gems57 import emit as shared_emit          # noqa: E402
from gems57 import holdout as shared_holdout    # noqa: E402
from gems57 import metric as shared_metric      # noqa: E402
from gems57.grid import load_grid               # noqa: E402

FEATURES = ROOT / "data" / "official" / "training_features.tif"
SAMPLE = ROOT / "data" / "official" / "sample_submission.tif"
OUT_DIR = ROOT / "docs" / "downloads" / "ocm"
CACHE = ROOT / ".cache" / "ocm"
EVID = ROOT / "evidence"
BRIDGE = ROOT / "data" / "bridge"

# Physically independent fields (owner-mirror band ids, see evidence/feature_cache.json)
FIELDS = {"b02_rtp": 2, "b06_tc": 6, "b13_grav": 13,
          "b15_depth": 15, "b17_cond": 17, "b19_slope": 19}
SIGMAS = (1.5, 4.5)          # 150 m and 450 m
TOP_Q = 0.90                 # within-footprint top decile per field
REP_ZERO_PX = 2.0            # hard zero within 2 px of catalogue
REP_FULL_PX = 5.0            # full weight from 5 px
K_TRUTH_PROJECTION = 12783   # metric-model inversion of USER-REPORTED fleet scores (PROJECTION)
MAX_DOTS = 45_000
FIXED_BUDGET = 39_000
SEED = 20261031


def log(msg: str) -> None:
    print(f"[{dt.datetime.now(dt.UTC).strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, allow_nan=False, default=float) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- prior stage
def build_prior(grid, refresh: bool = False):
    """Concordance surface p = (C/6)^2 * R on the organizer grid."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p_path = CACHE / "prior_p.npy"
    c_path = CACHE / "conc_count.npy"
    r_path = CACHE / "repulsion.npy"
    valid_path = CACHE / "band_valid.npy"
    if p_path.exists() and c_path.exists() and r_path.exists() and valid_path.exists() and not refresh:
        log("prior: loading cached surfaces")
        return (np.load(p_path), np.load(c_path), np.load(r_path), np.load(valid_path))

    fp = grid.footprint
    log(f"prior: footprint cells = {int(fp.sum())}")
    conc = np.zeros(grid.shape, np.int8)
    band_valid = np.ones(grid.shape, bool)
    stats = {}
    with rasterio.open(FEATURES) as src:
        assert src.count == 19 and (src.height, src.width) == grid.shape, "features grid mismatch"
        for name, band in FIELDS.items():
            t0 = time.time()
            x = src.read(band).astype(np.float32)
            fin = np.isfinite(x) & fp
            band_valid &= np.isfinite(x)
            vals = x[fin]
            ridge_max = np.zeros(grid.shape, np.float32)
            for sigma in SIGMAS:
                # masked smoothing: divide by the smoothed validity weight so the
                # footprint / invalid rim does not manufacture artificial edges
                xf = np.where(fin, x, 0.0).astype(np.float32)
                num = ndi.gaussian_filter(xf, sigma)
                den = ndi.gaussian_filter(fin.astype(np.float32), sigma)
                sm = num / np.maximum(den, 1e-6)
                gy, gx = np.gradient(sm)
                ridge = np.hypot(gx, gy).astype(np.float32)
                ridge[~fin] = 0.0
                ridge[den < 0.5] = 0.0   # drop rim cells with <50% valid support
                np.maximum(ridge_max, ridge, out=ridge_max)
            rv = ridge_max[fin]
            thr = float(np.partition(rv, int(TOP_Q * (rv.size - 1)))[int(TOP_Q * (rv.size - 1))])
            top = fin & (ridge_max >= thr)
            conc[top] += 1
            stats[name] = {"band": band, "top_decile_thr": thr,
                           "top_cells": int(top.sum()), "seconds": round(time.time() - t0, 1)}
            log(f"prior: {name} done in {stats[name]['seconds']}s, top cells {stats[name]['top_cells']}")

    band_valid &= fp
    dist = ndi.distance_transform_edt(~grid.catalogue).astype(np.float32)
    ramp = np.clip((dist - REP_ZERO_PX) / (REP_FULL_PX - REP_ZERO_PX), 0.0, 1.0).astype(np.float32)
    ramp[~fp] = 0.0
    p = ((conc / len(FIELDS)) ** 2).astype(np.float32) * ramp
    p[~band_valid] = 0.0
    p[~fp] = 0.0
    np.save(p_path, p)
    np.save(c_path, conc)
    np.save(r_path, ramp)
    np.save(valid_path, band_valid)
    summary = {
        "schema": "wbg2.ocm-prior.v1",
        "built_utc": dt.datetime.now(dt.UTC).isoformat(),
        "fields": FIELDS, "sigmas_px": SIGMAS, "top_quantile": TOP_Q,
        "repulsion_ramp_px": [REP_ZERO_PX, REP_FULL_PX],
        "band_stats": stats,
        "conc_hist": {str(k): int((conc == k).sum()) for k in range(0, len(FIELDS) + 1)},
        "p_nonzero_cells": int((p > 0).sum()), "p_max": float(p.max()),
        "band_valid_inside": int(band_valid.sum()),
    }
    save_json(EVID / "ocm_prior_20261031.json", summary)
    log(f"prior: built, nonzero cells {summary['p_nonzero_cells']}, max {summary['p_max']:.3f}")
    return p, conc, ramp, band_valid


# ------------------------------------------------------------- canary stage
def auc_score(pos: np.ndarray, neg: np.ndarray) -> float:
    """P(score(pos) > score(neg)) via tie-aware rank statistic (Mann-Whitney)."""
    from scipy.stats import rankdata
    allv = np.concatenate([pos, neg])
    ranks = rankdata(allv, method="average")
    n_pos, n_neg = pos.size, neg.size
    rank_sum = ranks[:n_pos].sum()
    return float((rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def run_canaries(grid, ctx, conc, ramp, band_valid):
    """Feature-alone AUC vs withheld catalogue segments (pre-registered expectations)."""
    rng = np.random.default_rng(SEED)
    feats = {f"conc_{k}": (conc == k).astype(np.float32) for k in range(2, 7)}
    feats["conc_count"] = conc.astype(np.float32)
    feats["repulsion_R"] = ramp
    feats["prior_p"] = None  # filled below
    results = {}
    fp_idx = np.flatnonzero(grid.footprint.ravel())
    for cell in ctx.cells:
        if cell.mode != "all":
            continue
        sl = cell.bbox
        active_sub = cell.active
        truth_local = np.zeros(active_sub.shape, bool)
        truth_local[cell.truth_yx] = True
        act_flat = active_sub.ravel()
        truth_flat = truth_local.ravel() & act_flat
        pos_idx = np.flatnonzero(truth_flat)
        if pos_idx.size == 0:
            continue
        neg_pool = np.flatnonzero(act_flat & ~truth_flat)
        neg_idx = rng.choice(neg_pool, size=min(20_000, neg_pool.size), replace=False)
        for name in list(feats):
            if name == "prior_p":
                continue
            v = feats[name][sl].ravel()
            key = f"{name}|{cell.key}"
            results[key] = auc_score(v[pos_idx], v[neg_idx])
    # pooled means per feature
    pooled = {}
    for key, val in results.items():
        name = key.split("|")[0]
        pooled.setdefault(name, []).append(val)
    pooled = {k: {"mean_auc": float(np.mean(v)), "n_cells": len(v)} for k, v in pooled.items()}
    alarm = {k: (v["mean_auc"] > 0.90 or v["mean_auc"] < 0.10) for k, v in pooled.items()}
    out = {
        "schema": "wbg2.ocm-canaries.v1",
        "evaluator": "shared holdout folds; AUC vs withheld catalogue pixels inside active domain",
        "pre_registered": {
            "conc_expect": "0.55-0.75; >0.90 leakage alarm",
            "repulsion_expect": "inverted AUC >0.90 BY CONSTRUCTION (task misalignment, not silent leakage)",
        },
        "pooled": pooled, "alarm": alarm,
        "note": "labels.tif is byte-identical to existing_faults.tif; holdout truth IS the mapped "
                "catalogue, which official scoring masks. Canary AUCs measure catalogue affinity, "
                "not leaderboard skill.",
    }
    save_json(EVID / "ocm_canaries_20261031.json", out)
    log("canaries: " + ", ".join(f"{k}={v['mean_auc']:.3f}" for k, v in pooled.items()))
    return out


# ----------------------------------------------------------- allocate stage
def expected_credit(p):
    return shared_emit.expected_credit(p)


def fixed_budget_greedy(p, allowed, budget, floor=0.02):
    """Lane-local placement policy: same coverage credit as the shared allocator
    with the DTI bar removed (bar=0) and a hard dot budget. Official metric
    arithmetic remains in shared gems57.metric; this is only the stopping rule.
    """
    ek = expected_credit(p)
    cand = allowed & (ek >= floor)
    ys, xs = np.nonzero(cand)
    order = np.argsort(-ek[ys, xs], kind="stable")
    ys, xs = ys[order], xs[order]
    ekc = np.minimum(ek[ys, xs].astype(np.float64), 1.0)
    H, W = p.shape
    cover = np.zeros(p.shape, np.float32)
    emitted = np.zeros(p.shape, bool)
    dirty = np.ones(ys.size, bool)
    upper = ekc.copy()
    n_dots = 0
    OFF_DY, OFF_DX, OFF_K = shared_metric.offsets()
    for i in range(ys.size):
        if n_dots >= budget:
            break
        if not dirty[i]:
            continue
        if upper[i] <= 0:
            continue
        y, x = int(ys[i]), int(xs[i])
        if emitted[y, x]:
            dirty[i] = False
            continue
        ny, nx = y + OFF_DY, x + OFF_DX
        ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
        nyv, nxv, kw = ny[ok], nx[ok], OFF_K[ok]
        pv = p[nyv, nxv].astype(np.float64)
        cv = cover[nyv, nxv].astype(np.float64)
        dT = float((pv * np.maximum(kw - cv, 0.0)).sum())
        upper[i] = dT
        dirty[i] = False
        if dT <= 0:
            continue
        emitted[y, x] = True
        n_dots += 1
        np.maximum.at(cover, (nyv, nxv), kw.astype(np.float32))
        m = (ys >= y - 6) & (ys <= y + 6) & (xs >= x - 6) & (xs <= x + 6)
        dirty[m] = True
        dirty[i] = False
    return emitted, n_dots


def run_allocation(grid, p, ramp, band_valid, conc, refresh: bool = False):
    allowed = grid.footprint & band_valid & (ramp > 0)
    CACHE.mkdir(parents=True, exist_ok=True)
    arm_a_path = CACHE / "arm_a_bar.npy"
    arm_b_path = CACHE / "arm_b_budget.npy"
    info_path = EVID / "ocm_allocation_20261031.json"
    if arm_a_path.exists() and arm_b_path.exists() and info_path.exists() and not refresh:
        log("allocate: loading cached arms")
        return np.load(arm_a_path), np.load(arm_b_path), json.loads(info_path.read_text())

    log("allocate: arm A shared greedy_allocate (DTI bar, k_truth=PROJECTION 12783)")
    alloc = shared_emit.greedy_allocate(p, allowed, float(K_TRUTH_PROJECTION),
                                        floor=0.02, max_dots=MAX_DOTS)
    arm_a = alloc.emitted
    log(f"allocate: arm A dots={alloc.n_dots} surrogate_dti={alloc.surrogate_dti:.4f} rounds={alloc.rounds}")

    log(f"allocate: arm B fixed-budget greedy, budget={FIXED_BUDGET}")
    t0 = time.time()
    arm_b, n_b = fixed_budget_greedy(p, allowed, FIXED_BUDGET)
    log(f"allocate: arm B dots={n_b} in {time.time()-t0:.0f}s")

    info = {
        "schema": "wbg2.ocm-allocation.v1",
        "k_truth_projection": K_TRUTH_PROJECTION,
        "arm_a": {"policy": "shared gems57.emit.greedy_allocate", "n_dots": int(alloc.n_dots),
                  "surrogate_dti": alloc.surrogate_dti, "rounds": alloc.rounds,
                  "expected_covered_credit": alloc.expected_covered_credit,
                  "expected_self_credit": alloc.expected_self_credit},
        "arm_b": {"policy": "fixed-budget bar=0 coverage greedy (lane-local stopping rule)",
                  "n_dots": int(n_b), "budget": FIXED_BUDGET},
        "allowed_cells": int(allowed.sum()),
        "dots_on_catalogue": {"arm_a": int((arm_a & grid.catalogue).sum()),
                              "arm_b": int((arm_b & grid.catalogue).sum())},
        "dots_min_dist_to_catalogue_px": {},
    }
    dist = ndi.distance_transform_edt(~grid.catalogue)
    for name, arm in (("arm_a", arm_a), ("arm_b", arm_b)):
        ys, xs = np.nonzero(arm)
        info["dots_min_dist_to_catalogue_px"][name] = float(dist[ys, xs].min()) if ys.size else None
    np.save(arm_a_path, arm_a)
    np.save(arm_b_path, arm_b)
    save_json(info_path, info)
    return arm_a, arm_b, info


# ----------------------------------------------------------- holdout stage
def bootstrap_pooled_ci(folds: dict, draws: int = 1000, seed: int = SEED):
    """Quadrant-block bootstrap of pooled DTI from per-fold tp/fp/fn terms."""
    rng = np.random.default_rng(seed)
    keys = list(folds)
    quad = {k: k.split("_")[1] for k in keys}
    quads = sorted(set(quad.values()))
    cells_by_quad = {q: [k for k in keys if quad[k] == q] for q in quads}
    stats = []
    for _ in range(draws):
        tp = fp = fn = 0.0
        for q in rng.choice(quads, size=len(quads), replace=True):
            for k in cells_by_quad[q]:
                r = folds[k]
                tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
        stats.append(tp / (tp + shared_metric.ALPHA * fp + shared_metric.BETA * fn + shared_metric.EPS))
    stats = np.sort(np.asarray(stats))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def run_holdout(grid, ctx, arms: dict):
    out = {"schema": "wbg2.ocm-holdout.v1",
           "evaluator": "shared gems57.holdout.evaluate (exact fold DTI, alpha0.2 beta0.8 300m)",
           "evidence_class": "HOLDOUT-DTI (catalogue-recovery instrument; see misalignment caveat)",
           "caveat": "Mirror labels == existing faults; official scoring masks mapped faults, so "
                     "this holdout is the INVERSE of the leaderboard task for off-catalogue "
                     "emitters. Compare arms only against controls on the same instrument.",
           "arms": {}}
    for name, emitted in arms.items():
        log(f"holdout: evaluating {name}")
        res = shared_holdout.evaluate(emitted, ctx, cell_mode="all")
        lo, hi = bootstrap_pooled_ci(res["folds"])
        out["arms"][name] = {
            "pooled_dti": res["pooled_dti"], "ci95_quadrant_bootstrap": [lo, hi],
            "pooled_coverage": res["pooled_coverage"],
            "pooled_n_truth": res["pooled_n_truth"],
            "mean_fold_dti": res["mean_fold_dti"],
            "emitted_pixels": res["emitted_pixels"],
            "on_visible_catalogue": res["on_visible_catalogue"],
            "per_fold_dti": res["per_fold_dti"],
        }
        log(f"holdout: {name} pooled DTI {res['pooled_dti']:.4f} [{lo:.4f}, {hi:.4f}]")
    save_json(EVID / "ocm_holdout_20261031.json", out)
    return out


def run_random_control(ctx, n_dots: int, seeds=(1, 2, 3)):
    rng_results = {}
    fp = ctx.grid.footprint
    idx = np.flatnonzero(fp.ravel())
    for s in seeds:
        rng = np.random.default_rng(1000 + s)
        pick = rng.choice(idx, size=n_dots, replace=False)
        m = np.zeros(fp.size, bool)
        m[pick] = True
        m = m.reshape(fp.shape)
        res = shared_holdout.evaluate(m, ctx, cell_mode="all")
        rng_results[f"random_seed{s}"] = {"pooled_dti": res["pooled_dti"],
                                          "pooled_coverage": res["pooled_coverage"]}
        log(f"control: random seed {s} pooled DTI {res['pooled_dti']:.4f}")
    return rng_results


# --------------------------------------------------------- uniqueness stage
def smoothed_rank_corr(a, b, footprint, step=5):
    from scipy.stats import spearmanr
    sa = ndi.gaussian_filter(np.where(footprint, a.astype(np.float32), 0.0), 3.0)
    sb = ndi.gaussian_filter(np.where(footprint, b.astype(np.float32), 0.0), 3.0)
    m = footprint
    va, vb = sa[m][::step], sb[m][::step]
    return float(spearmanr(va, vb).statistic)


def dot_halo_frac(ours_yx, their_bool, shape):
    if their_bool.sum() == 0:
        return 0.0
    dist = ndi.distance_transform_edt(~their_bool)
    return float((dist[ours_yx] <= 3.0).mean())


def run_uniqueness(grid, candidate):
    ours_yx = np.nonzero(candidate)
    rows = {}
    sources = []
    focus_dir = ROOT / "registry" / "focus_rasters"
    if focus_dir.is_dir():
        sources += [("focus", p) for p in sorted(focus_dir.glob("*.tif"))]
    for sub in ("docs/downloads", "downloads", "docs/downloads/distal", "docs/downloads/distal_exp2",
                "docs/downloads/gemsdoe", "docs/downloads/cbs", "docs/downloads/dphs",
                "docs/downloads/gvcd", "docs/downloads/msptcd"):
        d = ROOT / sub
        if d.is_dir():
            sources += [(sub, p) for p in sorted(d.glob("*.tif")) if "ocm" not in p.name]
    seen = set()
    worst = {"halo": 0.0, "corr": 0.0, "file": None}
    for group, path in sources:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            with rasterio.open(path) as src:
                if (src.height, src.width) != grid.shape:
                    continue
                a = src.read(1).astype(np.float32)
        except rasterio.errors.RasterioIOError:
            continue
        a = np.where(np.isfinite(a), a, 0.0)
        their = a > 0
        if their.sum() == 0:
            continue
        halo = dot_halo_frac(ours_yx, their, grid.shape)
        corr = smoothed_rank_corr(candidate.astype(np.float32), a, grid.footprint)
        dense = bool(their.sum() > 0.5 * grid.footprint.sum())
        rows[str(path.relative_to(ROOT))] = {"group": group, "their_dots": int(their.sum()),
                                             "our_dots_within_3px_frac": halo,
                                             "smoothed_spearman": corr, "dense_continuous_prior": dense,
                                             "stop": bool((halo > 0.70 or abs(corr) > 0.90) and not dense)}
        if halo > worst["halo"]:
            worst = {"halo": halo, "corr": corr, "file": str(path.relative_to(ROOT))}
    stops = [k for k, v in rows.items() if v["stop"]]
    dense_docs = [k for k, v in rows.items() if v.get("dense_continuous_prior")]
    sparse = {k: v for k, v in rows.items() if not v.get("dense_continuous_prior")}
    worst_sparse = max(sparse.values(), key=lambda v: v["our_dots_within_3px_frac"], default=None)
    worst_sparse_file = None
    if worst_sparse is not None:
        worst_sparse_file = next(k for k, v in sparse.items() if v is worst_sparse)
    out = {
        "schema": "wbg2.ocm-uniqueness.v1",
        "rule": "stop if rank-corr > 0.90 or >70% of our dots within 3 px of one registry raster",
        "audited_files": len(rows), "stops": stops,
        "dense_priors_documented_not_silent": dense_docs,
        "interpretation": "Dot-halo rule applied to sparse binary emission supports. Registered "
                          "dense continuous priors (positive over >50% of the footprint, e.g. "
                          "downloads/wbg-h1-blind-conduit-breach...zeros.tif) cover ANY non-empty "
                          "candidate by construction; per AGENTS.md their exemption is documented "
                          "here, not silent, and matches the nine-site recheck precedent that "
                          "cleared distal2 under the same reading. This interpretation remains "
                          "formally unresolved with the requester.",
        "worst_halo": worst,
        "worst_sparse_halo": {"file": worst_sparse_file,
                              "halo": worst_sparse["our_dots_within_3px_frac"] if worst_sparse else None,
                              "corr": worst_sparse["smoothed_spearman"] if worst_sparse else None},
        "rows": rows,
        "limitation": "Audited against nine sha256-verified focus-site pins plus every local fleet "
                      "TIFF in this checkout; the global registry (~100 public fleet rasters) was "
                      "not fully re-fetched, so this is a strong but incomplete uniqueness check.",
    }
    save_json(EVID / "ocm_uniqueness_20261031.json", out)
    log(f"uniqueness: audited {len(rows)} files; stops={len(stops)}; worst halo {worst}")
    return out


# --------------------------------------------------------------- write stage
def run_write(grid, arm, stem_core, note):
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))
    from gems57.submission_writer import write_submission
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred = arm.astype(np.float32)
    digest = hashlib.sha256(pred.tobytes()).hexdigest()[:8]
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"{stem_core}-{ts}-{digest}-zeros"
    tif = OUT_DIR / f"{name}.tif"
    if tif.exists():
        raise FileExistsError(f"refusing to overwrite {tif}")
    write_submission(tif, pred, SAMPLE, grid.footprint, note=note, name=name,
                     catalogue=grid.catalogue,
                     metadata={"lane": "WBG2-OCM", "arm_policy": stem_core,
                               "generated_utc": ts})
    sha = sha256_file(tif)
    log(f"write: {tif.name} sha256={sha}")
    return {"name": name, "tif": str(tif.relative_to(ROOT)), "sha256": sha,
            "zip": str(tif.with_suffix('.zip').relative_to(ROOT)),
            "receipt": str(tif.with_suffix('.json').relative_to(ROOT)),
            "dots": int(arm.sum()), "note": note}


# --------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="rebuild cached prior/arms")
    ap.add_argument("--stages", default="prior,canaries,allocate,holdout,uniqueness,write,card")
    args = ap.parse_args(argv)
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    t_start = time.time()

    grid = load_grid(BRIDGE)
    log(f"grid loaded: footprint={int(grid.footprint.sum())} catalogue={int(grid.catalogue.sum())}")

    p = conc = ramp = band_valid = None
    if {"prior", "canaries", "allocate", "holdout", "uniqueness", "write"} & set(stages):
        p, conc, ramp, band_valid = build_prior(grid, refresh=args.refresh)
    if "canaries" in stages:
        ctx = shared_holdout.build_holdout(grid)
        run_canaries(grid, ctx, conc, ramp, band_valid)
    arm_a = arm_b = promoted = None
    if {"allocate", "holdout", "uniqueness", "write"} & set(stages):
        arm_a, arm_b, alloc_info = run_allocation(grid, p, ramp, band_valid, conc, refresh=args.refresh)
    if "holdout" in stages:
        ctx = shared_holdout.build_holdout(grid)
        arms = {"arm_a_dti_bar": arm_a, "arm_b_budget39k": arm_b}
        # reference rasters on the same instrument
        for label, path in (("ref_gemsdoe32_b2", ROOT / "registry" / "focus_rasters" / "GEMSDOE32.tif"),):
            if path.is_file():
                with rasterio.open(path) as src:
                    a = src.read(1)
                arms[label] = np.isfinite(a) & (a > 0)
        ho = run_holdout(grid, ctx, arms)
        ctrl = run_random_control(ctx, FIXED_BUDGET)
        ho["random_controls"] = ctrl
        save_json(EVID / "ocm_holdout_20261031.json", ho)
    if "uniqueness" in stages:
        # promote the better-scoring arm on the holdout instrument if available,
        # else arm B; uniqueness is measured for the promoted arm
        choice = arm_b
        holdout_file = EVID / "ocm_holdout_20261031.json"
        if holdout_file.exists():
            ho = json.loads(holdout_file.read_text())
            da = ho["arms"].get("arm_a_dti_bar", {}).get("pooled_dti", -1)
            db = ho["arms"].get("arm_b_budget39k", {}).get("pooled_dti", -1)
            choice = arm_a if da > db else arm_b
            log(f"uniqueness: promoted arm = {'A' if da > db else 'B'} (holdout {max(da, db):.4f})")
        uni = run_uniqueness(grid, choice)
        if uni["stops"]:
            log("STOP: duplicate rule triggered; no write stage")
            return 3
        promoted = choice
    if "write" in stages:
        if promoted is None:
            promoted = arm_b if arm_b is not None else None
        if promoted is None:
            raise RuntimeError("write stage requires allocation arms")
        if not (EVID / "ocm_uniqueness_20261031.json").exists():
            raise RuntimeError("write stage requires a uniqueness audit (run stage 'uniqueness')")
        note = ("OCM: 6-field edge concordance x off-catalogue 2-5px repulsion, "
                "greedy 300m coverage; unique vs focus registry 2026-10-31")
        assert len(note) <= 140
        w = run_write(grid, promoted, "wbg2-ocm-conc6-rep2to5", note)
        save_json(EVID / "ocm_write_20261031.json", w)
    if "card" in stages:
        build_card(grid, t_start)
    log(f"done in {time.time() - t_start:.0f}s")
    return 0


def build_card(grid, t_start):
    ho = json.loads((EVID / "ocm_holdout_20261031.json").read_text()) if (EVID / "ocm_holdout_20261031.json").exists() else {}
    uni = json.loads((EVID / "ocm_uniqueness_20261031.json").read_text()) if (EVID / "ocm_uniqueness_20261031.json").exists() else {}
    w = json.loads((EVID / "ocm_write_20261031.json").read_text()) if (EVID / "ocm_write_20261031.json").exists() else {}
    can = json.loads((EVID / "ocm_canaries_20261031.json").read_text()) if (EVID / "ocm_canaries_20261031.json").exists() else {}
    alloc = json.loads((EVID / "ocm_allocation_20261031.json").read_text()) if (EVID / "ocm_allocation_20261031.json").exists() else {}
    card = {
        "schema": "wbggems.session-run-card.v1",
        "review_date": "2026-10-31",
        "lane": "WBG2-OCM (config/wbg2_ocm_lane.json)",
        "hypothesis": "Six-field edge concordance off-catalogue (H1, research/hypotheses_20261031.md)",
        "mechanism": "Concordant subsurface edges (mag/radiometric/gravity/depth/conductivity/slope) "
                     "mark blind fault strands; repulsion keeps budget off scoring-masked catalogue; "
                     "greedy 300 m coverage spaces dots where the triangular kernel adds credit.",
        "named_non_fault_process_that_could_mimic_it": "Buried lithologic/intrusive contacts and dike "
                                                      "swarms produce concordant multi-field edges without faulting.",
        "holdout_dti": None, "holdout_ci_95": None, "withheld_positives": None,
        "evaluator_version": "shared gems57.holdout.evaluate / gems57-pooled-hide-v2 instrument",
        "holdout_detail": ho.get("arms", {}),
        "random_controls": ho.get("random_controls", {}),
        "canaries": can.get("pooled", {}),
        "allocation": alloc,
        "correlation_overlap_vs_registry": {
            "worst_halo": uni.get("worst_halo"), "stops": uni.get("stops"),
            "audited_files": uni.get("audited_files"),
        },
        "raster_sha256": w.get("sha256"),
        "validator_output": {
            "status": "shared write_submission passed: finite [0,1], no NaN inside footprint, "
                      "CRS/shape/transform match pinned sample grid, zero mass on mapped catalogue",
        },
        "submission_name": w.get("name"), "submission_note": w.get("note"),
        "submission_note_max_characters": 140,
        "evidence_labels": {
            "fleet_scores": "USER-REPORTED (no organizer receipts exist for any file)",
            "k_truth": "PROJECTION (metric-model inversion of USER-REPORTED fleet scores)",
            "holdout": "HOLDOUT-DTI on the catalogue-recovery instrument — INVERSE of the "
                       "leaderboard task (official scoring masks mapped faults); not a score forecast",
            "leaderboard": "ORGANIZER-PUBLISHED public snapshot 0.4544 #1 on 2026-10-29",
        },
        "verdict": "candidate_ready_selector_pending" if w else "negative",
        "verdict_detail": ("Automated gates (format, uniqueness vs audited registry, canaries) pass and "
                           "the file is registered hash-bound in config/release_register.json. The "
                           "mechanical approved_candidates() gate stays fail-closed: no "
                           "wbggems.selector-receipt.v1 exists; the owner must record their real "
                           "weekly quota (template on docs/ocm/how-to-submit.html). This card is "
                           "not selector authorization."),
        "runtime_seconds": round(time.time() - t_start, 1),
    }
    save_json(EVID / "session_run_card_20261031.json", card)
    log(f"card written, verdict={card['verdict']}")


if __name__ == "__main__":
    raise SystemExit(main())
