#!/usr/bin/env python3
"""Score estimate for the candidate, from the validated empirical model.

Two independent estimates are produced and reported together:

1. EMPIRICAL-MODEL: gradient boosting fitted on the 93 measured fleet
   submissions. Its accuracy is known out of sample (scripts/score_model.py:
   external test on the nine focus sites, RMSE 0.094).
2. MASS-BALANCE BAND: invert T = s (0.2 M + 0.8 N) at the hit rate the best
   fleet submissions actually achieve, over a range of unknown GT sizes.

Neither is a competition score. Both are labelled estimates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score_model import FEATURES, make_model  # noqa: E402


def main() -> int:
    audit = json.loads((ROOT / "data_public" / "final_audit.json").read_text())
    geo = audit["candidate_geometry"]
    cand = json.loads((ROOT / "data_public" / "candidate.json").read_text())
    feats = json.loads((ROOT / "data_public" / "fleet_features.json").read_text())
    rows = [r for r in feats["rows"] if r["grid_matches_official"]]

    X = np.asarray([[
        np.log10(max(r["support_px"], 1)), r["median_px_to_catalogue"],
        r["frac_within_3px_catalogue"], np.log10(r["components_8conn"] + 1),
        r["binary_fraction"], np.log10(r["mass"] + 1.0)] for r in rows], float)
    y = np.asarray([r["reported_score"] for r in rows], float)
    model = make_model().fit(X, y)

    x_cand = np.asarray([[np.log10(max(geo["support_px"], 1)), geo["median_px_to_catalogue"],
                          geo["frac_within_3px_catalogue"], np.log10(geo["components_8conn"] + 1),
                          geo["binary_fraction"], np.log10(geo["mass"] + 1.0)]], float)
    point = float(model.predict(x_cand)[0])

    sm = json.loads((ROOT / "data_public" / "score_model.json").read_text())
    rmse = sm["external_test_nine_focus_sites"]["rmse"]
    mae = sm["external_test_nine_focus_sites"]["mae"]

    # mass-balance band: hit rates achieved by the top fleet submissions
    mb = json.loads((ROOT / "data_public" / "mass_balance.json").read_text())
    hr = [r["implied_hit_rate"] for r in mb["rows"][:6]]
    band = {}
    M = float(cand["mass"])
    for n_gt in ("10000", "20000", "30000"):
        lo = min(float(h[n_gt]) for h in hr)
        hi = max(float(h[n_gt]) for h in hr)
        # s = T / (T + 0.2(M - T) + 0.8(N - T))  with T = hit_rate * N
        def score(h):
            T = h * int(n_gt)
            return T / (T + 0.2 * (M - T) + 0.8 * (int(n_gt) - T))
        band[n_gt] = {"hit_rate_range": [lo, hi], "implied_dti_range": [score(lo), score(hi)]}

    est = {
        "point_estimate": round(point, 4),
        "interval95": [round(max(0.0, point - 1.96 * rmse), 4), round(point + 1.96 * rmse, 4)],
        "external_test_rmse": rmse,
        "external_test_mae": mae,
        "model_inputs": dict(zip(FEATURES, [float(v) for v in x_cand[0]])),
        "mass_balance_band": band,
        "calibration_note": (
            "The empirical model was fitted on the same fleet family the candidate belongs to "
            "(binary, isolated, 3-6e4 px, off-catalogue). Its out-of-sample RMSE on the nine "
            "focus sites is "
            f"{rmse:.3f}, i.e. the estimate carries roughly a +/-0.19 95% interval. It cannot "
            "certify anything about the 0.33-0.45 leaderboard band, which needs the geophysical "
            "feature stack."
        ),
    }
    (ROOT / "data_public" / "candidate_estimate.json").write_text(json.dumps(est, indent=1))
    print(json.dumps(est, indent=1)[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
