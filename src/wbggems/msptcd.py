"""Multi-Scale Potential-Field Tilt-Curvature & Conductive-Base Discontinuity (MSPTCD).

Implements historical label-free structural transforms on an owner-mirrored
19-band stack; this module is not an authorized candidate-generation entry point.

Metadata/provenance caveat: Band 6 is labeled ``tc`` and described as tilt or
curvature in the mirror, while the official page illustrates a radiometric tc
layer. The identity and units remain unresolved without authenticated metadata.
There are 3,073 masked NoData cells within the reference footprint; among the
5,164,300 valid cells none is negative. Those numbers do not prove physical band
identity or that a tilt angle must have any particular sign distribution. The
historical name ``tc_radiometric`` is retained for receipt reproducibility only.
Potential-field tilt transforms below are computed from potential-field
horizontal/vertical derivatives; they do not authenticate band 6.
- Band 15 (``depth_to_base_surf``) is described on the official competition page as
  depth to conductive base surface (mirror text says basement); no geological
  equivalence is assumed, so all transforms treat it strictly as an electrical/cover
  depth proxy.
- Zero catalogue/fault labels are read or accepted anywhere in this module.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from scipy import ndimage as ndi

RAW_BAND_NAMES: tuple[str, ...] = (
    "mag_anom",             # 01
    "rtp",                  # 02
    "tmi_hg",               # 03
    "geod_2ndinv",          # 04
    "iso_grav_anom_slope",  # 05
    "tc_radiometric",       # 06 historical variable name; physical identity unverified
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
    "grav_mag_orient_coherence",# 28: |cos 2(theta_grav - theta_mag)| * joint edge amplitude
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

    # 7. Azimuthal orientation coherence between gravity and magnetic horizontal gradients.
    # cos(2 * (theta_g - theta_m)) = ((gx*mx + gy*my)^2 - (gx*my - gy*mx)^2) / (|g|^2 |m|^2)
    dot_gm = gx * mx + gy * my
    cross_gm = gx * my - gy * mx
    denom_gm = (gh_s20 * gh_s20) * (mh_s15 * mh_s15) + eps
    cos2_diff = np.abs((dot_gm * dot_gm - cross_gm * cross_gm) / denom_gm).astype(np.float32)
    orient_coh = (cos2_diff * np.tanh(0.5 * (gh_norm + mh_norm))).astype(np.float32)
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


def build_or_load_msptcd_cache(
    band_cache_dir: Path,
    out_cache_dir: Path,
    footprint: np.ndarray,
) -> dict[str, Path]:
    """Compute and cache all 12 MSPTCD physics features into .npy files in .cache/."""
    out_cache_dir = Path(out_cache_dir)
    out_cache_dir.mkdir(parents=True, exist_ok=True)
    needed_names = CORE_PHYSICS_NAMES + STRAIN_SEIS_NAMES
    paths = {name: out_cache_dir / f"{name}.npy" for name in needed_names}
    if all(p.is_file() for p in paths.values()):
        return paths

    needed_bands = (2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 19)
    bands = {
        idx: np.load(Path(band_cache_dir) / f"band-{idx:02d}.npy", mmap_mode="r")
        for idx in needed_bands
    }
    computed = compute_physics_features_from_arrays(bands, footprint)
    for name in needed_names:
        tmp = paths[name].with_suffix(".tmp.npy")
        np.save(tmp, computed[name].astype(np.float32, copy=False))
        tmp.replace(paths[name])
    return paths
