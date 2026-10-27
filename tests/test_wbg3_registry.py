"""Uniqueness gates: the literal radius test and the capacity bound."""
import numpy as np
import pytest

from wbggems.novelty import capacity_bound
from wbg3.registry import literal_overlap, compare


def test_identical_field_is_a_full_duplicate():
    m = np.zeros((30, 30), bool)
    m[5:20, 7] = True
    assert literal_overlap(m, m) == pytest.approx(1.0)


def test_far_field_is_not_a_duplicate():
    a = np.zeros((40, 40), bool)
    b = np.zeros((40, 40), bool)
    a[2:10, 2] = True
    b[30:38, 37] = True
    assert literal_overlap(a, b) == pytest.approx(0.0)


def test_radius_is_inclusive_and_directed():
    a = np.zeros((10, 10), bool)
    b = np.zeros((10, 10), bool)
    a[5, 5] = True
    b[5, 8] = True          # exactly 3 px away
    assert literal_overlap(a, b) == pytest.approx(1.0)
    b[5, 8] = False
    b[5, 9] = True          # 4 px away
    assert literal_overlap(a, b) == pytest.approx(0.0)


def test_overlap_requires_a_nonempty_candidate():
    with pytest.raises(ValueError):
        literal_overlap(np.zeros((5, 5), bool), np.ones((5, 5), bool))


def test_compare_flags_the_worst_raster():
    cand = np.zeros((20, 20), bool)
    cand[10, :] = True
    dup = cand.copy()
    other = np.zeros((20, 20), bool)
    other[1, 1] = True
    rep = compare(cand, {"dup": dup, "other": other}, np.ones((20, 20), bool))
    assert rep["any_overlap_fail"] is True
    assert rep["worst_overlap"]["name"] == "dup"


def test_capacity_bound_reproduces_the_lattice_obstruction():
    """A witness covering all but u cells forces at least (D-u)/D overlap."""
    footprint = np.ones((200, 200), bool)
    covered = np.ones((200, 200), bool)
    covered[0, :6] = False           # 6 uncovered cells
    cap = capacity_bound(footprint, covered, 37654)
    assert cap.uncovered_cells == 6
    assert cap.minimum_overlap == pytest.approx((37654 - 6) / 37654)
    assert cap.feasible_under_limit is False
