"""Geothermal Vent & Concealed Dilatational Conduit Synthesis (WBG2-GVCD).

Implements the 5 preregistered GVCD geological & algorithmic hypotheses (GVCD-H1..H5)
on top of the 60 zero-catalogue DPHS features (total 72 zero-catalogue features):

1. GVCD-H2 (Mohr-Coulomb Tectonic Stress Dilation & Transtensional Gate):
   Exact axial Morris-Ferrill-Henderson (1996) dilation tendency
   ``T_d = sin^2(theta_strike - theta_shmin)`` and transtensional shear-dilation gate
   on Bouguer gravity, GeoDAWN RTP magnetics, and de-confounded piedmont scarps using
   the regional Great Basin stress tensor (``gb_regional_stress_grid_10km.csv``).
2. GVCD-H3 (Edge-Locked Geothermal Vent Plume & Borehole Heat-Flow Coupling):
   Fuses 1,546 borehole conductive/residual heat-flow stations
   (``usgs_heat_flow_wells_epsg32611.csv``), GDR #1391 thermal springs/wells, 2 m
   shallow temperature probes, paleo-sinter/travertine deposits, and Quaternary/Neogene
   volcanic unit margins (``derived_gdr_volcanics_100m_u8.tif``), multiplicatively
   locked onto subsurface gravity/magnetic/MT/basement-step structural edges so lateral
   aquifer outflow plumes collapse onto sub-vertical blind feeder faults.
3. GVCD-H4 (Post-INGENIOUS 2021-2026 ComCat Microseismicity & Seismogenic Corridors):
   Relocated USGS ComCat earthquakes (``usgs_comcat_geodawn.csv``) split into post-2021
   events postdating the GDR #1391 fault compilation cutoff and full-crustal seismogenic
   corridors coupled with GPS geodetic shear strain.
4. GVCD-H5 (Intrabasin Basement-Depth Hessian Tubular Ridge & Listric Dipole Asymmetry):
   Multi-scale second-order Hessian principal tubular ridgeness and cross-strike
   Laplacian dipole skewness of ``depth_to_base_surf`` concordant with ``iso_grav_anom_hg``.
5. GVCD-H1 (100% Spatial-OOF Slope-Blind Subsurface-Vent Specialist & Dual-Regime
   300 m CELF Submodular Allocation):
   Prevents steep range-front slope memorization and eliminates discrete fleet scarp
   duplication while maximizing expected Distance-Weighted Tversky Index.

Zero fault-catalogue pixels or fault-distance columns enter any feature computation.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

from .dphs import (
    EXP2_FEATURE_NAMES as DPHS60_NAMES,
    _robust_z,
    allocate_submodular_300m,
    build_or_load_dphs_cache,
)
from .msptcd import _clean_band, _hessian_ridge_crest

GVCD_EXTRA_NAMES: tuple[str, ...] = (
    "stress_grav_dilation_tendency",     # 61: GVCD-H2 Mohr-Coulomb T_d on Bouguer gravity strike
    "stress_mag_dilation_tendency",      # 62: GVCD-H2 Mohr-Coulomb T_d on RTP magnetic strike
    "stress_scarp_dilation_tendency",    # 63: GVCD-H2 Mohr-Coulomb T_d on deconfounded piedmont scarp
    "transtensional_shear_dilation_gate",# 64: GVCD-H2 Walker Lane sin^2(2*dtheta) * A_phi gate
    "borehole_heatflow_halo",            # 65: GVCD-H3 USGS/GDR 1,546-well residual heat-flow plume
    "gdr_volcanic_margin_conduit",       # 66: GVCD-H3 GDR #1391 volcanic contact & vent corridor
    "vent_structural_conduit_ridge",     # 67: GVCD-H3 Edge-locked 5-tracer geothermal vent conduit
    "epithermal_claycap_root_index",     # 68: GVCD-H3 K/Th + shallow demag + cond_surf over depth step
    "comcat_post2021_blind_halo",        # 69: GVCD-H4 Post-2021 (post-INGENIOUS) ComCat seismicity
    "comcat_seismogenic_corridor",       # 70: GVCD-H4 Crustal ComCat energy x GPS geodetic shear
    "basement_step_hessian_ridge",       # 71: GVCD-H5 2nd-order Hessian tubular ridge of depth_to_base
    "basement_bouguer_dipole_asymmetry", # 72: GVCD-H5 Listric hanging-wall depth-gravity dipole
)

GVCD_FEATURE_NAMES: tuple[str, ...] = DPHS60_NAMES + GVCD_EXTRA_NAMES

# Mountain-front slope/relief memorizers excluded from the Concealed-Basin Subsurface-Vent Specialist
MOUNTAIN_SLOPE_MEMORIZERS: frozenset[str] = frozenset(
    {
        "det_elev",
        "det_elev_slope",
        "scarp_hessian_ridge_s15",
        "scarp_hessian_ridge_s35",
        "lidar_relief",
        "dem10_slope_max",
        "dem10_steep_ratio_max",
        "dem10_hgm20_max",
        "dem10_hgm50_max",
        "dem10_curv_absmax",
        "dem10_onesided3",
        "scarp_ridge_10m_s2",
    }
)

SUBSURFACE_VENT_INDICES: tuple[int, ...] = tuple(
    i for i, name in enumerate(GVCD_FEATURE_NAMES) if name not in MOUNTAIN_SLOPE_MEMORIZERS
)


def compute_axial_dilation_and_shear(
    gx: np.ndarray,
    gy: np.ndarray,
    cos2_shmin: np.ndarray,
    sin2_shmin: np.ndarray,
    eps: float = 1e-8,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute exact axial Mohr-Coulomb dilation & horizontal shear tendency.

    On a north-up grid with ``gx = dF/dcol`` (+East) and ``gy = dF/drow`` (+South),
    the geographic strike tangent vector clockwise from North is ``(t_E, t_N) = (gy, gx)``
    with ``sin(theta_strike) = gy / r`` and ``cos(theta_strike) = gx / r``.
    Hence:
      ``cos(2 * theta_strike) = (gx^2 - gy^2) / (gx^2 + gy^2 + eps)``
      ``sin(2 * theta_strike) = (2 * gx * gy) / (gx^2 + gy^2 + eps)``
    Maximum normal dilation (``T_d = 1``) occurs when fault strike is perpendicular to
    ``theta_shmin``: ``T_d = sin^2(theta_strike - theta_shmin) = 0.5 * (1 - cos(2*(theta_strike - theta_shmin)))``.
    Maximum horizontal shear (``T_s = 1``) occurs at 45 deg to ``theta_shmin``:
    ``T_s = sin^2(2 * (theta_strike - theta_shmin)) = 1 - cos^2(2 * (theta_strike - theta_shmin))``.
    """
    gx32 = np.asarray(gx, dtype=np.float32)
    gy32 = np.asarray(gy, dtype=np.float32)
    r2 = gx32 * gx32 + gy32 * gy32 + float(eps)
    cos2_st = (gx32 * gx32 - gy32 * gy32) / r2
    sin2_st = (2.0 * gx32 * gy32) / r2
    cos_2diff = np.clip(cos2_st * cos2_shmin + sin2_st * sin2_shmin, -1.0, 1.0)
    t_dil = (0.5 * (1.0 - cos_2diff)).astype(np.float32, copy=False)
    t_shear = np.clip(1.0 - cos_2diff * cos_2diff, 0.0, 1.0).astype(np.float32, copy=False)
    return t_dil, t_shear


