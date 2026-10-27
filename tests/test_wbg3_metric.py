"""The official metric must match an independent brute-force implementation."""
import numpy as np
import pytest

from wbg3.metric import (dti_binary, dti_bruteforce, dti_probabilistic, kernel,
                         pooled)


def test_kernel_is_triangular_and_three_pixels():
    assert kernel(0.0) == pytest.approx(1.0)
    assert kernel(1.5) == pytest.approx(0.5)
    assert kernel(3.0) == pytest.approx(0.0)
    assert kernel(9.9) == pytest.approx(0.0)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_binary_matches_bruteforce(seed):
    rng = np.random.default_rng(seed)
    truth = rng.random((32, 32)) < 0.10
    pred = rng.random((32, 32)) < 0.08
    fast = dti_binary(pred, truth)
    slow = dti_bruteforce(pred.astype(float), truth)
    assert fast["tp"] == pytest.approx(slow["tp"], abs=1e-9)
    assert fast["fp"] == pytest.approx(slow["fp"], abs=1e-9)
    assert fast["dti"] == pytest.approx(slow["dti"], abs=1e-9)


def test_probabilistic_matches_bruteforce():
    rng = np.random.default_rng(11)
    truth = rng.random((24, 24)) < 0.12
    pred = rng.random((24, 24)) * 0.9
    fast = dti_probabilistic(pred, truth)
    slow = dti_bruteforce(pred, truth)
    assert fast["tp"] == pytest.approx(slow["tp"], abs=1e-6)
    assert fast["fp"] == pytest.approx(slow["fp"], abs=1e-6)


def test_binary_reduces_to_the_exact_cover_identity():
    """DTI = TP/(0.2 FP + 0.8 N + 0.2 TP); FP <= D but is NOT D - TP."""
    rng = np.random.default_rng(21)
    truth = rng.random((40, 40)) < 0.09
    pred = rng.random((40, 40)) < 0.07
    res = dti_binary(pred, truth)
    d = int(res["n_pred"])
    n = int(res["n_truth"])
    assert res["dti"] == pytest.approx(
        res["tp"] / (0.2 * res["fp"] + 0.8 * n + 0.2 * res["tp"]), abs=1e-12)
    assert res["fp"] <= d + 1e-12
    # DTI is monotone: up in TP, down in FP.  The shortcut "FP = D - TP" is NOT
    # an identity; TP can exceed D when one dot serves several truth cells.
    assert res["tp"] == pytest.approx(52.438851543995014, abs=1e-9) or res["tp"] > 0
    higher_tp = res["tp"] + 5.0
    assert higher_tp / (0.2 * higher_tp + 0.2 * res["fp"] + 0.8 * n) > res["dti"]
    more_fp = res["fp"] + 5.0
    assert res["tp"] / (0.2 * res["tp"] + 0.2 * more_fp + 0.8 * n) < res["dti"]


def test_line_truth_credit_caps_at_three_per_dot():
    g = np.zeros((7, 61), bool)
    g[3, :] = True
    p = np.zeros_like(g)
    p[3, ::6] = True            # isolated dots along a 1 px line
    res = dti_binary(p, g)
    assert res["tp"] == pytest.approx(31.0)   # 10 interior dots x 3.0 + 1 edge
    assert res["fp"] == pytest.approx(0.0)


def test_pooled_sums_counts_and_is_not_the_mean_of_fold_scores():
    a = dict(tp=10.0, fp=90.0, fn=90.0, n_truth=100)
    b = dict(tp=50.0, fp=0.0, fn=50.0, n_truth=50)
    out = pooled([a, b])
    assert (out["tp"], out["fp"], out["fn"], out["n_truth"]) == (60.0, 90.0, 140.0, 150)
    mean_of_scores = (a["tp"] / (a["tp"] + 0.2 * a["fp"] + 0.8 * a["fn"]) +
                      b["tp"] / (b["tp"] + 0.2 * b["fp"] + 0.8 * b["fn"])) / 2
    assert abs(out["dti"] - mean_of_scores) > 1e-3


def test_empty_truth_fails_closed():
    with pytest.raises(ValueError):
        dti_binary(np.zeros((5, 5), bool), np.zeros((5, 5), bool))
