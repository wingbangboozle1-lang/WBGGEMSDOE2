#!/usr/bin/env python3
"""Fetch every *named historical submission* we can resolve in public owner repos.

Scope is explicit: the 126 user-reported submission names in
``docs/data/user-reported-ledger.csv`` plus the 13 previously pinned witnesses.
This is an accessible public-repository inventory, NOT the organizer's registry:
unlinked, private, external, renamed or later-written rasters may be absent.
Files are hash-pinned by GitHub blob SHA-1 and by SHA-256 of the downloaded bytes.
Large binaries are skipped with a recorded reason. Nothing here scores or uploads.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'docs/data/user-reported-ledger.csv'
OUT_DIR = ROOT / 'data/registry_expanded'
EVIDENCE = ROOT / 'evidence/registry_expanded.json'
MAX_BYTES = 12_000_000
OWNER = 'buffedlizard55-lab'


def gh(*args: str) -> bytes:
    return subprocess.check_output(['gh', 'api', *args], stderr=subprocess.PIPE, timeout=180)


def norm(text: str) -> str:
    return re.sub(r'[^a-z0-9]', '', text.lower())


def inventory() -> dict[str, list[dict]]:
    sites: dict[str, list[str]] = {}
    with LEDGER.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if not row['submission_name']:
                continue
            sites.setdefault(row['site'], []).append(row['submission_name'])
    result: dict[str, list[dict]] = {}
    for site in sorted(sites):
        repo = f'{OWNER}/{site}'
        try:
            tree = json.loads(gh(f'repos/{repo}/git/trees/HEAD?recursive=1'))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            result[site] = [{'error': f'tree unavailable: {type(exc).__name__}'}]
            continue
        if tree.get('truncated'):
            result[site] = [{'error': 'truncated tree; inventory incomplete'}]
            continue
        blobs = [t for t in tree.get('tree', [])
                 if t.get('type') == 'blob' and t['path'].lower().endswith('.tif')
                 and ('download' in t['path'].lower() or 'submission' in t['path'].lower())]
        result[site] = [{'path': b['path'], 'sha': b['sha'], 'size': int(b['size'])} for b in blobs]
        print(f'[tree] {site}: {len(blobs)} TIFFs', flush=True)
    return result


def best_blob(name: str, blobs: list[dict]) -> dict | None:
    if not blobs:
        return None
    target = norm(name)
    scored = []
    for b in blobs:
        base = Path(b['path']).name.lower()
        for suffix in ('.tif', '-zeros', '-nan', '-allfinite', '_zeros', '_nan'):
            base = base.replace(suffix, '')
        bn = norm(base)
        if not bn:
            continue
        if bn == target or target.startswith(bn) or bn.startswith(target):
            scored.append((len(bn), b))
        elif len(target) >= 12 and (target[:12] in bn or bn[:12] in target):
            scored.append((0, b))
    if not scored:
        return None
    # Prefer the closest-length name, then the smallest file (a dot map, not a prior).
    scored.sort(key=lambda t: (abs(t[0] - len(target)), t[1]['size']))
    return scored[0][1]


def fetch_one(site: str, name: str, blob: dict) -> dict:
    repo = f'{OWNER}/{site}'
    path = blob['path']
    safe = re.sub(r'[^A-Za-z0-9_.-]', '_', f'{site}__{Path(path).name}')[:150]
    target = OUT_DIR / safe
    row = {'site': site, 'submission_name': name, 'repo': repo, 'path': path,
           'git_blob': blob['sha'], 'bytes': blob['size'],
           'url': f'https://github.com/{repo}/blob/HEAD/{path}?raw=1',
           'local': str(target.relative_to(ROOT))}
    if blob['size'] > MAX_BYTES:
        row['error'] = f'skipped: {blob["size"]} bytes exceeds {MAX_BYTES}'
        return row
    if not target.is_file() or target.stat().st_size != blob['size']:
        try:
            raw = gh(f'repos/{repo}/git/blobs/{blob["sha"]}',
                     '-H', 'Accept: application/vnd.github.raw+json')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            row['error'] = f'blob fetch failed: {type(exc).__name__}'
            return row
        if len(raw) != blob['size']:
            row['error'] = f'blob size mismatch: {len(raw)} != {blob["size"]}'
            return row
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    else:
        raw = target.read_bytes()
    git_blob_hash = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if git_blob_hash != blob['sha']:
        row['error'] = f'git blob SHA-1 mismatch: {git_blob_hash}'
        return row
    row['sha256'] = hashlib.sha256(raw).hexdigest()
    return row


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trees = inventory()
    requests = []
    with LEDGER.open(newline='', encoding='utf-8') as f:
        for entry in csv.DictReader(f):
            site, name = entry['site'], entry['submission_name']
            if not name:
                continue
            blobs = trees.get(site, [])
            if blobs and 'error' in blobs[0]:
                requests.append((site, name, None, blobs[0]['error']))
                continue
            match = best_blob(name, blobs)
            if match is None:
                requests.append((site, name, None, 'no matching TIFF in HEAD tree'))
            else:
                requests.append((site, name, match, None))
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for site, name, match, error in requests:
            if match is None:
                rows.append({'site': site, 'submission_name': name, 'error': error})
            else:
                futures[pool.submit(fetch_one, site, name, match)] = (site, name)
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as exc:  # one bad blob must not abort the audit
                site, name = futures[future]
                rows.append({'site': site, 'submission_name': name,
                             'error': f'unexpected {type(exc).__name__}: {exc}'})
    # Add the 13 previously pinned witnesses, keyed by their exact SHA-256.
    pinned = ROOT / 'data/registry'
    if pinned.is_dir():
        existing = {r.get('sha256') for r in rows if 'sha256' in r}
        for path in sorted(pinned.glob('*.tif')):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in existing:
                continue
            rows.append({'site': 'PINNED', 'submission_name': path.stem, 'repo': 'pinned',
                         'path': str(path.relative_to(ROOT)), 'sha256': digest,
                         'bytes': path.stat().st_size, 'local': str(path.relative_to(ROOT)),
                         'url': 'https://github.com/buffedlizard55-lab/'})
            existing.add(digest)
    rows.sort(key=lambda r: (r.get('site', ''), r.get('submission_name', '')))
    ok = [r for r in rows if 'sha256' in r]
    failures = [r for r in rows if 'error' in r]
    seen = {}
    for r in ok:
        seen.setdefault(r['sha256'], []).append(f"{r['site']}:{r['submission_name']}")
    receipt = {
        'schema': 'wbggems.expanded-registry.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'REGISTRY-MEASUREMENT',
        'scope': ('Public GitHub HEAD trees for every site named in the user-supplied 126-row '
                  'ledger, plus 13 pinned witnesses. Not an organizer-complete registry: '
                  'renamed, private, external, unlinked, deleted or later-written rasters may be absent. '
                  'A HEAD snapshot is not a pinned commit for unpinned rows.'),
        'ledger_rows': len(requests), 'resolved_files': len(ok),
        'distinct_sha256': len(seen), 'unresolved_or_skipped': len(failures),
        'max_bytes': MAX_BYTES, 'rows': rows,
    }
    EVIDENCE.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('ledger_rows', 'resolved_files',
          'distinct_sha256', 'unresolved_or_skipped')}, indent=2))
    print('Unresolved sample:', json.dumps(failures[:8], indent=1))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
