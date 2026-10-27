import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from submission_status import load_submission_status  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_valid_release(root: Path) -> tuple[Path, Path]:
    candidate = root / 'artifacts' / 'candidate.tif'
    candidate.parent.mkdir(parents=True, exist_ok=True)
    # Structural gate fixture only: the dedicated validator tests exercise
    # official-reference byte validation; this small raster tests hash binding.
    with rasterio.open(candidate, 'w', driver='GTiff', width=4, height=3, count=1,
                       dtype='float32', crs='EPSG:32611',
                       transform=from_origin(243350, 4508550, 100, 100)) as out:
        out.write(np.zeros((3, 4), dtype=np.float32), 1)
    candidate_hash = sha256(candidate.read_bytes())
    card = {
        'verdict': 'promote',
        'ok_to_submit': True,
        'ok_to_download_new_tif': True,
        'raster_sha256': candidate_hash,
        'submission_name': 'test-candidate-v1',
        'submission_note': 'Research experiment; exact version v1.',
        'mechanism': 'A named hypothetical physical mechanism tested in the fixture.',
        'named_non_fault_mimic': 'A non-fault lithologic contact.',
        'holdout_dti': {
            'evidence_class': 'HOLDOUT-DTI',
            'status': 'COMPLETED',
            'evaluator_version': 'test-evaluator-v1',
            'withheld_positives': 120,
            'value': 0.25,
            'ci95': [0.20, 0.30],
        },
        'validator': {
            'status': 'PASS',
            'validated_raster_sha256': candidate_hash,
            'no_nan_inside_footprint': True,
            'values_in_0_1': True,
            'crs_shape_transform_match': True,
        },
        'registry': {
            'all_current_registry_rasters_checked': True,
            'registry_manifest_sha256': 'b' * 64,
        },
        'uniqueness': {
            'preplacement_surface_max_abs_correlation': 0.90,
            'final_dot_max_overlap_3px': 0.70,
        },
    }
    card_path = root / 'evidence' / 'run_card.json'
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(card, indent=2) + '\n')
    release = {
        'schema': 'wbggems.submission-release.v1',
        'decision': 'promote',
        'run_card_sha256': sha256(card_path.read_bytes()),
        'candidate_path': 'artifacts/candidate.tif',
        'candidate_sha256': candidate_hash,
        'submission_name': card['submission_name'],
        'submission_note': card['submission_note'],
        'weekly_quota_checked': True,
        'weekly_quota_checked_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'weekly_quota_source_url': 'https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/',
        'remaining_weekly_slots': 1,
    }
    release_path = root / 'evidence' / 'submission_release.json'
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    return card_path, release_path


def test_current_repository_is_blocked_and_does_not_use_historical_lane_cards():
    status = load_submission_status(ROOT)
    assert status['approved'] is False
    assert status['card']['verdict'] == 'negative'
    assert status['card']['raster_sha256'] is None
    assert 'canonical run card is not promoted' in status['reason']
    assert 'separate weekly-slot selector record is absent' in status['reason']


def test_byte_bound_selector_and_required_science_fields_are_accepted(tmp_path):
    write_valid_release(tmp_path)
    status = load_submission_status(tmp_path)
    assert status['approved'] is True
    assert status['reason'] == 'Submission gates and selector record pass.'


def test_selector_is_invalidated_by_any_run_card_byte_change(tmp_path):
    card_path, _ = write_valid_release(tmp_path)
    card_path.write_bytes(card_path.read_bytes() + b' ')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'does not bind to the current run-card bytes' in status['reason']


def test_selector_is_invalidated_when_candidate_bytes_change(tmp_path):
    _, _ = write_valid_release(tmp_path)
    (tmp_path / 'artifacts/candidate.tif').write_bytes(b'changed candidate bytes')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'saved candidate bytes do not match' in status['reason']


def test_generic_run_card_note_cannot_substitute_for_submission_note(tmp_path):
    card_path, release_path = write_valid_release(tmp_path)
    card = json.loads(card_path.read_text())
    card['submission_note'] = None
    card['note'] = 'Old negative-run narrative that happens to be short.'
    card_path.write_text(json.dumps(card, indent=2) + '\n')
    release = json.loads(release_path.read_text())
    release['run_card_sha256'] = sha256(card_path.read_bytes())
    release['submission_note'] = card['note']
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'no valid submission note' in status['reason']


