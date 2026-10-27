"""Label-free geophysical feature bank for the 2026-10-27 WBGGEMSDOE2 lane.

Every input is one of the 19 raw bands cached from the hash-pinned owner mirror
(``evidence/feature_cache.json``). No catalogue/label raster enters this module:
per-fold catalogue context is derived separately from *visible* faults only.

Three physical transform families (see research/hypotheses.md):

* ``flex_*``  -- multi-scale curvature dipoles of detrended elevation, gated by
  low slope and concordance with conductive-base-depth / gravity gradients. A
  blind normal fault can flex the overlying surface without a mappable scarp.
* ``alt_*``   -- anti-parallel conductivity/magnetic gradients plus a local
  magnetic low coincident with a conductivity high (clay-capped alteration).
* ``strain_*``/``seis_*`` -- dilatation zero-crossings along shear gradients and
  local anomalies of the two earthquake-density layers.

All filters are footprint-normalized so NaN holes cannot create artificial edges.
Outputs are float32 arrays on the full 3730x3292 grid, exactly 0 outside the
footprint, clipped to [0, 1] with recorded percentile normalizers. They are
derived data, not observations, and are not organizer-verified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.cache/features'
OUT = ROOT / '.cache/derived'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def band(i: int) -> np.ndarray:
    a = np.load(CACHE / f'band-{i:02d}.npy').astype(np.float32)
    return np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)


def smooth(a: np.ndarray, sigma: float, weight: np.ndarray) -> np.ndarray:
    """Gaussian filter with a separate finite-support weight (edge-safe)."""
    num = ndi.gaussian_filter(a * weight, sigma, mode='constant', cval=0.0)
    den = ndi.gaussian_filter(weight, sigma, mode='constant', cval=0.0)
    return (num / np.maximum(den, 1e-6)).astype(np.float32)


def grad(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gy, gx = np.gradient(a.astype(np.float32))
    return gy.astype(np.float32), gx.astype(np.float32)


def laplacian(a: np.ndarray) -> np.ndarray:
    return (ndi.laplace(a.astype(np.float32)) / 4.0).astype(np.float32)


def percentile_scale(a: np.ndarray, fp: np.ndarray, lo=2.0, hi=98.0) -> tuple[np.ndarray, dict]:
    v = a[fp]
    p0, p1 = np.percentile(v, [lo, hi])
    scale = max(float(p1 - p0), 1e-6)
    out = np.clip((a - p0) / scale, 0, 1).astype(np.float32)
    out[~fp] = 0
    return out, dict(p_lo=float(p0), p_hi=float(p1), scale=scale)


def dipole(curv: np.ndarray, size: int) -> np.ndarray:
    """Adjacent opposite-sign curvature lobes inside one local window."""
    hi = ndi.maximum_filter(curv, size=size, mode='constant')
    lo = ndi.minimum_filter(curv, size=size, mode='constant')
    return np.maximum(np.minimum(hi, -lo), 0).astype(np.float32)


def build(footprint: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    fp = np.asarray(footprint, bool)
    w = fp.astype(np.float32)
    f: dict[str, np.ndarray] = {}
    stats: dict[str, dict] = {}

    def add(name: str, value: np.ndarray) -> None:
        scaled, st = percentile_scale(np.asarray(value, np.float32), fp)
        f[name] = scaled
        stats[name] = st

    det = band(12)
    depth = np.log1p(np.maximum(band(15), 0))
    grav = band(13)
    cond = band(17)
    tmi = band(14)
    tc = band(6)
    dil = band(8)
    shear = band(7)
    inv2 = band(4)
    ieq = np.log1p(np.maximum(band(16), 0))
    deq = np.log1p(np.maximum(band(10), 0))

    # --- A. flexural curvature dipole of blind fault-propagation folding ---
    for sigma, size, suffix in ((1.5, 5, 's2'), (3.5, 9, 's4')):
        sm = smooth(det, sigma, w)
        c = laplacian(sm)
        add(f'flex_dipole_{suffix}', dipole(c, size))
        if suffix == 's2':
            add('flex_curv_abs', np.abs(c))
    sm2 = smooth(det, 1.5, w)
    gy, gx = grad(sm2)
    slope = np.hypot(gy, gx)
    s = max(float(np.percentile(slope[fp], 60)), 1e-6)
    add('flex_lowslope', np.exp(-slope / s))
    dgy, dgx = grad(smooth(depth, 3.0, w))
    add('flex_depth_grad', np.hypot(dgy, dgx))
    ggy, ggx = grad(smooth(grav, 3.0, w))
    add('flex_grav_edge', np.hypot(ggy, ggx))
    add('flex_hinge_concord', f['flex_dipole_s2'] * f['flex_depth_grad'])
    add('flex_hinge_grav', f['flex_dipole_s2'] * f['flex_grav_edge'])

    # --- B. clay-capped alteration: conductor high + magnetic low / opposed edges ---
    cs = smooth(cond, 2.0, w)
    ms = smooth(tmi, 2.0, w)
    cgy, cgx = grad(cs)
    mgy, mgx = grad(ms)
    cmag = np.hypot(cgy, cgx)
    mmag = np.hypot(mgy, mgx)
    add('alt_cond_grad', cmag)
    add('alt_mag_grad', mmag)
    dot = cgy * mgy + cgx * mgx
    opposition = np.maximum(-dot / np.maximum(cmag * mmag, 1e-6), 0)
    add('alt_cross_opposition', opposition * np.minimum(cmag, mmag))
    add('alt_mag_low', np.maximum(smooth(tmi, 8.0, w) - tmi, 0))
    add('alt_cond_high', np.maximum(cond - smooth(cond, 8.0, w), 0))
    add('alt_clay_cap', f['alt_mag_low'] * f['alt_cond_high'])
    add('alt_cond_depth', cond / np.maximum(depth, 1.0))
    tgy, tgx = grad(smooth(tc, 2.0, w))
    add('alt_tilt_edge', np.hypot(tgy, tgx))

    # --- C. strain partitioning and seismicity anisotropy ---
    denom = np.maximum(np.abs(inv2), 1.0)
    dil_norm = dil / denom
    shear_norm = shear / denom
    add('strain_dil_zero', np.exp(-np.abs(dil_norm) / 0.25))
    sgy, sgx = grad(smooth(shear_norm, 3.0, w))
    add('strain_shear_grad', np.hypot(sgy, sgx))
    add('strain_partition', f['strain_dil_zero'] * f['strain_shear_grad'])
    add('strain_inv2', inv2)
    add('seis_intensity_anom', np.abs(ieq - smooth(ieq, 6.0, w)))
    add('seis_distance_anom', np.abs(deq - smooth(deq, 6.0, w)))
    return f, stats


def catalogue_context(visible: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Visible-fault-only context. Never receives the withheld component mask."""
    fp = np.asarray(footprint, bool)
    w = fp.astype(np.float32)
    v = np.asarray(visible, bool) & fp
    dist = ndi.distance_transform_edt(~v)
    density = ndi.gaussian_filter(v.astype(np.float32), sigma=8.0, mode='constant')
    return {
        'ctx_dist_visible': np.clip(np.log1p(dist) / np.log1p(50.0), 0, 1).astype(np.float32),
        'ctx_visible_density': (density / max(float(density.max()), 1e-6)).astype(np.float32) * fp,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ROOT / 'data/official/sample_submission.tif') as src:
        fp = np.isfinite(src.read(1))
    features, stats = build(fp)
    receipt = {
        'schema': 'wbggems.derived-features.v1',
        'evidence_class': 'DATA-MEASUREMENT',
        'origin': '19 label-free raw bands (owner mirror, SHA-256 4371c82e…); no label input',
        'footprint_cells': int(fp.sum()),
        'normalization': '2nd/98th percentile clipping inside footprint to [0,1]; zero outside',
        'features': {},
    }
    for name, arr in features.items():
        path = OUT / f'{name}.npy'
        np.save(path, arr)
        receipt['features'][name] = {
            'file': str(path.relative_to(ROOT)), 'sha256': digest(path),
            'bytes': path.stat().st_size, 'normalizer': stats[name],
            'min': float(arr.min()), 'max': float(arr.max()),
            'positive_in_footprint': int((arr[fp] > 0).sum()),
        }
    (ROOT / 'evidence/derived_features.json').write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'derived {len(features)} label-free features; '
          f'names: {", ".join(features)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
