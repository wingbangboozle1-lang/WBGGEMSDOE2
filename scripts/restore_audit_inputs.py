#!/usr/bin/env python3
"""Restore only immutable, hash-pinned public audit inputs via GitHub.

Historical rasters are for evaluation/research only. They are not submissions.
The local cache is ignored, and a hash mismatch never overwrites a good file.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def records():
    manifest = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    for item in manifest['inputs']:
        yield item['repo'], item
    for item in manifest['focus_sites']:
        yield item['repository'], item


def restore(repo: str, item: dict) -> str:
    dest = (ROOT / item['cache_path']).resolve()
    cache = (ROOT / '.cache').resolve()
    if not dest.is_relative_to(cache):
        raise ValueError('audit inputs must stay inside .cache')
    if dest.is_file() and sha256(dest) == item['sha256']:
        return 'verified cached'
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix='restore-', suffix='.partial')
    try:
        with os.fdopen(fd, 'wb') as out:
            endpoint = f"repos/{repo}/contents/{item['path']}?ref={item['ref']}"
            result = subprocess.run(
                ['gh', 'api', endpoint, '-H', 'Accept: application/vnd.github.raw+json'],
                stdout=out, stderr=subprocess.PIPE, timeout=120, check=False,
            )
        if result.returncode:
            raise RuntimeError(f"GitHub fetch failed: {result.stderr.decode(errors='replace')[:300]}")
        if sha256(Path(tmp)) != item['sha256']:
            raise ValueError(f"SHA-256 mismatch for {repo}/{item['path']}; refusing input")
        os.replace(tmp, dest)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return 'downloaded and verified'


def main() -> int:
    try:
        for repo, item in records():
            print(f"{item.get('id', item.get('site'))}: {restore(repo, item)}", flush=True)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'Input restoration stopped: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
