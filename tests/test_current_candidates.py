import json
from pathlib import Path

import numpy as np

from audit_current_candidates import overlaps

ROOT = Path(__file__).resolve().parents[1]


def test_directed_overlap_uses_candidate_count():
    candidate = np.array([[1, 1, 1], [0, 0, 0]], dtype=bool)
    lattice = np.array([[1, 0, 1], [1, 1, 1]], dtype=bool)
    dense = np.ones_like(candidate)
    result = overlaps(candidate, lattice, dense)
    assert result['positive_pixels_in_footprint'] == 3
    assert result['lattice']['within_3_pixels'] == 2
    assert result['lattice']['fraction'] == 2 / 3
    assert result['dense_probability']['fraction'] == 1.0


def test_empty_support_does_not_get_a_vacuous_pass():
    empty = np.zeros((2, 2), dtype=bool)
    result = overlaps(empty, ~empty, ~empty)
    assert result['lattice']['fraction'] is None
    assert result['dense_probability']['fraction'] is None


def test_recorded_current_files_are_negative_and_hash_bound():
    manifest = json.loads((ROOT / 'data/current_candidates.json').read_text())
    audit = json.loads((ROOT / 'evidence/current_candidates_audit.json').read_text())
    assert len(manifest['candidates']) == len(audit['results']) == 3
    for source, result in zip(manifest['candidates'], audit['results']):
        assert result['site'] == source['site']
        assert result['byte_sha256_verified'] == source['sha256']
        assert result['overlap']['dense_probability']['fraction'] == 1
        assert result['overlap']['lattice']['fraction'] > .70
        assert set(result['literal_duplicate_witnesses']) == {'lattice', 'dense_probability'}
        assert all(result['local_format_checks'].values())
        assert result['surface_rank_correlation'] is None
        assert result['ok_to_submit'] is False
