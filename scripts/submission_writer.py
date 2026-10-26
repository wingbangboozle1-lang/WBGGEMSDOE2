"""Disabled parallel private writers; use the reviewed pinned shared writer.

Original sources are preserved in evidence/parallel_archive and
 evidence/conduit_archive. The first writer marked zeros NoData inside the
footprint; neither private writer is the required shared implementation.
"""


def write_submission(*args, **kwargs):
    raise RuntimeError('STOP: retired private writer; use the reviewed shared writer after all gates pass.')


if __name__ == '__main__':
    raise SystemExit('STOP: retired private writer; use the reviewed shared writer after all gates pass.')
