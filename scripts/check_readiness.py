#!/usr/bin/env python3
"""Publish a dated read-only checkout diagnostic. --check exits 2 when blocked.

Default exit 0 means the diagnostic was written, NEVER permission to train or
submit. Error exit 1 means even the diagnostic could not be validated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.readiness import inspect_checkout, render_readiness


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='return exit 2 for the current blocked research state')
    args = parser.parse_args(argv)
    try:
        report = inspect_checkout(ROOT)
        payload = json.dumps(report, indent=2, allow_nan=False) + '\n'
        html = render_readiness(report)
        for relative, content in (
            ('evidence/checkout_readiness.json', payload),
            ('docs/data/checkout-readiness.json', payload),
            ('docs/readiness.html', html),
        ):
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + '.tmp')
            tmp.write_text(content, encoding='utf-8')
            tmp.replace(target)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Readiness diagnostic failed closed: {exc}', file=sys.stderr)
        return 1
    print('BLOCKED / DO NOT SUBMIT. Diagnostic written; no experiment or slot used.')
    return 2 if args.check else 0


if __name__ == '__main__':
    raise SystemExit(main())
