from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.base = set(), [], None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.add(values['id'])
        if tag == 'base' and values.get('href'):
            self.base = values['href']
            return
        for key in ('href', 'src'):
            if key in values:
                self.refs.append(values[key])


def test_all_internal_links_resolve():
    pages = list(SITE.rglob('*.html')) + list((ROOT / 'docs').rglob('*.html')) + [ROOT / 'index.html']
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        base = urljoin(page.as_uri(), parser.base) if parser.base else page.as_uri()
        for link in parser.refs:
            parts = urlsplit(urljoin(base, link))
            if parts.scheme != 'file' or parts.netloc:
                continue
            path = Path(unquote(parts.path)).resolve()
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
    assert source_card['verdict'] == 'promote-to-selector-only' and source_card['ok_to_submit'] is True
    assert source_card['holdout']['dti'] > .13 and len(source_card['raster_sha256']) == 64
    assert source_card['submission_name'] and len(source_card['note']) <= 140
    release = json.loads((SITE / 'data/release.json').read_text())
    assert release == json.loads((ROOT / 'docs/data/release.json').read_text())
    assert release['sha256'] == source_card['raster_sha256']
    assert release['ok_to_submit'] and all(release['gates'].values())
    assert (ROOT / 'docs/downloads' / Path(release['tif']).name).is_file()
    rows = json.loads((SITE / 'data/focus.json').read_text())['entries']
    assert len(rows) == 9 and len({r['site'] for r in rows}) == 9
    assert all(not r['ok_to_submit'] and not r['unique_under_literal_rule'] for r in rows)
    assert all((SITE / r['site_url']).is_file() for r in rows)
    assert all(r['leaderboard_estimate'] is None and len(r['sha256']) == 64 for r in rows)
    assert all(r['max_peer_overlap']['fraction'] > .7 for r in rows)
    home = (SITE / 'index.html').read_text()
    assert '1 FILE CLEARED' in home and 'OK TO SUBMIT' in home
    assert 'OK TO DOWNLOAD' in home and Path(release['tif']).name in home
    guide = (SITE / 'executive.html').read_text()
    assert source_card['submission_name'] in guide and source_card['submission_note'] in guide


def test_registered_continuous_witness_is_not_mislabeled_as_dots():
    audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
    prior = audit['items']['17GEMSDOE_dense_prior']
    assert prior['support_type'] == 'continuous_probability' and prior['dots'] is None
    assert prior['positive_support_cells'] == audit['lattice_capacity']['footprint_cells']
    assert audit['dense_probability_prior']['full_footprint_positive'] is True
    assert 'whether' in audit['dense_probability_prior']['implication']
