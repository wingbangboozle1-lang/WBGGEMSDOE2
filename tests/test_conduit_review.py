import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / 'evidence/conduit_review.json').read_text())


def test_conduit_artifact_and_zip_are_bound_to_stopped_receipt():
    path = ROOT / REVIEW['artifact']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == REVIEW['sha256']
    zip_path = path.with_suffix('.zip')
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == REVIEW['zip_sha256']
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.namelist() == [path.name]
        with archive.open(path.name) as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == REVIEW['sha256']
    with rasterio.open(path) as ds:
        assert ds.count == 1 and ds.dtypes[0] == 'float32' and ds.nodata is None
    assert REVIEW == json.loads((ROOT / 'docs/data/conduit_review.json').read_text())
    assert REVIEW == json.loads((ROOT / 'site/data/conduit_review.json').read_text())
    assert REVIEW['ok_to_submit'] is False and REVIEW['holdout_dti'] is None
    assert REVIEW['format']['format_valid_against_reference'] is True
    assert REVIEW['format']['masked_inside'] == 0
    lattice = REVIEW['witnesses']['13GEMSDOE']['source_threshold_ge_0_5']
    assert lattice['within_3px'] == 5_087_882 and lattice['selected_cells'] == 5_094_374
    assert lattice['fraction'] > .99
    assert REVIEW['witnesses']['17GEMSDOE_dense_prior']['source_threshold_ge_0_5']['fraction'] == 1
    assert REVIEW['preplacement_surface_correlation'] is None


def test_source_claim_is_superseded_and_unsafe_entry_points_disabled():
    name = Path(REVIEW['artifact']).stem
    audit = json.loads((ROOT / 'reports' / (name + '_audit.json')).read_text())
    card = json.loads((ROOT / 'reports' / (name + '_run_card.json')).read_text())
    assert audit['lane_unique_vs_all'] is False and card['lane_unique_vs_registry'] is False
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    for script in ('make_submission.py', 'evaluate_holdout.py', 'submission_writer.py'):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts' / script), '--selftest'],
                              capture_output=True, text=True, timeout=5)
        assert proc.returncode != 0 and 'STOP' in (proc.stdout + proc.stderr)
    alias = (ROOT / 'docs/executive-summary/index.html').read_text()
    brief = (ROOT / 'docs/executive-summary.html').read_text()
    assert 'DO NOT SUBMIT' in alias and 'url=../executive-summary.html' in alias
    assert '99.8726%' in brief and 'DO NOT SUBMIT' in brief


def test_private_evaluator_cannot_be_called():
    from evaluate_holdout import evaluate_holdout
    with pytest.raises(RuntimeError, match='private evaluator retired'):
        evaluate_holdout(None, None, None, None)
