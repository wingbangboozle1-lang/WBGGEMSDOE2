import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_builder_refuses_unreviewed_promotion(tmp_path):
    (tmp_path/'scripts').mkdir();(tmp_path/'docs').mkdir();(tmp_path/'config').mkdir()
    shutil.copy(ROOT/'scripts/build_site.py',tmp_path/'scripts/build_site.py')
    shutil.copy(ROOT/'config/research_hypotheses.json',tmp_path/'config/research_hypotheses.json')
    shutil.copytree(ROOT/'docs/data',tmp_path/'docs/data')
    card=tmp_path/'docs/data/run-card.json';data=json.loads(card.read_text());data['verdict']='promote';card.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,str(tmp_path/'scripts/build_site.py')],capture_output=True,text=True)
    assert result.returncode != 0 and 'renders only the audited negative run' in result.stderr
    assert not (tmp_path/'docs/index.html').exists()


def test_scheduled_and_legacy_pages_share_fail_closed_routes():
    workflow = (ROOT / '.github/workflows/pages.yml').read_text()
    assert 'cp -R docs/. _site/docs/' in workflow and 'cp -R site/. _site/site/' in workflow
    assert 'path: _site' in workflow and 'python scripts/build_legacy_routes.py' in workflow
    root = (ROOT / 'index.html').read_text()
    assert 'url=./docs/' in root and 'DO NOT SUBMIT' in root
    home = (ROOT / 'docs/index.html').read_text()
    assert 'href="executive-summary.html"' in home and 'href="sources.html"' in home
    assert 'No submission file' in home and 'ready to download and submit' not in home.lower()
    sub = (ROOT / 'docs/submission/index.html').read_text()
    assert 'DO NOT SUBMIT' in sub and 'url=../executive-summary.html' in sub
    site = (ROOT / 'docs/submission/sites/GEMSDOE32.html').read_text()
    assert 'DO NOT SUBMIT' in site and '../../../site/sites/GEMSDOE32.html' in site
    sources = (ROOT / 'docs/submission/sources.html').read_text()
    assert 'DO NOT SUBMIT' in sources and 'url=../sources.html' in sources
