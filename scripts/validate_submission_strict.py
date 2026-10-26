#!/usr/bin/env python3
"""Strict validator: re-opens the SAVED bytes. Fixes the reported
'Predicted values must be in range [0, 1]' failure by construction + check.
Usage: validate_submission.py FILE.tif [REFERENCE.tif]
Exit 0 = PASS. No human inspection involved."""
import sys, json, hashlib
import numpy as np, rasterio

def validate(path, ref=None):
    out={"file":path}
    with rasterio.open(path) as ds:
        a=ds.read(1); out.update(shape=list(ds.shape),crs=str(ds.crs),
            transform=list(ds.transform),dtype=str(ds.dtypes[0]),count=ds.count,
            nodata=ds.nodata)
        prof=dict(shape=ds.shape,crs=str(ds.crs),transform=ds.transform)
    finite=np.isfinite(a)
    out.update(all_finite=bool(finite.all()), nan_count=int((~finite).sum()),
        min=float(a.min()), max=float(a.max()),
        in_01=bool(a.min()>=0.0 and a.max()<=1.0),
        dots=int((a>0).sum()), mass=float(a.sum()))
    out["sha256"]=hashlib.sha256(open(path,'rb').read()).hexdigest()
    ok = ds.count==1 and out["all_finite"] and out["in_01"]
    if ref:
        with rasterio.open(ref) as r:
            match = (r.shape==prof["shape"] and str(r.crs)==prof["crs"]
                     and r.transform==prof["transform"])
        out["matches_reference"]=bool(match); ok = ok and match
    # footprint check if reference sample given separately is caller's job
    out["verdict"]="PASS" if ok else "FAIL"
    return out

if __name__=="__main__":
    r=validate(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
    print(json.dumps(r,indent=2)); sys.exit(0 if r["verdict"]=="PASS" else 1)
