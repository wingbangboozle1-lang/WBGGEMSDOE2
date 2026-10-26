import numpy as np
import pytest
from wbggems.novelty import capacity_bound, coverage, overlap_fraction, spearman_footprint, single_feature_auc, check_against_one


def test_closed_euclidean_radius_and_directional_overlap():
    ref = np.zeros((9, 9), bool)
    ref[4, 4] = True
    near = coverage(ref, 3)
    assert near[4, 7] and near[6, 6]
    assert not near[7, 7]
    dots = np.zeros_like(ref)
    dots[4, 7] = dots[7, 7] = True
    assert overlap_fraction(dots, near) == .5
    with pytest.raises(ValueError):
        overlap_fraction(np.zeros_like(ref), near)


def test_capacity_is_conservative_and_inclusive_at_threshold():
    fp = np.ones((10, 10), bool)
    cov = np.ones_like(fp)
    cov.ravel()[:3] = False
    exact = capacity_bound(fp, cov, 10)
    assert exact.minimum_overlap == .7 and exact.feasible_under_limit
    fail = capacity_bound(fp, cov, 11)
    assert fail.minimum_overlap > .7 and not fail.feasible_under_limit
    with pytest.raises(ValueError):
        capacity_bound(fp, cov, 101)
    with pytest.raises(ValueError):
        capacity_bound(fp, cov, True)


def test_exact_tie_aware_spearman_and_undefined():
    fp = np.ones((2, 3), bool)
    a = np.array([[0, 0, 1], [1, 2, 2]], dtype=float)
    assert spearman_footprint(a, a, fp) == pytest.approx(1)
    assert spearman_footprint(a, -a, fp) == pytest.approx(-1)
    with pytest.raises(ValueError, match='constant'):
        spearman_footprint(a, np.ones_like(a), fp)
    a[0, 0] = np.nan
    with pytest.raises(ValueError, match='nonfinite'):
        spearman_footprint(a, a, fp)


def test_one_witness_can_stop_but_cannot_claim_registry_complete():
    fp = np.ones((5, 5), bool)
    ref = np.zeros((5, 5))
    ref[2, 2] = 1
    dots = np.zeros((5, 5), bool)
    dots[2, 3] = True
    result = check_against_one(ref, dots, ref, fp)
    assert result['duplicate'] and result['overlap_3px'] == 1
    with pytest.raises(ValueError, match='outside footprint'):
        fp[2, 3] = False
        check_against_one(ref, dots, ref, fp)


def test_feature_canary_ties_and_inverse_leak():
    selection = np.ones((2, 4), bool)
    y = np.array([[False, False, False, False], [True, True, True, True]])
    tied = single_feature_auc(np.ones((2, 4)), y, selection)
    assert tied['auc'] == .5 and tied['canary_pass']
    inverted = single_feature_auc(1 - y.astype(float), y, selection)
    assert inverted['auc'] == 0 and not inverted['canary_pass']
    with pytest.raises(ValueError, match='both positive and negative'):
        single_feature_auc(np.ones((2, 4)), np.ones((2, 4), bool), selection)
