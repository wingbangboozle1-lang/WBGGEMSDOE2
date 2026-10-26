#!/usr/bin/env python3
"""Independently audit the already-produced parallel-run TIFF; never generate or promote one."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from audit_portfolio import disk, load_pinned, same_grid
from prepare_data import ROOT, digest
from validate_submission import run as format_report

CANDIDATE = ROOT / 'docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif'
CANDIDATE_SHA = '592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33'
SAMPLE = ROOT / 'data/official/sample_submission.tif'


def audit(fetch=False):
    pins=json.loads((ROOT/'registry/witnesses.json').read_text())
    if not CANDIDATE.is_file() or digest(CANDIDATE) != CANDIDATE_SHA:
        raise ValueError('Parallel candidate is missing or byte hash changed; do not reuse this audit')
    lattice=load_pinned(pins['lattice'],fetch)
    dense=load_pinned(pins['dense_probability'],fetch)
    report=format_report(CANDIDATE,SAMPLE)  # verifies sample and shared-template pins
    with rasterio.open(SAMPLE) as ref, rasterio.open(CANDIDATE) as src:
        if not same_grid(src,ref): raise ValueError('candidate grid differs from reference')
        fp=np.isfinite(ref.read(1)); a=src.read(1)
        support=np.isfinite(a)&(a>0)&fp
        count=int(support.sum())
        if not count: raise ValueError('candidate has empty in-footprint positive support')
        masked_inside=int((fp & (src.dataset_mask()==0)).sum())
        nodata=src.nodata
        details={}
        for key,path in [('lattice',lattice),('dense_probability',dense)]:
            with rasterio.open(path) as prior:
                if not same_grid(prior,ref): raise ValueError(f'{key} grid differs from reference')
                z=prior.read(1); prior_support=np.isfinite(z)&(z>0)&fp
            near=binary_dilation(prior_support,structure=disk(3))
            n=int((near & support).sum())
            details[key]={'sha256':pins[key]['sha256'],'source':pins[key]['source'],
                          'candidate_dots_within_3px':n,'candidate_dot_count':count,
                          'overlap_fraction':n/count,'passes_70_percent_limit':n/count<=.70}
    return {
        'evidence_class':'INDEPENDENT-POST-MERGE-RASTER-AUDIT',
        'audited_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'candidate_path':str(CANDIDATE.relative_to(ROOT)), 'candidate_sha256':CANDIDATE_SHA,
        'candidate_origin':'Parallel PR #10; file retained for research only',
        'positive_pixels_inside_footprint':count, 'witnesses':details,
        'surface_rank_correlation':None,'preplacement_surface_checked':False,
        'all_registry_rasters_checked':False,
        'result':'DUPLICATE / STOP: more than 70% of candidate dots are near the binary lattice',
        'continuous_prior_caveat':'The continuous prior gives 100% under the unchanged finite-positive support definition; whether continuous probabilities count as dots is unresolved. The binary-lattice failure is independent of that ambiguity.',
        'format':{'shared_local_format_report_ok':bool(report['shared_format_ok']), 'supplemental_project_mask_check_ok':report['project_mask_check']=='pass', 'no_nan_inside_footprint':report['no_nan_inside_footprint'],
                  'inside_values_in_0_1':report['inside_values_in_0_1'], 'crs_shape_transform_match':True,
                  'nodata_tag':nodata, 'dataset_mask_invalid_inside_footprint':masked_inside,
                  'mask_caveat':'The raw values are finite, but nodata=0 marks interior zero-valued pixels invalid in the dataset mask. The shared local format report does not reject this mask; organizer handling is unknown.'},
        'holdout_caveat':'Parallel run used a non-shared evaluator; run_lane.py samples training negatives using the full catalogue including withheld labels, and canaries report only fold 0. No independent protocol-valid holdout has been established.',
        'ok_to_submit':False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch',action='store_true',help='restore pinned witnesses from owner mirrors if needed')
    parser.add_argument('--output',type=Path,default=ROOT/'evidence/parallel_candidate_audit.json')
    args=parser.parse_args(); result=audit(args.fetch)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
