"""Score every fetched registry raster on the WBG4 hide-and-recover folds.

Output (``evidence/wbg4_registry_folds.json``):

* per-raster HOLDOUT-DTI on the identical folds used for the candidate, and
* a leave-one-out calibration of *reported leaderboard score* on HOLDOUT-DTI.

The calibration is what lets a new file be given an **estimated** leaderboard
range instead of a guess.  It is a projection: the leaderboard targets unmapped
faults, the holdout target is withheld catalogue faults.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import wbg4.evaluate as E  # noqa: E402


def main():
    index = E.load_registry_index(ROOT / "data" / "registry" / "index.json")
    keep = [r for r in index if (r["reported_score"] or 0) >= 0.20] + index[::4]
    seen, sel = set(), []
    for r in keep:
        if r["local"] in seen:
            continue
        seen.add(r["local"]); sel.append(r)
    index = sel
    print(f"scoring {len(index)} rasters", flush=True)
    caches = E.build_caches()
    rows = []
    for i, rec in enumerate(index, 1):
        path = ROOT / rec["local"]
        try:
            res = E.score_raster(path, caches)
        except Exception as exc:  # noqa: BLE001
            rows.append({**rec, "error": str(exc)})
            continue
        rows.append({
            "site": rec["site"], "file": res["file"], "bytes": rec["bytes"],
            "reported_score": rec["reported_score"],
            "score_evidence": rec["score_evidence"],
            "holdout_dti": round(res["dti"], 5),
            "holdout_coverage": round(res["coverage"], 5),
            "holdout_mass": res["mass"],
            "positives_in_footprint": int(res["positive_pixels_total"]),
        })
        print(f"{i}/{len(index)} {rec['site']} dti={res['dti']:.4f} "
              f"reported={rec['reported_score']:.4f}", flush=True)

    ok = [r for r in rows if "holdout_dti" in r]
    y = np.array([r["reported_score"] for r in ok], float)
    x = np.array([r["holdout_dti"] for r in ok], float)
    # least squares on the reported score, with leave-one-out error
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    loo = []
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        c, *_ = np.linalg.lstsq(A[m], y[m], rcond=None)
        loo.append(float(A[i] @ c))
    loo = np.array(loo)
    resid = y - loo
    ss_res = float((resid ** 2).sum()); ss_tot = float(((y - y.mean()) ** 2).sum())
    from scipy.stats import spearmanr, pearsonr
    rho = float(spearmanr(x, y).statistic)
    r = float(pearsonr(x, y).statistic)
    out = {
        "evidence_class": "MEASURED holdout scores vs USER-REPORTED leaderboard values",
        "evaluator": "wbg4-hide-recover-v1",
        "n_rasters": len(ok),
        "holdout_dti_range": [round(float(x.min()), 5), round(float(x.max()), 5)],
        "reported_range": [round(float(y.min()), 4), round(float(y.max()), 4)],
        "spearman_holdout_vs_reported": round(rho, 4),
        "pearson_holdout_vs_reported": round(r, 4),
        "linear_fit": {"slope": round(float(coef[0]), 6), "intercept": round(float(coef[1]), 6)},
        "loo": {
            "mae": round(float(np.abs(resid).mean()), 5),
            "rmse": round(float(np.sqrt((resid ** 2).mean())), 5),
            "r2": round(1 - ss_res / ss_tot, 4) if ss_tot else None,
        },
        "rows": rows,
        "generated_utc": np.datetime64("now").astype(str),
    }
    (ROOT / "evidence" / "wbg4_registry_folds.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("n_rasters", "holdout_dti_range", "reported_range",
                       "spearman_holdout_vs_reported", "pearson_holdout_vs_reported",
                       "linear_fit", "loo")}, indent=2))


if __name__ == "__main__":
    main()
