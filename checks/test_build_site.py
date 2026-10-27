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


def test_scheduled_and_legacy_pages_share_url_layout():
    workflow=(ROOT/'.github/workflows/pages.yml').read_text()
    assert 'cp -R docs/. _site/docs/' in workflow and 'cp -R site/. _site/site/' in workflow and 'path: _site' in workflow
    assert 'url=./docs/' in (ROOT/'index.html').read_text()
    home=(ROOT/'docs/index.html').read_text()
    # Dashboard must lead to the fail-closed guide, never a historical TIFF download.
    assert 'href="executive-summary.html"' in home
    assert 'href="sources.html"' in home
    assert 'href="submit/"' in home
    assert 'No submission download is available' in home
    assert 'href="downloads/h3-pack/' not in home
    sub=(ROOT/'docs/submission/index.html').read_text()
    assert 'href="../sites/GEMSDOE32.html"' in sub
    assert (ROOT/'docs/submission/sites/GEMSDOE32.html').is_file()
    assert 'Official source inventory' in (ROOT/'docs/submission/sources.html').read_text()
