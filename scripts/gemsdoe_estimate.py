"""Structural score estimate for a candidate emission (transparent, assumption-explicit).

No fitted model is used, because no local quantity was found that predicts the
public leaderboard (holdout DTI vs published score over 30 fleet rasters:
Spearman +0.31, p=0.10; and the 0.2778 file scores 0.0048 on the holdout while
uniform random dots score 0.0481).  Instead the organizer's own formula is
inverted:

    DTI = T / (T + 0.2 F + 0.8 (N - T)),  T = f N,  F = unmasked mass

Two questions are answered for a candidate with mass F:

1. If it covers a fraction f of the hidden truth set of size N, what DTI follows?
2. To reproduce an observed score s at the same mass, what f is required?

Both are arithmetic on the published metric; the unknown is (N, f), which must be
stated as an assumption.  Output: ``data_public/gemsdoe_estimate.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemsdoe import grid  # noqa: E402

ALPHA, BETA = 0.2, 0.8


def dti(f, N, F, alpha=ALPHA, beta=BETA):
    T = f * N
    return T / (T + alpha * F + beta * (N - T))


def required_f(s, N, F, alpha=ALPHA, beta=BETA):
    # s = fN / (fN + aF + bN(1-f))  ->  fN(1 - a s ... ) solved for f
    num = s * (alpha * F + beta * N)
    den = N * (1 - s * (1 - beta))
    return num / den


def main():
    card = json.loads(next((grid.ROOT / "submissions").glob("gems-wbg4-*.json")).read_text())
    mass = card["mass"]
    Ns = [10000, 20000, 40000]
    fs = [0.20, 0.30, 0.40, 0.50]
    out = {
        "evidence_class": "STRUCTURAL-ESTIMATE (arithmetic on the published metric; assumptions stated)",
        "candidate": card["name"], "mass": mass,
        "assumption_F": "every unit cell of the emission contributes full false-positive weight (1-k = 1); upper bound on cost",
        "grid": {f"N={N}": {f"f={f:.2f}": round(dti(f, N, mass), 4) for f in fs} for N in Ns},
        "required_coverage_to_match": {
            "public_0.2778": {f"N={N}": round(required_f(0.2778, N, 37654), 3) for N in Ns},
            "public_0.4544": {f"N={N}": round(required_f(0.4544, N, 38000), 3) for N in Ns},
        },
        "fleet_observed_band": {"min": 0.2449, "median": 0.2632, "max": 0.2778,
                                "n_files": 8, "evidence": "USER-REPORTED public leaderboard values"},
        "candidate_estimate_range": [0.20, 0.30],
        "candidate_estimate_label": ("EMPIRICAL-BAND ESTIMATE: the candidate matches the measured "
                                     "envelope (binary, 38k cells, reach 0.17) of the fleet's highest "
                                     "scoring submissions; no local measurement can certify a value "
                                     "above the observed maximum of 0.2778."),
    }
    (grid.ROOT / "data_public" / "gemsdoe_estimate.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":  # pragma: no cover
    main()
