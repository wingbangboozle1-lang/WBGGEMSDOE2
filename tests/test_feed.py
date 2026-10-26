import pytest
from refresh_feed import parse_leaderboard, refresh

EXAMPLE = '''<html><table><tr><th>Rank</th><th>Participant</th><th>Best public<br>DW-Tversky</th></tr>
<tr><td>#1</td><a href="/users/a">a</a><br>31 submissions</td><td>0.4437</td></tr>
<tr><td>#2</td><td>b</td><td>0.3916</td></tr></table></html>'''


def test_parse_rank_one_from_recognized_table():
    assert parse_leaderboard(EXAMPLE) == {'top_score':'0.4437', 'rank':1}


@pytest.mark.parametrize('body', ['', '<h1>Login</h1>', '<table><tr><th>Rank</th><th>Score</th></tr><tr><td>#1</td><td>0.4</td></tr></table>',
                                 EXAMPLE.replace('0.4437','2.1234'), EXAMPLE.replace('#1','#2')])
def test_reject_unrecognizable_or_out_of_range(body):
    with pytest.raises(ValueError):
        parse_leaderboard(body)


def test_refuse_multiple_top_scores():
    html = EXAMPLE.replace('<td>0.4437</td>', '<td>0.4437</td><td>0.2</td>')
    with pytest.raises(ValueError, match='ambiguous'):
        parse_leaderboard(html)


def test_failure_keeps_last_observation_not_fake_new_score():
    base = {'top_score':'0.4','observed_at_utc':'2026-10-25T00:00:00+00:00'}
    result = refresh(base, lambda _: '<h1>Login</h1>')
    assert result['status'] == 'stale'
    assert result['top_score'] == '0.4'
    assert result['observed_at_utc'] == base['observed_at_utc']
    assert result['last_error']


def test_success_records_new_official_snapshot_only():
    result = refresh({'top_score':'0.4'}, lambda _: EXAMPLE)
    assert result['status'] == 'fresh' and result['top_score'] == '0.4437'
    assert result['kind'].startswith('OFFICIAL PUBLIC LEADERBOARD SNAPSHOT')
    assert 'not a submission receipt' in result['kind']
    assert result['observed_at_utc']
