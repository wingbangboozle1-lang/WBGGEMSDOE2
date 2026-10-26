#!/usr/bin/env python3
"""Audit immutable historical raster inputs using the unmodified shared template.

This is a registry preflight, NOT a geological experiment. It never produces a
candidate. A universal witness proves the literal overlap gate impossible before
placement, so feature testing, holdout evaluation, and the submission writer do
not run. Missing, altered, or misaligned inputs cause a hard failure.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / '.cache/template/src'
PINNED_UNIQUENESS = '1c5094b814277ae801ccea6a47cf744429cffcdc10f9cc79f229d5fc44a8df95'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def shared_uniqueness():
    # Uniqueness imports the metric radius and other shared modules, so verifying
    # only uniqueness.py would not establish that the instrument is unmodified.
    template_root = TEMPLATE.parent.resolve()
    pins = ROOT / 'site-data/template-sha256.txt'
    seen = set()
    for line in pins.read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        path = (template_root / relative).resolve()
        if not path.is_relative_to(template_root) or not path.is_file() or digest(path) != expected:
            raise RuntimeError(f'Pinned shared template file missing or modified: {relative}')
        seen.add(relative)
    if not {'src/gems57/uniqueness.py', 'src/gems57/metric.py', 'evidence/registry_refreshed.json'} <= seen:
        raise RuntimeError('Shared template hash manifest is incomplete')
    path = TEMPLATE / 'gems57/uniqueness.py'
    if digest(path) != PINNED_UNIQUENESS:
        raise RuntimeError('Shared uniqueness pin does not match the audited version')
    # Refuse an already imported package from elsewhere; avoid silently using a fork.
    if 'gems57' in sys.modules:
        loaded = Path(sys.modules['gems57'].__file__).resolve()
        if not loaded.is_relative_to(TEMPLATE.resolve()):
            raise RuntimeError('A different gems57 package was already imported')
    if str(TEMPLATE) not in sys.path:
        sys.path.insert(0, str(TEMPLATE))
    from gems57.uniqueness import _dots, _near  # shared definitions, not a fork
    from gems57.metric import RADIUS_PX
    if RADIUS_PX != 3.0:
        raise RuntimeError('Shared uniqueness radius is not the required three pixels')
    return _dots, _near


def verify_witness_in_inventory(witness: dict) -> dict:
    """Verify that the blocking bytes are an indexed registry raster at the pinned snapshot."""
    path = TEMPLATE.parent / 'evidence/registry_refreshed.json'
    index = json.loads(path.read_text())  # source hash was checked by shared_uniqueness
    repo = witness['repo'].split('/')[-1]
    source = f"{repo}:{witness['path']}"
    snapshots = [row for row in index['snapshots'] if row['repo'] == repo]
    matches = [row for row in index['rasters']
               if row['sha256'] == witness['sha256'] and source in row['sources']]
    if len(snapshots) != 1 or snapshots[0]['commit'] != witness['ref'] or len(matches) != 1:
        raise RuntimeError('Blocking witness is not uniquely indexed at its pinned public registry snapshot')
    return {'index_sha256': digest(path), 'source': source, 'git_blob': matches[0]['blob']}


def universal_coverage(footprint: np.ndarray, prior: np.ndarray, dots, near) -> dict:
    """Calculate a proof valid for *all* nonempty candidate supports in footprint."""
    fp = np.asarray(footprint, dtype=bool)
    p = np.asarray(prior)
    if fp.ndim != 2 or p.shape != fp.shape or not fp.any():
        raise ValueError('prior and nonempty footprint must have the same 2-D shape')
    if not np.isfinite(p[fp]).all() or np.any((p[fp] < 0) | (p[fp] > 1)):
        raise ValueError('registry witness contains invalid values inside the footprint')
    support = dots(p) & fp
    covered = near(support) & fp
    uncovered = int(np.count_nonzero(fp & ~covered))
    return {
        'footprint_pixels': int(fp.sum()),
        'positive_pixels_in_footprint': int(support.sum()),
        'uncovered_pixels_within_3px': uncovered,
        'fraction_covered_within_3px': float(covered.sum() / fp.sum()),
        'universal_blocker': uncovered == 0,
    }


def checked_path(item: dict) -> Path:
    path = (ROOT / item['cache_path']).resolve()
    if not path.is_relative_to((ROOT / '.cache').resolve()):
        raise ValueError('input must be within the audit cache')
    if not path.is_file() or digest(path) != item['sha256']:
        raise ValueError(f"Missing or changed pinned input: {item.get('id', item.get('site'))}")
    return path


def load_grid(item):
    with rasterio.open(checked_path(item)) as ds:
        if ds.count != 1 or ds.dtypes != ('float32',) or ds.crs is None or ds.crs.to_epsg() != 32611:
            raise ValueError('reference grid is not a single-band float32 EPSG:32611 raster')
        if ds.transform.a != 100 or ds.transform.e != -100 or ds.transform.b != 0 or ds.transform.d != 0:
            raise ValueError('reference grid is not north-up at 100 m resolution')
        fp = ds.read_masks(1) != 0
        if not fp.any():
            raise ValueError('empty reference footprint')
        return fp, (ds.shape, ds.crs, ds.transform)


def load_matching(item, reference, fp, *, prediction=True):
    with rasterio.open(checked_path(item)) as ds:
        if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != reference:
            raise ValueError(f"Grid mismatch: {item.get('id', item.get('site'))}")
        if prediction and ds.dtypes != ('float32',):
            raise ValueError('prediction must be float32')
        array = ds.read(1)
    if prediction and (not np.isfinite(array[fp]).all() or np.any((array[fp] < 0) | (array[fp] > 1))):
        raise ValueError('invalid prediction values inside reference footprint')
    return array


def main() -> int:
    try:
        dots, near = shared_uniqueness()
        manifest = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
        inputs = {x['id']: x for x in manifest['inputs']}
        fp, reference = load_grid(inputs['reference_grid'])
        witness = load_matching(inputs['universal_witness'], reference, fp)
        blocker = universal_coverage(fp, witness, dots, near)
        blocker['indexed_registry'] = verify_witness_in_inventory(inputs['universal_witness'])
        lattice = load_matching(inputs['lattice_witness'], reference, fp)
        lattice_stats = universal_coverage(fp, lattice, dots, near)
        # General lower bound: at most U candidate pixels can lie outside the halo.
        lattice_stats['minimum_overlap_for_37654_dots'] = float(max(0, 1 - lattice_stats['uncovered_pixels_within_3px'] / 37654))
        catalogue = dots(load_matching(inputs['existing_faults'], reference, fp, prediction=False)) & fp
        h19 = dots(load_matching(inputs['h19_5'], reference, fp)) & fp
        supports = {}
        for row in manifest['focus_sites']:
            a = load_matching(row, reference, fp)
            inside = a[fp]
            if not np.isin(inside, [0, 1]).all():
                raise ValueError(f"Historical focus raster is not binary: {row['site']}")
            supports[row['site']] = dots(a) & fp
            if not supports[row['site']].any():
                raise ValueError('cannot compare an empty historical support')
        halos = {site: near(support) & fp for site, support in supports.items()}
        results = []
        for row in manifest['focus_sites']:
            site = row['site']
            support = supports[site]
            overlaps = {other: float(halo[support].mean()) for other, halo in halos.items() if other != site}
            worst = max(overlaps, key=overlaps.get)
            results.append({
                'site': site, 'filename': row['filename'], 'sha256': row['sha256'],
                'positive_pixels': int(support.sum()),
                'max_forward_overlap_3px': overlaps[worst], 'worst_focus_site': worst,
                'all_focus_overlaps_3px': overlaps,
                'unique_vs_nine_under_literal_rule': bool(overlaps[worst] <= 0.70),
                'user_reported_claim': row['claimed_value'],
                'evidence_class': row['claim_class'],
            })
        distance = distance_transform_edt(~catalogue)
        d28 = supports['GEMSDOE25']
        ancestry = {
            'h19_5_positive_pixels': int(h19.sum()),
            'd28_positive_pixels': int(d28.sum()),
            'd28_pixels_outside_h19_5': int((d28 & ~h19).sum()),
            'gems25_vs_gems30_support_xor_pixels': int(np.count_nonzero(d28 ^ supports['GEMSDOE30'])),
            'gems31_vs_d28_pruned_le_1px_xor_pixels': int(np.count_nonzero((d28 & (distance > 1)) ^ supports['GEMSDOE31'])),
            'gems32_vs_d28_pruned_le_2px_xor_pixels': int(np.count_nonzero((d28 & (distance > 2)) ^ supports['GEMSDOE32'])),
            'gems31_positive_pixels': int(supports['GEMSDOE31'].sum()),
            'gems32_positive_pixels': int(supports['GEMSDOE32'].sum()),
            'catalogue_pixels': int(catalogue.sum()),
        }
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        review = {
            'evidence_class': 'REGISTRY-MEASUREMENT', 'audited_at_utc': now,
            'reference_grid': {'shape': list(reference[0]), 'crs': str(reference[1]),
                               'transform': list(reference[2])[:6], 'footprint_pixels': int(fp.sum()),
                               'source_note': 'Hash-pinned public team mirror, not an authenticated organizer download.'},
            'scope': 'Nine pinned historical focus rasters only; directional overlap of each support with each other support within 3 pixels.',
            'threshold': 0.70, 'rows': results, 'ancestry': ancestry,
        }
        universal = bool(blocker['universal_blocker'])
        run = {
            'schema_version': 1, 'created_utc': now, 'verdict': 'negative', 'submission_allowed': False,
            'hypothesis': 'Provisional cross-scale magnetic contact-displacement aligned with detrended topography in covered basins.',
            'mechanism': 'Seek displaced magnetic edges and compatible surface gradients; no model or candidate was built.',
            'named_non_fault_process_that_could_mimic_it': 'Lithologic contacts without fault displacement or acquisition/levelling artifacts.',
            'lane_status': 'No single method paragraph was explicitly assigned; this is a provisional, untested hypothesis.',
            'holdout_dti': {'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': 'gems57-pooled-hide-v2',
                            'value': None, 'withheld_positives': None, 'ci95': None,
                            'status': 'not run; registry pre-placement STOP'},
            'leakage_canary': {'status': 'not run', 'features_tested': 0, 'auc_limit': 0.90},
            'correlation_overlap_vs_registry': {
                'candidate_surface_spearman': None, 'candidate_final_dot_overlap': None,
                'candidate_status': 'No candidate surface or dots generated.',
                'universal_witness': {'repo': inputs['universal_witness']['repo'],
                    'ref': inputs['universal_witness']['ref'], 'path': inputs['universal_witness']['path'],
                    'sha256': inputs['universal_witness']['sha256'], **blocker},
                'lattice_witness': {'sha256': inputs['lattice_witness']['sha256'], **lattice_stats},
                'literal_limit': 0.70,
            },
            'raster_sha256': None, 'submission_name': None, 'submission_note': None,
            'validator_output': {'status': 'not run: no new raster', 'no_nan_inside_footprint': None,
                                 'values_in_0_1': None, 'crs_shape_transform_match': None},
            'experiments_run': 0, 'submission_slots_used': 0,
            'reason': ('Universal positive-support witness covers the entire mirrored footprint; any nonempty candidate necessarily exceeds the literal overlap limit. Mandatory pre-placement STOP.'
                       if universal else 'No candidate, holdout, or complete registry certification; fail closed.'),
        }
        (ROOT / 'reports').mkdir(exist_ok=True)
        (ROOT / 'reports/focus-review.json').write_text(json.dumps(review, indent=2, allow_nan=False) + '\n')
        (ROOT / 'reports/run-card.json').write_text(json.dumps(run, indent=2, allow_nan=False) + '\n')
        print(f"Universal witness: {blocker['positive_pixels_in_footprint']}/{blocker['footprint_pixels']} positive, "
              f"{blocker['uncovered_pixels_within_3px']} uncovered within 3 px.")
        print('STOP: no candidate generated. Outputs: reports/focus-review.json and reports/run-card.json')
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f'Preflight failed closed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
