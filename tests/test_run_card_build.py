import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_inventory_counts_match_byte_bound_audit():
    audit = json.loads((ROOT / 'evidence/release_audit.json').read_text())
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    scope = audit['scope']
    assert card['existing_artifact_audit']['scope'] == scope
    assert card['release_reconciliation']['owned_tif_paths'] == scope['owned_tif_paths']
    assert card['release_reconciliation']['distinct_raster_sha256'] == scope['distinct_tif_sha256']
    assert card['release_reconciliation']['zip_archives'] == len(audit['zip_archives'])
    assert card['release_reconciliation']['pinned_witnesses'] == scope['registry_rasters_opened']


def test_inconsistent_card_never_publishes(tmp_path):
    for directory in ('scripts', 'evidence', 'docs/data'):
        (tmp_path / directory).mkdir(parents=True)
    for name in ('build_run_card.py',):
        shutil.copy(ROOT / 'scripts' / name, tmp_path / 'scripts' / name)
    for name in ('run_card.json', 'registry_audit.json', 'parallel_review.json', 'parallel_candidate_audit.json', 'conduit_review.json'):
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
