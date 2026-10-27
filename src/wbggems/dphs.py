"""Dual-Regime Piedmont & Hydrothermal-Structural Synthesis (WBG2-DPHS).

Combines:
1. 31 MSPTCD potential-field, electrical, strain & coarse topographic operators
   (from ``wbggems.msptcd``).
2. DPHS-H1: Dual-scale 1 m USGS 3DEP LiDAR scarp operators (encoding ``q == 0`` as
   ``NaN`` so gradient-boosted trees route the 24.7% un-flown LiDAR gap natively)
   paired with 100%-coverage seamless 10 m 3DEP DEM scarp operators de-confounded
   against US Census TIGER roads and Pleistocene Lake Lahontan shoreline benches.
3. DPHS-H3: USGS GeoDAWN spectral gamma-ray alteration (K, Th, U, K/Th) and shallow
   hydrothermal magnetite-destruction vertical differential (``z(RTP) - z(TMI_up150)``)
   plus Gallardo & Meju (2003) gravity-magnetic cross-gradient parallelism.
4. DPHS-H4: DOE GDR #1391 INGENIOUS blind hydrothermal conduit halos (thermal wells &
   springs with silica geothermometers, shallow 2 m temperature probes, paleo-sinter /
   travertine deposits, and Quaternary volcanic vents), strictly stripping
   ``dist_known_fault_px`` at CSV ingest so zero catalogue information enters features.
5. DPHS-H2 + DPHS-H5: Bounded ``[1.0, 1.25]`` fold-visible Voronoi stepover relay-breach
   & strike-projected tip continuation modulator paired with Minoux (1978) CELF
   lazy-greedy 300 m (``R = 3.0 px``) triangular-kernel submodular max-cover decoding
   outside the ``d_vis <= 2.05 px`` masked-catalogue bleed collar.
"""
from __future__ import annotations

import csv
import heapq
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

from .msptcd import (
    ALL_FEATURE_NAMES as MSPTCD_NAMES,
    RAW_BAND_NAMES,
    _clean_band,
    build_or_load_msptcd_cache,
)

LIDAR_SCARP_NAMES: tuple[str, ...] = (
    "lidar_ex_max",
    "lidar_ex_mean",
    "lidar_step_max",
    "lidar_lap_dipole",
    "lidar_updown_asym",
    "lidar_relief",
    "lidar_coh100",
)

DEM10_SCARP_NAMES: tuple[str, ...] = (
    "dem10_slope_max",
    "dem10_steep_ratio_max",
    "dem10_hgm20_max",
    "dem10_hgm50_max",
    "dem10_curv_absmax",
    "dem10_onesided3",
    "dem10_deconfounded_piedmont_scarp",
)

GEODAWN_SPEC_NAMES: tuple[str, ...] = (
    "geodawn_k",
    "geodawn_th",
    "geodawn_u",
    "geodawn_k_th_alteration",
    "mag_shallow_demag",
    "gallardo_meju_parallelism",
)

HYDRO_CONDUIT_NAMES: tuple[str, ...] = (
    "gdr_wellspring_geotherm",
    "gdr_2m_probe_halo",
    "gdr_paleo_sinter_halo",
    "gdr_volcanic_vent_halo",
)

MULTISCALE_RIDGE_NAMES: tuple[str, ...] = (
    "scarp_ridge_1m_s2",
    "scarp_ridge_10m_s2",
    "scarp_piedmont_contrast",
    "demag_along_strike_s3",
    "hydro_cond_coupling",
)

EXP1_FEATURE_NAMES: tuple[str, ...] = (
    MSPTCD_NAMES + LIDAR_SCARP_NAMES + DEM10_SCARP_NAMES + GEODAWN_SPEC_NAMES
)
EXP2_FEATURE_NAMES: tuple[str, ...] = (
    EXP1_FEATURE_NAMES + HYDRO_CONDUIT_NAMES + MULTISCALE_RIDGE_NAMES
)

