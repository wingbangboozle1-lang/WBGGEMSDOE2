import sys, os; sys.path.insert(0,"src")
import numpy as np
from wbg2.metric import dti_binary, dti_bruteforce
def test_metric_vs_bruteforce():
    rng=np.random.default_rng(0); t=rng.random((30,30))>0.9; p=rng.random((30,30))
    assert abs(dti_binary(p>0.5,t)["dti"]-dti_bruteforce((p>0.5).astype(float),t))<1e-9
    assert abs(dti_binary(p>0.5,t)["dti"]-dti_bruteforce(np.where(p>0.5,1.0,0.0),t))<1e-9
