#!/usr/bin/env python3
"""Forensically recheck the committed conduit TIFF and ZIP; not an experiment.

This reads existing saved bytes, a hash-pinned mirror grid and two registered
witnesses. It does not replay a pre-placement surface or authorize a slot.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from wbggems.novelty import coverage
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import verified, SMALL

NAME = 'wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros'
CANDIDATE = ROOT / 'downloads' / (NAME + '.tif')
CANDIDATE_SHA = '95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad'


def run():
    ref = ROOT / 'data/reference_grid_mirror.tif'
    blob, size, digest = SMALL['reference_grid_mirror.tif']
    if not verified(ref, size, blob=blob, sha256=digest):
        raise ValueError('Hash-pinned owner-mirrored grid is unavailable')
    if not CANDIDATE.is_file() or sha256(CANDIDATE) != CANDIDATE_SHA:
        raise ValueError('Conduit TIFF does not match its recorded bytes')
    zip_path = CANDIDATE.with_suffix('.zip')
    with zipfile.ZipFile(zip_path) as archive:
        if archive.namelist() != [CANDIDATE.name]:
            raise ValueError('ZIP must contain only the expected TIFF')
        digest = hashlib.sha256()
        with archive.open(CANDIDATE.name) as member:
            while chunk := member.read(1 << 20):
                digest.update(chunk)
        if digest.hexdigest() != CANDIDATE_SHA:
            raise ValueError('ZIP member is not the audited TIFF')
    with rasterio.open(ref) as ds:
        fp = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    with rasterio.open(CANDIDATE) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError('Candidate grid does not match reference')
        values = ds.read(1)
        positive = fp & np.isfinite(values) & (values > 0)
        threshold = fp & np.isfinite(values) & (values >= .5)
        outside_positive = int((~fp & np.isfinite(values) & (values > 0)).sum())
    if not positive.any() or not threshold.any():
        raise ValueError('Candidate support is empty')
    inputs = {x['id']: x for x in json.loads((ROOT / 'config/registry_inputs.json').read_text())['inputs']}
    witnesses = {}
    for ident in ('13GEMSDOE', '17GEMSDOE_dense_prior'):
        row = inputs[ident]
        path = ROOT / 'data/registry' / (ident + '.tif')
        if not verified(path, row['bytes'], blob=row['git_blob'], sha256=row['sha256']):
            raise ValueError(f'Pinned registry witness unavailable: {ident}')
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid:
                raise ValueError(f'Witness grid mismatch: {ident}')
            vals = ds.read(1)
        within = coverage(np.isfinite(vals) & (vals > 0) & fp, 3)
        stats = {}
        for label, selected in (('finite_positive', positive), ('source_threshold_ge_0_5', threshold)):
            count = int(selected.sum())
            hits = int((selected & within).sum())
            stats[label] = {'within_3px': hits, 'selected_cells': count, 'fraction': hits / count}
        witnesses[ident] = stats
    report = inspect_tif(CANDIDATE, ref, strict_all_finite=True)
    original = json.loads((ROOT / 'evidence/conduit_archive/original_run_card.json').read_text())
    source_audit = json.loads((ROOT / 'evidence/conduit_archive/original_uniqueness_audit.json').read_text())
    return {
        'evidence_class': 'INDEPENDENT-FORENSIC-RECHECK',
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'artifact': str(CANDIDATE.relative_to(ROOT)), 'sha256': CANDIDATE_SHA,
        'zip_sha256': sha256(zip_path), 'zip_contains_exact_audited_tiff': True,
        'status': 'REJECTED — RESEARCH ONLY; DO NOT SUBMIT', 'ok_to_submit': False,
        'positive_inside_footprint': int(positive.sum()),
        'positive_outside_footprint': outside_positive,
        'format': {k: report[k] for k in ('grid_match_reference', 'bands', 'dtype', 'nodata',
                   'footprint_cells', 'nonfinite_inside', 'masked_inside', 'all_finite',
                   'minimum_inside', 'maximum_inside', 'failures', 'format_valid_against_reference')},
        'reference_provenance': 'Hash-pinned owner mirror, not an authenticated organizer file',
        'witnesses': witnesses,
        'limit': .70,
        'dense_support_definition': 'Finite positive in the shared literal gate; whether a continuous field counts as dots needs policy clarification. The binary lattice fails independently at the source threshold.',
        'preplacement_surface_correlation': None,
        'preplacement_status': 'not independently replayed; original scan omitted at least both registered witnesses',
        'source_reported_uniqueness': {'tested': source_audit['registry_rasters_tested'],
            'max_overlap_3px': source_audit['max_dot_overlap_3px'],
            'claim': 'PASS is superseded: binary lattice is a counterexample'},
        'holdout_dti': None, 'organizer_receipt': None,
        'source_reported_experiments': 1,
        'source_code_review': [
            'Generator uses synthetic geometric trend fields and seeded smooth noise, not the listed geophysical feature arrays.',
            'Its calculated decay variable is unused in final output, so the claimed 300 m decay is not established.',
            'The private evaluator does not apply the buffer argument, mask visible faults pixel-exactly, or compute the required pooled metric.',
        ],
        'source_run_card_verdict': original['verdict'],
        'conclusion': 'Fails the literal any-registry binary-lattice gate and has no holdout; format-only pass is not upload authorization.'
    }


if __name__ == '__main__':
    try:
        result = run()
        path = ROOT / 'evidence/conduit_review.json'
        path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f'Forensic review stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
