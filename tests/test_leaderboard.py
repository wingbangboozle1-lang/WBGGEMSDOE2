import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import refresh_leaderboard as feed

GOOD = """<html><table><thead><tr><th>Rank</th><th>Participant</th>
<th>Best<br> public <span>DW-Tversky</span></th></tr></thead><tbody>
<tr><td>#1</td><td>A team</td><td>0.4437</td></tr>
<tr><td>#2</td><td>Other</td><td>0.3900</td></tr></tbody></table></html>"""


def test_parse_official_style_table():
    assert feed.parse_top(GOOD) == "0.4437"
    result = feed.snapshot(GOOD)
    assert result["status"] == "ok"
    assert result["top_public_dti"] == "0.4437"
    assert "not a submission-page receipt" in result["evidence_class"]


@pytest.mark.parametrize("page", [
    "<html><h1>Login</h1></html>",
    GOOD.replace("DW-Tversky", "Unrelated metric"),
    GOOD.replace("0.4437", "2.5"),
    GOOD.replace("#1", "#3"),
    GOOD.replace("<td>0.4437</td>", "<td>0.4437</td><td>0.3</td>"),
    GOOD + GOOD,
])
def test_bad_or_ambiguous_pages_are_unavailable(page):
    with pytest.raises(ValueError):
        feed.parse_top(page)
    result = feed.snapshot(page)
    assert result["status"] == "unavailable"
    assert result["top_public_dti"] is None
