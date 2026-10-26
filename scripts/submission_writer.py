#!/usr/bin/env python3
"""Write a binary {0,1} float32 GeoTIFF on the exact competition grid.
Values are clipped to [0,1] and NaN is impossible by construction
(input mask is boolean)."""
import numpy as np, rasterio

def write_submission(mask_bool, profile_source, out_path):
    with rasterio.open(profile_source) as ds:
        prof=ds.profile.copy()
    prof.update(dtype="float32", count=1, nodata=0.0, compress="deflate")
    a=np.asarray(mask_bool, bool).astype(np.float32)
    assert np.isfinite(a).all() and a.min()>=0 and a.max()<=1
    with rasterio.open(out_path,"w",**prof) as dst:
        dst.write(a,1)
    return out_path
