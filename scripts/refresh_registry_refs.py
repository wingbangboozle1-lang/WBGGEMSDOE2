#!/usr/bin/env python3
"""Check whether the nine audited GitHub commits have changed; never claim a new raster audit."""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def head(row: dict) -> dict:
    repo = row['repository']
    if not re.fullmatch(r'buffedlizard55-lab/GEMSDOE(?:24|25|27|28|30|31|32|33|36)', repo):
        raise ValueError('Unexpected priority repository in pinned manifest')
    try:
        result = subprocess.run(['gh','api',f'repos/{repo}/commits/main','--jq','.sha'],
                                capture_output=True, text=True, timeout=25, check=False)
        sha = result.stdout.strip()
        if result.returncode or not re.fullmatch(r'[0-9a-f]{40}', sha):
            raise ValueError('GitHub HEAD lookup failed or returned a malformed commit')
        return {'site':row['site'], 'audited_ref':row['ref'], 'current_head':sha,
                'changed':sha != row['ref'], 'status':'checked'}
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {'site':row['site'], 'audited_ref':row['ref'], 'current_head':None,
                'changed':None, 'status':'unknown', 'error':str(exc)[:180]}


def main() -> int:
    rows=json.loads((ROOT/'registry/focus_sites.json').read_text())['sites']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        checks=list(pool.map(head,rows))
    result={'evidence_class':'GITHUB-HEAD-FRESHNESS-ONLY',
            'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'changed_count':sum(r['changed'] is True for r in checks),
            'unknown_count':sum(r['changed'] is None for r in checks),
            'scope':'HEAD comparison only; newer rasters are not downloaded or audited by this check',
            'sites':checks}
    output=ROOT/'docs/data/focus-freshness.json'
    tmp=output.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    tmp.replace(output)
    print(f"[freshness] changed={result['changed_count']} unknown={result['unknown_count']}; no new raster audit")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
