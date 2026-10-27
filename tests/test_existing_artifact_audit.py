"""Synthetic, read-only checks for the historical-raster stop audit."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_existing_artifacts as audit


def write_tif(path: Path, data: np.ndarray, *, transform=None, nodata=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, 'w', driver='GTiff', count=1, width=data.shape[1],
                       height=data.shape[0], dtype='float32', crs='EPSG:32611',
                       transform=transform or from_origin(500000, 4500000, 100, 100),
                       nodata=nodata) as dst:
        dst.write(data.astype('float32'), 1)


@pytest.fixture
def miniature_audit(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    grid = np.ones((7, 7), dtype='float32')
    grid[0, :] = np.nan
    write_tif(data_dir / 'reference_grid_mirror.tif', grid, nodata=np.nan)
    lattice = np.zeros_like(grid)
    lattice[2, 2] = 1
    dense = np.full_like(grid, 0.5)
    write_tif(data_dir / 'registry/13GEMSDOE.tif', lattice)
    write_tif(data_dir / 'registry/17GEMSDOE_dense_prior.tif', dense)
    candidate = np.zeros_like(grid)
    candidate[0, :] = np.nan  # valid outside, but strict-all-finite rejects it
    candidate[2, 2] = candidate[5, 5] = 1
    file = tmp_path / 'archived.tif'
    write_tif(file, candidate)
    entries = [{'id': n, 'url': f'https://example.test/{n}', 'bytes': 1,
                'git_blob': 'test', 'sha256': 'test',
                'support_type': 'continuous_probability' if 'dense' in n else 'binary_dots'}
               for n in audit.WITNESSES]
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'inputs': entries}))
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    monkeypatch.setattr(audit, 'SMALL', {'reference_grid_mirror.tif': ('blob', 1, 'reference-sha')})
    monkeypatch.setattr(audit, 'verified', lambda *args, **kwargs: True)
    monkeypatch.setattr(audit, 'ARTIFACTS', (('fixture', 'archived.tif', audit.sha256(file)),))
    return data_dir, manifest, file, candidate


def test_directional_euclidean_overlap_and_empty_support():
    kernel = audit.disk(3)
    assert kernel.sum() == 29 and kernel[3, 6] and not kernel[6, 6]
    support = np.zeros((5, 5), dtype=bool)
    support[1, 1] = support[4, 4] = True
    covered = np.zeros_like(support)
    covered[1, 1] = True
    assert audit.fraction_near(support, covered) == 0.5
    with pytest.raises(ValueError, match='nonempty'):
        audit.fraction_near(np.zeros_like(support), covered)
    with pytest.raises(ValueError, match='reference grid'):
        audit.fraction_near(support, np.zeros((1, 1), dtype=bool))


def test_readback_is_stop_only_and_distinguishes_outside_nan(miniature_audit):
    data_dir, manifest, _, _ = miniature_audit
    result = audit.run(data_dir, manifest)
    row = result['artifacts'][0]
    assert row['format']['path'] == 'archived.tif'  # portable receipt
    assert row['format']['format_valid_against_reference'] is True
    assert row['format']['nan_inside'] == 0 and row['format']['nan_outside'] == 7
    assert row['strict_all_finite_format'] is False
    assert row['final_overlap_3px']['13GEMSDOE'] == 0.5
    assert row['final_overlap_3px']['17GEMSDOE_dense_prior'] == 1.0
    assert row['literal_stop_witnesses'] == ['17GEMSDOE_dense_prior']
    assert row['ok_to_submit'] is False and not row['complete_registry_checked']
    assert not row['preplacement_surface_checked'] and not row['final_spearman_checked']
    assert not result['reference_authenticated_by_organizer']
    assert result['experiment_count'] == result['weekly_slots_used'] == 0


def test_same_shape_with_wrong_transform_is_not_compared(miniature_audit, monkeypatch):
    data_dir, manifest, file, candidate = miniature_audit
    write_tif(file, candidate, transform=from_origin(500100, 4500000, 100, 100))
    monkeypatch.setattr(audit, 'ARTIFACTS', (('fixture', 'archived.tif', audit.sha256(file)),))
    with pytest.raises(ValueError, match='grid/band mismatch'):
        audit.run(data_dir, manifest)


def test_missing_reference_fails_without_writing_receipt(tmp_path):
    output = tmp_path / 'should-not-exist.json'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/audit_existing_artifacts.py'),
                             '--data-dir', str(tmp_path), '--output', str(output)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and 'failed closed' in result.stderr
    assert not output.exists()


@pytest.mark.parametrize('name', [
    'make_candidate.py', 'generate_h3_pack.py', 'write_h3_submission.py',
    'run_wbg2_msptcd.py', 'final_audit.py', 'uniqueness_audit.py',
    'candidate_estimate.py', 'h3_analysis.py',
])
def test_rejected_historical_entry_points_stop(name):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / name)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode != 0 and 'STOP' in result.stdout + result.stderr
