"""Distance-weighted Tversky index (DTI), DOE GEMS Prize.

Verified against the competition problem description
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):
alpha=0.2 (FP weight), beta=0.8 (FN weight), triangular kernel
k(d)=max(1-d/R,0), R=300 m = 3 px at 100 m/px.
TP_w = sum_g max_x p(x)k(d(x,g)); FP_w = sum_x p(x)(1-max_g k(d(x,g)));
FN_w = |G|-TP_w; DTI = TP/(TP+alpha*FP+beta*FN).
"""
import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA, BETA, RADIUS_PX = 0.2, 0.8, 3.0

def kernel(d, radius=RADIUS_PX):
    return np.maximum(1.0 - np.asarray(d, float) / radius, 0.0)

def dti_binary(pred_bool, truth, valid=None, known=None):
    p0 = np.asarray(pred_bool, bool); g0 = np.asarray(truth, bool)
    valid_ = np.ones(p0.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(p0.shape, bool) if known is None else np.asarray(known, bool)
    active = valid_ & ~known_
    p, g = p0 & active, g0 & active
    n = int(g.sum())
    if n == 0: return dict(tp=0.0, fp=float(p.sum()), fn=0.0, n_truth=0, dti=0.0)
    if not p.any(): return dict(tp=0.0, fp=0.0, fn=float(n), n_truth=n, dti=0.0)
    tp = float(kernel(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - kernel(distance_transform_edt(~g)[p])).sum())
    fn = float(n) - tp
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n,
                dti=float(tp/(tp+ALPHA*fp+BETA*fn+1e-12)))

def pooled_dti(fold_components):
    tp=sum(c["tp"] for c in fold_components); fp=sum(c["fp"] for c in fold_components)
    fn=sum(c["fn"] for c in fold_components); n=sum(c["n_truth"] for c in fold_components)
    return dict(tp=tp,fp=fp,fn=fn,n_truth=n,dti=float(tp/(tp+ALPHA*fp+BETA*fn+1e-12)))

def dti_bruteforce(pred, truth):
    pred=np.asarray(pred,float); truth=np.asarray(truth,bool)
    gs=np.argwhere(truth); xs=np.argwhere(pred>0); tp=fp=0.0
    for g in gs:
        tp+=max([pred[tuple(x)]*max(1-np.hypot(*(x-g))/RADIUS_PX,0) for x in xs]+[0.0])
    for x in xs:
        fp+=pred[tuple(x)]*(1-max([max(1-np.hypot(*(x-g))/RADIUS_PX,0) for g in gs]+[0.0]))
    fn=len(gs)-tp
    return tp/(tp+ALPHA*fp+BETA*fn+1e-12)
