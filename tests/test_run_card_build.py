import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def test_current_run_card_inventory_matches_release_audit_and_local_files():
    release = json.loads((ROOT / 'evidence/release_audit.json').read_text())
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    inventory = card['raw_feature_inputs']['current_availability']
    scope = release['scope']

    assert card['release_reconciliation']['owned_tif_paths'] == scope['owned_tif_paths']
    assert card['release_reconciliation']['distinct_raster_sha256'] == scope['distinct_tif_sha256']
    assert card['release_reconciliation']['pinned_witnesses'] == scope['registry_rasters_opened']
    assert card['release_reconciliation']['zip_archives'] == len(release['zip_archives'])
    assert f"{scope['owned_tif_paths']} TIFF paths" in card['validator']['status']
    assert f"{scope['distinct_tif_sha256']} distinct SHA-256 identities" in card['validator']['status']
    assert f"{len(release['zip_archives'])} ZIP archives" in card['validator']['status']

    for row in inventory['competition_inputs_from_prior_receipt']:
        path = ROOT / row['path']
        present = path.is_file() and not path.is_symlink()
        assert row['present'] is present
        if present:
            assert row['bytes'] == path.stat().st_size
            assert row['sha256'] == file_sha256(path)
            assert row['verified'] is (row['sha256'] == row['expected_sha256']
                                       and row['bytes'] == row['expected_bytes'])
        else:
            assert row['sha256'] is None and not row['verified']

    bands = sorted((ROOT / '.cache/features').glob('band-*.npy')) if (ROOT / '.cache/features').is_dir() else []
    band_rows = inventory['raw_band_cache']['files']
    assert inventory['raw_band_cache']['present_count'] == sum(row['present'] for row in band_rows)
    assert inventory['raw_band_cache']['verified_count'] == sum(row['verified'] for row in band_rows)
    assert inventory['raw_band_cache']['present_count'] == len(bands)
    for row in band_rows:
        path = ROOT / row['path']
        present = path.is_file() and not path.is_symlink()
        assert row['present'] is present
        if present:
            assert row['sha256'] == file_sha256(path)
            assert row['verified'] is (row['sha256'] == row['expected_sha256'])
    for row in inventory['shared_template']['required_files']:
        path = ROOT / row['path']
        present = path.is_file() and not path.is_symlink()
        assert row['present'] is present
        if present:
            assert row['sha256'] == file_sha256(path)
            assert row['verified'] is (row['sha256'] == row['expected_sha256']
                                       and row['bytes'] == row['expected_bytes'])
    for row in inventory['small_audit_mirrors']:
        path = ROOT / row['path']
        present = path.is_file() and not path.is_symlink()
        assert row['present'] is present
        if present:
            assert row['bytes'] == path.stat().st_size
            assert row['sha256'] == file_sha256(path)
            assert row['verified'] is (row['sha256'] == row['expected_sha256']
                                       and row['bytes'] == row['expected_bytes'])
    bank_paths = []
    for parent in (ROOT / '.cache', ROOT / 'data'):
        if parent.is_dir():
            bank_paths.extend(str(path.relative_to(ROOT)) for path in parent.rglob('bank_u8.npy')
                              if path.is_file() and not path.is_symlink())
    bank = inventory['derived_shared_feature_bank']
    assert bank['paths'] == sorted(bank_paths)
    assert bank['available'] is bool(bank_paths)
    assert card['generated_utc'] == inventory['checked_utc']
    assert card['updated_utc'] == inventory['checked_utc']
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['raster_sha256'] is None and card['submission_name'] is None


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
