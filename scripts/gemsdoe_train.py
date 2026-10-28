"""Train the fault-probability model on hidden-whole-segment folds and emit surfaces.

Lane: single explicit method paragraph of the session brief -- build a
catalogue-independent geophysical fault detector, then choose the *emission rule*
(threshold / dilation / flank mass) that maximises the organizer's own DTI on the
holdout.  Only fold-visible catalogue pixels are ever used as labels or as the
source of catalogue-distance features, so no fold can memorise its own truth.

Usage
-----
    PYTHONPATH=src python scripts/gemsdoe_train.py --folds 0 1 2 3 --final
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import features, grid, scoring  # noqa: E402
from gemsdoe.fastdti import fast_dti, pool  # noqa: E402

BLOCK = 128
NEG_PER_POS = 4
SEED = 20261028


def _feature_matrix(idx_rows, idx_cols, bank):
    """Gather (n, n_layers) geophysical features at the given cell indices.

    Catalogne-distance is deliberately excluded: with distance 0 exactly on the
    training positives it separates them perfectly and collapses the surface
    (measured: single-feature AUC 1.0, all other cells pinned at the floor
    probability).  Leakage canaries in ``scripts/gemsdoe_canary.py`` police this.
    """
    n_layers = bank.shape[0]
    X = np.empty((idx_rows.size, n_layers), dtype="float32")
    for li in range(n_layers):
        X[:, li] = bank[li][idx_rows, idx_cols]
    return X


def sample_training(visible, fp, bank, rng):
    pos_r, pos_c = np.nonzero(visible)
    # negatives keep a 2-px halo around visible faults out of the pool: the halo is
    # rasterisation-ambiguous and must not be taught as background
    halo = ndi.binary_dilation(visible, iterations=2)
    bg = fp & ~halo
    bg_r, bg_c = np.nonzero(bg)
    take = min(bg_r.size, NEG_PER_POS * pos_r.size)
    sel = rng.choice(bg_r.size, size=take, replace=False)
    r = np.concatenate([pos_r, bg_r[sel]])
    c = np.concatenate([pos_c, bg_c[sel]])
    y = np.concatenate([np.ones(pos_r.size, dtype="int8"), np.zeros(take, dtype="int8")])
    X = _feature_matrix(r, c, bank)
    return X, y


def predict_surface(model, bank, fp):
    h, w = grid.SHAPE
    out = np.zeros(grid.SHAPE, dtype="float16")
    n_layers = bank.shape[0]
    for r0 in range(0, h, BLOCK):
        r1 = min(h, r0 + BLOCK)
        X = np.empty(((r1 - r0) * w, n_layers), dtype="float32")
        for li in range(n_layers):
            X[:, li] = bank[li][r0:r1, :].reshape(-1)
        p = model.predict_proba(X)[:, 1]
        out[r0:r1, :] = p.reshape(r1 - r0, w).astype("float16")
    out[~fp] = 0
    return out


def fit(visible, fp, bank, seed=SEED, max_iter=200):
    rng = np.random.default_rng(seed)
    X, y = sample_training(visible, fp, bank, rng)
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter, learning_rate=0.06, max_leaf_nodes=31,
        min_samples_leaf=40, l2_regularization=1.0, max_bins=128,
        random_state=seed, early_stopping=False)
    clf.fit(X, y)
    return clf, {"n_train": int(y.size), "n_pos": int(y.sum()),
                 "n_features": int(X.shape[1]), "max_iter": int(max_iter)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, nargs="*", default=[0, 1, 2, 3])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--max-iter", type=int, default=200)
    ap.add_argument("--out", default=str(grid.WORK / "train_report.json"))
    args = ap.parse_args(argv)

    grid.ensure_work()
    fp = np.load(grid.WORK / "footprint.npy")
    bank = features.load()
    report = {"evidence_class": "MEASURED", "folds": [], "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    for k in args.folds:
        t0 = time.time()
        vis = np.load(grid.WORK / f"fold{k}_visible.npy")
        d_vis = ndi.distance_transform_edt(~vis).astype("float32")
        clf, info = fit(vis, fp, bank, seed=SEED + k, max_iter=args.max_iter)
        surf = predict_surface(clf, bank, fp)
        np.save(grid.WORK / f"surface_fold{k}.npy", surf)
        truth = np.load(grid.WORK / f"fold{k}_truth.npy")
        active = fp & ~vis
        diag = {}
        for t in (0.3, 0.5, 0.7, 0.85, 0.95):
            b = (surf >= t) & active
            diag[f"t{t}"] = fast_dti(b.astype("float32"), truth, active)
            diag[f"t{t}"]["cells"] = int(b.sum())
        report["folds"].append({"fold": k, **info, "seconds": round(time.time() - t0, 1),
                                "threshold_diagnostic": {kk: {k2: v2 for k2, v2 in vv.items()}
                                                         for kk, vv in diag.items()}})
        print(json.dumps(report["folds"][-1], indent=1)[:1500], flush=True)

    if args.final:
        t0 = time.time()
        cat = np.load(grid.WORK / "catalogue.npy")
        d_cat = ndi.distance_transform_edt(~cat).astype("float32")
        clf, info = fit(cat, fp, bank, seed=SEED, max_iter=args.max_iter)
        surf = predict_surface(clf, bank, fp)
        np.save(grid.WORK / "surface_final.npy", surf)
        np.save(grid.WORK / "dist_to_catalogue.npy", d_cat)
        report["final"] = {**info, "seconds": round(time.time() - t0, 1)}
        print(json.dumps(report["final"], indent=1))

    Path(args.out).write_text(json.dumps(report, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":  # pragma: no cover
    main()
