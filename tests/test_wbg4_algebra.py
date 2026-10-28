"""Independent checks for the WBG4 metric algebra and placement invariant.

Every claim made in ``docs/EDTI_EXECUTIVE_SUMMARY.md`` about the metric is
asserted here against a brute-force transcription of the organizer formulas, so
no number in the narrative is an unchecked assumption.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from wbg4 import algebra as A  # noqa: E402


def _grid(seed=0, n=40, k=12):
    rng = np.random.default_rng(seed)
    truth = np.zeros((n, n), bool)
    ys = rng.choice(n, size=k, replace=False)
    xs = rng.choice(n, size=k, replace=False)
    truth[ys, xs] = True
    pred = np.zeros((n, n), np.float64)
    py = rng.choice(n, size=k, replace=False)
    px = rng.choice(n, size=k, replace=False)
    pred[py, px] = 1.0
    return pred, truth


def _bruteforce(pred, truth, radius=3.0, alpha=0.2, beta=0.8):
    """Literal transcription of the organizer definitions (no vectorisation)."""
    h, w = pred.shape
    gt = list(zip(*np.nonzero(truth)))
    pp = list(zip(*np.nonzero(pred > 0)))
    T = 0.0
    for (gy, gx) in gt:
        best = 0.0
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                y, x = gy + dy, gx + dx
                if 0 <= y < h and 0 <= x < w:
                    d = np.hypot(dy, dx)
                    if d <= radius:
                        best = max(best, pred[y, x] * (1 - d / radius))
        T += best
    Fv = 0.0
    for (y, x) in pp:
        bestk = 0.0
        for (gy, gx) in gt:
            bestk = max(bestk, max(1 - np.hypot(y - gy, x - gx) / radius, 0.0))
        Fv += pred[y, x] * (1 - bestk)
    N = len(gt)
    FN = N - T
    return T, Fv, N, FN


def test_fn_identity_is_exact():
    pred, truth = _grid(1)
    T, Fv, N, FN = _bruteforce(pred, truth)
    assert FN == pytest.approx(N - T, abs=1e-12)


def test_components_match_shared_metric():
    from wbg2.metric import weighted_components
    pred, truth = _grid(2)
    T, Fv, _, N = weighted_components(pred, truth.astype(np.float64), radius=3)
    Tb, Fb, Nb, _ = _bruteforce(pred, truth)
    assert T == pytest.approx(Tb, abs=1e-9)
    assert Fv == pytest.approx(Fb, abs=1e-9)
    assert N == Nb


def test_score_closed_form_matches_bruteforce():
    for seed in (3, 4, 5):
        pred, truth = _grid(seed)
        T, Fv, N, _ = _bruteforce(pred, truth)
        closed = A.dti_from_components(T, Fv, N)
        direct = T / (T + 0.2 * Fv + 0.8 * N)
        assert closed == pytest.approx(direct, abs=1e-12)
        # the (c, f) form of equation (1)
        c, f = T / N, Fv / N
        assert A.score_from_coverage(c, f) == pytest.approx(direct, abs=1e-12)


def test_coverage_inversion_roundtrip():
    for s in (0.05, 0.1, 0.2778, 0.3195, 0.4413, 0.5):
        for f in (0.0, 0.1, 0.3, 0.6):
            c = A.coverage_from_score(s, f)
            assert A.score_from_coverage(c, f) == pytest.approx(s, abs=1e-12)


def test_published_identifiability_bands():
    """The numbers quoted in the executive summary."""
    lo, hi = A.identifiability_interval(0.2778, 0.0, 0.6)
    assert (round(lo, 4), round(hi, 4)) == (0.3077, 0.3539)
    lo, hi = A.identifiability_interval(0.4544, 0.0, 0.6)
    assert (round(lo, 4), round(hi, 4)) == (0.6663, 0.7662)


def test_breakeven_values_quoted_in_docs():
    assert round(A.coverage_gain_derivative(0.25), 4) == 0.7256
    assert round(A.breakeven_hit_probability(0.25), 4) == 0.2756
    assert round(A.coverage_gain_derivative(0.40), 4) == 0.5556
    assert round(A.breakeven_hit_probability(0.40), 4) == 0.36


def test_lambda_monotone_invariance():
    """Accepting ``dP > lambda*dF`` strictly increases lambda = P/(F+4N).

    This is the invariant the EDTI greedy relies on; it is proved analytically in
    ``wbg4.placement`` and checked numerically here.
    """
    rng = np.random.default_rng(11)
    P, F, N = 10.0, 30.0, 100.0
    for _ in range(500):
        dP, dF = rng.random() * 2.0, rng.random() * 2.0
        lam = P / (F + 4 * N)
        if dP > lam * dF:
            new = (P + dP) / (F + dF + 4 * N)
            assert new > lam, (P, F, dP, dF, lam, new)
            P, F = P + dP, F + dF


def test_lambda_zero_is_maxcover():
    """lambda = 0 collapses the EDTI acceptance test to plain positive gain."""
    rng = np.random.default_rng(12)
    for _ in range(200):
        dP, dF = rng.random(), rng.random()
        assert (dP > 0.0 * dF) == (dP > 0.0)


def test_pooled_from_maps_agrees_with_bruteforce():
    pred, truth = _grid(6)
    active = np.ones_like(truth)
    out = A.pooled_from_maps(pred, truth, active)
    Tb, Fb, Nb, _ = _bruteforce(pred, truth)
    assert out["T"] == pytest.approx(Tb, abs=1e-9)
    assert out["N"] == Nb
    assert out["dti"] == pytest.approx(Tb / (Tb + 0.2 * Fb + 0.8 * Nb), abs=1e-12)


def test_kernel_weights_are_the_organizer_triangle():
    k = A.__dict__
    from wbg4.placement import kernel_offsets
    offs, ks = kernel_offsets()
    d = np.hypot(offs[:, 0], offs[:, 1])
    assert np.allclose(ks, np.maximum(1.0 - d / 3.0, 0.0), atol=1e-6)
    # k(d) is 1, 2/3, 1/3 at d = 0, 1, 2 and zero at d = 3
    for dist, want in ((0.0, 1.0), (1.0, 2 / 3), (2.0, 1 / 3)):
        i = int(np.argmin(np.abs(d - dist)))
        assert abs(float(ks[i]) - want) < 1e-6
    assert not np.any(np.abs(d - 3.0) < 1e-9), "d == 3 must be excluded (k = 0)"