def test_missing_registry_metrics_or_invalid_confidence_interval_block(tmp_path):
    card_path, release_path = write_valid_release(tmp_path)
    card = json.loads(card_path.read_text())
    card['uniqueness']['preplacement_surface_max_abs_correlation'] = 0.901
    card['holdout_dti']['ci95'] = [0.31, 0.20]
    card_path.write_text(json.dumps(card, indent=2) + '\n')
    release = json.loads(release_path.read_text())
    release['run_card_sha256'] = sha256(card_path.read_bytes())
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'pre-placement surface correlation' in status['reason']
    assert '95% confidence interval is missing or invalid' in status['reason']


def test_non_object_run_card_and_selector_fail_closed(tmp_path):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    card_path = evidence / 'run_card.json'
    card_path.write_text('[]')
    status = load_submission_status(tmp_path)
    assert not status['approved'] and 'not a JSON object' in status['reason']

    card_path, release_path = write_valid_release(tmp_path)
    release_path.write_text('[]')
    status = load_submission_status(tmp_path)
    assert not status['approved'] and 'selector record is not a JSON object' in status['reason']


def test_malformed_nested_gate_fields_fail_closed_without_exception(tmp_path):
    card_path, release_path = write_valid_release(tmp_path)
    card = json.loads(card_path.read_text())
    card['holdout_dti'] = 'not-an-object'
    card['validator'] = []
    card['registry'] = []
    card['uniqueness'] = 'missing'
    card_path.write_text(json.dumps(card, indent=2) + '\n')
    release = json.loads(release_path.read_text())
    release['run_card_sha256'] = sha256(card_path.read_bytes())
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'completed HOLDOUT-DTI result is not recorded' in status['reason']
    assert 'byte-read-back validator has no PASS status' in status['reason']
    assert 'complete current registry has not been checked' in status['reason']
    assert 'pre-placement surface correlation' in status['reason']


def test_extreme_numeric_values_and_quota_overflow_fail_closed(tmp_path):
    card_path, release_path = write_valid_release(tmp_path)
    card = json.loads(card_path.read_text())
    enormous = 10**400
    card['holdout_dti']['withheld_positives'] = enormous
    card['holdout_dti']['value'] = enormous
    card['holdout_dti']['ci95'] = [0, enormous]
    card['uniqueness']['preplacement_surface_max_abs_correlation'] = enormous
    card_path.write_text(json.dumps(card, indent=2) + '\n')
    release = json.loads(release_path.read_text())
    release['run_card_sha256'] = sha256(card_path.read_bytes())
    release['remaining_weekly_slots'] = 2**100
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'withheld-positive count is missing or invalid' in status['reason']
    assert 'HOLDOUT-DTI value is missing or outside [0,1]' in status['reason']
    assert '95% confidence interval is missing or invalid' in status['reason']
    assert 'pre-placement surface correlation' in status['reason']
    assert 'within the current three-slot cap' in status['reason']


def test_selector_requires_fresh_utc_quota_check_from_official_competition_page(tmp_path):
    _, release_path = write_valid_release(tmp_path)
    release = json.loads(release_path.read_text())
    release['weekly_quota_checked_at_utc'] = '2020-01-01T00:00:00Z'
    release['weekly_quota_source_url'] = 'https://example.com/fake-quota'
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'timestamp is missing, stale, or not UTC' in status['reason']
    assert 'not linked to the official competition page' in status['reason']


def test_selector_cannot_escape_repository_for_candidate_bytes(tmp_path):
    _, release_path = write_valid_release(tmp_path)
    release = json.loads(release_path.read_text())
    release['candidate_path'] = '../outside.tif'
    release_path.write_text(json.dumps(release, indent=2) + '\n')
    status = load_submission_status(tmp_path)
    assert not status['approved']
    assert 'candidate path is missing or outside the repository' in status['reason']
