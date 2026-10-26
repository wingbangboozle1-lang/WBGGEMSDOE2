#!/usr/bin/env python3
"""Independently recheck the already-committed parallel TIFF; never promote it.

This is a forensic audit of existing bytes, not a new experiment, a surface
replay, or an exhaustive registry scan. Source-reported holdouts remain
unreproduced and are not used as submission scores.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from wbggems.novelty import coverage, overlap_fraction
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import verified, SMALL

CANDIDATE = ROOT / 'docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif'
CANDIDATE_SHA = '592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33'


def run():
    ref = ROOT / 'data/reference_grid_mirror.tif'
    blob, size, digest = SMALL['reference_grid_mirror.tif']
    if not verified(ref, size, blob=blob, sha256=digest):
        raise ValueError('Hash-pinned owner-mirrored grid is unavailable')
    if not CANDIDATE.is_file() or sha256(CANDIDATE) != CANDIDATE_SHA:
        raise ValueError('Parallel candidate does not match its recorded bytes')
    inputs = {x['id']: x for x in json.loads((ROOT / 'config/registry_inputs.json').read_text())['inputs']}
    with rasterio.open(ref) as ds:
        fp = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    arrays = {}
    for ident in ('13GEMSDOE', '17GEMSDOE_dense_prior'):
        row = inputs[ident]
        path = ROOT / 'data/registry' / (ident + '.tif')
        if not verified(path, row['bytes'], blob=row['git_blob'], sha256=row['sha256']):
            raise ValueError(f'Pinned registry witness unavailable: {ident}')
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid:
                raise ValueError(f'Witness grid mismatch: {ident}')
            arrays[ident] = ds.read(1)
    with rasterio.open(CANDIDATE) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError('Candidate grid does not match the reference')
        vals = ds.read(1)
        dots = np.isfinite(vals) & (vals > 0) & fp
        outside_positive = int((np.isfinite(vals) & (vals > 0) & ~fp).sum())
    if not dots.any():
        raise ValueError('Candidate support is empty')
    overlaps = {}
    for ident, vals in arrays.items():
        support = np.isfinite(vals) & (vals > 0) & fp
        overlaps[ident] = overlap_fraction(dots, coverage(support, 3))
    report = inspect_tif(CANDIDATE, ref, strict_all_finite=True)
    original = json.loads((ROOT / 'evidence/parallel_archive/original_run_card.json').read_text())
    stated = original['holdout']['experiments']['E2_lane_no_catalogue_distance']
    return {
        'evidence_class': 'INDEPENDENT-FORENSIC-RECHECK',
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'artifact': str(CANDIDATE.relative_to(ROOT)), 'sha256': CANDIDATE_SHA,
        'status': 'REJECTED — RESEARCH ONLY; DO NOT SUBMIT',
        'ok_to_submit': False, 'is_this_review_lane_candidate': False,
        'positive_inside_footprint': int(dots.sum()), 'positive_outside_footprint': outside_positive,
        'format': {k: report[k] for k in ('grid_match_reference', 'bands', 'dtype', 'nodata',
                   'footprint_cells', 'nonfinite_inside', 'masked_inside', 'all_finite',
                   'minimum_inside', 'maximum_inside', 'failures', 'format_valid_against_reference')},
        'reference_provenance': 'Hash-pinned owner mirror, not an authenticated organizer file',
        'literal_overlap_3px': {'lattice': overlaps['13GEMSDOE'], 'continuous_prior': overlaps['17GEMSDOE_dense_prior'],
            'limit': 0.70, 'dense_support_definition': 'finite value > 0 in shared literal gate; whether a continuous field should count as dots needs policy clarification'},
        'preplacement_surface_correlation': None,
        'preplacement_status': 'not replayed; source audit compared only nine final dot-density surfaces',
        'source_reported_holdout': {
            'evidence_class': 'HOLDOUT-DTI (SOURCE-REPORTED, NOT REPRODUCED)',
            'evaluator_version': 'WBGGEMSDOE2-HIDE-RECOVER-v2.0 (private parallel implementation, not the required shared evaluator)',
            'withheld_positive_pixels': original['holdout']['n_withheld_positives_pooled'],
            'dti': stated['dti'], 'reported_95ci': stated['fold_bootstrap_95ci'],
            'limitations': 'Evaluation cells were not excluded from the training zone; the four-fold interval is not reproduced by the committed lane script; canaries reported only for fold 0; no valid matched shared-evaluator incumbent or complete-registry preflight.'},
        'source_reported_experiments': 3, 'organizer_receipt': None,
        'conclusion': 'Fails the literal any-registry gate on the binary lattice alone; its zero NoData tag also masks most footprint cells. No submission, estimated live score, or promotion is authorized.'
    }


if __name__ == '__main__':
    try:
        result = run()
        path = ROOT / 'evidence/parallel_review.json'
        path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError) as exc:
        print(f'Forensic review stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
