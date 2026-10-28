"""What does the public leaderboard actually reward?  A measured answer, not a guess.

For every fleet raster that has BOTH a published (user-reported) score and a
measured holdout score, compute four candidate explanations and test them:

P1 ``holdout_dti``      pooled withheld-segment DTI (random-segment hide-and-recover)
P2 ``catalogue_dti``    DTI against the full catalogue with nothing masked (how much of
                        the file is simply a copy of the known map)
P3 ``collar_precision`` fraction of the file's positive cells within 300 m of a known fault
P4 ``reach``            fraction of the footprint within 300 m of a positive cell
                        (how widely the emission is spread, independent of where it is)
P5 ``catalogue_recall`` fraction of known fault pixels within 300 m of a positive cell

Then: univariate Spearman against the published score, and a leave-one-site-out
linear model.  Output is a diagnostic of the historical fleet, not a promise about
any new file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import grid  # noqa: E402
from gemsdoe.fastdti import fast_dti  # noqa: E402

MIN_PUB = 0.0


def main():
    grid.ensure_work()
    ev = json.loads((grid.WORK / "fleet_eval.json").read_text())
    fp = np.load(grid.WORK / "footprint.npy")
    cat = np.load(grid.WORK / "catalogue.npy")
    d_cat = ndi.distance_transform_edt(~cat).astype("float32")
    n_fp = int(fp.sum())

    rows = []
    for r in ev["rows"]:
        if r.get("published_score") is None or r.get("holdout_dti") is None:
            continue
        try:
            with rasterio.open(r["file"]) as ds:
                a = ds.read(1).astype("float32")
        except Exception:
            continue
        a[~np.isfinite(a)] = 0.0
        a = np.clip(a, 0, 1)
        pos = a > 0
        if not pos.any():
            continue
        d_pred = ndi.distance_transform_edt(~pos).astype("float32")
        s = d_pred <= 3.0
        p2 = fast_dti(pos.astype("float32"), cat, fp)
        rows.append({
            "stem": r["stem"], "published": r["published_score"],
            "P1_holdout_dti": r["holdout_dti"],
            "P2_catalogue_dti": p2["dti"],
            "P3_collar_precision": float((d_cat[pos] <= 3).mean()),
            "P4_reach": float(s[fp].sum() / n_fp),
            "P5_catalogue_recall": float(s[cat].mean()),
            "mass": r["mass_inside_footprint"], "dots": r["positive_cells"],
        })
        if len(rows) % 20 == 0:
            print(len(rows), r["stem"], round(r["published_score"], 4), flush=True)

    keys = ["P1_holdout_dti", "P2_catalogue_dti", "P3_collar_precision", "P4_reach",
            "P5_catalogue_recall", "mass", "dots"]
    y = np.array([r["published"] for r in rows])
    out = {"evidence_class": "MEASURED", "n": len(rows),
           "target": "USER-REPORTED public leaderboard score (unauthenticated)",
           "univariate_spearman": {}, "rows": rows}
    for k in keys:
        x = np.array([r[k] for r in rows], dtype=float)
        rho = spearmanr(x, y)
        out["univariate_spearman"][k] = {"rho": float(rho.statistic), "p": float(rho.pvalue)}

    # leave-one-site-out linear model on standardised predictors
    from sklearn.linear_model import Ridge
    X = np.column_stack([[r[k] for r in rows] for k in keys]).astype(float)
    X = (X - X.mean(0)) / (X.std(0) + 1e-12)
    sites = [r["stem"].split("-")[0] for r in rows]
    pred = np.zeros_like(y)
    for s in sorted(set(sites)):
        te = np.array([si == s for si in sites])
        tr = ~te
        if tr.sum() < 10 or te.sum() == 0:
            pred[te] = y[tr].mean()
            continue
        m = Ridge(alpha=3.0).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    out["loso_ridge"] = {"r2": 1 - ss_res / ss_tot,
                         "mae": float(np.abs(y - pred).mean()),
                         "rmse": float(np.sqrt(((y - pred) ** 2).mean())),
                         "spearman": float(spearmanr(pred, y).statistic)}
    coef = Ridge(alpha=3.0).fit(X, y).coef_
    out["full_fit_coefficients"] = dict(zip(keys, [float(c) for c in coef]))
    (grid.WORK / "strategy_diag.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n", "univariate_spearman", "loso_ridge",
                                          "full_fit_coefficients")}, indent=1))


if __name__ == "__main__":  # pragma: no cover
    main()
