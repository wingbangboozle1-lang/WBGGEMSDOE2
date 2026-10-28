#!/usr/bin/env python3
"""WBG4 expected-DTI campaign.

Usage::

    .venv/bin/python scripts/run_wbg4_edti.py exp1      # selector comparison
    .venv/bin/python scripts/run_wbg4_edti.py exp2      # budget sweep
    .venv/bin/python scripts/run_wbg4_edti.py final     # build the submission

Requires the hash-pinned public inputs listed in ``src/wbg4/features.py``.
Writes JSON to ``evidence/``; never authorises a competition upload.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wbg4 import features as F  # noqa: E402
from wbg4 import holdout as H  # noqa: E402
from wbg4 import placement as PL  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATHS = dict(template=os.path.join(ROOT, "scratch/bridge/sample_submission.tif"),
             labels=os.path.join(ROOT, "scratch/bridge/labels.tif"),
             lidar=os.path.join(ROOT, "scratch/features/lidar_scarp_features_u8.tif"),
             rad=os.path.join(ROOT, "scratch/features/geodawn_rad_u8.tif"),
             ext=os.path.join(ROOT, "scratch/features/geodawn_extensions_u8.tif"))
SEEDS = (20261028, 20261029)


def _f(x):
    return None if x is None else float(x)


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def load():
    g = F.load_grid(PATHS)
    X, y, idx = F.design_matrix(g)
    return g, X, y, idx


def train_predict(g, X, y, idx, train_mask_flat, neg_cap=900_000, seed=0, max_iter=220):
    from sklearn.ensemble import HistGradientBoostingClassifier
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y[train_mask_flat[idx]] == 1)
    neg_all = np.flatnonzero(y[train_mask_flat[idx]] == 0)
    neg = rng.choice(neg_all, size=min(neg_cap, neg_all.size), replace=False)
    sel = np.concatenate([pos, neg]); rng.shuffle(sel)
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter, learning_rate=0.06, max_leaf_nodes=63,
        min_samples_leaf=40, l2_regularization=1.0,
        early_stopping=False, random_state=seed)
    clf.fit(X[sel], y[sel])
    h = np.zeros(g["footprint"].size, np.float32)
    fp_idx = idx
    out = np.empty(fp_idx.size, np.float32)
    step = 400_000
    for s in range(0, fp_idx.size, step):
        out[s:s + step] = clf.predict_proba(X[s:s + step])[:, 1].astype(np.float32)
    h[fp_idx] = out
    return h.reshape(g["footprint"].shape), clf


def canaries(g, X, y, idx, fold, names):
    from sklearn.metrics import roc_auc_score
    tr = fold["train_domain"].ravel()[idx]
    pos = fold["withheld"].ravel()[idx]
    neg = tr & (y == 0)
    rng = np.random.default_rng(3)
    negi = np.flatnonzero(neg)
    negi = rng.choice(negi, size=min(120_000, negi.size), replace=False)
    pi = np.flatnonzero(pos)
    out = {}
    for j, n in enumerate(names):
        col = X[:, j]
        m = np.concatenate([pi, negi])
        v = col[m]
        ok = np.isfinite(v)
        if ok.sum() < 1000:
            out[n] = None; continue
        lab = np.concatenate([np.ones(pi.size), np.zeros(negi.size)])[ok]
        a = roc_auc_score(lab, v[ok])
        out[n] = float(max(a, 1 - a))
    return dict(auc_single_feature=out,
                alarm_threshold=0.90,
                flagged=[k for k, v in out.items() if v is not None and v > 0.90])


def exp1():
    t0 = time.time()
    g, X, y, idx = load()
    res = dict(experiment="WBG4-EXP1", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               evidence_class="HOLDOUT-DTI", evaluator="wbg2.metric.weighted_components (alpha 0.2, beta 0.8, R=3 px)",
               inputs=F.summary(g), folds=[], canaries=None)
    pooled = {m: [] for m in ("nms", "maxcover", "edti")}
    for seed in SEEDS:
        fold = H.build_folds(g["truth"], g["footprint"], holdout_frac=0.2, buffer_px=5, seed=seed)
        if res["canaries"] is None:
            res["canaries"] = canaries(g, X, y, idx, fold, g["names"])
        h, clf = train_predict(g, X, y, idx, fold["train_domain"].ravel())
        st = H.score_holdout(h, fold)
        # rank-normalise the hazard so the free parameters (lambda, budget) are comparable
        fr = dict(seed=seed, fold=fold["info"], hazard_map=st, selectors={})
        for mode in ("nms", "maxcover", "edti"):
            print(f"[seed {seed}] placing {mode} ...", flush=True)
            if mode == "nms":
                r = PL.nms_threshold(h, g["footprint"], budget=42_000)
            elif mode == "maxcover":
                r = PL.place(h, g["footprint"], mode="maxcover", budget=42_000, n_cand=140_000)
            else:
                r = PL.place(h, g["footprint"], mode="edti", budget=None, max_steps=60_000,
                             N_hat=float(fold["withheld"].sum()), n_cand=140_000)
            for masked in (False, True):
                s = H.score_holdout(r["mask"], fold, mask_visible=masked)
                key = mode + ("_masked" if masked else "")
                pooled[mode if not masked else mode + "_masked"] = pooled.get(mode if not masked else mode + "_masked", [])
                pooled.setdefault(mode + ("_masked" if masked else ""), []).append(s)
                fr["selectors"][key] = dict(dots=r["dots"], dti=s["dti"], c=s["c"], f=s["f"],
                                            T=s["T"], F=s["F"], N=s["N"])
            fr["selectors"][mode].update(dots=r["dots"], lam=r.get("lam"),
                                         P=r.get("P"), F_expected=r.get("F"))
        res["folds"].append(fr)
        print(f"[seed {seed}] " + "  ".join(
            f"{m}={fr['selectors'][m]['dti']:.4f}@{fr['selectors'][m]['dots']}" for m in ("nms", "maxcover", "edti")), flush=True)
    res["pooled"] = {k: dict(n_folds=len(v), mean_dti=float(np.mean([s["dti"] for s in v])),
                             dti=[float(s["dti"]) for s in v])
                     for k, v in pooled.items() if v}
    res["elapsed_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
    json.dump(_clean(res), open(os.path.join(ROOT, "evidence/wbg4_exp1.json"), "w"), indent=1)
    print(json.dumps(res["pooled"], indent=1))
    return res




# ---------------------------------------------------------------- experiment 2
SWEEP = (8000, 16000, 24000, 32000, 40000, 48000, 56000)


def _f(x):
    return None if x is None else float(x)


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def exp2():
    """Matched-budget sweep: one greedy run per (fold, mode), scored at checkpoints."""
    t0 = time.time()
    g, X, y, idx = load()
    res = dict(experiment="WBG4-EXP2",
               generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               evidence_class="HOLDOUT-DTI",
               evaluator="wbg2.metric.weighted_components (alpha 0.2, beta 0.8, R=3 px)",
               inputs=F.summary(g), sweep_budgets=list(SWEEP), folds=[])
    for seed in SEEDS:
        fold = H.build_folds(g["truth"], g["footprint"], holdout_frac=0.2, buffer_px=5, seed=seed)
        h, _ = train_predict(g, X, y, idx, fold["train_domain"].ravel())
        base = H.score_holdout(h, fold)
        fr = dict(seed=seed, fold=fold["info"], hazard_only=base, curves={})
        for mode in ("maxcover", "edti"):
            r = PL.place(h, g["footprint"], mode=mode, budget=None, max_steps=max(SWEEP),
                         N_hat=float(fold["withheld"].sum()), n_cand=140_000,
                         snapshot_budgets=SWEEP)
            curve = {}
            for b, m in r["snapshots"].items():
                s = H.score_holdout(m, fold)
                curve[int(b)] = dict(dti=s["dti"], c=s["c"], f=s["f"], T=s["T"], F=s["F"], N=s["N"])
            fr["curves"][mode] = dict(stopped_at=r["dots"], lam=r["lam"],
                                      auto_stop=(mode == "edti" and r["dots"] < max(SWEEP)),
                                      points=curve)
            print(f"[seed {seed}] {mode:8s} stopped={r['dots']:6d} " +
                  " ".join(f"{b}:{v['dti']:.4f}" for b, v in curve.items()), flush=True)
        res["folds"].append(fr)
    # pooled mean per (mode, budget)
    pooled = {}
    for mode in ("maxcover", "edti"):
        for b in SWEEP:
            vals = [fr["curves"][mode]["points"].get(b, {}).get("dti") for fr in res["folds"]]
            vals = [v for v in vals if v is not None]
            if vals:
                pooled[f"{mode}@{b}"] = dict(n=len(vals), mean_dti=float(np.mean(vals)),
                                             per_fold=[float(v) for v in vals])
    res["pooled"] = pooled
    best = max(pooled.items(), key=lambda kv: kv[1]["mean_dti"]) if pooled else None
    res["best"] = dict(config=best[0], mean_dti=float(best[1]["mean_dti"])) if best else None
    res["hazard_only_mean_dti"] = float(np.mean([fr["hazard_only"]["dti"] for fr in res["folds"]]))
    res["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(_clean(res), open(os.path.join(ROOT, "evidence/wbg4_exp2.json"), "w"), indent=1)
    print(json.dumps({k: round(v["mean_dti"], 4) for k, v in pooled.items()}, indent=1))
    print("best:", res["best"], " hazard-only:", round(res["hazard_only_mean_dti"], 4))
    return res


# ---------------------------------------------------------------- final build
FINAL_BUDGET = 40_000          # holdout-sweep optimum (see evidence/wbg4_exp2.json)
FINAL_NAME_STEM = "wbg4-mc40k-scarprad20-20261028"
FINAL_NOTE = ("Catalogue-free LiDAR+GeoDAWN hazard; 40k max-cover dots at holdout "
              "optimum 0.1190. Projection, not a score.")


def final():
    """Train on every label, place at the holdout optimum, write both twin rasters."""
    from wbg4 import writer as W
    t0 = time.time()
    g, X, y, idx = load()
    all_domain = g["footprint"].ravel()
    h, clf = train_predict(g, X, y, idx, all_domain, neg_cap=1_200_000, seed=20261028)
    r = PL.place(h, g["footprint"], mode="maxcover", budget=FINAL_BUDGET,
                 n_cand=140_000, N_hat=float(g["truth"].sum()))
    hsum = float(np.clip(h, 0, 1)[g["footprint"]].sum())
    os.makedirs(os.path.join(ROOT, "artifacts/wbg4"), exist_ok=True)
    zpath = os.path.join(ROOT, f"artifacts/wbg4/{FINAL_NAME_STEM}-zeros.tif")  # renamed after hashing
    rec_z = W.write_submission(g["footprint"], r["mask"], zpath, outside="zero",
                               template=PATHS["template"])
    npath = os.path.join(ROOT, f"artifacts/wbg4/{FINAL_NAME_STEM}-nan.tif")
    rec_n = W.write_submission(g["footprint"], r["mask"], npath, outside="nan",
                               template=PATHS["template"])
    # rename to the hash-bearing final names so the published link cannot drift from the bytes
    zfinal = os.path.join(ROOT, f"artifacts/wbg4/{FINAL_NAME_STEM}-{rec_z['sha256'][:8]}-zeros.tif")
    nfinal = os.path.join(ROOT, f"artifacts/wbg4/{FINAL_NAME_STEM}-{rec_n['sha256'][:8]}-nan.tif")
    os.replace(zpath, zfinal)
    os.replace(npath, nfinal)
    rec_z = W.validate_submission(zfinal, template=PATHS["template"])
    rec_n = W.validate_submission(nfinal, template=PATHS["template"])
    name = f"{FINAL_NAME_STEM}-{rec_z['sha256'][:8]}-zeros"
    out = dict(experiment="WBG4-FINAL",
               generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               hypothesis=("A catalogue-free hazard surface (LiDAR scarp morphometry + "
                           "GeoDAWN radiometrics/magnetics, 20 bands) emitted as sparse dots at "
                           "the holdout-optimal budget reproduces the leaderboard-favourable "
                           "emission family without copying any registered submission."),
               mechanism=("beta=0.8 makes DTI recall-dominated; a dot is worth placing while "
                          "d > lambda*dF, so dense-but-accurate emission near structural "
                          "evidence beats probability thresholding."),
               non_fault_mimic=("Alluvial/landslide scarps, eolian ridge crests, drainage "
                                "bank edges, and radiometric striping can imitate a fault scarp; "
                                "the downface/upface asymmetry pair plus strike coherence "
                                "suppress some but not all of these."),
               inputs=F.summary(g), hazard_mass_inside_footprint=hsum,
               placement=dict(mode=r["mode"], dots=r["dots"], budget=FINAL_BUDGET,
                              n_cand=140_000, P=r["P"], F_expected=r["F"], lam=r["lam"]),
               submission_name=name, note=FINAL_NOTE, note_len=len(FINAL_NOTE),
               zeros_twin=rec_z, nan_twin=rec_n,
               elapsed_s=round(time.time() - t0, 1))
    json.dump(_clean(out), open(os.path.join(ROOT, "evidence/wbg4_final.json"), "w"), indent=1)
    print(json.dumps(_clean({k: out[k] for k in ("submission_name", "note_len", "placement")}), indent=1))
    print("zeros sha256:", rec_z["sha256"], "format_valid:", rec_z["format_valid"])
    print("nan   sha256:", rec_n["sha256"], "format_valid:", rec_n["format_valid"])
    print("checks:", json.dumps(rec_z["checks"], indent=1))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "exp1"
    if cmd == "exp1":
        exp1()
    elif cmd == "exp2":
        exp2()
    elif cmd == "final":
        final()
    else:
        raise SystemExit(f"unknown command {cmd}")
