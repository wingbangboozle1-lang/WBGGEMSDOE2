import json
from urllib.error import URLError

import pytest
import refresh_leaderboard as feed

TABLE = '''<html><table><tr><th>Rank</th><th>Team members</th><th>Participant</th><th>Best<br>public<br>DW-Tversky</th><th>Shared work</th></tr>
<tr><td>#1</td><td></td><td>Alice <span>31 submissions</span></td><td>0.4437</td><td></td></tr>
<tr><td>#2</td><td></td><td>Bob</td><td>0.3916</td><td></td></tr></table></html>'''


def test_parses_only_rank_one_official_column():
    assert feed.parse_top(TABLE) == (0.4437, None)


def test_parses_organizer_thead_without_a_tr():
    fragment = '''<table id="leaderTable"><thead><th>Rank</th><th>Team members</th><th>Participant</th>
    <th><span>Best public</span><br><span>DW-Tversky</span><div>(in descending order)</div></th><th>Shared work</th></thead>
    <tbody><tr><td>#1</td><td></td><td>Alice</td><td>0.4437</td><td></td></tr></tbody></table>'''
    assert feed.parse_top(fragment) == (.4437, None)


@pytest.mark.parametrize('body', [
    '<html>please log in</html>',
    '<table><tr><th>Rank</th><th>Score</th></tr><tr><td>#1</td><td>0.7</td></tr></table>',
    TABLE.replace('<td>0.4437</td>', '<td>4.437</td>'),
    TABLE.replace('<td>#1</td>', '<td>#3</td>'),
    TABLE + TABLE,  # Multiple matching rank-one tables are not unambiguous.
])
def test_rejects_changed_or_ambiguous_page(body):
    with pytest.raises(ValueError):
        feed.parse_top(body)


def test_refresh_failure_preserves_old_capture_and_marks_stale(tmp_path, monkeypatch):
    path = tmp_path / 'leaderboard.json'
    path.write_text(json.dumps({'captured_utc':'2026-10-01T01:00:00Z', 'top_public_dti':0.4}))
    monkeypatch.setattr(feed, 'urlopen', lambda *a, **kw: (_ for _ in ()).throw(URLError('blocked')))
    assert not feed.refresh(path)
    result = json.loads(path.read_text())
    assert result['top_public_dti'] == 0.4
    assert result['captured_utc'] == '2026-10-01T01:00:00Z'
    assert result['status'] == 'stale'
    assert result['last_attempt_utc'] != result['captured_utc']


def test_fresh_observation_uses_official_url_and_timestamp(tmp_path, monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return feed.PARTIAL_URL
        def read(self, *args): return TABLE.encode()
    def official_request(req, **kwargs):
        assert req.full_url == feed.PARTIAL_URL and req.get_header('Hx-request') == 'true'
        return Response()
    monkeypatch.setattr(feed, 'urlopen', official_request)
    path = tmp_path / 'leaderboard.json'
    assert feed.refresh(path)
    result = json.loads(path.read_text())
    assert result['status'] == 'fresh' and result['top_public_dti'] == .4437
    assert result['source_url'] == feed.URL and result['data_url'] == feed.PARTIAL_URL
    assert result['captured_utc'] == result['last_attempt_utc']


def test_unofficial_redirect_is_not_accepted(tmp_path, monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def geturl(self): return 'https://evil.example/leaderboard/'
    monkeypatch.setattr(feed, 'urlopen', lambda *a, **kw: Response())
    path = tmp_path / 'out.json'
    assert not feed.refresh(path)
    assert json.loads(path.read_text())['status'] == 'stale'


def test_same_host_wrong_endpoint_is_not_accepted(tmp_path, monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def geturl(self): return feed.URL
    monkeypatch.setattr(feed, 'urlopen', lambda *a, **kw: Response())
    path=tmp_path/'out.json'
    assert not feed.refresh(path)
    assert json.loads(path.read_text())['status']=='stale'