def load_regional_stress_fields(
    csv_path: Path, shape: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Interpolate axial (cos 2*SHmin, sin 2*SHmin) and Simpson A_phi from 10 km blocks."""
    h, w = shape
    bh = (h + 99) // 100
    bw = (w + 99) // 100
    c2_blk = np.full((bh, bw), np.nan, dtype=np.float32)
    s2_blk = np.full((bh, bw), np.nan, dtype=np.float32)
    ap_blk = np.full((bh, bw), np.nan, dtype=np.float32)

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for col in (reader.fieldnames or []):
            if "fault" in col.lower() or "cat" in col.lower():
                raise ValueError(f"Forbidden column in stress grid: {col}")
        for row in reader:
            br = int(float(row["block_row_10km"]))
            bc = int(float(row["block_col_10km"]))
            if not (0 <= br < bh and 0 <= bc < bw):
                continue
            az_rad = np.deg2rad(float(row["shmin_az_deg"]))
            c2_blk[br, bc] = float(np.cos(2.0 * az_rad))
            s2_blk[br, bc] = float(np.sin(2.0 * az_rad))
            ap_blk[br, bc] = float(row["aphi"])

    def _fill_and_upsample(blk: np.ndarray) -> np.ndarray:
        valid = np.isfinite(blk)
        if not valid.any():
            raise ValueError("Empty regional stress block grid")
        if not valid.all():
            _, idx = ndi.distance_transform_edt(~valid, return_indices=True)
            blk = blk[idx[0], idx[1]]
        blk_s = ndi.gaussian_filter(blk.astype(np.float32), sigma=0.85, mode="nearest")
        up = ndi.zoom(blk_s, (h / float(bh), w / float(bw)), order=1)
        return up[:h, :w].astype(np.float32, copy=False)

    c2 = _fill_and_upsample(c2_blk)
    s2 = _fill_and_upsample(s2_blk)
    norm = np.hypot(c2, s2) + 1e-8
    c2 = (c2 / norm).astype(np.float32, copy=False)
    s2 = (s2 / norm).astype(np.float32, copy=False)
    aphi = _fill_and_upsample(ap_blk)
    return c2, s2, aphi


def load_borehole_heatflow_grid(csv_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize convective borehole heat-flow anomalies strictly without fault distance."""
    grid = np.zeros(shape, dtype=np.float32)
    h, w = shape
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for col in (reader.fieldnames or []):
            if "fault" in col.lower() or "cat" in col.lower():
                raise ValueError(f"Forbidden column in heat-flow CSV: {col}")
        for row in reader:
            r = int(float(row["row"]))
            c = int(float(row["col"]))
            if not (0 <= r < h and 0 <= c < w):
                continue
            try:
                hf_meas = float(row.get("hf_meas_mw_m2") or 0.0)
                hf_resid = float(row.get("hf_resid_mw_m2") or 0.0)
            except ValueError:
                continue
            if not (np.isfinite(hf_meas) and np.isfinite(hf_resid)):
                continue
            excess = max(0.0, min(hf_resid, 350.0)) + 0.65 * max(0.0, min(hf_meas, 400.0) - 85.0)
            if excess > 0.0:
                grid[r, c] = max(grid[r, c], float(np.log1p(excess)))
    halo = 0.65 * ndi.gaussian_filter(grid, sigma=5.0) + 0.35 * ndi.gaussian_filter(grid, sigma=16.0)
    return np.log1p(28.0 * halo).astype(np.float32, copy=False)


def load_comcat_seismicity_grids(
    csv_path: Path, shape: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Rasterize post-2021 (post-INGENIOUS) and full-crustal USGS ComCat seismicity."""
    post2021 = np.zeros(shape, dtype=np.float32)
    crustal = np.zeros(shape, dtype=np.float32)
    h, w = shape
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for col in (reader.fieldnames or []):
            if "fault" in col.lower():
                raise ValueError(f"Forbidden fault column in ComCat CSV: {col}")
        for row in reader:
            try:
                r = int(float(row["row_100m"]))
                c = int(float(row["col_100m"]))
                yr = int(float(row["year"]))
                mag = float(row["magnitude"]) if (row.get("magnitude") or "").strip() else 2.2
            except (ValueError, KeyError):
                continue
            if not (0 <= r < h and 0 <= c < w):
                continue
            dep_str = (row.get("depth_km") or "").strip()
            if dep_str:
                try:
                    dep = float(dep_str)
                    if np.isfinite(dep) and dep <= 0.5:
                        # Suppress zero-depth surface quarry/mine blasts
                        continue
                except ValueError:
                    pass
            energy_w = float(10.0 ** (0.42 * np.clip(mag - 1.5, 0.0, 5.0)))
            crustal[r, c] += energy_w
            if yr >= 2021:
                post2021[r, c] += energy_w

    post_damped = np.log1p(post2021)
    crust_damped = np.log1p(crustal)
    post_halo = np.log1p(
        35.0 * (0.65 * ndi.gaussian_filter(post_damped, sigma=3.5) + 0.35 * ndi.gaussian_filter(post_damped, sigma=11.0))
    ).astype(np.float32, copy=False)
    crust_halo = np.log1p(
        22.0 * (0.60 * ndi.gaussian_filter(crust_damped, sigma=4.0) + 0.40 * ndi.gaussian_filter(crust_damped, sigma=13.0))
    ).astype(np.float32, copy=False)
    return post_halo, crust_halo


def build_or_load_gvcd_cache(
    root: Path,
    footprint: np.ndarray,
    external_dir: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, np.ndarray]:
    """Build or memory-map all 72 zero-catalogue GVCD features in .cache/gvcd_features."""
    ext = external_dir or (root / ".cache" / "external")
    cdir = cache_dir or (root / ".cache" / "gvcd_features")
    cdir.mkdir(parents=True, exist_ok=True)

    dphs_feats = build_or_load_dphs_cache(root, footprint, external_dir=ext)
    version_file = cdir / "gvcd_cache_meta.json"
    want_version = "gvcd-v1-72feat-20261027"
    if (
        version_file.is_file()
        and json.loads(version_file.read_text(encoding="utf-8")).get("version") == want_version
        and all((cdir / f"{name}.npy").is_file() for name in GVCD_EXTRA_NAMES)
    ):
        out = dict(dphs_feats)
        for name in GVCD_EXTRA_NAMES:
            out[name] = np.load(cdir / f"{name}.npy", mmap_mode="r")
        return out

    shape = footprint.shape
    c2_shmin, s2_shmin, aphi = load_regional_stress_fields(ext / "gb_regional_stress_grid_10km.csv", shape)

    # GVCD-H2: Mohr-Coulomb Dilation & Transtensional Shear-Dilation Tendency
    grav = _clean_band(np.asarray(dphs_feats["iso_grav_anom"], dtype=np.float32), footprint)
    gy_g = ndi.gaussian_filter(grav, sigma=2.0, order=(1, 0), mode="nearest")
    gx_g = ndi.gaussian_filter(grav, sigma=2.0, order=(0, 1), mode="nearest")
    mag_g = np.hypot(gx_g, gy_g)
    scale_g = float(np.percentile(mag_g[footprint][::16], 75.0)) + 1e-6
    td_grav, ts_grav = compute_axial_dilation_and_shear(gx_g, gy_g, c2_shmin, s2_shmin)
    stress_grav_dil = (td_grav * np.log1p(mag_g / scale_g)).astype(np.float32)

    rtp = _clean_band(np.asarray(dphs_feats["rtp"], dtype=np.float32), footprint)
    gy_m = ndi.gaussian_filter(rtp, sigma=1.8, order=(1, 0), mode="nearest")
    gx_m = ndi.gaussian_filter(rtp, sigma=1.8, order=(0, 1), mode="nearest")
    mag_m = np.hypot(gx_m, gy_m)
    scale_m = float(np.percentile(mag_m[footprint][::16], 75.0)) + 1e-6
    td_mag, _ = compute_axial_dilation_and_shear(gx_m, gy_m, c2_shmin, s2_shmin)
    stress_mag_dil = (td_mag * np.log1p(mag_m / scale_m)).astype(np.float32)

    det_elev = _clean_band(np.asarray(dphs_feats["det_elev"], dtype=np.float32), footprint)
    gy_e = ndi.gaussian_filter(det_elev, sigma=1.6, order=(1, 0), mode="nearest")
    gx_e = ndi.gaussian_filter(det_elev, sigma=1.6, order=(0, 1), mode="nearest")
    td_scarp, _ = compute_axial_dilation_and_shear(gx_e, gy_e, c2_shmin, s2_shmin)
    deconf_scarp = _clean_band(
        np.asarray(dphs_feats["dem10_deconfounded_piedmont_scarp"], dtype=np.float32), footprint
    )
    stress_scarp_dil = (td_scarp * np.log1p(np.maximum(deconf_scarp, 0.0))).astype(np.float32)

    w_transtens = np.exp(-0.5 * ((aphi - 1.15) / 0.45) ** 2).astype(np.float32)
    transtens_gate = (
        ts_grav * w_transtens * (0.55 * np.log1p(mag_g / scale_g) + 0.45 * np.log1p(mag_m / scale_m))
    ).astype(np.float32)

    # GVCD-H5: Intrabasin Basement-Depth Hessian Tubular Ridge & Listric Dipole Asymmetry
    depth_base = _clean_band(np.asarray(dphs_feats["depth_to_base_surf"], dtype=np.float32), footprint)
    log_depth = np.log1p(np.maximum(depth_base, 0.0)).astype(np.float32)
    gy_d = ndi.gaussian_filter(log_depth, sigma=1.5, order=(1, 0), mode="nearest")
    gx_d = ndi.gaussian_filter(log_depth, sigma=1.5, order=(0, 1), mode="nearest")
    step_d = np.hypot(gx_d, gy_d).astype(np.float32)
    hess_d_18 = _hessian_ridge_crest(step_d, sigma=1.8)
    hess_d_38 = _hessian_ridge_crest(step_d, sigma=3.8)
    basement_hessian = np.maximum(
        _robust_z(hess_d_18, footprint), _robust_z(hess_d_38, footprint)
    ).clip(-4.0, 8.0).astype(np.float32)

    lap_d = ndi.gaussian_laplace(log_depth, sigma=2.5, mode="nearest")
    pos_l = ndi.maximum_filter(np.maximum(lap_d, 0.0), size=5)
    neg_l = ndi.maximum_filter(np.maximum(-lap_d, 0.0), size=5)
    grav_hg_z = np.clip(_robust_z(np.asarray(dphs_feats["iso_grav_anom_hg"], dtype=np.float32), footprint), 0.0, 6.0)
    basement_dipole = (np.sqrt(pos_l * neg_l) * (0.4 + 0.6 * grav_hg_z)).astype(np.float32)

    # GVCD-H3: Borehole Heat Flow + Volcanic Margins + Edge-Locked Geothermal Vent Conduit
    hf_halo = load_borehole_heatflow_grid(ext / "usgs_heat_flow_wells_epsg32611.csv", shape)
    with rasterio.open(ext / "derived_gdr_volcanics_100m_u8.tif") as ds:
        volc = (ds.read(1) > 0).astype(np.float32)
    volc_grad = np.hypot(
        ndi.gaussian_filter(volc, sigma=2.2, order=(0, 1)),
        ndi.gaussian_filter(volc, sigma=2.2, order=(1, 0)),
    )
    vent_h = np.asarray(dphs_feats["gdr_volcanic_vent_halo"], dtype=np.float32)
    volc_conduit = (np.log1p(25.0 * volc_grad) + 0.50 * vent_h).astype(np.float32)

    ws_h = np.asarray(dphs_feats["gdr_wellspring_geotherm"], dtype=np.float32)
    p2m_h = np.asarray(dphs_feats["gdr_2m_probe_halo"], dtype=np.float32)
    pal_h = np.asarray(dphs_feats["gdr_paleo_sinter_halo"], dtype=np.float32)
    total_vent_plume = (0.30 * hf_halo + 0.28 * ws_h + 0.20 * p2m_h + 0.22 * pal_h).astype(np.float32)

    grav_tilt_z = np.clip(_robust_z(np.asarray(dphs_feats["grav_tilt_grad"], dtype=np.float32), footprint), -1.0, 6.0)
    mag_tilt_z = np.clip(_robust_z(np.asarray(dphs_feats["mag_tilt_grad"], dtype=np.float32), footprint), -1.0, 6.0)
    subsurface_edge_env = (
        0.35 * np.maximum(0.0, grav_tilt_z + 0.5)
        + 0.25 * np.maximum(0.0, mag_tilt_z + 0.5)
        + 0.25 * np.maximum(0.0, basement_hessian + 0.5)
        + 0.15 * (td_grav + td_mag)
    ).astype(np.float32)
    vent_conduit_ridge = (total_vent_plume * subsurface_edge_env).astype(np.float32)

    kth_z = np.clip(_robust_z(np.asarray(dphs_feats["geodawn_k_th_alteration"], dtype=np.float32), footprint), 0.0, 6.0)
    demag_z = np.clip(-_robust_z(np.asarray(dphs_feats["mag_shallow_demag"], dtype=np.float32), footprint), 0.0, 6.0)
    cond_z = np.clip(_robust_z(np.asarray(dphs_feats["cond_surf"], dtype=np.float32), footprint), 0.0, 6.0)
    epithermal_claycap = ((0.40 * kth_z + 0.35 * demag_z + 0.25 * cond_z) * (0.35 + 0.65 * np.maximum(0.0, basement_hessian))).astype(np.float32)

    # GVCD-H4: Post-2021 Blind ComCat Microseismicity & Crustal Seismogenic Corridors
    comcat_post2021, comcat_crust = load_comcat_seismicity_grids(ext / "usgs_comcat_geodawn.csv", shape)
    shear_z = np.clip(_robust_z(np.asarray(dphs_feats["geod_shearrate"], dtype=np.float32), footprint), -0.5, 6.0)
    comcat_corridor = (comcat_crust * (0.45 + 0.55 * np.maximum(0.0, shear_z + 0.5))).astype(np.float32)

    computed: dict[str, np.ndarray] = {
        "stress_grav_dilation_tendency": stress_grav_dil,
        "stress_mag_dilation_tendency": stress_mag_dil,
        "stress_scarp_dilation_tendency": stress_scarp_dil,
        "transtensional_shear_dilation_gate": transtens_gate,
        "borehole_heatflow_halo": hf_halo,
        "gdr_volcanic_margin_conduit": volc_conduit,
        "vent_structural_conduit_ridge": vent_conduit_ridge,
        "epithermal_claycap_root_index": epithermal_claycap,
        "comcat_post2021_blind_halo": comcat_post2021,
        "comcat_seismogenic_corridor": comcat_corridor,
        "basement_step_hessian_ridge": basement_hessian,
        "basement_bouguer_dipole_asymmetry": basement_dipole,
    }
    assert tuple(computed.keys()) == GVCD_EXTRA_NAMES
    for name, arr in computed.items():
        np.save(cdir / f"{name}.npy", np.asarray(arr, dtype=np.float32))
    version_file.write_text(json.dumps({"version": want_version, "features": list(GVCD_EXTRA_NAMES)}, indent=2) + "\n", encoding="utf-8")

    out = dict(dphs_feats)
    for name in GVCD_EXTRA_NAMES:
        out[name] = np.load(cdir / f"{name}.npy", mmap_mode="r")
    return out


def compute_piedmont_concealed_gate(
    det_elev_slope: np.ndarray,
    depth_to_base: np.ndarray,
    footprint: np.ndarray,
) -> np.ndarray:
    """Smooth [0, 1] indicator of low-relief concealed alluvial/basin cover (label-free)."""
    slp = _clean_band(np.asarray(det_elev_slope, dtype=np.float32), footprint)
    dep = _clean_band(np.asarray(depth_to_base, dtype=np.float32), footprint)
    low_slope = 1.0 / (1.0 + np.exp((slp - 6.0) / 2.0))
    deep_cover = 1.0 / (1.0 + np.exp(-(dep - 90.0) / 75.0))
    gate = (0.65 * low_slope + 0.35 * deep_cover).astype(np.float32)
    gate[~footprint] = 0.0
    return gate


def allocate_dual_regime_submodular_300m(
    surface_proximal: np.ndarray,
    surface_distal: np.ndarray,
    allowed_mask: np.ndarray,
    dist_to_visible_px: np.ndarray,
    *,
    total_budget: int = 37000,
    distal_threshold_px: float = 32.0,
    distal_quota_fraction: float = 0.365,
    min_sep_px: float = 2.60,
    min_marginal_gain_distal: float = 0.008,
    min_marginal_gain_proximal: float = 0.016,
) -> np.ndarray:
    """Two-stage non-overlapping 300 m CELF submodular allocator across distal & proximal regimes.

    Stage 1 allocates ``round(total_budget * distal_quota_fraction)`` dots inside the
    concealed distal piedmont/basin regime (``dist_to_visible_px > distal_threshold_px``)
    driven by the slope-blind geothermal-vent & subsurface specialist surface, preventing
    steep mountain-front scarps from monopolizing the budget.
    Stage 2 allocates the remaining budget in the proximal relay/stepover/flank regime
    while strictly respecting ``min_sep_px`` against all Stage 1 dots so zero dots ever
    violate the pairwise separation constraint across the regime boundary.
    """
    allowed = np.asarray(allowed_mask, dtype=bool)
    d_vis = np.asarray(dist_to_visible_px, dtype=np.float32)
    distal_mask = allowed & (d_vis > float(distal_threshold_px))
    n_distal_target = int(round(float(total_budget) * float(distal_quota_fraction)))

    dots_distal = allocate_submodular_300m(
        surface_distal,
        distal_mask,
        max_dots=n_distal_target,
        min_sep_px=min_sep_px,
        min_marginal_gain=min_marginal_gain_distal,
        k_truth=None,
    )
    placed_distal = dots_distal > 0
    n_distal_actual = int(placed_distal.sum())

    # Exclude min_sep_px halo around Stage-1 distal dots so boundary pairs never clash
    if n_distal_actual > 0:
        d_to_stage1 = ndi.distance_transform_edt(~placed_distal)
        prox_allowed = allowed & ~distal_mask & (d_to_stage1 >= float(min_sep_px) - 1e-6)
    else:
        prox_allowed = allowed & ~distal_mask

    n_prox_target = max(0, int(total_budget) - n_distal_actual)
    dots_prox = allocate_submodular_300m(
        surface_proximal,
        prox_allowed,
        max_dots=n_prox_target,
        min_sep_px=min_sep_px,
        min_marginal_gain=min_marginal_gain_proximal,
        k_truth=None,
    )
    return np.clip(dots_distal + dots_prox, 0.0, 1.0).astype(np.float32)
