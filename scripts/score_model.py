#!/usr/bin/env python3
"""Empirical score model for GEMS fleet submissions.

What this is
------------
A regression of the requester's USER-REPORTED leaderboard scores on geometry
statistics measured directly from the submitted rasters. It exists so that a
score *estimate* for a new candidate can be produced with a stated,
out-of-sample error, instead of being asserted.

What this is NOT
----------------
* It is not an organizer receipt. No submission-page receipt exists for any
  fleet score used here; all targets are user-reported claims.
* It is not a holdout DTI. There is no access to the competition's true
  (expert-identified, off-catalogue) labels in this environment.
* It cannot predict scores for methods whose prior lives outside the observed
  family. Extrapolation beyond the fitted band is reported as such.

Validation protocol
-------------------
1. Leave-one-out cross-validation over all rows (optimistic for the top
   cluster, which is one lineage; interpreted with care).
2. Leave-one-site-out (grouped by site) cross-validation, which prevents the
   same-lineage rows (GEMSDOE28/30/31/32/36/29) from training and testing each
   other.
3. A hard external test: fit on all NON-focus rows, predict the nine focus
   sites named by the requester (24, 25, 27, 28, 30, 31, 32, 33, 36).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOCUS = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}

FEATURES = [
    "log10_support", "median_px_to_catalogue", "frac_within_3px_catalogue",
    "log10_components", "binary_fraction", "log10_mass",
]


def build_matrix(rows):
    X, y, groups = [], [], []
    for r in rows:
        sup = max(r["support_px"], 1)
        X.append([
            np.log10(sup),
            r["median_px_to_catalogue"],
            r["frac_within_3px_catalogue"],
            np.log10(r["components_8conn"] + 1),
            r["binary_fraction"],
            np.log10(r["mass"] + 1.0),
        ])
        y.append(r["reported_score"])
        groups.append(r["site"])
    return np.asarray(X, float), np.asarray(y, float), np.asarray(groups)


def metrics(y_true, y_pred):
    err = y_pred - y_true
    ss_res = float((err ** 2).sum())
    ss_tot = float(((y_true - y_true.mean()) ** 2).sum())
    return {
        "n": int(len(y_true)),
        "mae": float(np.abs(err).mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "r2": float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
        "bias": float(err.mean()),
        "spearman": float(np.corrcoef(np.argsort(np.argsort(y_pred)),
                                      np.argsort(np.argsort(y_true)))[0, 1]),
    }


def make_model(seed=0):
    from sklearn.ensemble import GradientBoostingRegressor
    return GradientBoostingRegressor(
        n_estimators=250, max_depth=3, learning_rate=0.05,
        subsample=0.9, random_state=seed)


def main() -> int:
    data = json.loads((ROOT / "data_public" / "fleet_features.json").read_text())
    rows = [r for r in data["rows"] if r["grid_matches_official"]]
    X, y, groups = build_matrix(rows)

    # ---- 1. leave-one-out ----
    loo = np.zeros_like(y)
    for i in range(len(y)):
        m = np.ones(len(y), bool)
        m[i] = False
        mdl = make_model().fit(X[m], y[m])
        loo[i] = mdl.predict(X[i:i + 1])[0]
    loo_stats = metrics(y, loo)

    # ---- 2. leave-one-site-out ----
    loso = np.zeros_like(y)
    for g in np.unique(groups):
        m = groups != g
        mdl = make_model().fit(X[m], y[m])
        loso[~m] = mdl.predict(X[~m])
    loso_stats = metrics(y, loso)

    # ---- 3. external test on the nine focus sites ----
    focus_mask = np.array([g in FOCUS for g in groups])
    mdl_focus = make_model().fit(X[~focus_mask], y[~focus_mask])
    pred_focus = mdl_focus.predict(X[focus_mask])
    focus_stats = metrics(y[focus_mask], pred_focus)

    final = make_model().fit(X, y)
    report = {
        "evidence_class": "EMPIRICAL-ESTIMATE",
        "target_label": "USER-REPORTED public leaderboard score (no organizer receipt)",
        "n_rows": int(len(y)),
        "features": FEATURES,
        "leave_one_out": loo_stats,
        "leave_one_site_out": loso_stats,
        "external_test_nine_focus_sites": {
            **focus_stats,
            "detail": [
                {"site": r["site"], "file": r["local"].split("__")[1],
                 "reported": float(r["reported_score"]), "predicted": float(p)}
                for r, p in zip([r for r, f in zip(rows, focus_mask) if f], pred_focus)
            ],
        },
        "residual_sd_all_rows": float(np.std(y - loo, ddof=1)),
        "interpretation": (
            "Estimates are only meaningful inside the observed family: binary, isolated, "
            "roughly 3-6e4-pixel dot emissions at 1-2 km median offset from the visible "
            "catalogue. The model cannot certify a score above the observed maximum "
            "(0.2778) and gives no evidence about the 0.33-0.45 leaderboard band, which "
            "requires the geophysical feature stack that is not obtainable here."
        ),
    }
    (ROOT / "data_public" / "score_model.json").write_text(json.dumps(report, indent=1))

    print("leave-one-out      ", json.dumps({k: round(v, 4) for k, v in loo_stats.items()}))
    print("leave-one-site-out ", json.dumps({k: round(v, 4) for k, v in loso_stats.items()}))
    print("nine-focus external", json.dumps({k: round(v, 4) for k, v in focus_stats.items()}))
    print("\nper-focus prediction:")
    for d in report["external_test_nine_focus_sites"]["detail"]:
        print(f"  {d['site']:10s} reported={d['reported']:.4f} predicted={d['predicted']:.4f}  {d['file'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
