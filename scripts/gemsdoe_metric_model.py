#!/usr/bin/env python3
"""Invert the organizer's DTI formula to explain the 0.24-0.28 plateau.

The formula (problem description, page 967) is exact and needs no simulation::

    DTI = T / (T + 0.2 F + 0.8 (N - T))

where, for a binary dot field, ``T`` is the kernel-weighted mass that lands on the
scored truth (``T = sum_g max_x p(x) k(d)``), ``F`` is the kernel-weighted cost of
the dots (``F <= mass``, with equality for dots further than 3 px from truth) and
``N`` is the number of scored truth pixels.

Given a reported score ``s`` and a measured mass ``M``, and taking ``F = M`` (the
most conservative choice: every dot pays full price), the implied coverage is

    T = s (0.2 M + 0.8 N) / (1 - 0.2 s)

so one reported score pins ``T`` once ``N`` is fixed.  ``N`` is unknown, but the
one pair of files in the fleet that is provably the *same detector with different
mass* -- D2.8 (44,090 dots, 0.2600) and B2 = D2.8 minus 6,436 collar dots
(37,654 dots, 0.2778) -- pins it, because pruning cannot change ``T``::

    0.2778 (0.2 x 37,654 + 0.8 N) / (1 - 0.05556)
      = 0.2600 (0.2 x 44,090 + 0.8 N) / (1 - 0.05200)

Nothing here is a leaderboard receipt: every score is USER-REPORTED, and the
inversion assumes (i) F = mass, (ii) the removed collar dots carried no scored
truth.  Both assumptions are stated in the output and tested by sensitivity.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data_public"
ALPHA, BETA = 0.2, 0.8


def implied_T(score: float, mass: float, n_truth: float) -> float:
    """Kernel-weighted coverage implied by one reported score (F = mass)."""
    return score * (ALPHA * mass + BETA * n_truth) / (1.0 - ALPHA * score)


def dti(T: float, mass: float, n_truth: float) -> float:
    return T / (T + ALPHA * mass + BETA * (n_truth - T))


def solve_pair(s_a=0.2600, m_a=44_090, s_b=0.2778, m_b=37_654) -> float:
    """N that makes 'same T, less mass' reproduce both reported scores."""
    def f(n):
        return implied_T(s_b, m_b, n) - implied_T(s_a, m_a, n)
    lo, hi = 1_000.0, 400_000.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def load_claims() -> list[dict]:
    """Measured mass and USER-REPORTED score for every fleet raster we opened."""
    feats = json.loads((PUB / "fleet_features.json").read_text())
    out = []
    for r in feats["rows"]:
        score = r.get("reported_score")
        if score is None or not r.get("mass"):
            continue
        out.append({"site": r["site"], "stem": Path(r["path"]).stem,
                    "score": float(score), "mass": float(r["mass"]),
                    "features": r})
    return out


def main() -> int:
    n_hat = solve_pair()
    claims = load_claims()
    scores = [c["score"] for c in claims if c.get("score") is not None]
    masses = [c["mass"] for c in claims if c.get("mass")]

    rows = []
    for c in claims:
        if not c.get("mass") or c["score"] <= 0:
            continue
        T = implied_T(c["score"], c["mass"], n_hat)
        rows.append({"site": c["site"], "file": c["stem"], "score": c["score"],
                     "mass": c["mass"], "implied_T": T,
                     "implied_coverage": T / n_hat})

    # sensitivity: move the two reported scores and the FP assumption, re-solve
    sens = []
    for dscore in (-0.0010, 0.0, 0.0010):
        for fp_share in (1.0, 0.9):        # F = mass, or only 90 % of it costs
            n_s = solve_pair(0.2600 + dscore, 44_090 * fp_share,
                             0.2778 + dscore, 37_654 * fp_share)
            sens.append({"score_shift": dscore, "fp_mass_share": fp_share,
                         "n_truth": n_s,
                         "implied_coverage_B2": implied_T(0.2778, 37_654 * fp_share, n_s) / n_s})

    # frontier: best achievable score for a detector of coverage f at mass M
    frontier = []
    for f in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
        for m in (15_000, 25_000, 38_000, 44_090, 60_000, 90_000, 130_000):
            frontier.append({"coverage": f, "mass": m,
                             "score": dti(f * n_hat, m, n_hat)})

    # the winning-mass curve at fixed coverage: what B2's coverage would score
    t_b2 = implied_T(0.2778, 37_654, n_hat)
    mass_curve = [{"mass": m, "score_at_B2_coverage": dti(t_b2, m, n_hat)}
                  for m in (10_000, 20_000, 30_000, 37_654, 44_090, 60_000, 90_000)]

    out = {
        "schema": "wbggems.metric-model.v1",
        "evidence_class": "USER-REPORTED scores inverted through the published formula",
        "formula": "DTI = T / (T + 0.2 F + 0.8 (N - T)); F = mass (conservative)",
        "assumptions": [
            "every dot pays full false-positive price (F = mass) - conservative",
            "the 6,436 dots removed by B2 carried no scored truth (they lie within "
            "2 px of the masked catalogue)",
            "the four scores used for the solve are accurate as reported",
        ],
        "n_truth_pixels_solved": n_hat,
        "n_truth_sensitivity_range": [min(x["n_truth"] for x in sens),
                                      max(x["n_truth"] for x in sens)],
        "score_pair": {"D2.8": {"mass": 44_090, "score": 0.2600},
                       "B2": {"mass": 37_654, "score": 0.2778}},
        "implied_T_at_B2": t_b2,
        "implied_coverage_at_B2": t_b2 / n_hat,
        "n_files_inverted": len(rows),
        "reported_score_range": [min(scores), max(scores)],
        "mass_range": [min(masses), max(masses)] if masses else None,
        "implied_coverage_quantiles": (np.quantile([r["implied_coverage"] for r in rows],
                                                   [0.1, 0.5, 0.9]).round(4).tolist()
                                       if rows else None),
        "rows": rows,
        "mass_curve_at_B2_coverage": mass_curve,
        "coverage_mass_frontier": frontier,
        "sensitivity": sens,
        "exchange_rate_at_02778": {
            # DTI = T / (0.2 T + alpha F + beta N):  dF < ((1/s) - alpha)/alpha * dT
            "one_unit_of_TP_justifies_FP_units": float((1 / 0.2778 - ALPHA) / ALPHA),
            "marginal_precision_needed_for_one_more_dot": float(
                ALPHA / (1 / 0.2778 - ALPHA)),
            "reading": ("a dot is worth adding only while the kernel-weighted truth mass "
                        "it can claim is >= 0.2/(1/s - 0.2) = 0.0588, i.e. while its "
                        "smoothed fault probability exceeds ~5.9 %"),
        },
    }
    (PUB / "gemsdoe_metric_model.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in
                      ("n_truth_pixels_solved", "implied_T_at_B2",
                       "implied_coverage_at_B2", "implied_coverage_quantiles",
                       "reported_score_range", "mass_range")}, indent=1))
    print("\nmass curve at B2 coverage:")
    for row in mass_curve:
        print(f"  mass {row['mass']:>7,} -> {row['score_at_B2_coverage']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
