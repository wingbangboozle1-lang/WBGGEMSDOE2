# Shared-template format-validator defect report

**Status, 2026-10-27:** Reproduced locally against the exact pinned commit. An attempt to open an upstream GitHub issue was rejected with `Resource not accessible by integration`; the connection has read-only permissions on that repository. No private fork or upstream fix was made. The project supplement remains fail-closed, and an upstream maintainer must apply and test the fix.

## Problem

At commit `822a0ce5546c7b6749cdd82eb145b6b3e616603d`, `gems57.gates.format_report` records that a GeoTIFF has a validity mask, but can still return `ok=True` when **in-footprint cells are masked**. For example, a finite all-zero raster with `nodata=0` is treated as a valid zero prediction even though GDAL marks every cell as missing. The sibling `gems57.validate.validate` reads the numerical array without checking the band mask too.

A real, previously published experimental file showed 5,132,809 masked cells out of 5,167,373 inside its owner-mirrored footprint. The counterexample and a supplemental stop are documented in [WBGGEMSDOE2's independent review](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/evidence/parallel_review.json). This does **not** establish what DrivenData's portal does, or diagnose a particular portal rejection.

## Minimal reproduction

Run with the dependencies of this repo and `PYTHONPATH=src`:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import rasterio
from rasterio.transform import from_origin
from gems57.gates import format_report

with TemporaryDirectory() as d:
    sample = Path(d) / 'sample.tif'
    cand = Path(d) / 'candidate.tif'
    p = dict(driver='GTiff', height=5, width=6, count=1, dtype='float32',
             crs='EPSG:32611', transform=from_origin(243350, 4508550, 100, 100))
    with rasterio.open(sample, 'w', **p) as ds:
        ds.write(np.ones((5, 6), dtype='float32'), 1)
    with rasterio.open(cand, 'w', nodata=0, **p) as ds:
        ds.write(np.zeros((5, 6), dtype='float32'), 1)
    r = format_report(cand, sample, footprint=np.ones((5, 6), dtype=bool))
    print(r['has_validity_mask'], r['ok'], r['problems'])
    # Actual: True True []. Expected: report is not OK because 30 in-footprint cells are masked.
```

## Suggested upstream correction

When an explicit footprint is provided, count `src.read_masks(1)[footprint] == 0`, record the count, and fail if it is nonzero. Similarly, check the band's mask in `validate` when a footprint is supplied. Check mask/footprint shapes before indexing and regression-test both `nodata=0` and explicit/internal masks; keep allowed outside-footprint nodata separate from interior mask validity. If no trustworthy footprint is available, do not claim this particular check passed. The all-finite export policy and actual organizer acceptance should remain separately labeled.

Please fix the shared template itself rather than a private fork. The separate WBGGEMSDOE2 supplemental check fails closed meanwhile; it is not a replacement for the upstream fix.