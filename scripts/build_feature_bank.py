"""Flatten the 19-band feature stack into a memory-mapped float32 bank.

The generator and the analysis script read this instead of the 419 MB GeoTIFF so
they never hold 19 x 12.3 M float32 in RAM.  NoData (-3.4028235e+38) becomes
NaN.  Per-band robust statistics (median, IQR) are written next to the bank for
reproducible z-scoring.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/official/training_features.tif"
OUT = ROOT / "scratch/fbank/bands.f32"
STATS = ROOT / "scratch/fbank/stats.json"


def main() -> int:
    if not SRC.exists():
        print(f"[stop] {SRC} is missing; run scripts/get_data.sh first")
        return 1
    t0 = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    stats = []
    with rasterio.open(SRC) as ds:
        h, w, nod = ds.height, ds.width, ds.nodata
        mm = np.memmap(OUT, dtype=np.float32, mode="w+", shape=(ds.count, h, w))
        for i in range(1, ds.count + 1):
            a = ds.read(i).astype(np.float32)
            a[~np.isfinite(a) | (a <= nod * 0.5)] = np.nan
            mm[i - 1] = a
            v = a[np.isfinite(a)]
            stats.append(dict(
                band=i, desc=ds.descriptions[i - 1], n_finite=int(v.size),
                p50=float(np.percentile(v, 50)),
                iqr=float(np.percentile(v, 75) - np.percentile(v, 25)),
                p01=float(np.percentile(v, 1)), p99=float(np.percentile(v, 99)),
            ))
            print(f"  band {i:2d} finite={v.size:9d} p50={stats[-1]['p50']:.5g}", flush=True)
        mm.flush()
    STATS.write_text(json.dumps(stats, indent=1) + "\n")
    print(f"[ok] wrote {OUT} in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
