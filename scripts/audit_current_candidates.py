#!/usr/bin/env python3
"""Read external research TIFF bytes and check the two literal registry witnesses.

This is not a model experiment, a complete registry audit or a portal submission.
No rasters are generated. Inputs and source refs are immutable and hash-checked.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage
import rasterio

from audit_portfolio import disk, sha256 as digest, _grid, _same_grid
from fetch_inputs import fetch

ROOT = Path(__file__).resolve().parents[1]


def obtain(row: dict) -> Path:
    """Restore the named file at its pinned commit, rejecting unexpected bytes."""
    destination = ROOT / '.cache' / 'current' / f"{row['site']}.tif"
    if destination.exists() and digest(destination) == row['sha256']:
        return destination
    fetch(f"buffedlizard55-lab/{row['site']}", row['ref'], row['path'],
          destination, row['sha256'])
    return destination


def overlaps(support: np.ndarray, lattice_neighborhood: np.ndarray,
             dense_neighborhood: np.ndarray) -> dict:
    total = int(support.sum())
    def measure(witness):
        hits = int((support & witness).sum())
        return {'within_3_pixels': hits, 'fraction': hits / total if total else None}
    return {'positive_pixels_in_footprint': total,
            'lattice': measure(lattice_neighborhood),
            'dense_probability': measure(dense_neighborhood)}


def main() -> None:
    manifest = json.loads((ROOT / 'data/current_candidates.json').read_text())
    # Recheck witness and footprint provenance, not just candidate files.
    required = {
        'sample_submission.tif': '2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc',
        '13gems_20261001_r13-lattice-s5_v2_nan-outside.tif': 'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2',
        '17gems-e-proba.tif': 'ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be',
    }
    for name, expected in required.items():
        if digest(ROOT / '.cache/data' / name) != expected:
            raise ValueError(f'Hash mismatch for core input: {name}')
    with rasterio.open(ROOT / '.cache/data/sample_submission.tif') as sample_ds:
        footprint = np.isfinite(sample_ds.read(1))
        grid = _grid(sample_ds)
        with rasterio.open(ROOT / '.cache/data/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif') as lattice_ds:
            if lattice_ds.count != 1 or not _same_grid(sample_ds, lattice_ds):
                raise ValueError('Lattice grid differs from mirrored sample')
            lattice = lattice_ds.read(1)
        with rasterio.open(ROOT / '.cache/data/17gems-e-proba.tif') as dense_ds:
            if dense_ds.count != 1 or not _same_grid(sample_ds, dense_ds):
                raise ValueError('Dense witness grid differs from mirrored sample')
            dense = dense_ds.read(1)
    lattice_near = ndimage.binary_dilation(footprint & np.isfinite(lattice) & (lattice > 0), structure=disk(3))
    dense_positive = footprint & np.isfinite(dense) & (dense > 0)
    # The dense raster is positive at the candidate pixels themselves; zero
    # distance is already within three pixels, so no large dilation is needed.
    if int(dense_positive.sum()) != int(footprint.sum()):
        raise ValueError('Dense witness is not positive throughout the mirrored footprint')
    results = []
    for row in manifest['candidates']:
        path = obtain(row)
        with rasterio.open(path) as raster:
            arr = raster.read(1)
            checks = {
                'one_float32_band': raster.count == 1 and raster.dtypes == ('float32',),
                'same_crs_shape_transform_as_mirror': (raster.crs.to_string() == grid['crs']
                    and list(raster.shape) == grid['shape'] and list(raster.transform)[:6] == grid['transform']),
                'no_nonfinite_inside_mirror_footprint': bool(np.isfinite(arr[footprint]).all()),
                'all_cells_finite': bool(np.isfinite(arr).all()),
                'all_cells_in_0_1': bool(np.isfinite(arr).all() and np.all((arr >= 0) & (arr <= 1))),
                'all_zero_outside_mirror_footprint': bool(np.all(arr[~footprint] == 0)),
            }
        support = footprint & np.isfinite(arr) & (arr > 0)
        overlap = overlaps(support, lattice_near, dense_positive)
        fail_witnesses = [name for name in ('lattice', 'dense_probability')
                          if overlap[name]['fraction'] is not None and overlap[name]['fraction'] > .70]
        results.append({
            **row,
            'reference_download': f"https://github.com/buffedlizard55-lab/{row['site']}/blob/{row['ref']}/{row['path']}?raw=1",
            'byte_sha256_verified': digest(path),
            'local_format_checks': checks,
            'overlap': overlap,
            'literal_duplicate_witnesses': fail_witnesses,
            'surface_rank_correlation': None,
            'full_registry_pass': False,
            'ok_to_submit': False,
            'verdict': 'DO NOT SUBMIT',
        })
    out = {
        'input_manifest': 'data/current_candidates.json',
        'observed_date_utc': manifest['observed_date_utc'],
        'scope': ('Local read-back against a hash-pinned mirrored sample and two registry witnesses only. '
                  'No official portal acceptance, complete registry clearance, pre-placement surface correlation, '
                  'organizer score or independent scientific holdout is established.'),
        'distance': 'Euclidean center-to-center distance <= 3 pixels',
        'overlap_denominator': 'positive candidate pixels within mirrored footprint',
        'footprint_pixels': int(footprint.sum()),
        'results': results,
    }
    target = ROOT / 'evidence/current_candidates_audit.json'
    target.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'output': str(target.relative_to(ROOT)),
                      'results': [{'site': r['site'], 'pixels': r['overlap']['positive_pixels_in_footprint'],
                                   'lattice': r['overlap']['lattice']['fraction'],
                                   'dense': r['overlap']['dense_probability']['fraction'],
                                   'verdict': r['verdict']} for r in results]}, indent=2))


if __name__ == '__main__':
    main()
