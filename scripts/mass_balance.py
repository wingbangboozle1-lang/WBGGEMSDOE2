#!/usr/bin/env python3
"""Mass-balance analysis of the official DTI on fleet submissions.

Derivation (from the organizers' formulas, see src/wbg2/metric.py):

    FN_w = |G| - TP_w                      (exact identity)
    DTI  = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)

Let N = |G|, T = TP_w, M = total predicted mass (sum of p), and assume the
sharp-loss limit in which every predicted pixel is either on ground truth
(kernel weight 1, contributes 0 to FP_w) or farther than 300 m from any truth
pixel (contributes its full value to FP_w). Then FP_w = M - T and

    s (T + 0.2 (M - T) + 0.8 (N - T)) = T
    s (0.2 M + 0.8 N) + s T (1 - 0.2 - 0.8) = T
    =>   T = s (0.2 M + 0.8 N)

because the coefficient of T is exactly zero. Two consequences:

1. The metric depends on prediction mass only through the *total* M, not its
   spatial arrangement, once the hit set is fixed. Redundant mass that does not
   add a new hit is pure cost (0.2 per unit).
2. For a fixed submission (known M and s) the implied number of true-positive
   equivalents T is linear in the unknown GT size N. So an observed score can be
   translated into a *hit rate* T/N only under an explicit assumption about N;
   the repository therefore reports a sensitivity table instead of one number.

Run: python scripts/mass_balance.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def implied_tp(score: float, mass: float, n_gt: float) -> float:
    return score * (0.2 * mass + 0.8 * n_gt)


def main() -> int:
    data = json.loads((ROOT / "data_public" / "fleet_features.json").read_text())
    rows = [r for r in data["rows"] if r["grid_matches_official"]]
    rows.sort(key=lambda r: -r["reported_score"])

    grid = [5000, 10000, 20000, 30000, 60088]
    header = " ".join(f"{'hit% N=' + str(n):>13s}" for n in grid)
    print(f"{'site':11s} {'score':>7s} {'mass':>8s} " + header)
    table = []
    for r in rows[:14]:
        s, m = r["reported_score"], r["mass"]
        hits = [implied_tp(s, m, n) / n for n in grid]
        table.append({"site": r["site"], "file": r["local"].split("__")[1],
                      "reported_score": s, "mass": m,
                      "implied_hit_rate": {str(n): h for n, h in zip(grid, hits)}})
        print(f"{r['site']:11s} {s:7.4f} {m:8.1f} " +
              " ".join(f"{h*100:12.1f}%" for h in hits))

    # marginal value of one extra correctly-placed unit of mass vs one wasted unit
    print("\nMarginal effect on DTI of adding one unit of mass (mass, score) grid:")
    for s in (0.10, 0.20, 0.28, 0.45):
        usable = 1.0 - s * (0.2 * 1.0)      # Δ from a unit that hits truth (dT=1, dF=0)
        wasted = -(s * 0.2)                  # Δ from a unit with no truth within 300 m
        print(f"  at DTI={s:.2f}: +{usable:+.4f} per hitting unit, {wasted:+.4f} per wasted unit")

    (ROOT / "data_public" / "mass_balance.json").write_text(json.dumps({
        "evidence_class": "DERIVED from the official metric formula",
        "identity": "T = s * (0.2*M + 0.8*N) in the sharp-loss limit; FN_w = N - T exactly",
        "assumed_n_gt_grid": grid,
        "rows": table,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
