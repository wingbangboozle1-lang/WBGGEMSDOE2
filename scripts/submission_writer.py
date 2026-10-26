#!/usr/bin/env python3
"""Historical writer, blocked: it sets nodata=0 and is not the shared template.

Use the pinned shared submission_writer only after policy and scientific gates
are resolved. This module cannot authorize or produce a competition file.
"""
import numpy as np, rasterio

def write_submission(mask_bool, profile_source, out_path):
    raise RuntimeError("STOP: use the pinned shared writer only after the registry and holdout gates are resolved")
    with rasterio.open(profile_source) as ds:
        prof=ds.profile.copy()
    prof.update(dtype="float32", count=1, nodata=0.0, compress="deflate")
    a=np.asarray(mask_bool, bool).astype(np.float32)
    assert np.isfinite(a).all() and a.min()>=0 and a.max()<=1
    with rasterio.open(out_path,"w",**prof) as dst:
        dst.write(a,1)
    return out_path
