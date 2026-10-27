#!/usr/bin/env python3
"""Historical DZ-16 placement method, DISABLED. Its saved raster fails the literal lattice gate. The owner mirror is not authenticated and its past projection is not a score. Retained only for research provenance."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data_public" / "official"
OUT = ROOT / "docs" / "downloads"

# lane parameters (frozen; ablations are separate runs, never silent edits)
OFFSET_PEAK_PX = 16.0     # 1.6 km damage-zone flank
OFFSET_SIGMA_PX = 12.0    # 1.2 km
DENSITY_SIGMA_PX = 20.0   # 2.0 km corridor density window
MIN_SEPARATION_PX = 8     # 800 m: guarantees no redundant 300 m support
TARGET_DOTS = 34500       # below the measured 37,654 optimum (pruning trend)
CANDIDATE_STRIDE = 3


def load_grid():
    with rasterio.open(OFFICIAL / "existing_faults.tif") as src:
        cat = src.read(1)
        cat_profile = src.profile.copy()
    with rasterio.open(OFFICIAL / "sample_submission.tif") as src:
        sub = src.read(1)
        profile = src.profile.copy()
        nodata = src.nodata
        count = src.count
    finite = np.isfinite(sub) & (sub != (nodata if nodata is not None else np.nan))
    return cat.astype(bool), finite, profile, cat_profile, count


def build_prior(cat: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, dict]:
    dist = ndi.distance_transform_edt(~cat)
    offset_w = np.exp(-0.5 * ((dist - OFFSET_PEAK_PX) / OFFSET_SIGMA_PX) ** 2)
    density = ndi.gaussian_filter(cat.astype(np.float32), DENSITY_SIGMA_PX)
    density = density / max(float(density.max()), 1e-9)
    prior = (density ** 0.5) * offset_w * footprint
    prior[dist <= 4] = 0.0          # never spend mass on the mapped traces
    stats = {
        "offset_peak_px": OFFSET_PEAK_PX, "offset_sigma_px": OFFSET_SIGMA_PX,
        "density_sigma_px": DENSITY_SIGMA_PX, "min_separation_px": MIN_SEPARATION_PX,
        "prior_min": float(prior[footprint].min()), "prior_max": float(prior.max()),
        "prior_mean_in_footprint": float(prior[footprint].mean()),
        "mapped_trace_exclusion_px": 4,
    }
    return prior, stats


def select_dots(prior: np.ndarray, target: int, min_sep: int, stride: int, seed: int = 20261027):
    h, w = prior.shape
    ys, xs = np.mgrid[0:h:stride, 0:w:stride]
    ys, xs = ys.ravel(), xs.ravel()
    vals = prior[ys, xs]
    keep = vals > 0
    ys, xs, vals = ys[keep], xs[keep], vals[keep]
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(len(vals)), -vals))  # prior desc, deterministic jitter

    blocked = np.zeros(prior.shape, dtype=bool)
    r = min_sep
    oy, ox = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (oy * oy + ox * ox) <= r * r
    dy, dx = oy[disk], ox[disk]

    out_y, out_x = [], []
    for idx in order:
        y, x = int(ys[idx]), int(xs[idx])
        if blocked[y, x]:
            continue
        out_y.append(y)
        out_x.append(x)
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        my = dy + y; mx = dx + x
        m = (my >= y0) & (my < y1) & (mx >= x0) & (mx < x1)
        blocked[my[m], mx[m]] = True
        if len(out_y) >= target:
            break
    return np.asarray(out_y, np.int32), np.asarray(out_x, np.int32)


def main() -> int:
    raise RuntimeError("STOP: historical lane fails the literal registry gate or lacks pre-placement evidence; see evidence/local_artifact_audit_20261027.json. Do not generate or approve a submission.")

    cat, footprint, profile, cat_profile, count = load_grid()
    assert cat.shape == footprint.shape == (3730, 3292), cat.shape
    prior, stats = build_prior(cat, footprint)
    ys, xs = select_dots(prior, TARGET_DOTS, MIN_SEPARATION_PX, CANDIDATE_STRIDE)
    print(f"selected {len(ys)} dots")

    raster = np.zeros(cat.shape, dtype=np.float32)
    raster[ys, xs] = 1.0

    # content hash over the dot lattice (order independent)
    lattice = np.zeros(cat.shape, dtype=bool)
    lattice[ys, xs] = True
    digest = hashlib.sha256(np.packbits(lattice).tobytes()).hexdigest()
    short = digest[:8]

    OUT.mkdir(parents=True, exist_ok=True)
    name = f"wbg2-dz16-n{len(ys)}-20261027T000000Z-{short}-zeros"
    path = OUT / f"{name}.tif"

    prof = dict(profile)
    prof.update(driver="GTiff", dtype="float32", count=1, nodata=None,
                compress="deflate", tiled=False)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(raster, 1)

    # ---- re-open and verify from the bytes on disk ----
    with rasterio.open(path) as src:
        back = src.read(1)
        grid = {
            "shape": [src.height, src.width], "crs": str(src.crs),
            "transform": [float(v) for v in list(src.transform)[:6]],
            "dtype": src.dtypes[0], "count": src.count, "nodata": src.nodata,
        }
    inside = back[footprint]
    checks = {
        "no_nan_anywhere": bool(np.isfinite(back).all()),
        "values_in_0_1_anywhere": bool(back.min() >= 0.0 and back.max() <= 1.0),
        "values_in_0_1_inside_footprint": bool(inside.min() >= 0.0 and inside.max() <= 1.0),
        "no_nan_inside_footprint": bool(np.isfinite(inside).all()),
        "single_band_float32": bool(grid["count"] == 1 and grid["dtype"] == "float32"),
        "crs_epsg32611": bool(grid["crs"] == "EPSG:32611"),
        "grid_matches_sample_submission": bool(grid["shape"] == [3730, 3292]),
        "outside_footprint_is_zero": bool(np.all(back[~footprint] == 0.0)),
        "dots_recovered": int((back > 0).sum()) == len(ys),
    }
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    record = {
        "name": name, "file": str(path.relative_to(ROOT)), "sha256": sha,
        "bytes": path.stat().st_size, "dots": int(len(ys)), "mass": float(back.sum()),
        "lane": "DZ-16 damage-zone-flank structural prior, isolated binary dots",
        "parameters": stats, "grid": grid, "checks": checks,
        "all_checks_pass": all(checks.values()),
        "fill_policy": "0.0 outside the organizer footprint; nodata unset. The portal rejected a "
                       "NaN-filled variant with 'Predicted values must be in range [0, 1]' "
                       "(requester-reported), so zeros are used everywhere.",
    }
    print(json.dumps(record, indent=1))
    np.save(ROOT / "data_public" / "_candidate_dots.npy", np.stack([ys, xs]))
    (ROOT / "data_public" / "candidate.json").write_text(json.dumps(record, indent=1))
    return 0 if record["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
