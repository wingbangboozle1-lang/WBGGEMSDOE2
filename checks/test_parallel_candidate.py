"""Guardrails around the already-produced parallel TIFF; no model experiment."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'docs/data/parallel_candidate_audit.json'


def test_independent_audit_is_byte_bound_and_fails_binary_witness():
    r=json.loads(RECEIPT.read_text());file=ROOT/r['candidate_path']
    assert hashlib.sha256(file.read_bytes()).hexdigest()==r['candidate_sha256']
    lat=r['witnesses']['lattice'];dense=r['witnesses']['dense_probability']
    assert lat['candidate_dot_count']==34564 and lat['candidate_dots_within_3px']==34351
    assert lat['overlap_fraction']==pytest.approx(34351/34564) and not lat['passes_70_percent_limit']
    assert dense['overlap_fraction']==1 and not dense['passes_70_percent_limit']
    assert r['format']['dataset_mask_invalid_inside_footprint']==5132809
    assert not r['ok_to_submit'] and not r['preplacement_surface_checked']


def test_nodata_zero_masks_interior_zeros_even_when_raw_bytes_are_finite(tmp_path):
    path=tmp_path/'zeros.tif';a=np.array([[0,1],[0,0]],dtype=np.float32)
    with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',nodata=0,transform=from_origin(0,2,1,1)) as ds:ds.write(a,1)
    with rasterio.open(path) as ds:
        assert np.isfinite(ds.read(1)).all()
        assert int((ds.dataset_mask()==0).sum())==3


def test_old_generator_cannot_make_new_file():
    result=subprocess.run([sys.executable,str(ROOT/'scripts/generate_final.py')],capture_output=True,text=True)
    assert result.returncode!=0 and 'STOP' in result.stderr


def test_old_lane_and_writer_are_stopped():
    import run_lane, submission_writer
    with pytest.raises(RuntimeError,match='STOP'):run_lane.main()
    with pytest.raises(RuntimeError,match='STOP'):submission_writer.write_submission(None,None,None)


def test_old_executive_report_points_to_current_audit():
    html=(ROOT/'docs/executive-summary/index.html').read_text()
    assert 'do not submit' in html.lower() and 'parallel_candidate_audit.json' in html
    assert '⬇ DOWNLOAD: YES' not in html


def test_primary_format_gate_rejects_interior_nodata_mask(tmp_path, monkeypatch):
    import prepare_data, validate_submission
    try:
        prepare_data.restore_template(False)
    except FileNotFoundError:
        pytest.skip('pinned shared template not restored')
    sample=tmp_path/'sample.tif';candidate=tmp_path/'candidate.tif';tr=from_origin(500000,4500000,100,100)
    for path,array,nodata in [(sample,np.ones((2,2),np.float32),None),(candidate,np.array([[0,1],[0,0]],np.float32),0)]:
        with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:32611',transform=tr,nodata=nodata) as ds:ds.write(array,1)
    monkeypatch.setattr(validate_submission,'SAMPLE_SHA',prepare_data.digest(sample))
    result=validate_submission.run(candidate,sample)
    assert result['shared_format_ok'] and result['no_nan_inside_footprint']
    assert result['dataset_mask_invalid_inside_footprint']==3
    assert not result['ok'] and not result['ok_to_submit']
