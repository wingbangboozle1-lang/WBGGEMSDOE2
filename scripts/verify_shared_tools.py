#!/usr/bin/env python3
"""Verify pinned shared soft-DTI, strict writer and the universal STOP witness.

This does not train a model or submit anything. It checks the upstream template,
not a private evaluator/writer, on small analytic fixtures and restored bytes.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
from fetch_template import fetch
sys.path.insert(0, str(fetch()))
from gems57 import evaluate_holdout, metric, submission_writer, uniqueness  # noqa: E402


def main():
    p = np.array([[0.25]], dtype=np.float32)
    truth = np.array([[True]])
    visible = np.array([[False]])
    exact = metric.dti_exact(p, truth)
    result, terms = evaluate_holdout.evaluate(p, {'region':truth, 'visible':visible, 'truth':truth}, truth, block_side=1)
    expected = .25 / (.25 + .8 * .75)
    if abs(exact['dti'] - expected) > 1e-10 or abs(result['dti'] - expected) > 1e-10:
        raise AssertionError('shared evaluator failed a 0.25 probability fixture')
    if abs(terms.sum(axis=0)[3] - 1) > 1e-10:
        raise AssertionError('truth count did not pool')
    strict_rejections = {}
    with tempfile.TemporaryDirectory() as tmp:
        for label, v in [('over_one', 1.01), ('negative', -0.01), ('nan', float('nan'))]:
            try:
                submission_writer.write_submission(Path(tmp)/f'{label}.tif', np.array([[v]]),
                    Path(tmp)/'unused.tif', truth, name='strict-test', note='strict-test')
            except ValueError:
                strict_rejections[label] = True
            else:
                raise AssertionError(f'shared writer silently accepted invalid {label}')
    sample = ROOT / '.cache/data/sample_submission.tif'
    prior = ROOT / '.cache/data/17gems-e-proba.tif'
    with rasterio.open(sample) as src:
        footprint = np.isfinite(src.read(1))
        expected_grid = (src.shape, src.crs, src.transform)
    witness = uniqueness.saturation_certificate(prior, footprint, expected_grid=expected_grid)
    if not witness['universal_overlap_blocker']:
        raise AssertionError('shared uniqueness gate did not confirm the witness')
    witness['witness_file'] = '17GEMSDOE:docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif'
    out = {
        'purpose':'analytical fixture and independent shared-template uniqueness verification; not a model score',
        'template_ref':'07806249f4ed3efe70b4fbf866183c32392b7853',
        'holdout_evaluator_version':evaluate_holdout.VERSION,
        'implementation_sha256':evaluate_holdout.implementation_hashes(),
        'soft_metric_fixture':{'prediction':0.25, 'truth':1, 'expected':expected, 'actual':result['dti'], 'pass':True},
        'writer_rejects_invalid':strict_rejections,
        'shared_literal_saturation_witness':witness,
        'note':'Actual holdout DTI, confidence interval, and candidate validator are not available; no candidate was built.'}
    path = ROOT / 'evidence/shared_tool_checks.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
