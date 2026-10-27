#!/usr/bin/env python3
"""Uniform, labelled score estimates for any candidate GeoTIFF.

Three independent estimators, none of which is a competition score:
1. EMPIRICAL-ESTIMATE: gradient boosting fit on the 93 measured fleet rasters
   with USER-REPORTED scores (out-of-sample RMSE on the nine focus sites 0.0937,
   from data_public/score_model.json). Interval = point +/- 1.96*RMSE.
2. PROJECTION (score law): OLS on the nine focus champions' measured
   (dots, collar fraction) refit here from data_public/fleet_features.json.
   The nine are one lineage and ~98% collinear in these variables, so this law
   constrains placement economics, not geology.
3. DERIVED mass-balance band: invert T = s(0.2M + 0.8N) at the hit rates the
   six best fleet submissions imply, over assumed hidden-truth sizes N.
Usage: python3 scripts/estimate_candidate.py file.tif [more.tif ...] --catalogue existing_faults.tif --reference reference.tif
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]

def geometry(path, cat, fp, dcat):
    with rasterio.open(path) as ds:
        a = ds.read(1)
    dots = np.isfinite(a) & (a > 0) & fp
    dd = dcat[dots]
    comps = int(label(dots, np.ones((3, 3)))[1])
    d = distance_transform_edt(~dots)
    kmass = float(np.maximum(1 - d[fp] / 3.0, 0).sum())
    vals = a[dots]
    return {"file": str(path), "support_px": int(dots.sum()), "mass": float(np.nansum(a[fp])),
            "median_px_to_catalogue": float(np.median(dd)) if dd.size else None,
            "frac_within_3px_catalogue": float((dd <= 3).mean()) if dd.size else None,
            "components_8conn": comps,
            "binary_fraction": float(((vals == 0) | (vals == 1)).mean()) if vals.size else 0.0,
            "kmass_per_dot": kmass / max(int(dots.sum()), 1)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tifs", nargs="+", type=Path)
    ap.add_argument("--catalogue", type=Path, default=Path("/tmp/wbg/mirror/existing_faults_mirror.tif"))
    ap.add_argument("--reference", type=Path, default=Path("/tmp/wbg/mirror/reference_grid_mirror.tif"))
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/candidate_estimates.json")
    a = ap.parse_args()
    with rasterio.open(a.catalogue) as ds:
        cat = ds.read(1) == 1
    with rasterio.open(a.reference) as ds:
        fp = np.isfinite(ds.read(1))
    cat &= fp
    dcat = distance_transform_edt(~cat)

    fleet = json.loads((ROOT / "data_public/fleet_features.json").read_text())["rows"]
    fleet = [r for r in fleet if r["grid_matches_official"]]
    from sklearn.ensemble import GradientBoostingRegressor
    X = np.array([[np.log10(max(r["support_px"], 1)), r["median_px_to_catalogue"],
                   r["frac_within_3px_catalogue"], np.log10(r["components_8conn"] + 1),
                   r["binary_fraction"], np.log10(r["mass"] + 1)] for r in fleet])
    y = np.array([r["reported_score"] for r in fleet])
    gbr = GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.05,
                                    subsample=0.9, random_state=0).fit(X, y)
    sm = json.loads((ROOT / "data_public/score_model.json").read_text())
    rmse = sm["external_test_nine_focus_sites"]["rmse"]

    focus_tbl = json.loads((ROOT / "data_public/focus_table.json").read_text())
    rows9 = focus_tbl["rows"] if isinstance(focus_tbl, dict) else focus_tbl
    X9 = np.array([[1, r["dots"] / 1000, r["frac_within_3px_catalogue"]] for r in rows9])
    y9 = np.array([r["user_reported_score"] for r in rows9])
    coef, *_ = np.linalg.lstsq(X9, y9, rcond=None)
    pred9 = X9 @ coef
    r2 = 1 - ((y9 - pred9) ** 2).sum() / ((y9 - y9.mean()) ** 2).sum()
    maxres = float(np.abs(y9 - pred9).max())

    mb = json.loads((ROOT / "data_public/mass_balance.json").read_text())
    hr = [r["implied_hit_rate"] for r in mb["rows"][:6]]

    out = {"evidence_class": "EMPIRICAL-ESTIMATE + PROJECTION + DERIVED (no organizer receipt)",
           "score_law": {"coef_intercept": float(coef[0]), "coef_per_1000_dots": float(coef[1]),
                         "coef_collar": float(coef[2]), "r2_nine_focus": float(r2), "max_abs_residual": maxres},
           "empirical_rmse_external_focus": rmse, "candidates": []}
    for p in a.tifs:
        g = geometry(p, cat, fp, dcat)
        x = np.array([[np.log10(max(g["support_px"], 1)), g["median_px_to_catalogue"],
                       g["frac_within_3px_catalogue"], np.log10(g["components_8conn"] + 1),
                       g["binary_fraction"], np.log10(g["mass"] + 1)]])
        pt = float(gbr.predict(x)[0])
        law = float(coef[0] + coef[1] * g["support_px"] / 1000 + coef[2] * g["frac_within_3px_catalogue"])
        band = {}
        for n in ("10000", "20000", "30000"):
            lo, hi = min(float(h[n]) for h in hr), max(float(h[n]) for h in hr)
            def sc(h, N=int(n), M=g["mass"]):
                T = h * N
                return T / (T + 0.2 * (M - T) + 0.8 * (N - T))
            band[n] = [sc(lo), sc(hi)]
        row = {**g, "empirical_estimate": pt,
               "empirical_interval95": [max(0.0, pt - 1.96 * rmse), pt + 1.96 * rmse],
               "score_law_projection": law, "mass_balance_band_if_best_lineage_hit_rate": band}
        out["candidates"].append(row)
        print(json.dumps(row, indent=1))
    # numpy float64 from the refit is not JSON-serializable by default in 3.11 for all objects
    a.out.write_text(json.dumps(out, indent=1, default=float) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
