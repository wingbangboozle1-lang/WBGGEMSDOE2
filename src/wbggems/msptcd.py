"""Multi-Scale Potential-Field Tilt-Curvature & Conductive-Base Discontinuity (MSPTCD).

Implements label-free geophysical, topographic, radiometric, electrical, and geodetic
structural transforms on the cached 19-band GeoDAWN 100 m stack (EPSG:32611).

Metadata/provenance notes (mirror observations, not organizer authentication):
- Band 6 (labeled ``tc`` in mirror descriptions as 'Tilt angle or total curvature')
  has positive values (current mirror q01=7.72, median=18.48, q99=29.10), consistent with the
  official DrivenData problem page's GeoDAWN *total radiometric counts per second*
  channel, and inconsistent with an unscaled [-pi/2, pi/2] magnetic tilt angle.
  Positive values alone do NOT prove physical identity or units. The transforms
  below are robustly rescaled derivative ratios, not a calibrated inversion or
  a verification that the supplied vertical derivative belongs to RTP magnetics.
- Band 15 (``depth_to_base_surf``) is described on the official competition page as
  depth to conductive base surface (mirror text says basement); no geological
  equivalence is assumed, so all transforms treat it strictly as an electrical/cover
  depth proxy.
- Zero catalogue/fault labels are read or accepted anywhere in this module.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import numpy as np
from scipy import ndimage as ndi

FEATURE_VERSION = "msptcd-v2-axial-cos-squared"

RAW_BAND_NAMES: tuple[str, ...] = (
    "mag_anom",             # 01
    "rtp",                  # 02
    "tmi_hg",               # 03
    "geod_2ndinv",          # 04
    "iso_grav_anom_slope",  # 05
    "tc_radiometric",       # 06 (GeoDAWN total radiometric counts; see module note)
    "geod_shearrate",       # 07
    "geod_dilaterate",      # 08
    "tmi_vg",               # 09
    "deq_n100a15",          # 10
    "iso_grav_anom_vg",     # 11
    "det_elev",             # 12
    "iso_grav_anom",        # 13
    "tmi",                  # 14
    "depth_to_base_surf",   # 15
    "ieq_n100a15",          # 16
    "cond_surf",            # 17
    "iso_grav_anom_hg",     # 18
    "det_elev_slope",       # 19
)

CORE_PHYSICS_NAMES: tuple[str, ...] = (
    "mag_tilt_grad",            # 20: |grad_h atan(vg / |grad_h rtp|)| (Verduzco et al., 2004)
    "grav_tilt_grad",           # 21: |grad_h atan(grav_vg / |grad_h grav|)|
    "dip_offset_concordance",   # 22: H1 depth-shifted paired gravity-magnetic edge concordance
    "cond_flank_asymmetry",     # 23: H2 cross-strike cond_surf flank asymmetry across depth step
    "scarp_hessian_ridge_s15",  # 24: fine-scale (150 m) Hessian principal ridge crest of det_elev
    "scarp_hessian_ridge_s35",  # 25: mesoscale (350 m) Hessian ridge crest of det_elev_slope
    "rad_terrain_residual_edge",# 26: |grad_h tc| / (1 + 0.2 * det_elev_slope)
    "depth_cover_log_step",     # 27: |grad_h log1p(max(depth_to_base_surf, 0))|
    "grav_mag_orient_coherence",# 28: cos²(theta_grav - theta_mag) * joint edge amplitude (v2)
)

STRAIN_SEIS_NAMES: tuple[str, ...] = (
    "strain_dilation_ratio",    # 29: geod_dilaterate / (geod_2ndinv + 1)
    "strain_shear_edge_gate",   # 30: |grad_h geod_shearrate| * potential-field edge envelope
    "seismic_structural_index", # 31: log1p(ieq) - 0.5 * log1p(deq)
)

ALL_FEATURE_NAMES: tuple[str, ...] = RAW_BAND_NAMES + CORE_PHYSICS_NAMES + STRAIN_SEIS_NAMES


REQUIRED_BAND_INDICES: tuple[int, ...] = (2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19)


def _clean_band(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Fill non-finite pixels smoothly for spatial derivative filtering only.

    Inside the footprint, missingness is tiny (~3,061-3,073 of 5,167,373 pixels);
    nearest-neighbor Euclidean filling prevents NaN halo expansion under Gaussian
    derivatives without using any label information.
    """
    out = np.asarray(arr, dtype=np.float32).copy()
    if out.shape != footprint.shape:
        raise ValueError(f"band shape {out.shape} must match footprint shape {footprint.shape}")
    valid = np.isfinite(out) & footprint
    if not valid.any():
        raise ValueError("band has no finite values inside footprint")
    if not valid.all():
        _, idx = ndi.distance_transform_edt(~valid, return_distances=True, return_indices=True)
        out = out[idx[0], idx[1]]
    return out.astype(np.float32, copy=False)


