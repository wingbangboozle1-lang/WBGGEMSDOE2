import pytest
from inspect_registry_index import summarize


def index(rows):
    return {'rasters': [{'sha256': x} for x in rows], 'n_unique_grid_rasters': len(rows),
            'repos_scanned': ['A'], 'errors': [], 'complete_accessible_scan': True}


def test_summary_only_counts_metadata_never_certifies_registry():
    a, b, c = 'a'*64, 'b'*64, 'c'*64
    manifest = {'inputs': [{'id': 'x', 'sha256': a}, {'id': 'y', 'sha256': c}]}
    result = summarize(index([a, b]), manifest)
    assert result['local_witness_ids_present_in_index'] == ['x']
    assert result['local_witness_ids_not_in_index'] == ['y']
    assert result['indexed_hashes_absent_from_local_witness_manifest'] == 1
    assert result['raster_bytes_opened_for_this_index_summary'] == 0
    assert result['current_complete_registry_established'] is False
    assert result['upstream_reported_complete_accessible_scan'] is True  # clearly attributed


def test_duplicate_bad_or_mismatched_index_fails_closed():
    manifest = {'inputs': [{'id': 'x', 'sha256': 'a'*64}]}
    with pytest.raises(ValueError, match='duplicate'):
        summarize(index(['a'*64, 'a'*64]), manifest)
    with pytest.raises(ValueError, match='invalid'):
        summarize(index(['not-a-hash']), manifest)
    broken = index(['a'*64]); broken['n_unique_grid_rasters'] = 3
    with pytest.raises(ValueError, match='disagrees'):
        summarize(broken, manifest)
    with pytest.raises(ValueError, match='invalid local'):
        summarize(index(['a'*64]), {'inputs': [{'id': 'x', 'sha256': 'a'*64}, {'id': 'x', 'sha256': 'b'*64}]})