FORBIDDEN_CSV_COLUMNS: frozenset[str] = frozenset({"dist_known_fault_px"})


def _robust_z(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    valid = np.isfinite(arr) & footprint
    vals = arr[valid]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826 + 1e-6
    out = (arr.astype(np.float32) - med) / mad
    return np.clip(out, -8.0, 8.0).astype(np.float32, copy=False)


def _dequantize_u8(q: np.ndarray, scale: float = 1.0, zero_is_nan: bool = True) -> np.ndarray:
    out = q.astype(np.float32) * float(scale)
    if zero_is_nan:
        out[q == 0] = np.nan
    return out


def load_gdr_wellspring_grid(csv_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize thermal excess from GDR #1391 wells/springs strictly without fault distance."""
    grid = np.zeros(shape, dtype=np.float32)
    h, w = shape
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        allowed_cols = {c for c in (reader.fieldnames or []) if c not in FORBIDDEN_CSV_COLUMNS}
        assert "dist_known_fault_px" not in allowed_cols
        for row in reader:
            r = int(float(row["row"]))
            c = int(float(row["col"]))
            if not (0 <= r < h and 0 <= c < w):
                continue
            vals = []
            for key, base, weight in (
                ("temp_c", 20.0, 1.0),
                ("geothermquartz_c", 65.0, 0.45),
                ("geothermchalc_c", 55.0, 0.45),
            ):
                raw = (row.get(key) or "").strip()
                if raw:
                    try:
                        v = float(raw)
                        if np.isfinite(v):
                            vals.append(weight * max(0.0, min(v, 260.0) - base))
                    except ValueError:
                        pass
            strength = sum(vals) if vals else 5.0
            grid[r, c] = max(grid[r, c], float(np.log1p(strength)))
    halo = 0.65 * ndi.gaussian_filter(grid, sigma=5.5) + 0.35 * ndi.gaussian_filter(grid, sigma=18.0)
    return np.log1p(25.0 * halo).astype(np.float32, copy=False)


def load_gdr_vent_grid(csv_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize Quaternary/Neogene volcanic vents strictly from (row, col)."""
    grid = np.zeros(shape, dtype=np.float32)
    h, w = shape
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        allowed_cols = {c for c in (reader.fieldnames or []) if c not in FORBIDDEN_CSV_COLUMNS}
        assert "dist_known_fault_px" not in allowed_cols
        for row in reader:
            r = int(float(row["row"]))
            c = int(float(row["col"]))
            if 0 <= r < h and 0 <= c < w:
                grid[r, c] = 1.0
    halo = 0.6 * ndi.gaussian_filter(grid, sigma=7.0) + 0.4 * ndi.gaussian_filter(grid, sigma=22.0)
    return np.log1p(60.0 * halo).astype(np.float32, copy=False)


def build_or_load_dphs_cache(
    root: Path,
    footprint: np.ndarray,
    external_dir: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, np.ndarray]:
    """Build or memory-map all 60 zero-catalogue DPHS feature rasters in .cache/dphs_features."""
    ext = external_dir or (root / ".cache" / "external")
    cdir = cache_dir or (root / ".cache" / "dphs_features")
    cdir.mkdir(parents=True, exist_ok=True)

    msptcd_dir = root / ".cache" / "msptcd_features"
    raw_dir = root / ".cache" / "features"
    msptcd_paths = build_or_load_msptcd_cache(raw_dir, msptcd_dir, footprint)
    base_feats: dict[str, np.ndarray] = {}
    for idx, name in enumerate(RAW_BAND_NAMES, start=1):
        base_feats[name] = np.load(raw_dir / f"band-{idx:02d}.npy", mmap_mode="r")
    for name, p in msptcd_paths.items():
        base_feats[name] = np.load(p, mmap_mode="r")

    extra_names = (
        LIDAR_SCARP_NAMES
        + DEM10_SCARP_NAMES
        + GEODAWN_SPEC_NAMES
        + HYDRO_CONDUIT_NAMES
        + MULTISCALE_RIDGE_NAMES
    )
    if all((cdir / f"{name}.npy").is_file() for name in extra_names):
        out = dict(base_feats)
        for name in extra_names:
            out[name] = np.load(cdir / f"{name}.npy", mmap_mode="r")
        return out

    shape = footprint.shape
    meta = json.loads((ext / "lidar_scarp_features.json").read_text(encoding="utf-8"))
    scales = meta.get("quantisation", {}).get("scales", {})

    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds:
        ex_max = _dequantize_u8(ds.read(1), scales.get("ex_max", 1.0 / 255.0))
        ex_mean = _dequantize_u8(ds.read(2), scales.get("ex_mean", 1.0 / 255.0))
        step_max = _dequantize_u8(ds.read(3), scales.get("step_max", 1.0 / 255.0))
        lapneg = _dequantize_u8(ds.read(4), scales.get("lapneg_max", 1.0 / 255.0))
        lappos = _dequantize_u8(ds.read(5), scales.get("lappos_max", 1.0 / 255.0))
        downface = _dequantize_u8(ds.read(6), scales.get("downface_max", 1.0 / 255.0))
        upface = _dequantize_u8(ds.read(7), scales.get("upface_max", 1.0 / 255.0))
        relief = _dequantize_u8(ds.read(9), scales.get("relief", 1.0 / 255.0))
        coh100 = _dequantize_u8(ds.read(10), scales.get("coh100", 1.0 / 255.0))

    lap_dipole = np.sqrt(np.maximum(0.0, lapneg * lappos)).astype(np.float32)
    updown_asym = np.abs(upface - downface).astype(np.float32)

    def _unpack_dem10(fname: str) -> np.ndarray:
        vec = np.load(dem10_dir / fname)
        arr = np.full(footprint.shape, np.nan, dtype=np.float32)
        arr[footprint] = vec.astype(np.float32, copy=False)
        return arr

    dem10_dir = ext / "dem10"
    d10_slope_max = _unpack_dem10("dem10_slope_max.f32.npy")
    d10_steep_ratio = _unpack_dem10("dem10_steep_ratio_max.f32.npy")
    d10_hgm20 = _unpack_dem10("dem10_hgm20_max.f32.npy")
    d10_hgm50 = _unpack_dem10("dem10_hgm50_max.f32.npy")
    d10_curv = _unpack_dem10("dem10_curv_absmax.f32.npy")
    d10_onesided3 = _unpack_dem10("dem10_onesided3.f32.npy")

    with rasterio.open(ext / "tiger_road_distance_m.tif") as ds:
        road_dist_m = _clean_band(ds.read(1), footprint)

    det_elev = _clean_band(np.asarray(base_feats["det_elev"], dtype=np.float32), footprint)
    depth_base = _clean_band(np.asarray(base_feats["depth_to_base_surf"], dtype=np.float32), footprint)
    road_w = np.clip(road_dist_m / 250.0, 0.15, 1.0).astype(np.float32)
    # Suppress Pleistocene Lake Lahontan highstand shoreline benches (~1,315-1,348 m)
    lahontan_w = (1.0 - 0.50 * np.exp(-0.5 * ((det_elev - 1332.0) / 15.0) ** 2)).astype(np.float32)
    pied_w = (0.55 + 0.45 * np.tanh(np.clip(depth_base, 0.0, 1500.0) / 250.0)).astype(np.float32)
    d10_clean_onesided = _clean_band(d10_onesided3, footprint)
    deconfounded_piedmont = (d10_clean_onesided * road_w * lahontan_w * pied_w).astype(np.float32)

    with rasterio.open(ext / "geodawn_rad_u8.tif") as ds:
        gd_k = _dequantize_u8(ds.read(1), 1.0 / 255.0)
        gd_th = _dequantize_u8(ds.read(2), 1.0 / 255.0)
        gd_u = _dequantize_u8(ds.read(3), 1.0 / 255.0)

    with rasterio.open(ext / "geodawn_extensions_u8.tif") as ds:
        gd_thk = _dequantize_u8(ds.read(1), 1.0 / 255.0)
        tmi_up150 = _dequantize_u8(ds.read(4), 1.0 / 255.0)

    k_clean = _clean_band(gd_k, footprint)
    th_clean = _clean_band(gd_th, footprint)
    thk_clean = _clean_band(gd_thk, footprint)
    k_th_alt = (k_clean / (th_clean + 0.08) - 0.5 * thk_clean).astype(np.float32)

    rtp = _clean_band(np.asarray(base_feats["rtp"], dtype=np.float32), footprint)
    tmi_up150_clean = _clean_band(tmi_up150, footprint)
    mag_shallow_demag = (_robust_z(rtp, footprint) - _robust_z(tmi_up150_clean, footprint)).astype(np.float32)

    grav = _clean_band(np.asarray(base_feats["iso_grav_anom"], dtype=np.float32), footprint)
    gy_g, gx_g = np.gradient(ndi.gaussian_filter(grav, sigma=1.5))
    gy_m, gx_m = np.gradient(ndi.gaussian_filter(rtp, sigma=1.5))
    cross = np.abs(gx_g * gy_m - gy_g * gx_m)
    norm_gm = np.hypot(gx_g, gy_g) * np.hypot(gx_m, gy_m) + 1e-5
    gallardo_meju = ((1.0 - np.clip(cross / norm_gm, 0.0, 1.0)) * np.log1p(norm_gm)).astype(np.float32)

    wellspring_halo = load_gdr_wellspring_grid(ext / "gdr_wellspring_in_footprint.csv", shape)
    vent_halo = load_gdr_vent_grid(ext / "gdr_volcanic_vents_in_footprint.csv", shape)

    with rasterio.open(ext / "derived_gdr_2m_probes_100m_u8.tif") as ds:
        p2m = (ds.read(1) > 0).astype(np.float32)
    probe_halo = np.log1p(
        45.0 * ndi.gaussian_filter(p2m, sigma=5.0) + 180.0 * ndi.gaussian_filter(p2m, sigma=18.0)
    ).astype(np.float32)

    with rasterio.open(ext / "derived_gdr_paleo_100m_u8.tif") as ds:
        paleo = (ds.read(1) > 0).astype(np.float32)
    paleo_halo = np.log1p(
        60.0 * ndi.gaussian_filter(paleo, sigma=5.0) + 220.0 * ndi.gaussian_filter(paleo, sigma=16.0)
    ).astype(np.float32)

    # Multi-scale contextual ridge integrators (EXP-2)
    lidar_valid = np.isfinite(ex_max).astype(np.float32)
    ex_zero = np.where(np.isfinite(ex_max), ex_max * road_w, 0.0).astype(np.float32)
    num_1m = ndi.gaussian_filter(ex_zero, sigma=2.0)
    den_1m = ndi.gaussian_filter(lidar_valid, sigma=2.0)
    scarp_ridge_1m_s2 = np.where(den_1m > 0.25, num_1m / np.maximum(den_1m, 1e-4), np.nan).astype(np.float32)

    d10_hgm20_clean = _clean_band(d10_hgm20, footprint) * road_w
    scarp_ridge_10m_s2 = ndi.gaussian_filter(d10_hgm20_clean, sigma=2.2).astype(np.float32)
    scarp_bg_10m = ndi.gaussian_filter(d10_hgm20_clean, sigma=10.0) + 1e-3
    scarp_piedmont_contrast = ((d10_hgm20_clean - scarp_bg_10m) / scarp_bg_10m * pied_w).astype(np.float32)

    demag_trough = np.maximum(0.0, -mag_shallow_demag)
    demag_along_strike_s3 = (
        ndi.gaussian_filter(demag_trough, sigma=2.8) * ndi.gaussian_filter(_robust_z(k_th_alt, footprint).clip(0, 6), sigma=2.8)
    ).astype(np.float32)

    cond_surf = _clean_band(np.asarray(base_feats["cond_surf"], dtype=np.float32), footprint)
    cond_z = np.clip(_robust_z(cond_surf, footprint), 0.0, 6.0)
    hydro_cond_coupling = ((wellspring_halo + probe_halo + paleo_halo) * (0.4 + 0.6 * cond_z)).astype(np.float32)

    computed: dict[str, np.ndarray] = {
        "lidar_ex_max": ex_max,
        "lidar_ex_mean": ex_mean,
        "lidar_step_max": step_max,
        "lidar_lap_dipole": lap_dipole,
        "lidar_updown_asym": updown_asym,
        "lidar_relief": relief,
        "lidar_coh100": coh100,
        "dem10_slope_max": d10_slope_max,
        "dem10_steep_ratio_max": d10_steep_ratio,
        "dem10_hgm20_max": d10_hgm20,
        "dem10_hgm50_max": d10_hgm50,
        "dem10_curv_absmax": d10_curv,
        "dem10_onesided3": d10_onesided3,
        "dem10_deconfounded_piedmont_scarp": deconfounded_piedmont,
        "geodawn_k": gd_k,
        "geodawn_th": gd_th,
        "geodawn_u": gd_u,
        "geodawn_k_th_alteration": k_th_alt,
        "mag_shallow_demag": mag_shallow_demag,
        "gallardo_meju_parallelism": gallardo_meju,
        "gdr_wellspring_geotherm": wellspring_halo,
        "gdr_2m_probe_halo": probe_halo,
        "gdr_paleo_sinter_halo": paleo_halo,
        "gdr_volcanic_vent_halo": vent_halo,
        "scarp_ridge_1m_s2": scarp_ridge_1m_s2,
        "scarp_ridge_10m_s2": scarp_ridge_10m_s2,
        "scarp_piedmont_contrast": scarp_piedmont_contrast,
        "demag_along_strike_s3": demag_along_strike_s3,
        "hydro_cond_coupling": hydro_cond_coupling,
    }
    assert tuple(computed.keys()) == extra_names
    for name, arr in computed.items():
        np.save(cdir / f"{name}.npy", np.asarray(arr, dtype=np.float32))

    out = dict(base_feats)
    for name in extra_names:
        out[name] = np.load(cdir / f"{name}.npy", mmap_mode="r")
    return out


def compute_relay_tip_modulator(
    visible_faults: np.ndarray,
    footprint: np.ndarray,
    max_boost: float = 0.24,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute bounded [1.0, 1.0 + max_boost] DPHS-H2 relay-breach & tip-lobe modulator.

    Uses ONLY ``visible_faults`` (``fold['visible']`` during spatial holdout CV;
    ``existing_faults`` only at final full-map emission). Distal pixels far from
    ``visible_faults`` receive ``1.0`` (zero distal starvation).

    Returns ``(modulator, dist_to_visible_px)``.
    """
    vis = np.asarray(visible_faults, dtype=bool) & np.asarray(footprint, dtype=bool)
    if not vis.any():
        inf_d = np.full(footprint.shape, np.inf, dtype=np.float32)
        return np.ones(footprint.shape, dtype=np.float32), inf_d

    comp, _ = ndi.label(vis, structure=np.ones((3, 3), dtype=bool))
    d1, (iy, ix) = ndi.distance_transform_edt(~vis, return_indices=True)
    d1 = d1.astype(np.float32, copy=False)
    c1 = comp[iy, ix]

    # 1. Two-component Voronoi medial bridge inside 2.5..26 px stepover/relay gaps
    voronoi_seam = (
        (ndi.maximum_filter(c1, size=3) != ndi.minimum_filter(c1, size=3))
        & footprint
        & (d1 >= 2.5)
        & (d1 <= 26.0)
    )
    relay_bridge = ndi.gaussian_filter(voronoi_seam.astype(np.float32), sigma=3.0)
    relay_bridge = np.clip(relay_bridge * 4.5, 0.0, 1.0) * np.exp(-np.maximum(0.0, d1 - 3.0) / 18.0)

    # 2. Strike-projected fault-tip continuation lobe
    nbr_count = ndi.convolve(vis.astype(np.int8), np.ones((3, 3), dtype=np.int8), mode="constant", cval=0)
    tips = vis & (nbr_count <= 2)
    tip_halo_on_vis = np.clip(ndi.gaussian_filter(tips.astype(np.float32), sigma=2.0) * 6.0, 0.0, 1.0)

    vis_s = ndi.gaussian_filter(vis.astype(np.float32), sigma=2.0)
    gy, gx = np.gradient(vis_s)
    # Normal to fault trace is (gx, gy), so tangent (strike) vector is (-gy, gx)
    tx, ty = -gy, gx
    tnorm2 = tx * tx + ty * ty + 1e-8
    t_cos2 = (tx * tx - ty * ty) / tnorm2
    t_sin2 = (2.0 * tx * ty) / tnorm2

    yy, xx = np.indices(vis.shape, dtype=np.float32)
    dx = xx - ix.astype(np.float32)
    dy = yy - iy.astype(np.float32)
    r2 = dx * dx + dy * dy + 1e-6
    u_cos2 = (dx * dx - dy * dy) / r2
    u_sin2 = (2.0 * dx * dy) / r2

    align = 0.5 * (1.0 + u_cos2 * t_cos2[iy, ix] + u_sin2 * t_sin2[iy, ix])
    tip_lobe = (
        tip_halo_on_vis[iy, ix]
        * np.clip(align, 0.0, 1.0) ** 2
        * np.exp(-np.maximum(0.0, d1 - 2.0) / 16.0)
        * (d1 >= 2.0)
    )

    combined = np.clip(relay_bridge + 0.85 * tip_lobe, 0.0, 1.0)
    mod = (1.0 + float(max_boost) * combined).astype(np.float32, copy=False)
    mod[~footprint] = 1.0
    return mod, d1


def _kernel_offsets(radius: float = 3.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r_int = int(np.ceil(radius))
    ys, xs, ks = [], [], []
    for dy in range(-r_int, r_int + 1):
        for dx in range(-r_int, r_int + 1):
            dist = float(np.hypot(dy, dx))
            w = max(0.0, 1.0 - dist / float(radius))
            if w > 1e-6:
                ys.append(dy)
                xs.append(dx)
                ks.append(w)
    return np.array(ys, dtype=np.int32), np.array(xs, dtype=np.int32), np.array(ks, dtype=np.float32)


def allocate_submodular_300m(
    prob_map: np.ndarray,
    allowed_mask: np.ndarray,
    *,
    max_dots: int = 36500,
    min_sep_px: float = 2.2,
    min_marginal_gain: float = 0.020,
    k_truth: float | None = None,
    candidate_pool: int = 280000,
) -> np.ndarray:
    """Minoux (1978) CELF lazy-greedy 300 m (R=3.0 px) submodular max-cover allocator.

    Maximizes ``sum_u prob_map[u] * max_{s in S} K(||u - s||_2)`` subject to
    ``s in allowed_mask``, ``|S| <= max_dots``, pairwise distance ``>= min_sep_px``
    (default ``2.2 px``, guaranteeing zero touching dots in every 3x3 neighborhood),
    and optional exact DW-Tversky dynamic marginal DTI break-even stopping when
    ``k_truth`` (expected truth pixel count in ``allowed_mask``) is provided.
    """
    p = np.where(np.isfinite(prob_map) & (prob_map > 0), prob_map, 0.0).astype(np.float32)
    allowed = np.asarray(allowed_mask, dtype=bool)
    h, w = p.shape
    out = np.zeros((h, w), dtype=np.float32)
    if max_dots <= 0 or not allowed.any():
        return out

    k_dy, k_dx, k_wt = _kernel_offsets(3.0)
    kern = np.zeros((7, 7), dtype=np.float32)
    for dy, dx, kw in zip(k_dy, k_dx, k_wt):
        kern[dy + 3, dx + 3] = kw
    init_gain = ndi.convolve(p, kern, mode="constant", cval=0.0)
    cand_ys, cand_xs = np.nonzero(allowed & (init_gain > max(min_marginal_gain, 1e-8)))
    if cand_ys.size == 0:
        return out

    gains = init_gain[cand_ys, cand_xs]
    if cand_ys.size > candidate_pool:
        top_idx = np.argpartition(gains, -candidate_pool)[-candidate_pool:]
        cand_ys = cand_ys[top_idx]
        cand_xs = cand_xs[top_idx]
        gains = gains[top_idx]

    sep_r = int(np.floor(min_sep_px))
    b_dy, b_dx = [], []
    for dy in range(-sep_r, sep_r + 1):
        for dx in range(-sep_r, sep_r + 1):
            if dy * dy + dx * dx < min_sep_px * min_sep_px - 1e-6:
                b_dy.append(dy)
                b_dx.append(dx)
    b_dy_a = np.array(b_dy, dtype=np.int32)
    b_dx_a = np.array(b_dx, dtype=np.int32)

    pad = 3
    p_pad = np.pad(p, pad, mode="constant", constant_values=0.0)
    cov_pad = np.zeros_like(p_pad, dtype=np.float32)
    blocked_pad = np.zeros((h + 2 * pad, w + 2 * pad), dtype=bool)

    heap: list[tuple[float, int]] = [(-float(g), int(i)) for i, g in enumerate(gains)]
    heapq.heapify(heap)

    n_placed = 0
    t_acc = 0.0
    fp_acc = 0.0
    use_dti_bar = k_truth is not None and float(k_truth) > 0.0
    k_tr = float(k_truth) if use_dti_bar else 0.0

    cand_ys_p = cand_ys + pad
    cand_xs_p = cand_xs + pad

    while heap and n_placed < max_dots:
        neg_g, idx = heapq.heappop(heap)
        if -neg_g <= min_marginal_gain:
            break
        yp = int(cand_ys_p[idx])
        xp = int(cand_xs_p[idx])
        if blocked_pad[yp, xp]:
            continue

        ys = yp + k_dy
        xs = xp + k_dx
        delta_cov = k_wt - cov_pad[ys, xs]
        pos = delta_cov > 0.0
        exact_gain = float(np.dot(p_pad[ys[pos], xs[pos]], delta_cov[pos])) if pos.any() else 0.0
        if exact_gain <= min_marginal_gain:
            continue

        next_ub = -heap[0][0] if heap else -1.0
        if exact_gain >= next_ub - 1e-7:
            self_q = min(1.0, float(gains[idx]))
            fp_dot = max(0.02, 1.0 - self_q)
            if use_dti_bar and n_placed >= 250:
                denom = 0.8 * k_tr + 0.2 * (t_acc + fp_acc) + 1e-12
                cur_dti = t_acc / denom
                bar = (0.2 * cur_dti / max(1e-6, 1.0 - 0.2 * cur_dti)) * fp_dot
                if exact_gain <= bar:
                    continue
            out[yp - pad, xp - pad] = 1.0
            cov_pad[ys[pos], xs[pos]] = k_wt[pos]
            blocked_pad[yp + b_dy_a, xp + b_dx_a] = True
            t_acc += exact_gain
            fp_acc += fp_dot
            n_placed += 1
        else:
            heapq.heappush(heap, (-exact_gain, idx))

    return out
