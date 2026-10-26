#!/usr/bin/env python3
"""Uniqueness audit vs registry rasters (protocol lane rule):
FAIL/drift if Spearman rank-corr(surface, registry surface) > 0.90 OR
>70% of candidate dots lie within 3 px of a registry raster's dots.
Dots = pixels > 0. Surface = candidate values (for binary, the dot-density
surface smoothed by the 300 m triangular kernel is used for rank-corr)."""
import sys, json
import numpy as np, rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

def dots(p):
    with rasterio.open(p) as ds: return ds.read(1) > 0
def density(m):
    yy,xx=np.mgrid[-3:4,-3:4]; k=np.maximum(1-np.hypot(yy,xx)/3,0)
    return ndi.convolve(m.astype(np.float32), k, mode="constant")
def audit(cand_path, registry_paths):
    cand=dots(cand_path); cs=density(cand); out=[]
    cd = ndi.distance_transform_edt(~cand)
    for rp in registry_paths:
        r=dots(rp)
        frac=float((cd[r]<=3).mean()) if r.any() else 0.0  # reg dots near cand
        # candidate dots near registry (the protocol direction)
        rd=ndi.distance_transform_edt(~r)
        frac_c=float((rd[cand]<=3).mean()) if cand.any() else 0.0
        rs=density(r)
        samp=np.random.default_rng(0).choice(cs.size, 200000, replace=False)
        rho=float(spearmanr(cs.ravel()[samp], rs.ravel()[samp]).statistic)
        out.append(dict(registry=rp, rank_corr=round(rho,4),
                        cand_dots_within3px_frac=round(frac_c,4),
                        drift=bool(abs(rho)>0.90 or frac_c>0.70)))
    return out

if __name__=="__main__":
    res=audit(sys.argv[1], sys.argv[2:])
    print(json.dumps(res,indent=2))
    sys.exit(1 if any(r["drift"] for r in res) else 0)
