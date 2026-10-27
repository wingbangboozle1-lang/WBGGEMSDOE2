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
    assert 'path: _site' in workflow and 'python scripts/build_release_review.py' in workflow
    assert 'build_legacy_routes()' in (ROOT / 'scripts/build_release_review.py').read_text()
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


def test_builder_refuses_changed_archived_raster_bytes(tmp_path):
    """Publication cannot silently reuse an audit for different TIFF bytes."""
    import json
    for directory in ('scripts', 'config', 'evidence'):
        (tmp_path / directory).mkdir()
    shutil.copy(ROOT / 'scripts/build_site.py', tmp_path / 'scripts/build_site.py')
    shutil.copy(ROOT / 'config/research_hypotheses.json', tmp_path / 'config/research_hypotheses.json')
    shutil.copytree(ROOT / 'docs/data', tmp_path / 'docs/data')
    for name in ('parallel_review.json', 'conduit_review.json', 'local_artifact_audit_20261027.json'):
        shutil.copy(ROOT / 'evidence' / name, tmp_path / 'evidence' / name)
    report = json.loads((tmp_path / 'evidence/local_artifact_audit_20261027.json').read_text())
    first = report['artifacts'][0]
    altered = tmp_path / first['path']
    altered.parent.mkdir(parents=True, exist_ok=True)
    altered.write_bytes((ROOT / first['path']).read_bytes() + b'changed')
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Archived raster bytes changed' in result.stderr
    assert not (tmp_path / 'docs/index.html').exists()
