import pytest
from scripts.refresh_leaderboard import parse_leaderboard, update_snapshot

HTML = '''<!doctype html><table><thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
<th>Best<br>public<br>DW-Tversky</th><th>Shared work</th></tr></thead><tbody>
<tr><td>#1</td><td><a href="/profile"><img alt="avatar"></a></td><td><a href="/u">xiaofanhu</a><br>18h ago</td><td>0.4437</td><td></td></tr>
<tr><td>#2</td><td></td><td>second</td><td>0.3916</td><td></td></tr></tbody></table>'''


def test_parse_public_rank_one():
    assert parse_leaderboard(HTML) == {'participant': 'xiaofanhu', 'score': 0.4437}


@pytest.mark.parametrize('bad', [
    '<html><h1>Login</h1></html>',
    HTML.replace('public', 'private'),
    HTML.replace('0.4437', '1.2'),
    HTML.replace('0.4437', 'nan'),
    HTML.replace('#1', '#3'),
    HTML + HTML,
])
def test_reject_wrong_or_ambiguous_page(bad):
    with pytest.raises(ValueError):
        parse_leaderboard(bad)


def test_failed_fetch_keeps_last_good_value_and_timestamp():
    previous = {'participant': 'prior', 'score': 0.4, 'observed_at_utc': '2026-01-01T00:00:00Z'}
    result = update_snapshot(previous, '<html>login</html>', '2026-01-02T00:00:00Z')
    assert result['score'] == 0.4 and result['participant'] == 'prior'
    assert result['observed_at_utc'] == '2026-01-01T00:00:00Z'
    assert result['last_attempt_at_utc'] == '2026-01-02T00:00:00Z'
    assert result['last_attempt_result'].startswith('failed:')


def test_success_advances_observation_and_does_not_mutate_previous():
    previous = {'participant': 'prior', 'score': 0.4, 'observed_at_utc': '2026-01-01T00:00:00Z'}
    result = update_snapshot(previous, HTML, '2026-01-02T00:00:00Z')
    assert result['score'] == 0.4437 and result['last_attempt_result'] == 'success'
    assert result['observed_at_utc'] == '2026-01-02T00:00:00Z'
    assert previous['score'] == 0.4


def test_corrupt_cache_falls_back_to_valid_snapshot(tmp_path):
    import json
    from scripts.refresh_leaderboard import load_previous, URL
    valid = {'score': 0.42, 'participant': 'example', 'observed_at_utc': '2026-10-26T00:00:00Z',
             'source_url': URL, 'evidence_class': 'PUBLIC-LEADERBOARD-OBSERVATION'}
    output, cache = tmp_path / 'source.json', tmp_path / 'cache.json'
    output.write_text(json.dumps(valid))
    cache.write_text('{broken')
    assert load_previous(output, cache) == valid
    cache.write_text(json.dumps({**valid, 'source_url': 'https://not-the-organizer.example'}))
    assert load_previous(output, cache) == valid
    cache.write_text(json.dumps({**valid, 'observed_at_utc': 123}))
    assert load_previous(output, cache) == valid
    output.write_text('{}')
    with pytest.raises(ValueError, match='no valid previous'):
        load_previous(output, cache)
