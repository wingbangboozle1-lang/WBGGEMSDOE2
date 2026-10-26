#!/usr/bin/env python3
"""Compatibility wrapper for the pinned shared format checker; never authorizes upload.

The earlier parallel-run checker ignored validity masks and could not establish
organizer acceptance. This wrapper delegates to the shared template and retains
an explicit warning where nodata or a mask can hide interior cells.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from prepare_data import ROOT
from validate_submission import run


def validate(path, ref=None):
    sample = Path(ref) if ref else ROOT / 'data/official/sample_submission.tif'
    result = run(Path(path), sample)
    result['submission_authorized'] = False
    result['verdict'] = 'NOT AUTHORIZED — local format check is not a registry, holdout or organizer receipt'
    result['mask_warning'] = ('Dataset has invalid/nodata mask cells; inspect their footprint location before any future review.'
                              if result.get('has_validity_mask') else None)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raster', type=Path);parser.add_argument('reference',type=Path,nargs='?')
    args=parser.parse_args()
    try:
        print(json.dumps(validate(args.raster,args.reference),indent=2,allow_nan=False))
    except (OSError,ValueError,RuntimeError) as exc:
        print(f'STOP: {exc}',file=sys.stderr)
    return 1  # this interface is diagnostic, never upload authorization


if __name__=='__main__':raise SystemExit(main())
