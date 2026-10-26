#!/usr/bin/env python3
"""Retired conduit generator. It failed the all-registry preflight.

The original source is archived at evidence/conduit_archive/make_submission.py.txt.
It generates synthetic trends rather than the stated geophysical features; it
must not be rerun or used to select a weekly submission slot.
"""


def main(*args, **kwargs):
    raise RuntimeError('STOP: conduit generator failed the registered lattice gate; see evidence/conduit_review.json.')


if __name__ == '__main__':
    raise SystemExit('STOP: conduit generator failed the registered lattice gate; see evidence/conduit_review.json.')
