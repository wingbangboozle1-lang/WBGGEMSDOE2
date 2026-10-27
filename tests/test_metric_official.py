"""Tests for the official distance-weighted Tversky index implementation."""
from __future__ import annotations

import numpy as np
import pytest

from wbg2.metric import (
    dti,
    dti_bruteforce,
    triangular_kernel,
    weighted_components,
)


def test_kernel_values_match_official_300m_support():
    # R = 300 m = 3 px at 100 m -> k = 1, 2/3, 1/3, 0
    assert triangular_kernel(0.0) == pytest.approx(1.0)
    assert triangular_kernel(1.0) == pytest.approx(2.0 / 3.0)
    assert triangular_kernel(2.0) == pytest.approx(1.0 / 3.0)
    assert triangular_kernel(3.0) == pytest.approx(0.0)
    assert triangular_kernel(4.0) == pytest.approx(0.0)


def test_perfect_prediction_scores_one():
    gt = np.zeros((15, 15))
    gt[7, 3:12] = 1
    assert dti(gt.copy(), gt) == pytest.approx(1.0)
    tp, fp, fn, n = weighted_components(gt, gt)
    assert (tp, fp, fn, n) == pytest.approx((9.0, 0.0, 0.0, 9.0))


def test_empty_prediction_scores_zero():
    gt = np.zeros((15, 15))
    gt[7, 3:12] = 1
    assert dti(np.zeros_like(gt), gt) == 0.0


def test_offbyone_prediction_uses_kernel_two_thirds():
    gt = np.zeros((15, 15))
    gt[7, 7] = 1
    pred = np.zeros((15, 15))
    pred[7, 8] = 1  # 1 px right of truth
    tp, fp, fn, _ = weighted_components(pred, gt)
    assert tp == pytest.approx(2.0 / 3.0)
    # the predicted pixel is 1 px from truth -> costs p*(1 - 2/3) = 1/3
    assert fp == pytest.approx(1.0 / 3.0)
    # FN identity
    assert fn == pytest.approx(1.0 - 2.0 / 3.0)
    expected = (2 / 3) / ((2 / 3) + 0.2 * (1 / 3) + 0.8 * (1 / 3))
    assert dti(pred, gt) == pytest.approx(expected)


def test_beyond_radius_is_only_false_positive():
    gt = np.zeros((20, 20))
    gt[10, 10] = 1
    pred = np.zeros((20, 20))
    pred[10, 15] = 1  # 5 px away: outside the 3 px support
    tp, fp, fn, _ = weighted_components(pred, gt)
    assert tp == 0.0
    assert fp == pytest.approx(1.0)
    assert fn == pytest.approx(1.0)
    assert dti(pred, gt) == pytest.approx(0.0)


def test_dense_wrong_prediction_is_penalised_by_mass():
    gt = np.zeros((40, 40))
    gt[20, 5:35] = 1
    pred = np.zeros((40, 40))
    pred[2, 2:38] = 1  # 18 px away
    tp, _, _, _ = weighted_components(pred, gt)
    assert tp == 0.0
    assert dti(pred, gt) == 0.0


def test_probabilistic_mass_scales_linearly():
    gt = np.zeros((15, 15))
    gt[7, 7] = 1
    pred = np.zeros((15, 15))
    pred[7, 7] = 0.5
    tp, fp, fn, _ = weighted_components(pred, gt)
    assert tp == pytest.approx(0.5)
    assert fp == pytest.approx(0.0)
    assert fn == pytest.approx(0.5)


def test_identity_fn_equals_ntruth_minus_tp():
    rng = np.random.default_rng(0)
    pred = (rng.random((30, 30)) > 0.9) * rng.random((30, 30))
    gt = (rng.random((30, 30)) > 0.95).astype(float)
    tp, fp, fn, n = weighted_components(pred, gt)
    assert fn == pytest.approx(n - tp)


def test_fast_matches_bruteforce_random_cases():
    rng = np.random.default_rng(7)
    for _ in range(5):
        pred = np.where(rng.random((18, 18)) > 0.93, rng.random((18, 18)), 0.0)
        gt = (rng.random((18, 18)) > 0.94).astype(float)
        assert dti(pred, gt) == pytest.approx(dti_bruteforce(pred, gt), abs=1e-12)


def test_rejects_out_of_range_and_nonfinite():
    gt = np.zeros((5, 5))
    gt[2, 2] = 1
    with pytest.raises(ValueError):
        dti(np.full((5, 5), 1.5), gt)
    bad = np.zeros((5, 5))
    bad[0, 0] = np.nan
    with pytest.raises(ValueError):
        dti(bad, gt)
