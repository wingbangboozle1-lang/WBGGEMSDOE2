#!/usr/bin/env python3
"""Audit nine immutable historical rasters and the literal lattice STOP witness.

Not a model, scorer, holdout evaluator, or submission generator.  It never writes
GeoTIFFs.  An overlap is directional: fraction of the candidate's positive cells
within a Euclidean 3-pixel radius of positive cells of the comparison raster.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
RADIUS_PX = 3
DOT_BUDGET = 37654


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def disk(radius: int) -> np.ndarray:
    if radius < 0:
        raise ValueError('radius must be nonnegative')
    coords = np.arange(-radius, radius + 1)
    return coords[:, None] ** 2 + coords[None, :] ** 2 <= radius ** 2


def dot_overlap(candidate: np.ndarray, covered: np.ndarray) -> float:
    c, d = np.asarray(candidate, bool), np.asarray(covered, bool)
    if c.shape != d.shape or c.ndim != 2:
        raise ValueError('candidate and coverage grid must match')
    count = int(c.sum())
    if count == 0:
        raise ValueError('empty predictions have no defined overlap')
    return float(np.count_nonzero(c & d) / count)


def minimum_overlap(dot_budget: int, uncovered_pixels: int) -> float:
    """Tight pigeonhole lower bound for distinct dots inside the footprint."""
    if dot_budget <= 0 or uncovered_pixels < 0:
        raise ValueError('invalid dot budget or uncovered area')
    return max(0, dot_budget - uncovered_pixels) / dot_budget


def _grid(ds):
    return {'shape': list(ds.shape), 'crs': str(ds.crs), 'transform': list(ds.transform)[:6]}


def _same_grid(a, b):
    return a.shape == b.shape and a.crs == b.crs and a.transform == b.transform


def audit() -> dict:
    config = json.loads((ROOT / 'data/focus_sources.json').read_text())
    sample_path = ROOT / '.cache/data/sample_submission.tif'
    label_path = ROOT / '.cache/data/labels.tif'
    lattice_path = ROOT / '.cache/data/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif'
    dense_path = ROOT / '.cache/data/17gems-e-proba.tif'
    required = {sample_path:'2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc',
                label_path:'7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093',
                lattice_path:'b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2',
                dense_path:'ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be'}
    for p, expected in required.items():
        if not p.is_file() or sha256(p) != expected:
            raise ValueError(f'missing or changed pinned input {p}; run scripts/fetch_inputs.py')
    with rasterio.open(sample_path) as template:
        sample = template.read(1)
        foot = np.isfinite(sample)
        grid_info = _grid(template)
        with rasterio.open(label_path) as labels_ds:
            if not _same_grid(template, labels_ds):
                raise ValueError('label grid mismatch')
            lab = labels_ds.read(1)
        with rasterio.open(lattice_path) as lattice_ds:
            if lattice_ds.count != 1 or not _same_grid(template, lattice_ds):
                raise ValueError('lattice grid mismatch')
            lattice_values = lattice_ds.read(1)
        with rasterio.open(dense_path) as dense_ds:
            if dense_ds.count != 1 or not _same_grid(template, dense_ds):
                raise ValueError('dense registry grid mismatch')
            dense_values = dense_ds.read(1)
        masks: dict[str, np.ndarray] = {}
        rows = []
        for s in config['sites']:
            p = ROOT / '.cache/portfolio' / f"{s['site']}.tif"
            if not p.is_file():
                raise FileNotFoundError(f'missing {p}; run scripts/fetch_inputs.py')
            # A cache is not trusted merely because a file exists.
            from fetch_inputs import blob_digest
            if blob_digest(p) != s['blob_sha']:
                raise ValueError(f"pinned blob mismatch for {s['site']}")
            with rasterio.open(p) as ds:
                if ds.count != 1 or not _same_grid(template, ds):
                    raise ValueError(f"grid mismatch for {s['site']}")
                a = ds.read(1)
                values = a[foot]
                if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
                    raise ValueError(f"invalid in-footprint values for {s['site']}")
                m = (a > 0) & np.isfinite(a) & foot
                if not m.any():
                    raise ValueError(f"empty raster {s['site']}")
                masks[s['site']] = m
                rows.append({**s, 'sha256': sha256(p), 'bytes': p.stat().st_size,
                    'link': f"https://github.com/{config['owner']}/{s['site']}/blob/{s['ref']}/{s['path']}?raw=1",
                    'dots': int(m.sum()), 'dtype': ds.dtypes[0],
                    'full_grid_nonfinite': int((~np.isfinite(a)).sum()),
                    'in_footprint_finite': bool(np.isfinite(values).all()),
                    'in_footprint_min': float(values.min()), 'in_footprint_max': float(values.max()),
                    'predictions_binary': bool(np.all((values == 0) | (values == 1))),
                    'claimed_score_evidence': 'USER-REPORTED / UNVERIFIED; no organizer receipt',
                    'leaderboard_estimate': None,
                    'original_preplacement_surface_available': False,
                    'usage': 'reference only; not approved for a competition submission'})
    structure = disk(RADIUS_PX)
    coverages = {name: binary_dilation(mask, structure=structure) for name, mask in masks.items()}
    for row in rows:
        overlaps = {peer: dot_overlap(masks[row['site']], cov) for peer, cov in coverages.items()
                    if peer != row['site']}
        peer = max(overlaps, key=overlaps.get)
        row.update(overlap_vs_focus_sites=overlaps, max_overlap_peer=peer,
                   max_overlap=overlaps[peer],
                   distinct_from_other_eight_by_3px=bool(overlaps[peer] <= 0.70))
    lattice = np.isfinite(lattice_values) & (lattice_values > 0)
    if np.any(lattice & ~foot):
        raise ValueError('lattice support extends beyond template footprint')
    lattice_cover = binary_dilation(lattice, structure=structure)
    uncovered = int(np.count_nonzero(foot & ~lattice_cover))
    nfoot = int(foot.sum())
    lower = minimum_overlap(DOT_BUDGET, uncovered)
    if lower <= .70:
        raise ValueError('lattice does not prove the preregistered budget fails; do not reuse this STOP')
    dense_positive = np.isfinite(dense_values) & (dense_values > 0) & foot
    dense_covered = binary_dilation(dense_positive, structure=structure)
    dense_uncovered = int(np.count_nonzero(foot & ~dense_covered))
    if dense_uncovered != 0:
        raise ValueError('dense raster is not a universal witness; do not reuse the universal STOP')
    labels = np.isfinite(lab) & (lab > 0) & foot
    dist = distance_transform_edt(~labels)
    d28, h33 = masks['GEMSDOE25'], masks['GEMSDOE32']
    b2_reconstruction = d28 & (dist > 2)
    h33_xor = int(np.count_nonzero(b2_reconstruction ^ h33))
    return {
        'schema_version': 1,
        'audited_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Nine pinned historical rasters, their pairwise supports, and two registered stop witnesses. Not an exhaustive registry inventory.',
        'grid_reference': {**grid_info, 'sample_sha256': required[sample_path],
                           'labels_sha256': required[label_path], 'footprint_pixels': nfoot,
                           'positive_sample_pixels': int(np.count_nonzero(foot & (sample > 0))),
                           'positive_catalogue_pixels': int(labels.sum()),
                           'sample_positive_mismatch_catalogue': int(np.count_nonzero(((sample > 0) & foot) ^ labels)),
                           'provenance': 'owner mirror only; not authenticated organizer bytes'},
        'dense_surface_witness': {
            'repo':'17GEMSDOE', 'ref':'6fc71d19d49dca4960d5434bd81b6dd06fcc030a',
            'path':'docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif',
            'sha256':required[dense_path], 'registered':True,
            'registration_evidence':'https://github.com/buffedlizard55-lab/57GEMSDOE/blob/822a0ce5546c7b6749cdd82eb145b6b3e616603d/evidence/registry_refreshed.json',
            'finite_positive_footprint_pixels':int(dense_positive.sum()),
            'footprint_pixels':nfoot, 'uncovered_footprint_pixels_within_3px':dense_uncovered,
            'min_inside':float(dense_values[foot].min()), 'max_inside':float(dense_values[foot].max()),
            'universal_overlap_lower_bound':1.0,
            'verdict':'DUPLICATE_BY_BOUND FOR EVERY NONEMPTY IN-FOOTPRINT DOT SET',
            'interpretation':'Shared literal registry gate treats every finite positive cell as support; this is a dense soft-probability raster, so overlap does not demonstrate scientific copying. Excluding it would change the requested rule.'},
        'lattice_witness': {
            'repo':'GEMSDOE24', 'ref':'07345ea0604953d7efb858d9cfbc21e20c7aca0b',
            'path':'inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif',
            'sha256':required[lattice_path], 'radius_px':RADIUS_PX,
            'lattice_positive_pixels':int(lattice.sum()),
            'covered_footprint_pixels':nfoot-uncovered, 'uncovered_footprint_pixels':uncovered,
            'fraction_covered':(nfoot-uncovered)/nfoot, 'hypothetical_dot_budget':DOT_BUDGET,
            'min_possible_overlap':lower,
            'max_dot_count_not_ruled_out_by_this_witness':math.floor(uncovered / .30),
            'verdict':'DUPLICATE_BY_BOUND; STOP BEFORE PLACEMENT',
            'caveat':'This bound applies to distinct dots in the footprint at this budget, not every possible smaller candidate.'},
        'forensic': {'claim':'GEMSDOE32 B2 equals GEMSDOE25 D2.8 with dots <=2 px from mirrored catalogue removed',
                     'candidate_xor_pixels':h33_xor, 'exact':h33_xor == 0,
                     'd28_positive_pixels':int(d28.sum()), 'b2_positive_pixels':int(h33.sum()),
                     'removed_by_b2':int((d28 & (dist <= 2)).sum()),
                     'note':'Exact raster relation is not proof of why an unseen test set scored as reported.'},
        'focus_sites':rows,
        'score_disclaimer':'Claims provided by the user are not organizer-confirmed; no score-to-bytes receipt was available. Leaderboard estimates are unavailable.',
    }


def main():
    report = audit()
    path = ROOT / 'evidence/portfolio_audit.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output':str(path), 'dense_witness':report['dense_surface_witness'],
                      'lattice':report['lattice_witness'], 'forensic':report['forensic'],
                      'sites':len(report['focus_sites'])}, indent=2))


if __name__ == '__main__':
    main()
