#!/usr/bin/env python3
"""Validate both independent negative release reviews before publishing routes.

The two-candidate release review is retained alongside the later five-artifact
review. This entry point checks the TIFF hashes and both reports, copies the
machine-readable evidence, and generates only fail-closed canonical redirects.
It cannot promote a candidate or run a model, writer or competition upload.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil

from build_legacy_routes import main as build_legacy_routes

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def check_evidence(report):
    rows = report.get('candidates', [])
    if (report.get('ok_to_submit') is not False or len(rows) != 2
            or {row.get('id') for row in rows} != {'DZ-16', 'H3-PACK'}):
        raise ValueError('Only the two audited negative release decisions can be published')
    later = {row['name']: row for row in load('evidence/local_artifact_audit_20261027.json')['artifacts']}
    for row in rows:
        if (row.get('ok_to_submit') is not False or row.get('verdict') != 'negative'
                or row.get('literal_duplicate_stop') is not True
                or row['final_dot_overlap_3px']['13GEMSDOE'] <= .70):
            raise ValueError('Release decision contradicts literal duplicate stop')
        other = later.get(row['id'])
        if (not other or other['sha256'] != row['sha256'] or other['path'] != row['file']
                or other['final_overlap_3px'] != row['final_dot_overlap_3px']
                or other['ok_to_submit'] is not False):
            raise ValueError('The independently reopened artifact reports disagree')
        if sha256((ROOT / row['file']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Candidate bytes changed; re-audit before publication')
    for rel in ('data_public/final_audit.json', 'data_public/run_card.json', 'evidence/RUN_CARD_H3.json'):
        record = load(rel)
        if record.get('ok_to_submit') is not False or record.get('verdict') != 'negative':
            raise ValueError(f'Conflicting approval: {rel}')


def check_focus_evidence():
    """Retain the concurrent review's pinned-focus hash and lattice guards."""
    registry = load('evidence/registry_recheck_20261027.json')
    inputs = load('config/registry_inputs.json')['inputs'][:9]
    if len(inputs) != 9 or len({item['id'] for item in inputs}) != 9:
        raise ValueError('Focus inventory changed; re-review before publishing')
    for item in inputs:
        measurement = registry['items'][item['id']]
        if measurement['sha256'] != item['sha256'] or not measurement['literal_lattice_duplicate']:
            raise ValueError('Focus evidence changed; re-review before publishing')


def main():
    report = load('evidence/release_recheck_20261027.json')
    check_evidence(report)
    check_focus_evidence()
    for name in ('release_recheck_20261027.json', 'registry_recheck_20261027.json'):
        shutil.copyfile(ROOT / 'evidence' / name, DOCS / 'data' / name)
    for source, target in [('evidence/RUN_CARD_H3.json', 'RUN_CARD_H3.json'),
                           ('data_public/run_card.json', 'run-card-current.json')]:
        shutil.copyfile(ROOT / source, DOCS / 'data' / target)
    build_legacy_routes()
    print('Checked both independent negative reviews; legacy URLs point to canonical evidence.')


if __name__ == '__main__':
    main()
