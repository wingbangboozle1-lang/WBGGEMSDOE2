import itertools
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import binary_dilation

from audit_nine_sites import disk, dot_overlap, minimum_overlap

ROOT = Path(__file__).resolve().parents[1]


def test_disk_is_euclidean_and_includes_exact_radius():
    d = disk(3)
    assert d.shape == (7, 7)
    assert d[3, 6] and d[0, 3]
    assert not d[0, 0]
    assert int(d.sum()) == 29


def test_overlap_is_directional():
    sparse = np.zeros((10, 10), bool)
    dense = np.zeros_like(sparse)
    sparse[1, 1] = True
    dense[1, 1] = dense[8, 8] = True
    assert dot_overlap(sparse, binary_dilation(dense, structure=disk(3))) == 1
    assert dot_overlap(dense, binary_dilation(sparse, structure=disk(3))) == .5


@pytest.mark.parametrize('budget,uncovered,expected', [(10, 2, .8), (10, 10, 0), (2, 7, 0), (10, 0, 1)])
def test_lower_bound(budget, uncovered, expected):
    assert minimum_overlap(budget, uncovered) == pytest.approx(expected)


def test_lower_bound_is_exact_in_every_small_configuration():
    # Brute force every coverage mask and placement on a six-cell footprint.
    for covered_set in itertools.product([False, True], repeat=6):
        coverage = np.asarray(covered_set)
        uncovered = int((~coverage).sum())
        for n in range(1, 7):
            observed = min(sum(bool(coverage[i]) for i in indexes) / n
                           for indexes in itertools.combinations(range(6), n))
            assert minimum_overlap(n, uncovered) == pytest.approx(observed)


@pytest.mark.parametrize('n,u', [(0, 0), (-1, 2), (1, -1)])
def test_invalid_budget_rejected(n, u):
    with pytest.raises(ValueError):
        minimum_overlap(n, u)


def test_overlap_empty_and_shape_fail_closed():
    with pytest.raises(ValueError):
        dot_overlap(np.zeros((3, 3), bool), np.zeros((3, 3), bool))
    with pytest.raises(ValueError):
        dot_overlap(np.ones((2, 2), bool), np.ones((3, 3), bool))


def test_recorded_universal_stop_and_finite_budget_bound():
    audit = json.loads((ROOT / 'evidence/portfolio_audit.json').read_text())
    dense, lattice = audit['dense_surface_witness'], audit['lattice_witness']
    assert dense['finite_positive_footprint_pixels'] == dense['footprint_pixels']
    assert dense['uncovered_footprint_pixels_within_3px'] == 0
    assert dense['universal_overlap_lower_bound'] == 1.0
    assert minimum_overlap(lattice['hypothetical_dot_budget'], lattice['uncovered_footprint_pixels']) == pytest.approx(lattice['min_possible_overlap'])
    assert lattice['min_possible_overlap'] > .70
    assert len(audit['focus_sites']) == 9
    assert all(s['max_overlap'] > .7 for s in audit['focus_sites'])
    assert audit['forensic']['candidate_xor_pixels'] == 0


def test_negative_card_has_no_fake_file_or_score():
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert card['verdict'] == 'negative' and not card['ok_to_submit']
    assert card['raster_sha256'] is None
    assert card['holdout_dti']['value'] is None and card['holdout_dti']['ci95'] is None
    assert card['validator']['status'].startswith('not run')
    assert len(card['note']) <= 140
