#!/usr/bin/env python3
"""Cache capped distance-to-support fields for fast uniqueness iteration."""
import sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data_public'/'_cache'/'edt'; OUT.mkdir(parents=True,exist_ok=True)
for p in sorted((ROOT/'data_public'/'rasters').glob('*.tif')):
    dst=OUT/(p.stem+'.npz')
    if dst.exists(): continue
    try:
        with rasterio.open(p) as s:
            if (s.height,s.width)!=(3730,3292): continue
            a=s.read(1)
    except Exception: continue
    sup=np.isfinite(a)&(a>0)
    if not sup.any(): continue
    d=np.minimum(ndi.distance_transform_edt(~sup),10.0).astype(np.uint8)
    np.savez_compressed(dst,d=d)
    print(p.name,flush=True)