def _robust_scale(arr: np.ndarray, footprint: np.ndarray, eps: float = 1e-6) -> float:
    vals = arr[footprint]
    if vals.size > 65_536:
        vals = vals[::16]
    q25, q75 = np.percentile(vals, [25.0, 75.0])
    iqr = float(q75 - q25)
    if iqr > eps:
        return iqr
    std = float(np.std(vals))
    return max(std, eps)


def _grad_xy(field: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gy = ndi.gaussian_filter(field, sigma=sigma, order=(1, 0), mode="nearest")
    gx = ndi.gaussian_filter(field, sigma=sigma, order=(0, 1), mode="nearest")
    mag = np.hypot(gx, gy).astype(np.float32)
    return gx.astype(np.float32), gy.astype(np.float32), mag


def _hessian_ridge_crest(field: np.ndarray, sigma: float) -> np.ndarray:
    """Maximum negative principal curvature (sigma^2 * max(-lambda_min, 0))."""
    fyy = ndi.gaussian_filter(field, sigma=sigma, order=(2, 0), mode="nearest")
    fxx = ndi.gaussian_filter(field, sigma=sigma, order=(0, 2), mode="nearest")
    fxy = ndi.gaussian_filter(field, sigma=sigma, order=(1, 1), mode="nearest")
    trace = fxx + fyy
    rad = np.hypot(fxx - fyy, 2.0 * fxy)
    lambda_min = 0.5 * (trace - rad)
    crest = np.maximum(-lambda_min, 0.0) * (sigma * sigma)
    return crest.astype(np.float32)


def _bilinear_sample(field: np.ndarray, y_coords: np.ndarray, x_coords: np.ndarray) -> np.ndarray:
    h, w = field.shape
    if h < 2 or w < 2:
        raise ValueError("field must be at least 2x2 for spatial derivative sampling")
    yc = np.clip(y_coords, 0.0, float(h - 1))
    xc = np.clip(x_coords, 0.0, float(w - 1))
    y0 = np.minimum(np.floor(yc).astype(np.int32), h - 2)
    x0 = np.minimum(np.floor(xc).astype(np.int32), w - 2)
    y1 = y0 + 1
    x1 = x0 + 1
    wy = (yc - y0).astype(np.float32)
    wx = (xc - x0).astype(np.float32)
    v00 = field[y0, x0]
    v01 = field[y0, x1]
    v10 = field[y1, x0]
    v11 = field[y1, x1]
    top = v00 * (1.0 - wx) + v01 * wx
    bot = v10 * (1.0 - wx) + v11 * wx
    return (top * (1.0 - wy) + bot * wy).astype(np.float32)


def compute_physics_features_from_arrays(
    bands: dict[int, np.ndarray],
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute the 12 MSPTCD physics features purely from label-free GeoDAWN bands.

    Parameters
    ----------
    bands : dict[int, np.ndarray]
        1-indexed bands (requiring 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19).
    footprint : np.ndarray
        Boolean 2-D mask of valid GeoDAWN footprint pixels.
    """
    fp = np.asarray(footprint, dtype=bool)
    if fp.ndim != 2 or fp.shape[0] < 2 or fp.shape[1] < 2 or not fp.any():
        raise ValueError("footprint must be a nonempty 2-D boolean mask of shape at least 2x2")
    missing = [idx for idx in REQUIRED_BAND_INDICES if idx not in bands]
    if missing:
        raise ValueError(f"missing required GeoDAWN band(s): {missing}")

    rtp = _clean_band(bands[2], fp)
    tmi_vg = _clean_band(bands[9], fp)
    grav = _clean_band(bands[13], fp)
    grav_vg = _clean_band(bands[11], fp)
    tc_rad = _clean_band(bands[6], fp)
    det_elev = _clean_band(bands[12], fp)
    elev_slope = np.maximum(_clean_band(bands[19], fp), 0.0)
    depth_base = np.maximum(_clean_band(bands[15], fp), 0.0)
    cond_surf = _clean_band(bands[17], fp)
    geod_2nd = np.maximum(_clean_band(bands[4], fp), 0.0)
    geod_shear = _clean_band(bands[7], fp)
    geod_dilat = _clean_band(bands[8], fp)
    deq = np.maximum(_clean_band(bands[10], fp), 0.0)
    ieq = np.maximum(_clean_band(bands[16], fp), 0.0)

    eps = 1e-6
    out: dict[str, np.ndarray] = {}

    # 1. Potential-field tilt horizontal gradients (Miller & Singh 1994; Verduzco et al. 2004).
    mx, my, mh_s15 = _grad_xy(rtp, sigma=1.5)
    _, _, mh_s35 = _grad_xy(rtp, sigma=3.5)
    mv_s15 = ndi.gaussian_filter(tmi_vg, sigma=1.5, mode="nearest").astype(np.float32)
    m_ratio_scale = _robust_scale(mh_s15, fp) / _robust_scale(mv_s15, fp)
    mag_tilt = np.arctan2(mv_s15 * m_ratio_scale, mh_s15 + eps).astype(np.float32)
    _, _, mag_tilt_grad = _grad_xy(mag_tilt, sigma=1.2)
    out["mag_tilt_grad"] = np.where(fp, mag_tilt_grad, np.nan).astype(np.float32)

    gx, gy, gh_s20 = _grad_xy(grav, sigma=2.0)
    _, _, gh_s40 = _grad_xy(grav, sigma=4.0)
    gv_s20 = ndi.gaussian_filter(grav_vg, sigma=2.0, mode="nearest").astype(np.float32)
    g_ratio_scale = _robust_scale(gh_s20, fp) / _robust_scale(gv_s20, fp)
    grav_tilt = np.arctan2(gv_s20 * g_ratio_scale, gh_s20 + eps).astype(np.float32)
    _, _, grav_tilt_grad = _grad_xy(grav_tilt, sigma=1.5)
    out["grav_tilt_grad"] = np.where(fp, grav_tilt_grad, np.nan).astype(np.float32)

    # 2. H1: Depth-shifted gravity-magnetic discontinuity concordance (both polarities).
    # Unit normal along gravity horizontal gradient; shift proxy delta = clip(depth / 200 m, 0, 4) px.
    inv_gh = 1.0 / (gh_s20 + eps)
    nx = (gx * inv_gh).astype(np.float32)
    ny = (gy * inv_gh).astype(np.float32)
    shift_px = np.clip(ndi.gaussian_filter(depth_base, sigma=2.0, mode="nearest") / 200.0, 0.0, 4.0).astype(np.float32)

    h, w = fp.shape
    yy, xx = np.meshgrid(
        np.arange(h, dtype=np.float32),
        np.arange(w, dtype=np.float32),
        indexing="ij",
    )
    mh_norm = (0.5 * (mh_s15 / _robust_scale(mh_s15, fp) + mh_s35 / _robust_scale(mh_s35, fp))).astype(np.float32)
    gh_norm = (0.5 * (gh_s20 / _robust_scale(gh_s20, fp) + gh_s40 / _robust_scale(gh_s40, fp))).astype(np.float32)

    m_plus = _bilinear_sample(mh_norm, yy + shift_px * ny, xx + shift_px * nx)
    m_minus = _bilinear_sample(mh_norm, yy - shift_px * ny, xx - shift_px * nx)
    best_shifted_mag = np.maximum(mh_norm, np.maximum(m_plus, m_minus))
    dip_concord = np.sqrt(np.maximum(gh_norm, 0.0) * np.maximum(best_shifted_mag, 0.0)).astype(np.float32)
    out["dip_offset_concordance"] = np.where(fp, dip_concord, np.nan).astype(np.float32)
    del m_plus, m_minus, best_shifted_mag

    # 3. H2: Conductive flank asymmetry across depth_to_base_surf gradient normal.
    log_depth = np.log1p(depth_base).astype(np.float32)
    dx_d, dy_d, dh_mag = _grad_xy(log_depth, sigma=2.0)
    inv_dh = 1.0 / (dh_mag + eps)
    ndx = (dx_d * inv_dh).astype(np.float32)
    ndy = (dy_d * inv_dh).astype(np.float32)
    cond_smooth = ndi.gaussian_filter(cond_surf, sigma=1.5, mode="nearest").astype(np.float32)
    c_plus = _bilinear_sample(cond_smooth, yy + 3.0 * ndy, xx + 3.0 * ndx)
    c_minus = _bilinear_sample(cond_smooth, yy - 3.0 * ndy, xx - 3.0 * ndx)
    cond_iqr = _robust_scale(cond_smooth, fp)
    flank_asym = (np.abs(c_plus - c_minus) / cond_iqr) * np.tanh(dh_mag / _robust_scale(dh_mag, fp))
    out["cond_flank_asymmetry"] = np.where(fp, flank_asym.astype(np.float32), np.nan)
    del yy, xx, c_plus, c_minus, ndx, ndy

    # 4. Multi-scale Hessian principal scarp ridge crests (150 m and 350 m).
    ridge_15 = _hessian_ridge_crest(det_elev, sigma=1.5)
    ridge_35 = _hessian_ridge_crest(elev_slope, sigma=3.5)
    out["scarp_hessian_ridge_s15"] = np.where(fp, ridge_15, np.nan).astype(np.float32)
    out["scarp_hessian_ridge_s35"] = np.where(fp, ridge_35, np.nan).astype(np.float32)

    # 5. Radiometric total-count horizontal gradient normalized by terrain slope.
    _, _, tc_hg = _grad_xy(tc_rad, sigma=1.5)
    rad_res = (tc_hg / (1.0 + 0.2 * elev_slope)).astype(np.float32)
    out["rad_terrain_residual_edge"] = np.where(fp, rad_res, np.nan).astype(np.float32)

    # 6. Log-scale conductive-base cover step sharpness.
    out["depth_cover_log_step"] = np.where(fp, dh_mag, np.nan).astype(np.float32)

    # 7. Axial (polarity-invariant) parallel-normal alignment. The historical
    # abs(cos(2*delta)) assigned maximal coherence to perpendicular edges too.
    # cos²(delta) correctly yields 1 for parallel/antiparallel and 0 at 90 deg.
    alignment = axial_alignment_squared(gx, gy, mx, my)
    orient_coh = (alignment * np.tanh(0.5 * (gh_norm + mh_norm))).astype(np.float32)
    out["grav_mag_orient_coherence"] = np.where(fp, orient_coh, np.nan).astype(np.float32)

    # 8-10. EXP-2 Active Transtensional Strain-Rate & Microseismicity Conditioning.
    dilat_ratio = (geod_dilat / (geod_2nd + 1.0)).astype(np.float32)
    out["strain_dilation_ratio"] = np.where(fp, dilat_ratio, np.nan).astype(np.float32)

    _, _, shear_hg = _grad_xy(geod_shear, sigma=3.0)
    shear_gate = ((shear_hg / _robust_scale(shear_hg, fp)) * np.tanh(0.5 * (gh_norm + mh_norm))).astype(np.float32)
    out["strain_shear_edge_gate"] = np.where(fp, shear_gate, np.nan).astype(np.float32)

    seis_idx = (np.log1p(ieq) - 0.5 * np.log1p(deq)).astype(np.float32)
    out["seismic_structural_index"] = np.where(fp, seis_idx, np.nan).astype(np.float32)

    return out


def axial_alignment_squared(gx, gy, mx, my) -> np.ndarray:
    """Squared cosine of edge normals, invariant to magnetic polarity.

    Zero-amplitude normals have zero alignment rather than arbitrary direction.
    This geometry identity is unit-tested, not a new model/holdout experiment.
    """
    gx, gy, mx, my = (np.asarray(a, dtype=np.float64) for a in (gx, gy, mx, my))
    if len({a.shape for a in (gx, gy, mx, my)}) != 1:
        raise ValueError("edge-normal arrays must have the same shape")
    if not all(np.isfinite(a).all() for a in (gx, gy, mx, my)):
        raise ValueError("edge normals must be finite")
    # Normalize components first: squaring raw finite values can overflow (or
    # underflow to an arbitrary zero direction). Do not mutate caller arrays.
    gs = np.maximum(np.abs(gx), np.abs(gy))
    ms = np.maximum(np.abs(mx), np.abs(my))
    gx, gy = (np.divide(a, gs, out=np.zeros_like(a), where=gs > 0) for a in (gx, gy))
    mx, my = (np.divide(a, ms, out=np.zeros_like(a), where=ms > 0) for a in (mx, my))
    numerator = (gx * mx + gy * my) ** 2
    denominator = (gx * gx + gy * gy) * (mx * mx + my * my)
    out = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
    return np.clip(out, 0., 1.).astype(np.float32)


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_or_load_msptcd_cache(
    band_cache_dir: Path,
    out_cache_dir: Path,
    footprint: np.ndarray,
) -> dict[str, Path]:
    """Content-bound cache: inputs, footprint, implementation AND outputs checked.

    A v1 cache consisting of filenames alone is deliberately not reused. Outputs
    stage together and the manifest is installed last, so an interrupted rebuild
    can never be mistaken for a complete verified cache. No labels are inputs.
    """
    fp = np.asarray(footprint)
    if fp.dtype != np.bool_ or fp.ndim != 2 or min(fp.shape) < 2 or not fp.any():
        raise ValueError("footprint must be a nonempty 2-D boolean mask of shape at least 2x2")
    out_cache_dir = Path(out_cache_dir)
    out_cache_dir.mkdir(parents=True, exist_ok=True)
    needed_names = CORE_PHYSICS_NAMES + STRAIN_SEIS_NAMES
    paths = {name: out_cache_dir / f"{name}.npy" for name in needed_names}
    inputs = {idx: Path(band_cache_dir) / f"band-{idx:02d}.npy" for idx in REQUIRED_BAND_INDICES}
    signature = {
        "feature_version": FEATURE_VERSION,
        "implementation_sha256": _file_sha256(Path(__file__)),
        "shape": list(fp.shape),
        "footprint_sha256": hashlib.sha256(np.packbits(fp).tobytes()).hexdigest(),
        "input_sha256": {str(idx): _file_sha256(path) for idx, path in inputs.items()},
    }
    manifest_path = out_cache_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError):
        manifest = {}
    if (manifest.get("signature") == signature
            and set(manifest.get("outputs", {})) == set(paths)
            and all(p.is_file() and _file_sha256(p) == manifest["outputs"][name]
                    for name, p in paths.items())):
        return paths

    bands = {idx: np.load(p, mmap_mode="r", allow_pickle=False) for idx, p in inputs.items()}
    computed = compute_physics_features_from_arrays(bands, fp)
    with tempfile.TemporaryDirectory(prefix="msptcd-", dir=out_cache_dir) as tmp:
        staged = {}
        for name in needed_names:
            path = Path(tmp) / f"{name}.npy"
            np.save(path, computed[name].astype(np.float32, copy=False), allow_pickle=False)
            staged[name] = path
        receipt = {"signature": signature,
                   "outputs": {name: _file_sha256(p) for name, p in staged.items()}}
        for name, p in staged.items():
            p.replace(paths[name])
        staged_manifest = Path(tmp) / "manifest.json"
        staged_manifest.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
        staged_manifest.replace(manifest_path)
    return paths
