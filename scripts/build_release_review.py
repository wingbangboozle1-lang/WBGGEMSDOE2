#!/usr/bin/env python3
"""Validate the independent concurrent release recheck without overriding the site.

The canonical negative-only renderer is build_site.py. This extra, independently
hash-bound review keeps its own measured evidence and refuses contradictory
promotion or stale bytes; it never makes a submission decision or creates TIFFs.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def load(rel):
    return json.loads((ROOT / rel).read_text())


def check_evidence(report):
    if report.get('ok_to_submit') is not False or len(report['candidates']) != 2:
        raise ValueError('Only audited negative release decisions can be published')
    for row in report['candidates']:
        if (row.get('ok_to_submit') is not False or row.get('verdict') != 'negative'
                or row.get('literal_duplicate_stop') is not True
                or not row['final_dot_overlap_3px']['13GEMSDOE'] > .70):
            raise ValueError('Release decision contradicts literal duplicate stop')
        if sha256((ROOT / row['file']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Candidate bytes changed; re-audit before publication')
    for rel in ('data_public/final_audit.json', 'data_public/run_card.json',
                'evidence/RUN_CARD_H3.json'):
        record = load(rel)
        if record.get('ok_to_submit') is not False or record.get('verdict') != 'negative':
            raise ValueError(f'Conflicting approval: {rel}')
    final_audit = load('data_public/final_audit.json')
    if (final_audit['verdicts']['literal_rule']['result'] != 'FAIL'
            or final_audit['verdicts']['normalized_rule']['operative'] is not False):
        raise ValueError('Historical normalized diagnostic cannot override literal stop')


def main():
    # Keep the independent two-artifact receipt as a scoped historical check,
    # then publish only through the complete current owned-inventory renderer.
    check_evidence(load('evidence/release_recheck_20261027.json'))
    from build_release import main as publish_negative_release
    return publish_negative_release()


if __name__ == '__main__':
    raise SystemExit(main())
