from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = set(), []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.add(values['id'])
        for key in ('href', 'src'):
            if key in values:
                self.refs.append(values[key])


def test_all_internal_links_resolve():
    pages = list(SITE.rglob('*.html')) + list((ROOT / 'docs').rglob('*.html')) + [ROOT / 'index.html']
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        for link in parser.refs:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith('mailto:'):
                continue
            path = (page.parent / unquote(parts.path)).resolve() if parts.path else page
            if path.is_dir():
                path /= 'index.html'
            assert path.exists(), f'{page.name}: broken local link {link}'
            if parts.fragment and path.suffix == '.html':
                target = Links(); target.feed(path.read_text())
                assert parts.fragment in target.ids, f'{page.name}: broken anchor {link}'


def test_published_evidence_is_fail_closed_and_synced():
    source_card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    published_card = json.loads((SITE / 'data/run_card.json').read_text())
    assert source_card == published_card == json.loads((ROOT / 'docs/data/run-card.json').read_text())
    assert source_card == json.loads((ROOT / 'docs/data/run_card.json').read_text())
    assert source_card['verdict'] == 'negative' and source_card['ok_to_submit'] is False
    assert source_card['holdout']['dti'] is None and source_card['raster_sha256'] is None
    assert source_card['submission_name'] is None and len(source_card['note']) <= 140
    rows = json.loads((SITE / 'data/focus.json').read_text())['entries']
    assert len(rows) == 9 and len({r['site'] for r in rows}) == 9
    assert all(not r['ok_to_submit'] and not r['unique_under_literal_rule'] for r in rows)
    assert all((SITE / r['site_url']).is_file() for r in rows)
    assert all(r['leaderboard_estimate'] is None and len(r['sha256']) == 64 for r in rows)
    assert all(r['max_peer_overlap']['fraction'] > .7 for r in rows)
    home = (SITE / 'index.html').read_text()
    assert 'Submission download unavailable' in home and 'NO FILE CLEARED' in home
    freshness = json.loads((SITE / 'data/focus-freshness.json').read_text())
    assert freshness == json.loads((ROOT / 'docs/data/focus-freshness.json').read_text())
    assert 'newer rasters are not downloaded or audited' in freshness['scope'].lower()
    app = (SITE / 'assets/app.js').read_text()
    assert "data/focus-freshness.json" in app and 'Newer rasters have not been audited' in app


def test_registered_continuous_witness_is_not_mislabeled_as_dots():
    audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
    prior = audit['items']['17GEMSDOE_dense_prior']
    assert prior['support_type'] == 'continuous_probability' and prior['dots'] is None
    assert prior['positive_support_cells'] == audit['lattice_capacity']['footprint_cells']
    assert audit['dense_probability_prior']['full_footprint_positive'] is True
    assert 'whether' in audit['dense_probability_prior']['implication']
