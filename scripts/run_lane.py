#!/usr/bin/env python3
"""Disabled historical lane: its literal registry preflight failed.

Original source is preserved in evidence/parallel_archive/run_lane.py.txt for
research; it used a private evaluator and is not an authorized shared lane.
"""

def main(*args, **kwargs):
    raise RuntimeError('STOP: parallel lane failed the any-registry gate; see evidence/parallel_review.json. Do not rerun or promote.')

if __name__ == '__main__':
    raise SystemExit('STOP: parallel lane failed the any-registry gate; see evidence/parallel_review.json. Do not rerun or promote.')
