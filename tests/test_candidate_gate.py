import numpy as np
from audit_candidate import stage


def test_witness_stops_before_rank_and_before_final():
    fp = np.ones((9, 9), bool)
    raster = np.zeros((9, 9))
    raster[4, 4] = 1
    dots = np.zeros_like(fp)
    dots[4, 4] = True
    # Constant surface would have undefined rank: witness stops earlier.
    result = stage(np.zeros((9, 9)), dots, fp, [('lattice', raster)])
    assert result['status'] == 'duplicate-stop'
    assert result['witness'] == 'lattice'
    assert result['overlap_3px'] == 1 and result['spearman'] is None
