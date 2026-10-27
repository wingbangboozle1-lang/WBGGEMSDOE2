import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _stage(tmp_path):
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'docs' / 'data').mkdir(parents=True)
    (tmp_path / 'docs' / 'downloads').mkdir(parents=True)
    (tmp_path / 'config').mkdir()
    shutil.copy(ROOT / 'scripts/build_site.py', tmp_path / 'scripts/build_site.py')
    for f in (ROOT / 'docs/data').glob('*'):
        if f.is_file():
            shutil.copy(f, tmp_path / 'docs/data' / f.name)
    shutil.copy(ROOT / 'config/registry_inputs.json', tmp_path / 'config/registry_inputs.json')
    release = json.loads((ROOT / 'docs/data/release.json').read_text())
    tif = ROOT / 'docs/downloads' / Path(release['tif']).name
    if tif.is_file():
        shutil.copy(tif, tmp_path / 'docs/downloads' / tif.name)
    return release


def test_builder_refuses_unreviewed_promotion(tmp_path):
    """A mismatched raster hash must stop before any green HTML is written."""
    release = _stage(tmp_path)
    broken = tmp_path / 'docs/data/release.json'
    release['sha256'] = '0' * 64
    broken.write_text(json.dumps(release))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            capture_output=True, text=True)
    assert result.returncode != 0 and 'manual review required before publication' in result.stderr
    assert not (tmp_path / 'docs/index.html').exists()


def test_builder_accepts_fully_receipted_release(tmp_path):
    release = _stage(tmp_path)
    assert release['ok_to_submit'] is True
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'OK TO DOWNLOAD AND SUBMIT' in (tmp_path / 'docs/index.html').read_text()


def test_scheduled_and_legacy_pages_share_url_layout():
    workflow = (ROOT / '.github/workflows/pages.yml').read_text()
    assert 'cp -R docs/. _site/docs/' in workflow and 'cp -R site/. _site/site/' in workflow and 'path: _site' in workflow
    assert 'href="../site/sites/GEMSDOE32.html"' in (ROOT / 'docs/index.html').read_text() or 'site/sites' in (ROOT / 'docs/index.html').read_text()
    assert 'url=./docs/' in (ROOT / 'index.html').read_text()
    assert 'href="sources.html"' in (ROOT / 'docs/index.html').read_text()
    assert 'Official source inventory' in (ROOT / 'docs/sources.html').read_text()
