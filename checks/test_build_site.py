import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def test_builder_refuses_unreviewed_promotion(tmp_path):
    (tmp_path/'scripts').mkdir();(tmp_path/'docs').mkdir()
    shutil.copy(ROOT/'scripts/build_site.py',tmp_path/'scripts/build_site.py')
    shutil.copytree(ROOT/'docs/data',tmp_path/'docs/data')
    card=tmp_path/'docs/data/run-card.json';data=json.loads(card.read_text());data['verdict']='promote';card.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,str(tmp_path/'scripts/build_site.py')],capture_output=True,text=True)
    assert result.returncode != 0 and 'renders only the audited negative run' in result.stderr
    assert not (tmp_path/'docs/index.html').exists()
