"""Regressions for literal novelty, retired entry points and a complete site rebuild."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_release_triage import audit_one


RETIRED = (
    'make_candidate.py', 'final_audit.py', 'uniqueness_audit.py',
    'generate_h3_pack.py', 'write_h3_submission.py', 'run_wbg2_msptcd.py',
    'run_wbg2_cbs.py', 'run_campaign_20261027.py',
)


@pytest.mark.parametrize('script', RETIRED)
def test_retired_entry_points_stop_before_writing(script):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script), '--selftest'],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'STOP' in result.stdout + result.stderr
    assert any((folder / (script + '.txt')).is_file() for folder in (ROOT / 'evidence/retired_20261027', ROOT / 'evidence/reconciliation_archive/incoming-29abbf69'))


def write_raster(path: Path, values: np.ndarray) -> None:
    with rasterio.open(path, 'w', driver='GTiff', width=values.shape[1], height=values.shape[0],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=from_origin(0, values.shape[0] * 100, 100, 100)) as dst:
        dst.write(values.astype('float32'), 1)


def test_literal_stop_is_strictly_over_seventy_percent_and_never_approves(tmp_path):
    reference = tmp_path / 'reference.tif'
    candidate = tmp_path / 'candidate.tif'
    footprint = np.ones((10, 10), dtype=bool)
    values = np.zeros((10, 10), dtype='float32')
    values[0, :10] = 1
    write_raster(reference, np.zeros((10, 10)))
    write_raster(candidate, values)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    coverage = np.zeros((10, 10), dtype=bool)
    coverage[0, :7] = True
    at_limit = audit_one(candidate, digest, reference, footprint, coverage)
    assert at_limit['final_dot_overlap_3px_vs_13GEMSDOE'] == 0.7
    assert at_limit['literal_witness_result'] == 'no-witness-in-scope'
    assert at_limit['registry_complete'] is False and at_limit['ok_to_submit'] is False
    coverage[0, 7] = True
    above_limit = audit_one(candidate, digest, reference, footprint, coverage)
    assert above_limit['final_dot_overlap_3px_vs_13GEMSDOE'] == 0.8
    assert above_limit['literal_witness_result'] == 'duplicate-stop'
    assert above_limit['preplacement_surface_rank_correlation'] is None
    assert above_limit['ok_to_submit'] is False
    with pytest.raises(ValueError, match='hash mismatch'):
        audit_one(candidate, '0' * 64, reference, footprint, coverage)


def copy_site_sources(destination: Path) -> None:
    for name in ('scripts', 'src', 'config', 'docs', 'site', 'evidence', 'downloads', 'research', 'data_public', 'registry'):
        shutil.copytree(ROOT / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy(ROOT / 'index.html', destination / 'index.html')


def test_site_regeneration_cannot_restore_a_historical_approval(tmp_path):
    copy_site_sources(tmp_path)
    for name in ('build_hypotheses.py', 'build_run_card.py', 'build_site.py',
                 'build_site_data.py', 'build_msptcd_site.py'):
        result = subprocess.run([sys.executable, str(tmp_path / 'scripts' / name)],
                                cwd=tmp_path, capture_output=True, text=True, timeout=25)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    rejected_phrases = (
        'one file is approved to download and submit',
        'one file is ready to download and submit',
        'submit exactly one file:',
        'cleared exactly one submission',
        'zero-leakage holdout',
        'forensic proof',
    )
    pages = [tmp_path / 'index.html', *list((tmp_path / 'docs').rglob('*.html')),
             *list((tmp_path / 'site').rglob('*.html'))]
    for page in pages:
        text = page.read_text(encoding='utf-8').lower()
        assert all(phrase not in text for phrase in rejected_phrases), page
    # Every entrypoint must retain the independently measured negative decision.
    for rel in ('docs/index.html', 'docs/executive-summary.html'):
        text = (tmp_path / rel).read_text(encoding='utf-8')
        assert 'DO NOT SUBMIT' in text and 'OK TO DOWNLOAD AND SUBMIT' not in text, rel
    for rel in ('docs/submit/index.html', 'docs/submission/index.html',
                'docs/msptcd/index.html'):
        text = (tmp_path / rel).read_text(encoding='utf-8')
        assert 'No file is approved for submission.' in text and 'DO NOT SUBMIT' in text, rel
    card = json.loads((tmp_path / 'docs/data/RUN_CARD_FINAL.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['submission_note'] is None and len(card['note']) <= 140


def test_builder_refuses_if_historical_artifact_no_longer_matches_triage(tmp_path):
    copy_site_sources(tmp_path)
    artifact = tmp_path / 'docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif'
    artifact.write_bytes(artifact.read_bytes() + b'tamper')
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and 'Changed or multiply-listed research artifact' in result.stderr


def test_builder_refuses_tampered_final_card_even_if_legacy_card_is_negative(tmp_path):
    copy_site_sources(tmp_path)
    card_path = tmp_path / 'evidence/RUN_CARD_FINAL.json'
    card = json.loads(card_path.read_text())
    card['ok_to_submit'] = True
    card_path.write_text(json.dumps(card))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and 'negative-only dashboard refuses to publish' in result.stderr
