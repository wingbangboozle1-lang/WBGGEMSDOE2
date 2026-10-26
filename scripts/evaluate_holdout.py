#!/usr/bin/env python3
"""Retired private holdout evaluator; this is not the required shared tool.

Its original source is archived in evidence/conduit_archive. It did not apply
its buffer or pixel-exact visible-fault mask and averaged block scores instead
of pooling the required metric. Restore and use the pinned shared evaluator
only after the scientific and registry-policy blockers have been resolved.
"""


def evaluate_holdout(*args, **kwargs):
    raise RuntimeError('STOP: private evaluator retired; use the reviewed shared template after all prerequisites pass.')


def main(*args, **kwargs):
    raise RuntimeError('STOP: private evaluator retired; use the reviewed shared template after all prerequisites pass.')


if __name__ == '__main__':
    raise SystemExit('STOP: private evaluator retired; use the reviewed shared template after all prerequisites pass.')
