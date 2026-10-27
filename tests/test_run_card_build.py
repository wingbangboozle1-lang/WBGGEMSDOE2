import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ['campaign_20261027.json', 'soft_novelty_refinement.json',
            'holdout_20261027.json', 'canaries_20261027.json',
            'final_uniqueness.json', 'final_format.json',
            'registry_union.json', 'registry_expanded.json', 'registry_audit.json',
            'run_card_20261026_negative.json']


def _stage(tmp_path):
    for directory in ('scripts', 'evidence', 'docs/data', 'site/data', 'config', 'docs/downloads'):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / 'scripts/build_run_card.py', tmp_path / 'scripts/build_run_card.py')
    for name in EVIDENCE:
        shutil.copy(ROOT / 'evidence' / name, tmp_path / 'evidence' / name)
    shutil.copy(ROOT / 'config/registry_inputs.json', tmp_path / 'config/registry_inputs.json')
    release = json.loads((ROOT / 'docs/data/release.json').read_text())
    tif = ROOT / 'docs/downloads' / Path(release['tif']).name
    if tif.is_file():
        shutil.copy(tif, tmp_path / 'docs/downloads' / tif.name)


def test_inconsistent_receipt_never_publishes(tmp_path):
    _stage(tmp_path)
    path = tmp_path / 'evidence/final_uniqueness.json'
    data = json.loads(path.read_text())
    data['tif_sha256'] = '0' * 64
    path.write_text(json.dumps(data))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_run_card.py')],
                            capture_output=True, text=True)
    assert result.returncode != 0 and 'manual review required' in result.stderr
    assert not (tmp_path / 'docs/data/run-card.json').exists()
    assert not (tmp_path / 'site/data/run_card.json').exists()


def test_consistent_receipts_publish_identical_cards(tmp_path):
    _stage(tmp_path)
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_run_card.py')],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    card = (tmp_path / 'evidence/run_card.json').read_text()
    assert card == (tmp_path / 'docs/data/run-card.json').read_text()
    assert card == (tmp_path / 'site/data/run_card.json').read_text()
    assert json.loads(card)['verdict'] == 'promote-to-selector-only'
