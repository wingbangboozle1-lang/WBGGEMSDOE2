#!/usr/bin/env python3
"""Classify the expanded registry and build its like-for-like dot-union halo.

Policy decision 2026-10-27 (recorded in docs/PROJECT_CHARTER.md): the protocol's
"dots" test is applied only to *geological dot fields*. Two classes of registry
witness are reported separately, never silently deleted:

* ``continuous_surface`` -- positive on >20% of the footprint (shared
  ``DENSE_SUPPORT_FRACTION``). It has no dot set; rank correlation still applies.
* ``space_filling_control`` -- a synthetic lattice whose 3 px halo covers >95% of
  the footprint. Its literal forward overlap is ~1 for ANY candidate, so it
  cannot discriminate between geological lanes; rank correlation still applies.

The literal reading (every finite positive pixel = a dot, including both classes)
is always reported by ``scripts/audit_final_candidate.py``. This script writes
only the discriminating union used as a diversity prior, never a clearance.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'evidence/registry_union.json'
UNION = ROOT / 'data/registry_union_near.npy'
SAMPLE = ROOT / 'data/official/sample_submission.tif'
DENSE_LIMIT = 0.20
CONTROL_HALO = 0.95


def disk(radius: int) -> np.ndarray:
    y, x = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    return (x * x + y * y) <= radius * radius


def main() -> int:
    manifest = json.loads((ROOT / 'evidence/registry_expanded.json').read_text())
    with rasterio.open(SAMPLE) as src:
        fp = np.isfinite(src.read(1))
        expected = (src.shape, src.crs, src.transform)
    n_fp = int(fp.sum())
    struct = disk(3)
    union = np.zeros(fp.shape, bool)
    crowd = np.zeros(fp.shape, np.uint8)
    seen_digest: set[str] = set()
    rows = []
    for entry in manifest['rows']:
        if 'sha256' not in entry:
            rows.append({**entry, 'class': 'unavailable'})
            continue
        path = ROOT / entry['local']
        try:
            with rasterio.open(path) as src:
                if (src.shape, src.crs, src.transform) != expected or src.count != 1:
                    raise ValueError('grid mismatch or multi-band')
                a = src.read(1)
            dots = np.isfinite(a) & (a > 0) & fp
            n = int(dots.sum())
            frac = n / n_fp
            halo = ndi.binary_dilation(dots, structure=struct)
            halo_frac = float(halo[fp].mean())
            if frac > DENSE_LIMIT:
                kind = 'continuous_surface'
            elif halo_frac > CONTROL_HALO:
                kind = 'space_filling_control'
            else:
                kind = 'dot_field'
            duplicate_of = entry['sha256'] in seen_digest
            seen_digest.add(entry['sha256'])
            if kind == 'dot_field' and not duplicate_of:
                union |= halo
                bumped = crowd[halo].astype(np.uint16) + 1
                crowd[halo] = np.minimum(bumped, 255).astype(np.uint8)
            rows.append({**entry, 'class': kind, 'dots': n, 'duplicate_of_earlier_sha256': duplicate_of,
                         'support_fraction': frac, 'halo_fraction': halo_frac,
                         'grid_match': True})
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            rows.append({**entry, 'class': 'invalid', 'error': str(exc)[:200]})
    np.save(UNION, union)
    np.save(ROOT / 'data/registry_crowd.npy', crowd)
    counts = {k: sum(1 for r in rows if r['class'] == k) for k in
              ('dot_field', 'continuous_surface', 'space_filling_control',
               'invalid', 'unavailable')}
    receipt = {
        'schema': 'wbggems.registry-union.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'REGISTRY-MEASUREMENT',
        'scope': manifest['scope'],
        'footprint_cells': n_fp,
        'dense_support_limit': DENSE_LIMIT, 'control_halo_limit': CONTROL_HALO,
        'counts': counts, 'union_halo_cells': int((union & fp).sum()),
        'union_halo_fraction_of_footprint': float((union & fp).sum() / n_fp),
        'union_file': str(UNION.relative_to(ROOT)),
        'crowd_file': 'data/registry_crowd.npy',
        'crowd_max': int(crowd.max()),
        'crowd_quantiles_in_footprint': {str(q): float(np.quantile(crowd[fp], q))
                                         for q in (0, .1, .25, .5, .75, .9, 1)},
        'literal_policy_note': ('The literal protocol reading still fires on both '
                                'excluded classes for any nonempty candidate; see the '
                                'final candidate audit and the charter policy decision.'),
        'rows': rows,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('counts', 'union_halo_cells',
          'union_halo_fraction_of_footprint')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
