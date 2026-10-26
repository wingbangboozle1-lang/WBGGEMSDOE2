#!/usr/bin/env python3
"""Compatibility CLI for the shared + supplemental fail-closed format check.

The optional second positional reference is accepted only if it matches the
pinned owner mirror. A local pass never authorizes an upload. The original
parallel validator is archived because it ignored in-footprint NoData masks.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from validate_submission import ROOT, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raster', type=Path)
    parser.add_argument('reference', type=Path, nargs='?', default=ROOT / 'data/official/sample_submission.tif')
    args = parser.parse_args()
    try:
        report = run(args.raster, args.reference)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if report['ok'] else 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'STOP: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
