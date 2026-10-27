#!/usr/bin/env python3
"""Reopen EXISTING rejected candidates; never place dots or approve a submission.

Uses the independent read-back validator, not a replacement shared writer/evaluator.
A witness failure is enough to reject; it is not a complete registry audit.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.validate import inspect_tif, sha256
from restore_public_mirrors import verified, SMALL


def main():
    manifest = json.loads((ROOT / 'config/registry_inputs.json').read_text())
    ref = ROOT / 'data/reference_grid_mirror.tif'
    blob, size, digest = SMALL[ref.name]
    if not verified(ref, size, sha256=digest, blob=blob):
        raise ValueError('Reference mirror hash mismatch')
    with rasterio.open(ref) as src:
        fp = np.isfinite(src.read(1)) & (src.read_masks(1) > 0)
        grid = (src.shape, src.crs, src.transform)
    coverage = {}
    witnesses = {}
    for ident in ('13GEMSDOE', '17GEMSDOE_dense_prior'):
        entry = next(e for e in manifest['inputs'] if e['id'] == ident)
        path = ROOT / 'data/registry' / f'{ident}.tif'
        if not verified(path, entry['bytes'], sha256=entry['sha256'], blob=entry['git_blob']):
            raise ValueError(f'Unverified witness: {ident}')
        with rasterio.open(path) as src:
            if (src.shape, src.crs, src.transform) != grid or src.count != 1:
                raise ValueError('Witness grid mismatch')
            arr = src.read(1)
        support = np.isfinite(arr) & (arr > 0) & fp
        coverage[ident] = distance_transform_edt(~support) <= 3
        witnesses[ident] = {'sha256': sha256(path), 'source': entry['url']}
    dz = json.loads((ROOT / 'data_public/candidate.json').read_text())
    h3 = json.loads((ROOT / 'evidence/h3_submission.json').read_text())
    inputs = [('DZ-16', dz['file'], dz['sha256']),
              ('H3-PACK', h3['mirrors'][0], h3['tif_sha256'])]
    rows = []
    for ident, rel, digest in inputs:
        path = ROOT / rel
        if sha256(path) != digest:
            raise ValueError(f'Candidate hash mismatch: {ident}')
        validation = inspect_tif(path, ref)
        if not validation['grid_match_reference'] or validation['bands'] != 1:
            raise ValueError(f'Candidate grid/band mismatch: {ident}')
        validation['path'] = rel
        with rasterio.open(path) as src:
            arr = src.read(1)
        dots = np.isfinite(arr) & (arr > 0) & fp
        if not dots.any():
            raise ValueError('No dots to compare')
        overlap = {k: float(v[dots].mean()) for k, v in coverage.items()}
        rows.append({'id': ident, 'file': rel, 'sha256': digest,
                     'dots': int(dots.sum()), 'validator': validation,
                     'final_dot_overlap_3px': overlap,
                     'preplacement_surface_rank_correlation': None,
                     'preplacement_status': 'NOT REPRODUCED; original surfaces unavailable',
                     'all_registry_rasters_checked': False,
                     'literal_duplicate_stop': any(v > .70 for v in overlap.values()),
                     'compliant_holdout_win': False, 'leaderboard_estimate': None,
                     'ok_to_submit': False, 'verdict': 'negative'})
    report = {'schema': 'wbg.release-recheck.v1',
              'generated_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Existing-file forensic review only; no experiment, new placement or upload.',
              'evidence_class': 'REGISTRY-MEASUREMENT + LOCAL-FORMAT-MEASUREMENT',
              'reference_sha256': sha256(ref), 'reference_authenticated': False,
              'continuous_prior_caveat': 'Finite-positive support is the shared literal rule; no exemption is assumed.',
              'witnesses': witnesses, 'candidates': rows,
              'experiments_run': 0, 'slots_used': 0, 'ok_to_submit': False}
    out = ROOT / 'evidence/release_recheck_20261027.json'
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({r['id']: r['final_dot_overlap_3px'] for r in rows}, indent=2))


if __name__ == '__main__':
    main()
