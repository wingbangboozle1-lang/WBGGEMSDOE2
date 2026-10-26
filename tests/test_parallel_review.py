import hashlib
import json
from pathlib import Path
import subprocess
import sys

import rasterio
import pytest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / 'evidence/parallel_review.json').read_text())


def test_rejected_artifact_bytes_and_independent_result_are_bound():
    path = ROOT / REVIEW['artifact']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == REVIEW['sha256']
    with rasterio.open(path) as ds:
        assert ds.count == 1 and ds.dtypes[0] == 'float32' and ds.nodata == 0
    assert REVIEW == json.loads((ROOT / 'docs/data/parallel_review.json').read_text())
    assert REVIEW == json.loads((ROOT / 'site/data/parallel_review.json').read_text())
    assert REVIEW['ok_to_submit'] is False
    assert REVIEW['format']['format_valid_against_reference'] is False
    assert REVIEW['format']['masked_inside'] == 5_132_809
    assert REVIEW['positive_inside_footprint'] == 34_564
    assert REVIEW['literal_overlap_3px']['lattice'] > .99
    assert REVIEW['literal_overlap_3px']['continuous_prior'] == 1
    assert REVIEW['preplacement_surface_correlation'] is None
    source = REVIEW['source_reported_holdout']
    assert 'NOT REPRODUCED' in source['evidence_class']
    assert source['withheld_positive_pixels'] == 58_016 and len(source['reported_95ci']) == 2


def test_retired_partial_lane_cannot_execute():
    for script in ('run_lane.py', 'generate_final.py', 'audit_uniqueness.py'):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)],
                              capture_output=True, text=True, timeout=5)
        assert proc.returncode != 0 and 'STOP' in (proc.stdout + proc.stderr)
    brief = (ROOT / 'docs/executive-summary/index.html').read_text()
    assert 'DO NOT SUBMIT' in brief and '99.3838%' in brief
    assert 'Unique: ≤70% of dots' not in brief


def test_retired_private_writer_refuses_to_write():
    from submission_writer import write_submission
    with pytest.raises(RuntimeError, match='retired private writer'):
        write_submission(None, None, None)
