"""Regression checks for the static Pages layout and research claims."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://pages.invalid/"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.base = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base" and attrs.get("href"):
            self.base = attrs["href"]
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])
        for key in ("href", "src"):
            if attrs.get(key) and not (tag == "base" and key == "href"):
                self.refs.append(attrs[key])


def test_local_links_and_html_anchors_are_in_pages_artifact():
    files = [ROOT / "index.html", *(ROOT / "docs").rglob("*.html"), *(ROOT / "site").rglob("*.html")]
    parsed = {}
    for file in files:
        page = Page()
        page.feed(file.read_text(encoding="utf-8"))
        parsed[file.resolve()] = page
    problems = []
    for file, page in parsed.items():
        origin = ORIGIN + file.relative_to(ROOT).as_posix()
        effective = urljoin(origin, page.base) if page.base else origin
        for ref in page.refs:
            url = urlsplit(urljoin(effective, ref))
            if url.netloc != "pages.invalid" or url.scheme != "https":
                continue
            target = (ROOT / unquote(url.path).lstrip("/")).resolve()
            if target.is_dir():
                target = target / "index.html"
            staged = target == ROOT / "index.html" or ROOT / "docs" in target.parents or ROOT / "site" in target.parents
            if not staged or not target.is_file():
                problems.append(f"{file.relative_to(ROOT)}: {ref} is missing or not staged for Pages")
            elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                problems.append(f"{file.relative_to(ROOT)}: {ref} has no matching anchor")
    assert not problems, "\n".join(problems)


def test_b2_analysis_is_rendered_and_does_not_invent_a_catalogue_buffer():
    source = (ROOT / "docs/research/why-b2-scored-2778.md").read_text()
    html = (ROOT / "docs/research/why-b2-scored-2778.html").read_text()
    assert "1–2 pixels away are **not** known to be masked" in source
    assert "0.0178 (0.2778 − 0.2600)" in source
    assert '<base href="../">' in html
    assert "<h1>Why GEMSDOE32 B2" in html and "<h2>1. What the bytes" in html
    assert "<pre" not in html
    assert "research/why-b2-scored-2778.html" in (ROOT / "docs/index.html").read_text()


def test_ranked_proposals_match_both_dashboards():
    import json
    data = json.loads((ROOT / "config/research_hypotheses.json").read_text())
    rows = data["hypotheses"]
    assert 3 <= len(rows) <= 5
    assert data["method_lane"]["status"] == "UNASSIGNED"
    ranking = (ROOT / "research/hypotheses.md").read_text()
    docs = (ROOT / "docs/research.html").read_text()
    fieldnotes = (ROOT / "site/research.html").read_text()
    for row in rows:
        assert row["title"] in ranking and row["title"] in docs and row["title"] in fieldnotes
    assert "UNASSIGNED" in docs and "UNASSIGNED" in fieldnotes
