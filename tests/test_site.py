import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site


def test_build_has_every_site_and_no_candidate_download(tmp_path):
    build_site.build(tmp_path)
    landing = (tmp_path / "index.html").read_text()
    summary = (tmp_path / "executive-summary.html").read_text()
    manifest = json.loads((ROOT / "data/focus-inputs.json").read_text())
    assert "No file approved for submission" in landing
    assert "DO NOT SUBMIT — no new TIFF was created" in summary
    assert summary.count("Historical mirror · research only") == 9
    for item in manifest["focus_sites"]:
        assert item["site"] in summary and item["filename"] in summary
    assert "{{FOCUS_ROWS}}" not in summary
    assert not list(tmp_path.rglob("*.tif"))
    card = json.loads((tmp_path / "docs/data/run-card.json").read_text())
    assert card["raster_sha256"] is None and card["ok_to_submit"] is False
    assert len(card["submission_note"]) <= 140


def test_internal_site_links_and_anchors_resolve(tmp_path):
    from html.parser import HTMLParser
    from urllib.parse import urlsplit, unquote

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs, self.ids = [], set()
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                self.ids.add(attrs["id"])
            if tag == "a" and "href" in attrs:
                self.hrefs.append(attrs["href"])

    build_site.build(tmp_path)
    for page in (tmp_path / "index.html", tmp_path / "executive-summary.html"):
        parser = Links()
        parser.feed(page.read_text())
        for link in parser.hrefs:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = page if not url.path else (page.parent / unquote(url.path))
            assert target.is_file(), f"Broken local link {link} in {page.name}"
            if url.fragment and target.suffix == ".html":
                dest = Links()
                dest.feed(target.read_text())
                assert url.fragment in dest.ids, f"Missing anchor {link} in {page.name}"


def test_branch_published_pages_match_generated_output(tmp_path):
    build_site.build(tmp_path)
    for name in ("index.html", "executive-summary.html"):
        assert (ROOT / name).read_text() == (tmp_path / name).read_text(), f"Regenerate {name} for branch-based Pages"


def test_builder_fails_closed_if_evidence_changes():
    manifest = json.loads((ROOT / "data/focus-inputs.json").read_text())
    audit = json.loads((ROOT / "docs/data/focus-audit.json").read_text())
    audit["historical_focus"][0]["literal_peer_duplicate"] = False
    with pytest.raises(ValueError):
        build_site.focus_rows(manifest, audit)
