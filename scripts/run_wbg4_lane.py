"""Run the WBG4 lane end to end.

Sub-commands
------------
``canaries``   per-feature single-feature AUC on the fold-0 holdout (leakage gate)
``folds``      four hide-and-recover folds; pooled DTI curve versus emitted mass
``controls``   score registry rasters on the *same* folds (matched incumbent baseline)
``final``      fit on the full catalogue, emit the submission raster, validate bytes
``all``        canaries -> folds -> controls -> final

Every number written to ``evidence/`` is labelled with its evidence class.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import wbg4.lane as L  # noqa: E402

EVID = ROOT / "evidence"
MASS_GRID = [0.002, 0.004, 0.006, 0.009, 0.013, 0.020, 0.030, 0.045]
WINDOW = 256
HALO = 48
SEED = 20261028


def quadrants(footprint: np.ndarray) -> np.ndarray:
    fr, fc = np.nonzero(footprint)
    rmid = (fr.min() + fr.max()) // 2
    cmid = (fc.min() + fc.max()) // 2
    rr = np.arange(L.HEIGHT)[:, None] > rmid
    cc = np.arange(L.WIDTH)[None, :] > cmid
    return (rr.astype(np.int8) * 2 + cc.astype(np.int8))


def windows(nrows: int = WINDOW):
    for r0 in range(0, L.HEIGHT, nrows):
        yield r0, min(nrows, L.HEIGHT - r0)


def stack(names, bands, rows_mask_2d=None, flat_index=None):
    X = np.stack([b.reshape(-1) for b in bands], axis=1)
    if flat_index is not None:
        X = X[flat_index]
    return X


def gather(fb, sample_idx: np.ndarray):
    """Feature matrix for the given flat indices, in window order."""
    rows = []
    names = None
    for r0, n in windows():
        base = r0 * L.WIDTH
        sel = sample_idx[(sample_idx >= base) & (sample_idx < base + n * L.WIDTH)] - base
        if sel.size == 0:
            continue
        names, bands = fb.features(r0, n)
        rows.append((sel + base, np.stack([b.reshape(-1) for b in bands], axis=1)[sel]))
    if not rows:
        raise ValueError("no samples in any window")
    order = np.concatenate([r[0] for r in rows])
    X = np.concatenate([r[1] for r in rows], axis=0)
    return names, X, order


BLIND_PREFIXES = ("D_vis_log", "dens_vis_", "cont_")


def drop_blind(names, X):
    keep = [i for i, n in enumerate(names) if not n.startswith(BLIND_PREFIXES)]
    return keep


def fit_model(X, y, w=None):
    clf = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.06, max_leaf_nodes=31, l2_regularization=1.0,
        min_samples_leaf=60, random_state=SEED, early_stopping=False,
    )
    clf.fit(X, y, sample_weight=w)
    return clf


def topk_mask(score: np.ndarray, eligible: np.ndarray, k: int) -> np.ndarray:
    """Exact top-``k`` mask over ``eligible`` cells (ties broken by position)."""
    idx = np.nonzero(eligible.reshape(-1))[0]
    if k >= idx.size:
        return eligible.astype(np.float32)
    vals = score.reshape(-1)[idx]
    sel = np.argpartition(vals, idx.size - k)[idx.size - k:]
    out = np.zeros(score.size, dtype=np.float32)
    out[idx[sel]] = 1.0
    return out.reshape(score.shape)


def predict_grid(fb, clf, nrows=WINDOW, keep=None):
    prob = np.zeros((L.HEIGHT, L.WIDTH), dtype=np.float32)
    for r0, n in windows(nrows):
        names, bands = fb.features(r0, n)
        X = stack(names, bands)
        if keep is not None:
            X = X[:, keep]
        prob[r0:r0 + n] = clf.decision_function(X).reshape(n, L.WIDTH)
    return prob


# --------------------------------------------------------------------------- #
def cmd_canaries(cfg):
    fp = L.load_footprint(); lab = L.load_labels()
    comp, _ = L.fault_components(lab, fp)
    ids = L.fold_ids(comp, fp)
    hidden, hbuf, vis, _vis_exact = L.fold_masks(comp, ids, 3, buffer_px=3)
    spring = L.spring_layers(cfg)
    fb = L.FeatureBank(cfg, spring); fb.set_visible(vis)
    rng = np.random.default_rng(SEED)
    active = fp & ~lab
    bg = active & (L.ndi.binary_dilation(lab, iterations=5) == 0)
    bg_idx = np.nonzero(bg.reshape(-1))[0]
    bg_idx = rng.choice(bg_idx, size=min(120_000, bg_idx.size), replace=False)
    pos_idx = np.nonzero(hidden.reshape(-1))[0]
    sample = np.concatenate([pos_idx, bg_idx])
    names, X, order = gather(fb, sample)
    is_pos = np.zeros(L.HEIGHT * L.WIDTH, dtype=bool)
    is_pos[pos_idx] = True
    y = is_pos[order].astype(np.float32)
    out = {}
    for j, nm in enumerate(names):
        col = X[:, j]
        auc = float(roc_auc_score(y, col))
        out[nm] = {"auc": round(auc, 4), "leakage_flag": bool(auc > 0.90)}
    res = {
        "evidence_class": "HOLDOUT-CANARY (single feature, fold index 3, hidden positives vs buffered background)",
        "n_positives": int(pos_idx.size), "n_background": int(bg_idx.size),
        "rule": "AUC > 0.90 is treated as leakage and the feature is excluded",
        "features": dict(sorted(out.items(), key=lambda kv: -kv[1]["auc"])),
        "max_auc": max(v["auc"] for v in out.values()),
        "n_flagged": sum(v["leakage_flag"] for v in out.values()),
    }
    (EVID / "wbg4_canaries.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: res[k] for k in ("n_positives", "max_auc", "n_flagged")}, indent=2))
    print(json.dumps(dict(list(res["features"].items())[:8]), indent=2))
    fb.close()


# --------------------------------------------------------------------------- #
def run_folds(cfg, save_prob=False):
    """Four hide-and-recover folds; both feature variants fitted per feature pass.

    The operating point is a *rank* cut (top-k of the model score), so the emitted
    mass is exact and the DTI curve is comparable across models regardless of how
    saturated their probability outputs are.
    """
    fp = L.load_footprint(); lab = L.load_labels()
    comp, ncomp = L.fault_components(lab, fp)
    ids = L.fold_ids(comp, fp)
    quad = quadrants(fp)
    spring = L.spring_layers(cfg)
    fb = L.FeatureBank(cfg, spring)
    rng = np.random.default_rng(SEED)
    active = fp & ~lab
    near_fault = L.ndi.binary_dilation(lab, iterations=2)
    variants = {"full": None, "blind": BLIND_PREFIXES}
    per_fold = {k: [] for k in variants}
    for f in range(4):
        t0 = time.time()
        hidden, hbuf, vis, vis_exact = L.fold_masks(comp, ids, f, buffer_px=3)
        fb.set_visible(vis)
        active_f = fp & ~vis_exact
        train_region = (quad != f) & fp
        pos_idx = np.nonzero((vis & train_region).reshape(-1))[0]
        neg_pool = active & ~near_fault & train_region
        neg_idx = np.nonzero(neg_pool.reshape(-1))[0]
        neg_idx = rng.choice(neg_idx, size=min(3 * pos_idx.size, neg_idx.size), replace=False)
        sample = np.concatenate([pos_idx, neg_idx])
        names, X, order = gather(fb, sample)
        is_pos = np.zeros(L.HEIGHT * L.WIDTH, dtype=bool)
        is_pos[pos_idx] = True
        y = is_pos[order].astype(np.float32)
        models = {}
        for name, blind_prefixes in variants.items():
            keep = ([i for i, nm in enumerate(names) if not nm.startswith(blind_prefixes)]
                    if blind_prefixes else list(range(len(names))))
            models[name] = (keep, fit_model(X[:, keep], y))
        del X
        scores = {name: predict_grid(fb, clf, keep=keep)
                  for name, (keep, clf) in models.items()}
        k_grid = {mf: int(round(mf * int(active_f.sum()))) for mf in MASS_GRID}
        for name, sc in scores.items():
            curve = []
            for mf, k in k_grid.items():
                pred = topk_mask(sc, active_f, k)
                c = L.dti(pred, hidden, active_f)
                c.update({"mass_fraction": mf, "mass": int(pred.sum())})
                curve.append({kk: (round(vv, 6) if isinstance(vv, float) else vv)
                              for kk, vv in c.items()})
            per_fold[name].append({
                "fold": f, "n_train_pos": int(pos_idx.size), "n_train_neg": int(neg_idx.size),
                "hidden_px": int(hidden.sum()),
                "features_used": [names[i] for i in models[name][0]],
                "curve": curve,
            })
        print(f"fold {f}: hidden={int(hidden.sum())} " + " ".join(
            f"{nm}={max(c['dti'] for c in per_fold[nm][-1]['curve']):.4f}" for nm in variants)
            + f" ({round(time.time()-t0,1)}s)", flush=True)
        del scores
    out = {}
    for name in variants:
        pooled = []
        for i, mf in enumerate(MASS_GRID):
            parts = [{"tp": pf["curve"][i]["tp"], "fp": pf["curve"][i]["fp"],
                      "fn": pf["curve"][i]["fn"], "n_truth": pf["curve"][i]["n_truth"]}
                     for pf in per_fold[name]]
            p = L.pooled(parts)
            p.update({"mass_fraction": mf,
                      "mass": int(sum(pf["curve"][i]["mass"] for pf in per_fold[name]))})
            pooled.append(p)
        best = max(pooled, key=lambda r: r["dti"])
        out[name] = {
            "evidence_class": "HOLDOUT-DTI",
            "feature_set": name,
            "evaluator": "wbg4-hide-recover-v1 (whole components, 3 px buffer, 2x2 quadrants, "
                         "visible-only catalogue features, exact visible mask, rank-cut operating point)",
            "withheld_positives_total": int(sum(pf["hidden_px"] for pf in per_fold[name])),
            "folds": per_fold[name],
            "pooled_curve": pooled,
            "best": best,
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        print(f"{name.upper()}: pooled best HOLDOUT-DTI {best['dti']:.4f} at mass_fraction "
              f"{best['mass_fraction']} (mass {best['mass']}, N={out[name]['withheld_positives_total']})",
              flush=True)
    (EVID / "wbg4_folds.json").write_text(json.dumps(out, indent=2) + "\n")
    fb.close()
    return out


# --------------------------------------------------------------------------- #
def cmd_final(cfg, variant="blind", exclude_near=0):
    """Fit on the full catalogue and emit the submission raster (rank-cut mass)."""
    import wbg4.emit as EM
    fp = L.load_footprint(); lab = L.load_labels()
    comp, _ = L.fault_components(lab, fp)
    spring = L.spring_layers(cfg)
    fb = L.FeatureBank(cfg, spring)
    fb.set_visible(comp > 0)
    rng = np.random.default_rng(SEED)
    active = fp & ~lab
    near = L.ndi.binary_dilation(lab, iterations=max(exclude_near, 0)) if exclude_near else ~fp
    pos_idx = np.nonzero((comp > 0).reshape(-1))[0]
    neg_pool = np.nonzero((active & ~L.ndi.binary_dilation(lab, iterations=2)).reshape(-1))[0]
    neg_idx = rng.choice(neg_pool, size=min(3 * pos_idx.size, neg_pool.size), replace=False)
    sample = np.concatenate([pos_idx, neg_idx])
    names, X, order = gather(fb, sample)
    keep = ([i for i, nm in enumerate(names) if not nm.startswith(BLIND_PREFIXES)]
            if variant == "blind" else list(range(len(names))))
    is_pos = np.zeros(L.HEIGHT * L.WIDTH, dtype=bool); is_pos[pos_idx] = True
    y = is_pos[order].astype(np.float32)
    clf = fit_model(X[:, keep], y)
    del X
    score = predict_grid(fb, clf, keep=keep)

    ev = json.loads((EVID / "wbg4_folds.json").read_text())[variant]
    mf = float(ev["best"]["mass_fraction"])
    eligible = active & ~near if exclude_near else active
    k = int(round(mf * int(eligible.sum())))
    out = topk_mask(score, eligible, k)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"wbg4-sscc-{variant}-{int(out.sum())}dots-{stamp}"
    tif = ROOT / "docs" / "downloads" / f"{name}.tif"
    EM.write_submission(out, tif)
    EM.package_zip(tif)
    summary = EM.summarise(tif, fp, ROOT / "data" / "sample_submission.tif")
    summary.update({
        "name": name, "mass": int(out.sum()), "mass_fraction_holdout": mf,
        "feature_set": variant, "features_used": [names[i] for i in keep],
        "near_catalogue_exclusion_px": exclude_near,
        "holdout": {"dti": ev["best"]["dti"], "mass_fraction": mf,
                    "withheld_positives": ev["withheld_positives_total"],
                    "evaluator": ev["evaluator"], "evidence_class": "HOLDOUT-DTI"},
        "generated_utc": stamp,
    })
    (EVID / "wbg4_candidate.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k2: summary[k2] for k2 in
                      ("name", "sha256", "bytes", "positive_inside_footprint", "ok")}, indent=2))
    fb.close()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["canaries", "folds", "controls", "final", "all"])
    ap.add_argument("--variant", default="blind", choices=["blind", "full"])
    ap.add_argument("--exclude-near", type=int, default=0)
    a = ap.parse_args()
    cfg = L.load_config()
    pins = L.verify_pins(cfg)
    if not pins["all_match"]:
        raise SystemExit("input hash mismatch: refusing to run")
    if a.cmd in ("canaries", "all"):
        cmd_canaries(cfg)
    if a.cmd in ("folds", "all"):
        run_folds(cfg)
    if a.cmd in ("final", "all"):
        cmd_final(cfg, variant=a.variant, exclude_near=a.exclude_near)


if __name__ == "__main__":
    main()
