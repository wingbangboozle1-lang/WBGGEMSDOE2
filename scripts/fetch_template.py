#!/usr/bin/env python3
"""Fetch only hash-verified shared evaluator/writer files from an immutable commit.

The upstream shared code stays in ignored .cache; this project does not fork or
silently patch it. Public GitHub-hosted source has no explicit license in that
repository: consult its owner before redistributing it separately.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/template_manifest.json'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch() -> Path:
    m = json.loads(MANIFEST.read_text())
    target = ROOT / '.cache/template' / m['ref'] / 'gems57'
    if all((target / name).is_file() and sha256((target/name).read_bytes()) == digest
           for name, digest in m['files_sha256'].items()):
        return target.parent
    url = f"https://codeload.github.com/{m['owner_repo']}/tar.gz/{m['ref']}"
    request = urllib.request.Request(url, headers={'User-Agent':'WBGGEMSDOE2-research/1.0'})
    with urllib.request.urlopen(request, timeout=120) as response:
        if not response.geturl().startswith('https://codeload.github.com/'):
            raise ValueError('unexpected template download redirect')
        data = response.read(80_000_001)
    if len(data) > 80_000_000:
        raise ValueError('template archive exceeds safety limit')
    temp = target.parent.with_name(target.parent.name + '.partial')
    if temp.exists():
        shutil.rmtree(temp)
    (temp / 'gems57').mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for name, expected in m['files_sha256'].items():
                # Accept only exact expected regular-file members, never extract paths/links.
                suffix = '/' + m['path'] + '/' + name
                matches = [item for item in archive.getmembers() if item.name.endswith(suffix)]
                if len(matches) != 1 or not matches[0].isfile() or matches[0].size > 1_000_000:
                    raise ValueError(f'missing/unsafe shared module: {name}')
                content = archive.extractfile(matches[0]).read()
                if sha256(content) != expected:
                    raise ValueError(f'shared template hash mismatch: {name}')
                (temp / 'gems57' / name).write_bytes(content)
        if target.parent.exists():
            shutil.rmtree(target.parent)
        os.replace(temp, target.parent)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return target.parent


if __name__ == '__main__':
    print('Verified shared template:', fetch())
