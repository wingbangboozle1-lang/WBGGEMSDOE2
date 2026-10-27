#!/usr/bin/env python3
"""Compatibility publisher: use the one byte-bound negative release renderer.

The original competing publisher and its claims are recoverable at main parent
29abbf694c2084569080fea6eaea275eb800f800. This entrypoint does not rerun CBS,
write a new candidate, reconstruct its historical card, or estimate a live score.
"""
from build_release import main

if __name__ == '__main__':
    raise SystemExit(main())
