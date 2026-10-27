import json
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_builder_refuses_unreviewed_promotion(tmp_path):
    for directory in ('scripts', 'docs/data', 'config', 'evidence'):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / 'scripts/build_site.py', tmp_path / 'scripts/build_site.py')
    shutil.copy(ROOT / 'scripts/submission_status.py', tmp_path / 'scripts/submission_status.py')
    shutil.copy(ROOT / 'config/research_hypotheses.json', tmp_path / 'config/research_hypotheses.json')
    shutil.copytree(ROOT / 'docs/data', tmp_path / 'docs/data', dirs_exist_ok=True)
    shutil.copy(ROOT / 'evidence/run_card.json', tmp_path / 'evidence/run_card.json')
    card_path = tmp_path / 'evidence/run_card.json'
    card = json.loads(card_path.read_text())
    card['verdict'] = 'promote'
    card['ok_to_submit'] = True
    card['ok_to_download_new_tif'] = True
    card['raster_sha256'] = 'a' * 64
    card_path.write_text(json.dumps(card))
    (tmp_path / 'docs/data/run-card.json').write_text(json.dumps(card))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            capture_output=True, text=True)
    assert result.returncode != 0 and 'renders only the audited negative run' in result.stderr
    assert not (tmp_path / 'docs/index.html').exists()


def test_scheduled_and_legacy_pages_share_fail_closed_status():
    workflow = (ROOT / '.github/workflows/pages.yml').read_text()
    assert 'cp -R docs/. _site/docs/' in workflow and 'cp -R site/. _site/site/' in workflow and 'path: _site' in workflow
    for builder in ('build_submit_page.py', 'build_site_v2.py', 'build_msptcd_site.py'):
        assert builder in workflow
    root = (ROOT / 'index.html').read_text()
    assert 'url=./docs/' in root and 'DO NOT SUBMIT' in root
    home = (ROOT / 'docs/index.html').read_text()
    assert 'DO NOT SUBMIT' in home and 'no candidate is cleared for download' in home.lower()
    assert 'submission/index.html' not in home
    assert 'sources.html' in home
    submit = (ROOT / 'docs/submit/index.html').read_text()
    assert 'DO NOT SUBMIT' in submit and 'No GeoTIFF is approved' in submit
    assert not any(f'.{ext}' in submit for ext in ('tif', 'zip'))
    archive = (ROOT / 'docs/submission/index.html').read_text()
    assert 'DO NOT SUBMIT' in archive and 'Research archive' in archive
    links = re.findall(r'href="([^"]+)"', archive)
    assert not any(link.lower().split('?', 1)[0].endswith(('.tif', '.zip')) for link in links)
    assert 'Historical file name (not linked)' in archive
    assert 'Official source' in (ROOT / 'docs/submission/sources.html').read_text()
