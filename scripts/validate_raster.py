#!/usr/bin/env python3
"""Inspect existing TIFF bytes using the shared validator; never approve a slot.

A format pass alone is not uniqueness, holdout, or organizer acceptance. The
literal registry witness remains a stop; this command does not write, clip, or
repair predictions. Historical files may be inspected for research only.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

try:
    from scripts import run_preflight as preflight
except ModuleNotFoundError:  # direct invocation: python scripts/validate_raster.py
    import run_preflight as preflight

ROOT = preflight.ROOT


def inspect(path: Path) -> dict:
    dots, near = preflight.shared_uniqueness()
    from gems57.gates import format_report
    manifest = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    inputs = {x['id']: x for x in manifest['inputs']}
    footprint, grid = preflight.load_grid(inputs['reference_grid'])
    witness = preflight.load_matching(inputs['universal_witness'], grid, footprint)
    blocker = preflight.universal_coverage(footprint, witness, dots, near)
    preflight.verify_witness_in_inventory(inputs['universal_witness'])
    report = format_report(path, preflight.checked_path(inputs['reference_grid']), footprint=footprint)
    actual_overlap = None
    # Invalid shapes or files are never treated as having passed uniqueness.
    with rasterio.open(path) as src:
        if src.count == 1 and (src.shape, src.crs, src.transform) == grid:
            a = src.read(1)
            support = dots(a) & footprint
            if support.any():
                actual_overlap = float((near(dots(witness) & footprint) & footprint)[support].mean())
    return {
        'evidence_class': 'LOCAL-FORMAT-AND-REGISTRY-INSPECTION',
        'format_policy': 'Shared conservative all-finite policy; public spec requires null/NaN outside data bounds but does not clearly define in-bounds uncovered cells. Not organizer acceptance.',
        'format_report': report,
        'witness_overlap_3px': actual_overlap,
        'overlap_limit': 0.70,
        'universal_blocker': blocker['universal_blocker'],
        'registry_complete': False,
        'surface_check_available': False,
        'holdout_eligible': False,
        'submission_allowed': False,
        'verdict': 'negative',
        'reason': 'Format inspection is not upload approval; no eligible surface, full registry clearance, or paired holdout evidence is supplied.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raster', type=Path, help='existing single-band TIFF to inspect; not an instruction to submit')
    args = parser.parse_args()
    try:
        if not args.raster.is_file():
            raise ValueError('input file does not exist')
        result = inspect(args.raster)
        print(json.dumps(result, indent=2, allow_nan=False))
        # A completed inspection is not approval: nonzero prevents `&& submit`.
        return 2
    except (OSError, ValueError, RuntimeError, KeyError, rasterio.errors.RasterioError) as exc:
        print(f'Inspection failed closed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
