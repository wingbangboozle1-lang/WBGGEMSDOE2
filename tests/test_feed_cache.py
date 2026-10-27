from datetime import datetime, timezone
import json

import pytest

from feed_cache import read_observation, restore, save, validate_observation
from refresh_leaderboard import PARTIAL_URL, URL

NOW = datetime(2026, 10, 27, 18, 0, tzinfo=timezone.utc)


def observation(stamp='2026-10-27T17:00:00Z', value=.4544, status='fresh'):
    return {'evidence_class': 'OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT',
            'source_url': URL, 'data_url': PARTIAL_URL,
            'captured_utc': stamp, 'last_attempt_utc': stamp,
            'top_public_dti': value, 'status': status}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_restore_newer_cache_is_stale_until_official_refresh(tmp_path):
    cache, output = tmp_path / 'cache.json', tmp_path / 'leader.json'
    write(cache, observation())
    write(output, observation('2026-10-26T17:00:00Z', .4))
    assert restore(cache, output, now=NOW)
    result = json.loads(output.read_text())
    assert result['top_public_dti'] == .4544
    assert result['captured_utc'] == '2026-10-27T17:00:00Z'
    assert result['status'] == 'stale'
    assert 'stale' in result['note']


def test_cache_cannot_roll_back_newer_committed_snapshot(tmp_path):
    cache, output = tmp_path / 'cache.json', tmp_path / 'leader.json'
    write(cache, observation('2026-10-26T17:00:00Z', .4))
    write(output, observation())
    original = output.read_bytes()
    assert not restore(cache, output, now=NOW)
    assert output.read_bytes() == original
    assert save(output, cache, now=NOW)
    assert json.loads(cache.read_text())['top_public_dti'] == .4544


@pytest.mark.parametrize('change', [
    {'source_url': 'https://evil.example/'},
    {'data_url': 'https://evil.example/'},
    {'evidence_class': 'ORGANIZER-CONFIRMED'},
    {'top_public_dti': float('nan')},
    {'top_public_dti': True},
    {'top_public_dti': 1.1},
    {'captured_utc': '2026-10-27T19:00:00Z'},
    {'captured_utc': '2026-10-27T17:00:00'},
    {'status': 'unknown'},
])
def test_invalid_cache_cannot_replace_snapshot(tmp_path, change):
    cache, output = tmp_path / 'cache.json', tmp_path / 'leader.json'
    bad = observation(); bad.update(change)
    write(cache, bad)
    write(output, observation('2026-10-26T17:00:00Z', .4))
    original = output.read_bytes()
    assert read_observation(cache, now=NOW) is None
    assert not restore(cache, output, now=NOW)
    assert output.read_bytes() == original


def test_same_timestamp_conflicting_value_is_not_saved(tmp_path):
    cache, output = tmp_path / 'cache.json', tmp_path / 'leader.json'
    write(cache, observation(value=.4)); write(output, observation(value=.5))
    assert not save(output, cache, now=NOW)
    assert json.loads(cache.read_text())['top_public_dti'] == .4


def test_bad_json_and_missing_cache_are_noops(tmp_path):
    cache, output = tmp_path / 'cache.json', tmp_path / 'leader.json'
    cache.write_text('{bad')
    assert not restore(cache, output, now=NOW)
    assert not save(output, cache, now=NOW)
    assert not output.exists()


def test_validation_requires_aware_current_time():
    with pytest.raises(ValueError, match='current time'):
        validate_observation(observation(), now=datetime(2026, 10, 27))
