"""Disabled parallel writer: its zero-NoData encoding masked footprint cells.

Do not use a private writer; fix and use the pinned shared template's writer.
The original source is preserved in evidence/parallel_archive for research.
"""

def write_submission(*args, **kwargs):
    raise RuntimeError('STOP: retired private writer marked zeros NoData; use the reviewed shared writer after all gates pass.')
