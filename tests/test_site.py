from html.parser import HTMLParser
from pathlib import Path
import json
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / x for x in ('research-desk.html', 'executive-summary.html', 'research.html')]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


def test_local_links_and_anchors_exist():
    parsed = {}
    for page in PAGES:
        parser = Links()
        parser.feed(page.read_text(encoding='utf-8'))
        parsed[page] = parser
    for page, parser in parsed.items():
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            assert target.exists(), f'{page.name}: missing {link}'
            if url.fragment and target.suffix == '.html':
                assert url.fragment in parsed[target].ids, f'{page.name}: missing {link}'


def test_focus_table_matches_audit_and_never_offers_upload():
    text = (ROOT / 'executive-summary.html').read_text()
    pins = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    for row in pins['focus_sites']:
        assert row['filename'] in text and row['research_download'] in text
    assert text.count('class="table-status">DO NOT SUBMIT') == 10
    assert 'No new candidate file' in text and 'Unavailable' in text
    assert 'USER-REPORTED' in text and 'not organizer-confirmed' in text


def test_critical_status_visible_without_javascript():
    home = (ROOT / 'research-desk.html').read_text()
    summary = (ROOT / 'executive-summary.html').read_text()
    assert 'No new file is' in home and 'cleared to submit' in home
    assert 'Do not submit. There is no new eligible GeoTIFF.' in summary
    assert home.index('SUBMISSION READINESS') < home.index('THE CURRENT PICTURE')
    assert 'research only' in summary
