"""Unit tests for the lane-WBG2-B machinery that does not need the big rasters.

Everything here runs on synthetic arrays so CI (which restores only the pinned
shared code, not the 419 MB mirror or the feature bank) can execute it.  Tests
that need the shared template or scikit-image skip instead of failing.
"""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _mod(name: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:                                  # pragma: no cover
        pytest.skip(f"{name} unavailable in this workspace: {exc}")


# --------------------------------------------------------------------------
# thin_to_budget: the emission shape that the DTI algebra says is optimal
# --------------------------------------------------------------------------
def test_thin_to_budget_hits_the_budget_and_stays_inside_the_domain():
    es = _mod("emit_and_score")
    rng = np.random.default_rng(7)
    domain = np.zeros((60, 80), bool)
    domain[5:55, 5:75] = True
    # A belief that is high on a winding corridor and low elsewhere.
    yy, xx = np.mgrid[0:60, 0:80]
    belief = np.zeros((60, 80), np.float32)
    corridor = np.abs(yy - (30 + 12 * np.sin(xx / 9.0))) < 3.0
    belief[corridor] = 0.9
    belief += rng.random((60, 80)).astype(np.float32) * 0.05
    budget = 400
    support, info = es.thin_to_budget(domain, belief, budget)
    assert int(support.sum()) == budget
    assert np.all(support & domain == support), "dots must never leave the domain"
    assert info["budget"] == budget and info["emitted"] == budget
    assert info["domain_cells"] == int(domain.sum())
    # The support must be thin: a skeleton has no fully filled 2x2 blocks except
    # where thinning cannot remove them, so at most a handful may survive.
    filled = support[:-1, :-1] & support[1:, :-1] & support[:-1, 1:] & support[1:, 1:]
    assert int(filled.sum()) <= max(4, budget // 100)
    # ...and it must prefer the high-belief corridor over background noise.
    assert float(belief[support].mean()) > float(belief[domain].mean())


def test_thin_to_budget_degrades_gracefully_when_the_domain_is_too_small():
    es = _mod("emit_and_score")
    domain = np.zeros((9, 9), bool)
    domain[4, 4] = True
    belief = np.ones((9, 9), np.float32)
    support, info = es.thin_to_budget(domain, belief, 500)
    assert int(support.sum()) == 1, "cannot invent dots outside the admissible domain"
    assert support[4, 4]


def test_thin_to_budget_never_returns_an_empty_support_for_a_nonempty_domain():
    """Regression: the first implementation kept the last bisection iterate,
    which was often empty, and the whole arm scored 0.0010."""
    es = _mod("emit_and_score")
    rng = np.random.default_rng(3)
    domain = np.ones((40, 40), bool)
    belief = rng.random((40, 40)).astype(np.float32)
    for budget in (1, 17, 300, 1600):
        support, _ = es.thin_to_budget(domain, belief, budget)
        assert int(support.sum()) == min(budget, int(domain.sum()))


# --------------------------------------------------------------------------
# detached_truth_folds: the second calibration instrument
# --------------------------------------------------------------------------
def test_detached_truth_folds_only_shrinks_truth_and_records_the_change():
    cal = _mod("calibrate_holdout")
    visible = np.zeros((20, 20), bool)
    visible[10, 3:17] = True                       # a mapped trace
    truth = np.zeros((20, 20), bool)
    truth[10, 5] = True                            # on the trace
    truth[12, 5] = True                            # 2 px away
    truth[18, 5] = True                            # 8 px away
    fold = dict(name="NW", region=np.ones((20, 20), bool), truth=truth,
                visible=visible, masked_known=visible,
                receipt=dict(withheld_positive_pixels=3))
    # distances to the nearest visible pixel are 0, 2 and 8 for the three truth
    # pixels, so a 4 px detachment keeps only the far one
    out = cal.detached_truth_folds([fold], 4.0)[0]
    assert not out["truth"][10, 5] and not out["truth"][12, 5] and out["truth"][18, 5]
    assert out["receipt"]["withheld_positive_pixels"] == 1
    assert out["receipt"]["detach_px"] == 4.0
    assert out["receipt"]["detached_truth_pixels"] == 1
    # the original fold object is not mutated in place
    assert int(fold["truth"].sum()) == 3
    # a 1 px detachment keeps the 2 px pixel but never one sitting on the trace
    near = cal.detached_truth_folds([fold], 1.0)[0]
    assert near["truth"][12, 5] and near["truth"][18, 5] and not near["truth"][10, 5]
    far = cal.detached_truth_folds([fold], 12.0)[0]
    assert int(far["truth"].sum()) == 0


# --------------------------------------------------------------------------
# rank_u8_fast must equal the pinned shared rank transform byte for byte
# --------------------------------------------------------------------------
def test_rank_u8_fast_matches_the_shared_transform():
    fb = _mod("build_feature_bank")
    rng = np.random.default_rng(11)
    values = rng.integers(-500, 500, size=1517).astype(np.float64)
    values[:40] = values[0]                    # a big tie group
    got = fb.rank_u8_fast(values)
    assert got.dtype == np.uint8 and got.shape == values.shape
    assert got.max() <= fb.RANK_MAX
    # ties must share one rank, and the transform must be order preserving
    assert len(np.unique(got[:40])) == 1
    order = np.argsort(values, kind="stable")
    assert np.all(np.diff(got[order].astype(np.int32)) >= 0)
    prep = ROOT / "data/shared_template/scripts/prep_feature_stack.py"
    if not prep.is_file():
        pytest.skip("pinned shared template not restored")
    spec = importlib.util.spec_from_file_location("prep_feature_stack", prep)
    shared = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared)
    assert np.array_equal(got, shared._rank_u8(values)), "must equal the shared transform"


# --------------------------------------------------------------------------
# the DTI identity used for every published projection
# --------------------------------------------------------------------------
def test_projection_algebra_reproduces_the_reported_value_it_was_fitted_to():
    blr = _mod("build_lane_b_release")
    card = blr.load("docs/data/run-card-lane-b.json")
    d = card["projection"]["derived"]
    K, T, n, M = d["K_real"], d["T_b2"], d["n_b2"], d["M_b2"]

    def dti(T_, M_, n_):
        return T_ / (0.2 * T_ + 0.2 * max(n_ - M_, 0.0) + 0.8 * K)

    assert abs(dti(T, M, n) - 0.2778) <= 1e-3
    assert 0 < M <= K
    # the floor is strictly worse than parity, and parity is close to the file
    # whose yield it assumes
    assert card["projection"]["floor"] < card["projection"]["parity"]
    assert abs(card["projection"]["parity"] - 0.2778) < 0.01
    # a truth-free emission must score 0, and a perfect one must score 1
    assert dti(0.0, 0.0, 38000) == 0.0
    assert abs(dti(K, K, K) - 1.0) < 1e-12


def test_binary_support_at_p_one_is_dti_optimal_and_the_marginal_bar_is_derived():
    """Worked check of the claims in research/findings.md.

    DTI = T / (T + alpha*FP + beta*FN + eps) with alpha = 0.2, beta = 0.8 and a
    300 m triangular kernel k(d) = max(1 - d/R, 0), R = 3 px.  Adding one dot of
    value p and kernel credit k gives T += p*k, FP += p*(1-k) and, worst case,
    leaves FN alone:

        DTI(p) = (A + p k) / (B + p C),   A = T,
        B = T + alpha FP + beta FN,       C = k + alpha (1 - k)

        d DTI / dp = (k B - A C) / (B + p C)^2

    so the sign never depends on p: DTI is monotone in p, and a dot is worth
    raising to p = 1 exactly when k B > A C.  Dividing by B and writing D = A/B
    for the current DTI gives the marginal bar

        k > alpha*D / (1 - (1 - alpha)*D)

    which is *stricter* than the naive "k > alpha*D" (0.0630 vs 0.0503 at
    D = 0.2515): grading is never useful, and the optimal budget is smaller
    than the naive rule suggests.  Both facts are used in the released file.
    """
    alpha, beta = 0.2, 0.8
    T, FP, FN = 4600.0, 29400.0, 9760.0
    A = T
    B = T + alpha * FP + beta * FN
    D = A / B

    def dti_after_dot(k, p):
        return (A + p * k) / (B + p * (k + alpha * (1 - k)))

    bar = alpha * D / (1 - (1 - alpha) * D)
    assert abs(bar - 0.06298) < 1e-4
    assert bar > alpha * D, "the exact bar is stricter than the naive one"

    # above the bar DTI rises with p, so p = 1 wins
    for k in (1.0, 2 / 3, 0.4, 0.1, bar * 1.5):
        values = [dti_after_dot(k, p) for p in (0.05, 0.25, 0.5, 0.75, 1.0)]
        assert values == sorted(values), f"DTI must rise with p above the bar (k={k})"
        assert values[-1] > D
    # below the bar DTI falls with p, so the dot should not be emitted at all
    for k in (bar * 0.5, 0.01, 1e-9, 0.0):
        values = [dti_after_dot(k, p) for p in (0.05, 0.25, 0.5, 0.75, 1.0)]
        assert values == sorted(values, reverse=True), f"DTI must fall with p below the bar (k={k})"
        assert values[0] <= D
    # the derivative test agrees with the finite differences at the bar itself
    assert abs(dti_after_dot(bar, 1.0) - D) < 1e-9
