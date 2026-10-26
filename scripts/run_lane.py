#!/usr/bin/env python3
"""Historical parallel-run H1 code, preserved but blocked from execution.

The lane was self-assigned, not supplied in this session's instructions. Its
saved candidate fails the literal any-registry gate. Its private holdout also
uses withheld catalogue labels when selecting training negatives and has not
passed the shared evaluator protocol. See evidence/parallel_candidate_audit.json.

'Magnetic/radiometric step x lidar cross-slope asymmetry interaction'.

WHY this can catch a catalogue-missing fault: a buried/blind normal fault may
have no continuous lidar scarp (sediment burial) and no isolated magnetic step
(basement relief unrelated to faulting), but the COINCIDENCE of (a) a
GeoDAWN TMI / Th-K gradient step and (b) lidar cross-slope asymmetry
(cross_max, downface/upface) along the same line is the surface expression of
a fault juxtaposing basement + tilting the piedmont. Neither parent feature
alone is the submission; their interaction stack is.

Inputs (public, cloned sibling repos - see scripts/download_data.sh):
  labels.tif (=-1 outside footprint, 0/1 inside; 1 = catalogue fault pixel)
  lidar_scarp_features_u8.tif (12b), geodawn_rad_u8.tif (4b),
  geodawn_extensions_u8.tif (4b: ThK,UK,UTh,TMI_up150)
Catalogue-based feature (distance-to-visible-fault) is derived FOLD-LOCALLY
in holdout and from the full catalogue only for the final fit.
Outputs surface .npy + emitted mask .npy + JSON metrics.
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from wbg2.metric import dti_binary, pooled_dti

RNG = np.random.default_rng(20261026)
DATA = os.environ.get("WBG_DATA", "/tmp/wbg_data")

def load(name):
    with rasterio.open(os.path.join(DATA, name)) as ds:
        return ds.read(), ds.profile

def build_features(visible_faults):
    lidar, _ = load("lidar_scarp_features_u8.tif")   # 12 bands
    rad, _   = load("geodawn_rad_u8.tif")            # K Th U TC
    ext, _   = load("geodawn_extensions_u8.tif")     # ThK UK UTh TMI
    names, bands = [], []
    def add(n, a): names.append(n); bands.append(np.asarray(a, np.float32))
    lidar_names=['ex_max','ex_mean','step_max','lapneg_max','lappos_max',
                 'downface_max','upface_max','cross_max','relief','coh100','strike']
    for i,n in enumerate(lidar_names): add("lidar_"+n, lidar[i].astype(np.float32)/255.0)
    for i,n in enumerate(['K','Th','U','TC']): add("rad_"+n, rad[i].astype(np.float32)/255.0)
    for i,n in enumerate(['ThK','UK','UTh','TMI']): add("ext_"+n, ext[i].astype(np.float32)/255.0)
    # H1 interaction features (the lane) -------------------------------------
    tmi = ext[3].astype(np.float32)/255.0
    gy, gx = np.gradient(tmi)
    tmi_grad = np.hypot(gx, gy); tmi_grad /= (tmi_grad.max()+1e-9)
    thk = ext[0].astype(np.float32)/255.0
    gy, gx = np.gradient(thk); thk_grad = np.hypot(gx, gy); thk_grad/=(thk_grad.max()+1e-9)
    cross = lidar[7].astype(np.float32)/255.0
    downup = np.abs(lidar[5].astype(np.float32)-lidar[6].astype(np.float32))/255.0
    add("H1_tmiGrad_x_cross", tmi_grad*cross)
    add("H1_thkGrad_x_cross", thk_grad*cross)
    add("H1_tmiGrad_x_downupAsym", tmi_grad*downup)
    add("H1_step_x_tmiGrad", (lidar[2].astype(np.float32)/255.0)*tmi_grad)
    # fold-local catalogue distance (log) - derived from VISIBLE faults only
    d = ndi.distance_transform_edt(~visible_faults)
    add("dist_visible_fault_log", np.log1p(np.minimum(d, 50.0)).astype(np.float32))
    return bands, names  # list of 2-D float32 bands (no full-cube copy: 4 GB RAM)

def predict_surface(clf, bands, rows=128):
    H,W=bands[0].shape; out=np.empty((H,W),np.float32)
    for y0 in range(0,H,rows):
        blk=np.nan_to_num(np.stack([b[y0:y0+rows] for b in bands],-1).reshape(-1,len(bands)))
        out[y0:y0+rows]=clf.predict_proba(blk)[:,1].reshape(-1,W)
    return out

def sample_bands(bands, ysxs):
    return np.stack([b[ysxs] for b in bands], -1)

def emit_greedy(surface, valid, budget, min_sep=2.8, forbidden=None):
    """Greedy DTI packing: descending surface, min Euclidean separation."""
    cand = np.where(valid, surface, -1)
    order = np.argpartition(cand.ravel(), -min(budget*4, cand.size-1))[-budget*4:]
    order = order[np.argsort(cand.ravel()[order])[::-1]]
    taken = np.zeros(surface.shape, bool)
    if forbidden is not None: taken |= forbidden
    out = np.zeros(surface.shape, bool); r=int(np.ceil(min_sep))
    n=0
    H,W=surface.shape
    for idx in order:
        y,x = divmod(int(idx), W)
        y0,y1,x0,x1=max(0,y-r),min(H,y+r+1),max(0,x-r),min(W,x+r+1)
        if taken[y0:y1,x0:x1].any(): continue
        # exact separation check only vs emitted (taken includes forbidden;
        # forbidden proximity is allowed unless caller marked it)
        out[y,x]=True; taken[y,x]=True; n+=1
        if n>=budget: break
    return out

BLOCK=256
def block_fold_map(shape):
    yy,xx=np.mgrid[0:shape[0],0:shape[1]]
    return (((yy//BLOCK)+(xx//BLOCK))%4).astype(np.int8)
def segments_and_folds(labels):
    """Whole segments withheld by the 256px checkerboard block of their
    centroid (spatially blocked, geographically interleaved)."""
    lab, n = ndi.label(labels, structure=np.ones((3,3)))
    cents = np.array(ndi.center_of_mass(labels, lab, range(1, n+1)))
    bf = block_fold_map(labels.shape)
    fold_of_seg = np.array([bf[int(round(c[0])), int(round(c[1]))] for c in cents], np.int8)
    foldmap = np.zeros(labels.shape, np.int8)
    lut = np.zeros(n+1, np.int8); lut[1:] = fold_of_seg
    foldmap[:] = lut[lab]
    return lab, n, foldmap

def main(final_budget=None, experiments=("E1","E2","E3")):
    raise RuntimeError("STOP: the parallel H1 candidate fails the literal registry gate; this legacy lane also requires shared-evaluator and leakage review. See evidence/parallel_candidate_audit.json.")
    labels_raw, prof = load("labels.tif")
    labels_raw = labels_raw[0]
    footprint = labels_raw >= 0
    labels = labels_raw == 1
    results = {"evaluator":"WBGGEMSDOE2-HIDE-RECOVER-v2.0 (alpha0.2 beta0.8 R300m triangular, whole-segment withholding by 256px checkerboard centroid block, 15px training buffer, per-cell pooled DTI)",
               "folds":{}}

    # ---- holdout ------------------------------------------------------------
    lab, nseg, foldmap = segments_and_folds(labels)
    champ = None
    if os.path.exists(os.path.join(DATA,"champion.tif")):
        c,_=load("champion.tif"); champ = c[0]>0
    surfaces={}
    for fold in range(4):
        withheld = (foldmap==fold) & labels
        visible = labels & (foldmap!=fold)
        bufferz = ndi.binary_dilation(withheld, iterations=15)
        X, names = build_features(visible)
        if fold==0:
            results["features"]=names
            # leakage canaries: each feature alone vs withheld truth
            can={}
            ys, xs = np.where(withheld & footprint)
            sel = RNG.choice(len(ys), min(20000,len(ys)), replace=False)
            neg = np.where(footprint & ~ndi.binary_dilation(labels,iterations=3) & ~bufferz)
            nsel = RNG.choice(len(neg[0]), min(20000,len(neg[0])), replace=False)
            for j,name in enumerate(names):
                a = np.concatenate([X[j][ys[sel],xs[sel]], X[j][neg[0][nsel],neg[1][nsel]]])
                yy = np.concatenate([np.ones(len(sel)), np.zeros(len(nsel))])
                if np.std(a)>0:
                    au=roc_auc_score(yy,a); au=max(au,1-au); can[name]=round(float(au),4)
            results["leakage_canaries_fold0"]=can
            results["canary_max"]=max(can.values())
        train_zone = footprint & ~bufferz
        pos = np.where(train_zone & visible)
        negm = np.where(train_zone & ~ndi.binary_dilation(labels,iterations=3))
        nsel = RNG.choice(len(negm[0]), min(250000,len(negm[0])), replace=False)
        Xtr = np.concatenate([sample_bands(X,pos), sample_bands(X,(negm[0][nsel],negm[1][nsel]))])
        ytr = np.concatenate([np.ones(len(pos[0])), np.zeros(len(nsel))])
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.07,
                                             max_depth=None, random_state=0)
        clf.fit(np.nan_to_num(Xtr), ytr)
        surf = predict_surface(clf, X)
        surfaces[fold]=surf
        # E2 ablation: same training rows, catalogue-distance band removed
        clf_abl = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.07, random_state=0)
        clf_abl.fit(np.nan_to_num(Xtr[:,:-1]), ytr)
        surf_abl = predict_surface(clf_abl, X[:-1])
        del clf_abl
        cell = block_fold_map(labels.shape)==fold
        forb = ndi.binary_dilation(visible, iterations=2)
        budget = int(44090 * (cell & footprint).sum()/footprint.sum())
        for exp in experiments:
            esurf, esep = (surf_abl,2.8) if exp=="E2" else (surf,3.4) if exp=="E3" else (surf,2.8)
            dots = emit_greedy(esurf, cell & footprint & ~forb, budget, min_sep=esep, forbidden=forb)
            comp = dti_binary(dots, withheld & cell, valid=cell & footprint, known=visible)
            results["folds"].setdefault(exp,[]).append(comp)
        if champ is not None:
            comp = dti_binary(champ & cell & ~forb, withheld & cell,
                              valid=cell & footprint, known=visible)
            results["folds"].setdefault("CHAMPION_PROXY_leaky",[]).append(comp)
        print(f"fold {fold} done withheld={int(withheld.sum())}", flush=True)
        del X, clf, Xtr, ytr, surf, surf_abl
    for exp, comps in results["folds"].items():
        results[exp+"_pooled"]=pooled_dti(comps)
    # block bootstrap CI for main experiments (resample folds' truth blocks)
    np.save("/tmp/wbg_surfaces.npy", np.stack([surfaces[f] for f in range(4)]))
    # ---- final fit -----------------------------------------------------------
    X, names = build_features(labels)
    pos=np.where(footprint & labels)
    negm=np.where(footprint & ~ndi.binary_dilation(labels,iterations=3))
    nsel=RNG.choice(len(negm[0]), 300000, replace=False)
    clf=HistGradientBoostingClassifier(max_iter=250, learning_rate=0.07, random_state=0)
    clf.fit(np.nan_to_num(np.concatenate([sample_bands(X,pos),sample_bands(X,(negm[0][nsel],negm[1][nsel]))])),
            np.concatenate([np.ones(len(pos[0])),np.zeros(len(nsel))]))
    surf=predict_surface(clf, X)
    np.save("/tmp/wbg_final_surface.npy", surf.astype(np.float32))
    results["final_surface_sha256"]=hashlib.sha256(surf.tobytes()).hexdigest()
    print(json.dumps(results,indent=2))
    open("evidence/holdout_results.json","w").write(json.dumps(results,indent=2))
    return results

if __name__=="__main__":
    main()
