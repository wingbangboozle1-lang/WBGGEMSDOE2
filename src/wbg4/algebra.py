"""Exact algebra of the official GEMS Prize DTI metric.

All identities here are derived from the organizer definitions transcribed in
``wbggems.metric`` / ``wbg2.metric``; each is asserted in
``tests/test_wbg4_algebra.py`` against an independent brute-force evaluator, so
none of them is an assumption.

Official definitions (alpha = 0.2, beta = 0.8, R = 300 m = 3 px at 100 m):

    k(d)  = max(1 - d/R, 0)
    T     = TP_w = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
    F     = FP_w = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
    N     = |G|                      (number of scored truth pixels)
    FN_w  = N - T                    (exact identity, not an approximation)
    DTI   = T / (T + alpha*F + beta*N)

Because ``FN_w = N - T`` exactly, the whole metric is a function of only two
observables: the weighted true-positive mass ``T`` and the weighted
false-positive mass ``F``, at fixed ``N``.  Write ``c = T/N`` (weighted
coverage of the truth set) and ``f = F/N`` (false-positive mass per unit truth).
Then

    DTI = c / (c + 0.8 + 0.2 f)                                       (1)

which is the form used throughout this package.  Three consequences:

1. **Recall dominates.** ``beta/beta = 1`` for coverage but ``alpha/beta = 0.25``
   for false positives: one unit of covered truth is worth four units of
   false-positive mass.
2. **Scores are NOT directly comparable across submissions with different N.**
   ``c`` can only be inferred from a reported score if ``f`` is known.
3. **Break-even rule for a single dot.**  Differentiating (1) at fixed ``f``,

       dDTI/dc = A = (0.8 + 0.2 f) / (c + 0.8 + 0.2 f)**2

   A dot at distance ``d`` from a truth pixel adds ``k(d)`` to ``T`` (i.e.
   ``k(d)/N`` to ``c``) and, if it finds no truth within ``R`` at all, adds
   ``1/N`` to ``f``.  Rescaling both by ``N``, a dot is worth placing iff

       q * k(d) * A  >  alpha

   where ``q`` is the probability that the dot is within ``R`` of a truth pixel.
   At ``c = 0.25, f = 0``: ``A = 0.8 / 1.05**2 = 0.7256``, so the break-even hit
   probability at ``d = 0`` is ``0.2 / 0.7256 = 0.2756``.  At ``c = 0.40``:
   ``A = 0.8 / 1.20**2 = 0.5556`` and the break-even rises to ``0.360``.  Both
   values are materially *below* a balanced-classifier threshold of 0.5, which is
   why sparse "dotted" emissions can beat probability-thresholded maps even when
   the underlying hazard surface is identical, and it is the quantitative core of
   the 0.2778 analysis in ``docs/EDTI_EXECUTIVE_SUMMARY.md``.
"""
from __future__ import annotations

import numpy as np

ALPHA = 0.2
BETA = 0.8


def dti_from_components(T: float, F: float, N: float) -> float:
    """DTI from weighted TP mass, weighted FP mass and truth count."""
    if N <= 0:
        raise ValueError("N must be positive")
    return T / (T + ALPHA * F + BETA * N)


def coverage_from_score(score: float, f: float = 0.0) -> float:
    """Invert (1): weighted coverage ``c = T/N`` implied by a reported score.

    ``f`` (false-positive mass per truth pixel) must be supplied by the caller;
    it is *not* identifiable from the score alone.  Returns ``nan`` for scores
    outside ``[0, 1)``.
    """
    if not (0.0 <= score < 1.0):
        return float("nan")
    return score * (BETA + ALPHA * f) / (1.0 - score)


def score_from_coverage(c: float, f: float = 0.0) -> float:
    """Forward form of (1)."""
    return c / (c + BETA + ALPHA * f)


def coverage_gain_derivative(c: float, f: float = 0.0) -> float:
    """``dDTI/dc`` at fixed ``f`` -- the marginal value of covering more truth."""
    denom = c + BETA + ALPHA * f
    return (BETA + ALPHA * f) / denom ** 2


def breakeven_hit_probability(c: float, f: float = 0.0, k: float = 1.0) -> float:
    """Minimum P(truth within R) at kernel weight ``k`` for a dot to be worth it."""
    A = coverage_gain_derivative(c, f)
    return ALPHA / (A * k)


def identifiability_interval(score: float, f_lo: float, f_hi: float) -> tuple[float, float]:
    """Range of implied coverage ``c`` consistent with ``score`` for ``f`` in a band.

    This is the honest answer to "what does 0.2778 mean about coverage?" -- the
    score alone does not identify ``c``; only a band does.
    """
    return (coverage_from_score(score, f_lo), coverage_from_score(score, f_hi))


def pooled_from_maps(pred: np.ndarray, truth: np.ndarray, active: np.ndarray,
                     radius: float = 3.0) -> dict:
    """Compute (T, F, N) exactly, then DTI.  Thin wrapper over ``wbg2.metric``."""
    from wbg2.metric import weighted_components
    p = np.where(active, np.clip(np.nan_to_num(np.asarray(pred, np.float64)), 0, 1), 0.0)
    g = (np.asarray(truth, bool) & active).astype(np.float64)
    T, F, _, N = weighted_components(p, g, radius=int(radius))
    return {"T": T, "F": F, "N": N, "c": T / N if N else float("nan"),
            "f": F / N if N else float("nan"),
            "dti": dti_from_components(T, F, N) if N else float("nan")}
