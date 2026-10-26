import json
from pathlib import Path
import sys
import tempfile

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT/'data/template_manifest.json').read_text())
TEMPLATE = ROOT / '.cache/template' / MANIFEST['ref']
pytestmark = pytest.mark.skipif(not TEMPLATE.is_dir(), reason='run scripts/fetch_template.py first')
sys.path.insert(0, str(TEMPLATE))


def test_shared_evaluator_preserves_soft_probability():
    from gems57.evaluate_holdout import evaluate
    p = np.array([[.25]], np.float32)
    b = np.array([[True]])
    score, terms = evaluate(p, {'region':b, 'truth':b, 'visible':~b}, b, block_side=1)
    assert score['dti'] == pytest.approx(.25 / (.25 + .8 * .75), abs=1e-10)
    assert score['n_truth'] == 1
    assert terms.sum(axis=0)[3] == 1


@pytest.mark.parametrize('invalid', [float('nan'), float('inf'), -0.1, 1.1])
def test_shared_writer_rejects_bad_values_before_writing(invalid):
    from gems57.submission_writer import write_submission
    with tempfile.TemporaryDirectory() as d:
        output = Path(d)/'bad.tif'
        with pytest.raises(ValueError):
            write_submission(output, np.array([[invalid]]), Path(d)/'not-used.tif',
                             np.array([[True]]), name='fixture', note='fixture')
        assert not output.exists()
