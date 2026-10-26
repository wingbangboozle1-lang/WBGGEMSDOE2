from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'deep-review'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ('a', 'link') and 'href' in values:
            self.links.append(values['href'])
        if tag == 'script' and 'src' in values:
            self.links.append(values['src'])


def test_all_local_site_links_exist():
    for p in DOCS.glob('*.html'):
        parser = Links()
        parser.feed(p.read_text(encoding='utf8'))
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path:
                continue
            dest = (p.parent / unquote(u.path)).resolve()
            assert dest.is_relative_to(DOCS.resolve()), link
            assert dest.is_file(), f'{p.name}: broken {link}'


def test_site_exposes_fail_closed_decision_and_nine_rows():
    page = (DOCS / 'index.html').read_text(encoding='utf8')
    assert 'No new TIFF is approved for submission' in page
    assert page.count('<tr data-site=') == 9
    assert 'No calibrated estimate' in page
    assert 'not proof of scientific copying' in page
    card = json.loads((DOCS/'data/run-card.json').read_text())
    assert not card['ok_to_submit'] and card['raster_sha256'] is None


def test_guide_reports_format_and_current_stop():
    page = (DOCS / 'executive-summary.html').read_text(encoding='utf8')
    assert 'DO NOT SUBMIT' in page
    assert '[0,1]' in page and 'EPSG:32611' in page
    assert 'actual cause has not been established' in page


def test_legacy_pages_root_redirects_to_committed_site():
    landing = (ROOT / 'index.html').read_text(encoding='utf8')
    assert 'url=./docs/' in landing and (ROOT / 'docs/index.html').is_file()
    assert (DOCS / 'index.html').is_file()


def test_guides_include_evidence_and_newer_research_only_links():
    guide = (DOCS / 'executive-summary.html').read_text(encoding='utf8')
    assert guide.count('<tr data-site=') == 9
    assert 'current-candidates-audit.json' in guide
    evidence = json.loads((DOCS / 'data/current-candidates-audit.json').read_text())
    assert len(evidence['results']) == 3
    assert all(row['verdict'] == 'DO NOT SUBMIT' for row in evidence['results'])


def test_primary_dashboard_links_to_independently_audited_research():
    primary = (ROOT / 'docs/index.html').read_text(encoding='utf8')
    assert 'Newer external research files' in primary
    assert 'deep-review/index.html' in primary
    assert 'current-candidates-audit.json' in primary
    data = json.loads((ROOT / 'docs/data/current-candidates-audit.json').read_text())
    assert all(not row['ok_to_submit'] for row in data['results'])
