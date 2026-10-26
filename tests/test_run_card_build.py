import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_inconsistent_card_never_publishes(tmp_path):
    for directory in ('scripts', 'evidence', 'docs/data'):
        (tmp_path / directory).mkdir(parents=True)
    for name in ('build_run_card.py',):
        shutil.copy(ROOT / 'scripts' / name, tmp_path / 'scripts' / name)
    for name in ('run_card.json', 'registry_audit.json'):
        shutil.copy(ROOT / 'evidence' / name, tmp_path / 'evidence' / name)
    shutil.copy(ROOT / 'docs/data/portfolio.json', tmp_path / 'docs/data/portfolio.json')
    path = tmp_path / 'evidence/run_card.json'
    card = json.loads(path.read_text())
    card['uniqueness']['minimum_overlap_bound'] = .1
    path.write_text(json.dumps(card))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_run_card.py')],
                            capture_output=True, text=True)
    assert result.returncode != 0 and 'manual review required' in result.stderr
    assert not (tmp_path / 'docs/data/run-card.json').exists()
    assert not (tmp_path / 'site/data/run_card.json').exists()
