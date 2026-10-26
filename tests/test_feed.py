from datetime import datetime, timezone
import json
import pytest
from refresh_feed import PARTIAL_URL, parse_leaderboard, refresh

HTML = '''<table><thead><tr><th>Rank</th><th>Participant</th>
<th>Best<br>public<br>DW-Tversky (in descending order)</th></tr></thead>
<tbody><tr><td>#1</td><td><a>person</a> 4 hours ago</td><td>0.4437</td></tr>
<tr><td>#2</td><td>someone</td><td>0.3</td></tr></tbody></table>'''


def test_parse_specific_official_table():
    assert parse_leaderboard(HTML) == .4437
    for bad in ('<html></html>', HTML.replace('DW-Tversky', 'Other'),
                HTML.replace('0.4437', 'score: 0.4437'), HTML.replace('#1', '#2')):
        with pytest.raises(ValueError):
            parse_leaderboard(bad)


def test_fallback_is_stale_and_token_never_output():
    sha = 'a' * 40
    snapshots = {'sites': [{'site': 'GEMSDOE24', 'observed_main_sha': sha}]}
    fallback = {'leaderboard': {'value': .4, 'observed_at': '2020-01-01T00:00:00Z'}}
    def fetch(url, *, github=False):
        if github:
            return json.dumps({'sha': 'b' * 40})
        raise OSError('offline')
    result = refresh(fallback, snapshots, fetch=fetch, now=datetime(2026, 10, 26, tzinfo=timezone.utc))
    assert result['leaderboard']['status'] == 'stale'
    assert result['leaderboard']['value'] == .4 and result['leaderboard']['observed_at'].startswith('2020')
    assert result['sites'][0]['status'] == 'changed'


def test_fresh_feed_unknown_github_and_unlisted_site():
    snapshots = {'sites': [{'site': 'GEMSDOE25', 'observed_main_sha': 'a' * 40}]}
    def fetch(url, *, github=False):
        if github:
            raise OSError('offline')
        assert url == PARTIAL_URL
        return HTML
    result = refresh({}, snapshots, fetch=fetch)
    assert result['leaderboard']['status'] == 'fresh' and result['leaderboard']['value'] == .4437
    assert result['sites'][0]['status'] == 'unknown'
    snapshots['sites'][0]['site'] = 'NOT-ALLOWED'
    with pytest.raises(ValueError):
        refresh({}, snapshots, fetch=fetch)


def test_fragment_implicit_header_and_ambiguous_tables():
    fragment = HTML.replace('<thead><tr>', '<thead>').replace('</tr></thead>', '</thead>')
    assert parse_leaderboard(fragment) == .4437
    with pytest.raises(ValueError):
        parse_leaderboard(fragment + fragment)
