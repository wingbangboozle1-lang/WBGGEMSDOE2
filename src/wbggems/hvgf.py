"""Hydrothermal Vent-Guided Structural-Tensor & Relay Submodular Fault Discovery (WBG2-HVGF).

Strict scientific & protocol invariants:
  1. Zero historical submission or registry prediction rasters are read anywhere here.
  2. ``sgmc_faults_100m.tif`` is NEVER added to predictor matrices or training labels;
     it is quarantined strictly for out-of-sample evaluation in ``run_wbg2_hvgf.py``.
  3. Label-derived columns in external point tables (``dist_known_fault_px``, ``known_fault``,
     ``label``) are explicitly blocked and asserted unused.
  4. Visible-only structural relay, bend, tip, and slip-sense features are computed
     strictly from ``visible`` masks inside each holdout fold (never touching withheld truth).
  5. Features are streamed column-by-column into a disk-backed ``float32`` memmap on
     in-footprint pixels so peak RAM remains well below 800 MB on CPU.
"""
from __future__ import annotations

import csv
import io
import json
import struct
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
from scipy import ndimage as ndi

FORBIDDEN_POINT_COLUMNS = frozenset({"dist_known_fault_px", "known_fault", "label"})

TF_BAND_NAMES = [
    "mag_anom",
    "rtp",
    "tmi_hg",
    "geod_2ndinv",
    "iso_grav_anom_slope",
    "tc",
    "geod_shearrate",
    "geod_dilatrate",
    "tmi_vg",
    "deq_n100a15",
    "iso_grav_anom_vg",
    "det_elev",
    "iso_grav_anom",
    "tmi",
    "depth_to_base_surf",
    "ieq_n100a15",
    "cond_surf",
    "iso_grav_anom_hg",
    "det_elev_slope",
]

LIDAR_BAND_NAMES = [
    "lidar_ex_max",
    "lidar_ex_mean",
    "lidar_step_max",
    "lidar_lapneg_max",
    "lidar_lappos_max",
    "lidar_downface_max",
    "lidar_upface_max",
    "lidar_cross_max",
    "lidar_relief",
    "lidar_coh100",
    "lidar_strike",
]

TOPO10_BAND_NAMES = [
    "topo10_slope_p90",
    "topo10_slope_max",
    "topo10_steep_frac",
    "topo10_slope_std",
    "topo10_relief_local",
    "topo10_curv_prof_absmax",
    "topo10_aspect_coherence",
    "topo10_hs_lineament",
    "topo10_dem_mean",
]

CHI_BAND_NAMES = [
    "chi_step_max",
    "chi_step_min",
    "chi_ksn_max",
    "chi_log10_area",
    "chi_zmean_m",
]


def _utm_to_rc(
    xs: list[float] | np.ndarray,
    ys: list[float] | np.ndarray,
    transform: Any,
    shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_arr = np.asarray(xs, dtype=np.float64)
    y_arr = np.asarray(ys, dtype=np.float64)
    cols = np.floor((x_arr - transform.c) / transform.a).astype(np.int64)
    rows = np.floor((y_arr - transform.f) / transform.e).astype(np.int64)
    ok = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    return rows[ok], cols[ok], ok


def _robust_z_fp(arr2d: np.ndarray, fp: np.ndarray) -> np.ndarray:
    vals = arr2d[fp]
    med = float(np.nanmedian(vals[::8]))
    iqr = float(np.nanpercentile(vals[::8], 75) - np.nanpercentile(vals[::8], 25))
    scale = max(iqr / 1.3489795, 1e-6)
    return np.clip((arr2d - med) / scale, -8.0, 8.0).astype(np.float32)


def _grad_mag(arr: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    sm = ndi.gaussian_filter(arr.astype(np.float32), sigma=sigma)
    gy, gx = np.gradient(sm)
    return np.hypot(gy, gx).astype(np.float32)


def _parse_2m_probes_dbf(
    zip_path: Path, transform: Any, shape: tuple[int, int]
) -> tuple[np.ndarray, int]:
    """Read DOE GDR #1391 INGENIOUS 2-meter temperature probes (T2m, F2mDAB)."""
    imp_dab = np.zeros(shape, dtype=np.float32)
    imp_cnt = np.zeros(shape, dtype=np.int32)
    if not zip_path.is_file():
        return imp_dab, 0
    with zipfile.ZipFile(zip_path) as zf:
        dbf_name = next(n for n in zf.namelist() if n.lower().endswith(".dbf"))
        buf = zf.read(dbf_name)
    numrec, lenhdr, lenrec = struct.unpack("<4xIHH20x", buf[:32])
    fields: list[tuple[str, int, int]] = []
    pos = 32
    offset = 1
    while buf[pos] != 0x0D:
        fname = buf[pos : pos + 11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        assert fname not in FORBIDDEN_POINT_COLUMNS, f"Forbidden column: {fname}"
        flen = buf[pos + 16]
        fields.append((fname, offset, flen))
        offset += flen
        pos += 32
    fmap = {name: (off, flen) for name, off, flen in fields}
    lats, lons, dabs = [], [], []
    for i in range(numrec):
        rec = buf[lenhdr + i * lenrec : lenhdr + (i + 1) * lenrec]
        if not rec or rec[0:1] == b"*":
            continue
        try:
            lat = float(rec[fmap["LatDegreeN"][0] : fmap["LatDegreeN"][0] + fmap["LatDegreeN"][1]].strip())
            lon = float(rec[fmap["LongDegree"][0] : fmap["LongDegree"][0] + fmap["LongDegree"][1]].strip())
            dab_s = rec[fmap["F2mDAB"][0] : fmap["F2mDAB"][0] + fmap["F2mDAB"][1]].strip()
            t2m_s = rec[fmap["T2m"][0] : fmap["T2m"][0] + fmap["T2m"][1]].strip()
            dab = float(dab_s) if dab_s else 0.0
            t2m = float(t2m_s) if t2m_s else 0.0
        except ValueError:
            continue
        if not (25.0 <= lat <= 50.0 and -130.0 <= lon <= -100.0):
            continue
        excess = max(0.0, dab) + 0.25 * max(0.0, t2m - 22.0)
        lats.append(lat)
        lons.append(lon)
        dabs.append(excess)
    if lons:
        ux, uy = rio_transform("EPSG:4269", "EPSG:32611", lons, lats)
        rows, cols, ok = _utm_to_rc(ux, uy, transform, shape)
        vals = np.asarray(dabs, dtype=np.float32)[ok]
        np.add.at(imp_cnt, (rows, cols), 1)
        np.maximum.at(imp_dab, (rows, cols), vals)
    return imp_dab, int((imp_cnt > 0).sum())


def load_sense_source_raster(csv_path: Path, transform: Any, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize INGENIOUS slip sense (N=1, RL=2, LL=3) onto 100 m grid.

    Downstream callers MUST mask this array strictly by ``visible`` inside each fold.
    """
    sense_grid = np.zeros(shape, dtype=np.int8)
    code_map = {"N": 1, "RL": 2, "LL": 3}
    if not csv_path.is_file():
        return sense_grid
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_code = code_map.get(row.get("sense", "").strip(), 0)
            if s_code == 0:
                continue
            try:
                x0, y0 = float(row["x0"]), float(row["y0"])
                x1, y1 = float(row["x1"]), float(row["y1"])
            except (KeyError, ValueError):
                continue
            steps = max(2, int(np.hypot(x1 - x0, y1 - y0) / 50.0) + 1)
            xs = np.linspace(x0, x1, steps)
            ys = np.linspace(y0, y1, steps)
            rr, cc, _ = _utm_to_rc(xs, ys, transform, shape)
            if rr.size:
                # Strike-slip codes (2, 3) take precedence at junctions for kinematic mixing
                sense_grid[rr, cc] = np.maximum(sense_grid[rr, cc], s_code)
    return sense_grid


def build_or_load_hvgf_feature_bank(
    cache_dir: Path,
    fp: np.ndarray,
    transform: Any,
    fbank_path: Path,
    ext_dir: Path,
) -> tuple[np.memmap, list[str], dict[str, list[str]], dict[str, Any]]:
    """Build or load the 86-feature label-free HVGF matrix on footprint pixels."""
    shape = fp.shape
    fp_idx = np.flatnonzero(fp)
    n_fp = int(fp_idx.size)
    cache_dir.mkdir(parents=True, exist_ok=True)
    mmap_path = cache_dir / "hvgf_X_fp.mmap"
    meta_path = cache_dir / "hvgf_X_fp.meta.json"
    strike_path = cache_dir / "struct_strike_cos_sin_fp.npz"

    expected_cols = 88
    if mmap_path.is_file() and meta_path.is_file() and strike_path.is_file():
        meta = json.loads(meta_path.read_text())
        if meta.get("n_features") == expected_cols and meta.get("n_footprint_pixels") == n_fp:
            X = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(expected_cols, n_fp))
            return X, meta["feature_names"], meta["feature_groups"], meta["provenance"]

    X = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(expected_cols, n_fp))
    names: list[str] = []
    groups: dict[str, list[str]] = {"ctrl_19b": [], "e1_core_vent": [], "e2_strain_kinematics": []}
    col_ptr = 0

    bad_fp = ~fp
    idx_fp = ndi.distance_transform_edt(bad_fp, return_distances=False, return_indices=True).astype(np.int16)
    idx_cache: list[tuple[np.ndarray, np.ndarray]] = [(bad_fp, idx_fp)]

    def _fast_fill(arr: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
        bad = ~valid_mask
        if not bad.any():
            return arr.astype(np.float32, copy=False)
        found_idx = None
        for prev_bad, prev_idx in idx_cache:
            if np.array_equal(bad, prev_bad):
                found_idx = prev_idx
                break
        if found_idx is None:
            found_idx = ndi.distance_transform_edt(bad, return_distances=False, return_indices=True).astype(np.int16)
            if len(idx_cache) >= 2:
                idx_cache.pop()
            idx_cache.append((bad.copy(), found_idx))
        out = arr.astype(np.float32, copy=True)
        out[bad] = out[found_idx[0][bad], found_idx[1][bad]]
        return out

    def _push(name: str, group: str, arr: np.ndarray, is_fp_1d: bool = False) -> None:
        nonlocal col_ptr
        assert name not in FORBIDDEN_POINT_COLUMNS, f"Forbidden column {name}"
        assert "sgmc" not in name.lower(), f"SGMC banned from predictors: {name}"
        vec = arr if is_fp_1d else arr.ravel()[fp_idx]
        X[col_ptr, :] = vec.astype(np.float32, copy=False)
        names.append(name)
        groups[group].append(name)
        col_ptr += 1
        if col_ptr % 12 == 0:
            X.flush()

    # 1. Official 19-band stack from flattened scratch/fbank/bands.f32
    raw_mm = np.memmap(fbank_path, dtype=np.float32, mode="r", shape=(19, shape[0], shape[1]))
    saved: dict[str, np.ndarray] = {}
    keep_names = {
        "tmi_hg", "tmi_vg", "iso_grav_anom_hg", "iso_grav_anom_vg",
        "depth_to_base_surf", "cond_surf", "det_elev",
        "geod_2ndinv", "geod_shearrate", "geod_dilatrate",
        "deq_n100a15", "ieq_n100a15",
    }
    for i, b_name in enumerate(TF_BAND_NAMES):
        raw = np.asarray(raw_mm[i], dtype=np.float32)
        fin = fp & np.isfinite(raw)
        filled = _fast_fill(raw, fin)
        _push(b_name, "ctrl_19b", filled)
        if b_name in keep_names:
            saved[b_name] = filled

    # Potential-field tilt zero-crossings & depth-persistence worms (H-HVGF-4)
    grav_tilt_zero = np.cos(
        np.arctan2(saved["iso_grav_anom_vg"], np.maximum(np.abs(saved["iso_grav_anom_hg"]), 1e-4))
    ).astype(np.float32)
    mag_tilt_zero = np.cos(
        np.arctan2(saved["tmi_vg"], np.maximum(np.abs(saved["tmi_hg"]), 1e-3))
    ).astype(np.float32)
    grav_worm = (saved["iso_grav_anom_hg"] - ndi.gaussian_filter(saved["iso_grav_anom_hg"], 8.0)).astype(np.float32)
    mag_worm = (saved["tmi_hg"] - ndi.gaussian_filter(saved["tmi_hg"], 8.0)).astype(np.float32)
    base_grad = _grad_mag(saved["depth_to_base_surf"], 1.5)
    base_curv = (saved["depth_to_base_surf"] - ndi.gaussian_filter(saved["depth_to_base_surf"], 8.0)).astype(np.float32)
    cond_grad = _grad_mag(saved["cond_surf"], 1.5)
    det_lrm = (saved["det_elev"] - ndi.gaussian_filter(saved["det_elev"], 6.0)).astype(np.float32)

    _push("grav_tilt_zero_ridge", "e1_core_vent", grav_tilt_zero)
    _push("mag_tilt_zero_ridge", "e1_core_vent", mag_tilt_zero)
    _push("grav_worm_persistence", "e1_core_vent", grav_worm)
    _push("mag_worm_persistence", "e1_core_vent", mag_worm)
    _push("basement_step_grad", "e1_core_vent", base_grad)
    _push("basement_curv_lrm", "e1_core_vent", base_curv)
    _push("clay_cap_cond_grad", "e1_core_vent", cond_grad)
    _push("det_elev_lrm", "e1_core_vent", det_lrm)
    del grav_tilt_zero, mag_tilt_zero, grav_worm, mag_worm, base_curv, cond_grad, det_lrm
    saved.pop("tmi_vg", None)
    saved.pop("iso_grav_anom_vg", None)
    saved.pop("depth_to_base_surf", None)

    # 2. 1 m 3DEP LiDAR scarp polarity & dipoles (native NaN outside LiDAR coverage)
    with rasterio.open(ext_dir / "lidar_scarp_features_u8.tif") as ds:
        has_lidar_fp = ((ds.read(12) > 0) & fp).ravel()[fp_idx]
        _push("lidar_has_coverage", "e1_core_vent", has_lidar_fp.astype(np.float32), is_fp_1d=True)
        l_cache: dict[str, np.ndarray] = {}
        for b_idx, b_name in enumerate(LIDAR_BAND_NAMES, start=1):
            v_fp = ds.read(b_idx).ravel()[fp_idx].astype(np.float32)
            v_fp[~has_lidar_fp] = np.nan
            _push(b_name, "e1_core_vent", v_fp, is_fp_1d=True)
            if b_name in ("lidar_step_max", "lidar_lapneg_max", "lidar_lappos_max", "lidar_upface_max", "lidar_downface_max", "lidar_relief"):
                l_cache[b_name] = v_fp
        dipole = np.sqrt(np.maximum(0.0, l_cache["lidar_lapneg_max"] * l_cache["lidar_lappos_max"]))
        graben_pair = np.sqrt(np.maximum(0.0, l_cache["lidar_upface_max"] * l_cache["lidar_downface_max"]))
        sharpness = l_cache["lidar_step_max"] / (l_cache["lidar_relief"] + 5.0)
        _push("lidar_crest_toe_dipole", "e1_core_vent", dipole, is_fp_1d=True)
        _push("lidar_graben_antithetic_pair", "e1_core_vent", graben_pair, is_fp_1d=True)
        _push("lidar_scarp_sharpness", "e1_core_vent", sharpness, is_fp_1d=True)
        l_cache.clear()

    # 3. Seamless 10 m 3DEP attributes
    topo_curv = None
    topo_hs = None
    with rasterio.open(ext_dir / "topo_10m_derived_100m_u8.tif") as ds:
        for b_idx, b_name in enumerate(TOPO10_BAND_NAMES, start=1):
            q = ds.read(b_idx)
            filled = _fast_fill(q.astype(np.float32), fp & (q > 0))
            _push(b_name, "e1_core_vent", filled)
            if b_name == "topo10_curv_prof_absmax":
                topo_curv = filled
            elif b_name == "topo10_hs_lineament":
                topo_hs = filled
    assert topo_curv is not None and topo_hs is not None
    _push("topo10_hs_dog", "e1_core_vent", topo_hs - ndi.gaussian_filter(topo_hs, 6.0))
    _push("topo10_curv_dog", "e1_core_vent", topo_curv - ndi.gaussian_filter(topo_curv, 6.0))

    # Build multi-physics structural strike unit vector s_hat = (-gy, gx)/|g|
    comp_step = (
        0.45 * _robust_z_fp(saved["iso_grav_anom_hg"], fp)
        + 0.35 * _robust_z_fp(base_grad, fp)
        + 0.20 * _robust_z_fp(topo_curv, fp)
    ).astype(np.float32)
    sm_step = ndi.gaussian_filter(comp_step, 2.5)
    gy_s, gx_s = np.gradient(sm_step)
    gnorm = np.hypot(gx_s, gy_s) + 1e-5
    # Normal vector points across-strike; strike tangent is (-gy_s, gx_s) in (x, y) -> (sy=gx_s, sx=-gy_s)
    sy_unit = (gx_s / gnorm).astype(np.float32)
    sx_unit = (-gy_s / gnorm).astype(np.float32)
    ny_unit = (gy_s / gnorm).astype(np.float32)
    nx_unit = (gx_s / gnorm).astype(np.float32)
    np.savez_compressed(
        strike_path,
        ny_fp=ny_unit.ravel()[fp_idx].astype(np.float16),
        nx_fp=nx_unit.ravel()[fp_idx].astype(np.float16),
    )
    del topo_curv, topo_hs, base_grad, sm_step, gy_s, gx_s, gnorm, ny_unit, nx_unit

    # 4. 10 m Fluvial chi / ksn + Pluvial Lahontan/Bonneville Shoreline Suppression (H-HVGF-3)
    with rasterio.open(ext_dir / "dem10_chi_100m_i16.tif") as ds:
        ksn_arr = None
        z_arr = None
        for b_idx, b_name in enumerate(CHI_BAND_NAMES, start=1):
            arr = _fast_fill(ds.read(b_idx).astype(np.float32), fp)
            _push(b_name, "e1_core_vent", arr)
            if b_name == "chi_ksn_max":
                ksn_arr = arr
            elif b_name == "chi_zmean_m":
                z_arr = arr
    assert ksn_arr is not None and z_arr is not None
    _push("chi_ksn_dog", "e1_core_vent", ksn_arr - ndi.gaussian_filter(ksn_arr, 8.0))
    d_shore = np.minimum(
        np.abs(z_arr - 1332.0),
        np.minimum(np.abs(z_arr - 1463.0), np.abs(z_arr - 1552.0)),
    ).astype(np.float32)
    _push("pluvial_shoreline_elev_dist_m", "e1_core_vent", d_shore)
    _push("zmean_lrm_400m", "e1_core_vent", z_arr - ndi.gaussian_filter(z_arr, 4.0))

    # 5. GeoDAWN Radiometric K/Th/U Alteration & 150 m Upward-Continued Magnetic Demagnetization (H-HVGF-1)
    with rasterio.open(ext_dir / "geodawn_rad_u8.tif") as ds:
        rad_k = None
        for b_idx, b_name in enumerate(["rad_K", "rad_Th", "rad_U", "rad_TC"], start=1):
            q = ds.read(b_idx)
            arr = _fast_fill(q.astype(np.float32), fp & (q > 0))
            _push(b_name, "e1_core_vent", arr)
            if b_name == "rad_K":
                rad_k = arr
    with rasterio.open(ext_dir / "geodawn_extensions_u8.tif") as ds:
        tmi_up = None
        ext_thk = None
        for b_idx, b_name in enumerate(["ext_ThK", "ext_UK", "ext_UTh", "ext_TMI_up150"], start=1):
            q = ds.read(b_idx)
            arr = _fast_fill(q.astype(np.float32), fp & (q > 0))
            _push(b_name, "e1_core_vent", arr)
            if b_name == "ext_TMI_up150":
                tmi_up = arr
            elif b_name == "ext_ThK":
                ext_thk = arr
    assert rad_k is not None and tmi_up is not None and ext_thk is not None
    rad_k_halo = (rad_k - ndi.gaussian_filter(rad_k, 10.0)).astype(np.float32)
    tmi_demag = (ndi.gaussian_filter(tmi_up, 10.0) - tmi_up).astype(np.float32)
    tmi_up_hg = _grad_mag(tmi_up, 2.0)
    mag_up_persist = np.sqrt(
        np.maximum(0.0, np.maximum(0.0, _robust_z_fp(saved["tmi_hg"], fp)) * np.maximum(0.0, _robust_z_fp(tmi_up_hg, fp)))
    ).astype(np.float32)

    # Coupled K-metasomatism * magnetite-destruction * smectite clay-cap alteration composite
    z_k_enrich = np.maximum(0.0, _robust_z_fp(rad_k_halo, fp) - 0.35 * _robust_z_fp(ext_thk, fp))
    z_demag = np.maximum(0.0, _robust_z_fp(tmi_demag, fp))
    z_clay = np.maximum(0.0, _robust_z_fp(saved["cond_surf"], fp))
    coupled_alt = np.cbrt(z_k_enrich * z_demag * z_clay).astype(np.float32)

    _push("rad_K_alteration_halo", "e1_core_vent", rad_k_halo)
    _push("tmi_demagnetization_trough", "e1_core_vent", tmi_demag)
    _push("mag_upward_persistence", "e1_core_vent", mag_up_persist)
    _push("coupled_vent_alteration_index", "e1_core_vent", coupled_alt)
    idx_cache.clear()
    del idx_fp, rad_k, tmi_up, ext_thk, rad_k_halo, tmi_demag, tmi_up_hg, mag_up_persist, z_k_enrich, z_demag, z_clay, coupled_alt
    saved.pop("tmi_hg", None)
    saved.pop("iso_grav_anom_hg", None)
    saved.pop("cond_surf", None)

    # 6. Structurally Guided Anisotropic & Up-Gradient Back-Projected Hydrothermal Plumes (H-HVGF-1)
    imp_therm = np.zeros(shape, dtype=np.float32)
    ws_count = 0
    with (ext_dir / "gdr_wellspring_in_footprint.csv").open(newline="") as f:
        reader = csv.DictReader(f)
        used_ws_cols = ("row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c")
        assert set(used_ws_cols).isdisjoint(FORBIDDEN_POINT_COLUMNS)
        for r in reader:
            rr, cc = int(r["row"]), int(r["col"])
            if not (0 <= rr < shape[0] and 0 <= cc < shape[1]):
                continue
            vals_t = []
            for k_col, base_t in (
                ("temp_c", 20.0),
                ("geothermquartz_c", 70.0),
                ("geothermchalc_c", 60.0),
                ("geothermcat_c", 75.0),
            ):
                s_val = r.get(k_col, "")
                if s_val and s_val != "nan":
                    try:
                        vals_t.append(max(0.0, float(s_val) - base_t))
                    except ValueError:
                        pass
            if vals_t:
                sc = float(np.log1p(max(vals_t)))
                if sc > imp_therm[rr, cc]:
                    imp_therm[rr, cc] = sc
                ws_count += 1

    imp_dab, probe_cells = _parse_2m_probes_dbf(
        ext_dir / "2m_temperature_probe_INGENIOUS_regional_data.zip", transform, shape
    )
    imp_probe = np.log1p(imp_dab).astype(np.float32)

    imp_paleo = np.zeros(shape, dtype=np.float32)
    paleo_count = 0
    with zipfile.ZipFile(ext_dir / "paleo_geothermal_regional.zip") as zf:
        cname = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        with io.TextIOWrapper(zf.open(cname), encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            lons, lats = [], []
            for r in reader:
                try:
                    lons.append(float(r["Long_deg_NAD83"]))
                    lats.append(float(r["Lat_deg_NAD83"]))
                except (KeyError, ValueError):
                    continue
    if lons:
        ux, uy = rio_transform("EPSG:4269", "EPSG:32611", lons, lats)
        rr, cc, _ = _utm_to_rc(ux, uy, transform, shape)
        imp_paleo[rr, cc] = 1.0
        paleo_count = int(rr.size)

    imp_vent = np.zeros(shape, dtype=np.float32)
    vent_count = 0
    with (ext_dir / "gdr_volcanic_vents_in_footprint.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            rr, cc = int(r["row"]), int(r["col"])
            if 0 <= rr < shape[0] and 0 <= cc < shape[1]:
                imp_vent[rr, cc] = 1.0
                vent_count += 1

    # Hydraulic up-gradient back-projection (shifts distal down-fan thermal plumes up-slope onto piedmont conduits)
    det_sm = ndi.gaussian_filter(saved["det_elev"], 4.0)
    ug_y, ug_x = np.gradient(det_sm)
    ug_norm = np.hypot(ug_x, ug_y) + 0.5
    uy_up = (ug_y / ug_norm).astype(np.float32)
    ux_up = (ug_x / ug_norm).astype(np.float32)

    comb_fluid = (imp_therm + 0.85 * imp_probe + 1.25 * imp_paleo).astype(np.float32)
    pts_y, pts_x = np.nonzero(comb_fluid > 0)
    pts_w = comb_fluid[pts_y, pts_x]
    upgrad_imp = np.zeros(shape, dtype=np.float32)
    for shift_px, decay in ((0.0, 0.55), (8.0, 1.00), (18.0, 0.80)):
        ry = np.clip(np.round(pts_y + shift_px * uy_up[pts_y, pts_x]).astype(np.int64), 0, shape[0] - 1)
        rx = np.clip(np.round(pts_x + shift_px * ux_up[pts_y, pts_x]).astype(np.int64), 0, shape[1] - 1)
        np.maximum.at(upgrad_imp, (ry, rx), (decay * pts_w).astype(np.float32))
    hydro_upgradient = ndi.gaussian_filter(upgrad_imp, 3.8).astype(np.float32)

    # Strike-aligned anisotropic hydrothermal conduit propagation along +/- s_hat(x)
    aniso_imp = np.zeros(shape, dtype=np.float32)
    uy_src, ux_src = np.nonzero(upgrad_imp > 0)
    uw_src = upgrad_imp[uy_src, ux_src]
    for step_px in (0.0, 4.0, 8.0, 13.0, 18.0):
        w_s = float(np.exp(-0.5 * (step_px / 11.0) ** 2))
        for sgn in (-1.0, 1.0) if step_px > 0 else (1.0,):
            ry = np.clip(np.round(uy_src + sgn * step_px * sy_unit[uy_src, ux_src]).astype(np.int64), 0, shape[0] - 1)
            rx = np.clip(np.round(ux_src + sgn * step_px * sx_unit[uy_src, ux_src]).astype(np.int64), 0, shape[1] - 1)
            np.maximum.at(aniso_imp, (ry, rx), (w_s * uw_src).astype(np.float32))
    step_gate = np.clip(0.5 + 0.25 * comp_step, 0.1, 1.5).astype(np.float32)
    hydro_strike_aniso = (ndi.gaussian_filter(aniso_imp, 2.4) * step_gate).astype(np.float32)

    _push("gdr_thermal_upflow_s5", "e1_core_vent", ndi.gaussian_filter(imp_therm, 5.0))
    _push("gdr_thermal_upflow_s15", "e1_core_vent", ndi.gaussian_filter(imp_therm, 15.0))
    _push("probe2m_dab_s5", "e1_core_vent", ndi.gaussian_filter(imp_probe, 5.0))
    _push("probe2m_dab_s14", "e1_core_vent", ndi.gaussian_filter(imp_probe, 14.0))
    _push("paleo_sinter_tufa_s6", "e1_core_vent", ndi.gaussian_filter(imp_paleo, 6.0))
    _push("paleo_sinter_tufa_s18", "e1_core_vent", ndi.gaussian_filter(imp_paleo, 18.0))
    _push("quaternary_volcanic_vent_s16", "e1_core_vent", ndi.gaussian_filter(imp_vent, 16.0))
    _push("hydro_upgradient_vent_source", "e1_core_vent", hydro_upgradient)
    _push("hydro_strike_aniso_plume", "e1_core_vent", hydro_strike_aniso)

    # 7. Experiment E2: Mohr-Coulomb Geodetic Principal-Strain & Microseismic Coupling (H-HVGF-2)
    transtens = (
        saved["geod_dilatrate"] * saved["geod_shearrate"] / (np.abs(saved["geod_2ndinv"]) + 1.0)
    ).astype(np.float32)
    dilat_ratio = (saved["geod_dilatrate"] / (np.abs(saved["geod_shearrate"]) + 1.0)).astype(np.float32)
    # Proximity to declustered & raw seismicity (bands 10 & 16 are distance-like metrics in m/km)
    seis_deq_prox = (-_robust_z_fp(saved["deq_n100a15"], fp)).astype(np.float32)
    seis_ieq_prox = (-_robust_z_fp(saved["ieq_n100a15"], fp)).astype(np.float32)
    seis_strain_eff = (
        np.maximum(0.0, seis_deq_prox) * np.maximum(0.0, _robust_z_fp(saved["geod_2ndinv"], fp))
    ).astype(np.float32)
    # Fault-strike axial orientation cos(2*theta), sin(2*theta) coupled with shear/dilatation regime
    cos2_strike = (sx_unit * sx_unit - sy_unit * sy_unit).astype(np.float32)
    sin2_strike = (2.0 * sx_unit * sy_unit).astype(np.float32)
    strike_strain_obliq = (
        cos2_strike * _robust_z_fp(saved["geod_dilatrate"], fp)
        - sin2_strike * _robust_z_fp(saved["geod_shearrate"], fp)
    ).astype(np.float32)

    _push("transtensional_partition_index", "e2_strain_kinematics", transtens)
    _push("dilatational_strain_ratio", "e2_strain_kinematics", dilat_ratio)
    _push("seis_declustered_proximity", "e2_strain_kinematics", seis_deq_prox)
    _push("seis_swarm_proximity", "e2_strain_kinematics", seis_ieq_prox)
    _push("seismic_strain_coupling", "e2_strain_kinematics", seis_strain_eff)
    _push("strike_strain_obliquity", "e2_strain_kinematics", strike_strain_obliq)

    assert col_ptr == expected_cols, f"Expected {expected_cols} columns, wrote {col_ptr}"
    X.flush()
    provenance = {
        "n_footprint_pixels": n_fp,
        "n_features": expected_cols,
        "forbidden_columns_blocked": sorted(FORBIDDEN_POINT_COLUMNS),
        "sgmc_in_feature_matrix": False,
        "historical_predictions_in_feature_matrix": False,
        "point_records_ingested": {
            "gdr_wellspring_records": ws_count,
            "probe_2m_cells": probe_cells,
            "paleo_sinter_travertine_tufa_records": paleo_count,
            "quaternary_volcanic_vents": vent_count,
        },
    }
    meta_path.write_text(
        json.dumps(
            {
                "n_features": expected_cols,
                "n_footprint_pixels": n_fp,
                "feature_names": names,
                "feature_groups": groups,
                "provenance": provenance,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return X, names, groups, provenance


def compute_visible_relay_mechanics(
    visible_mask: np.ndarray,
    sense_src: np.ndarray,
    fp: np.ndarray,
    rba_mod: Any,
    cache_path: Path | None = None,
) -> dict[str, np.ndarray]:
    """Compute strictly fold-safe two-host relay (C1!=C2), tip stress lobes, and slip-sense transitions.

    Uses ONLY ``visible_mask`` (never withheld truth). Suppressed inside ``d_vis <= 2.8 px``
    so near-catalogue collars are never artificially inflated.
    """
    if cache_path is not None and cache_path.is_file():
        d = np.load(cache_path)
        return {k: d[k] for k in d.files}

    vis = np.asarray(visible_mask, dtype=bool) & fp
    shape = vis.shape
    if not vis.any():
        z = np.zeros(shape, dtype=np.float32)
        return {"two_host_relay": z, "tip_stress_lobe": z, "bend_kinematic_transfer": z}

    th = rba_mod.two_host_frame(vis)
    d1 = th["d1"].astype(np.float32)
    d2 = th["d2"].astype(np.float32)
    del th

    # Inter-strand relay corridor between TWO DISTINCT visible fault components (C1 != C2):
    # peaks when a pixel bridges two distinct strands at 3..24 px separation with balanced d1, d2.
    # No artificial zeroing on d1==0: the 2.8 px off-catalogue collar is applied strictly at allocation.
    bridge_span = d1 + d2
    balance = 1.0 - np.abs(d1 - d2) / (bridge_span + 2.0)
    two_host_relay = (
        np.exp(-0.5 * ((bridge_span - 13.0) / 9.5) ** 2)
        * np.clip(balance, 0.0, 1.0)
    ).astype(np.float32)

    # Crack-tip outward strike-propagation lobes from major visible segments (>= 8 px)
    comp, _ = ndi.label(vis, structure=np.ones((3, 3), dtype=int))
    sizes = np.bincount(comp.ravel())
    major = vis & (sizes[comp] >= 8)
    nb = ndi.convolve(major.astype(np.uint8), np.ones((3, 3), dtype=np.uint8), mode="constant", cval=0)
    tips = major & ((nb == 2) | (nb == 3))
    sm = ndi.gaussian_filter(major.astype(np.float32), sigma=2.5)
    gy, gx = np.gradient(sm)
    norm = np.hypot(gx, gy) + 1e-6
    tx, ty = -gx / norm, gy / norm
    ty_idx, tx_idx = np.nonzero(tips)
    lobe = np.zeros(shape, dtype=np.float32)
    for step in (3.0, 6.5, 10.5, 15.0, 20.0):
        w = float(np.exp(-0.5 * (step / 11.5) ** 2))
        for sgn in (-1.0, 1.0):
            ry = np.clip(np.round(ty_idx + sgn * step * ty[ty_idx, tx_idx]).astype(np.int64), 0, shape[0] - 1)
            rx = np.clip(np.round(tx_idx + sgn * step * tx[ty_idx, tx_idx]).astype(np.int64), 0, shape[1] - 1)
            np.maximum.at(lobe, (ry, rx), w)
    tip_stress_lobe = ndi.gaussian_filter(lobe, sigma=2.5).astype(np.float32)

    # Releasing/restraining bend curvature + RL/LL vs N kinematic domain transition
    bend = rba_mod.host_bend_fields(vis, fine_px=3.0, coarse_px=9.0)
    turn_halo = ndi.gaussian_filter(np.where(vis, bend["turn"], 0.0).astype(np.float32), sigma=7.0)
    del bend
    kin_trans = rba_mod.kinematic_transition_field(vis, sense_src, smooth_px=15.0)
    bend_kin = (0.6 * kin_trans + 0.4 * np.clip(turn_halo * 12.0, 0.0, 1.0)).astype(np.float32)

    out = {
        "two_host_relay": two_host_relay,
        "tip_stress_lobe": tip_stress_lobe,
        "bend_kinematic_transfer": bend_kin,
    }
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache_path, **out)
    return out


def non_touching_ridge_candidates(
    score_2d: np.ndarray,
    allowed_2d: np.ndarray,
    ny_2d: np.ndarray,
    nx_2d: np.ndarray,
    min_dist_px: float = 2.3,
    top_pool: int = 900_000,
) -> tuple[np.ndarray, np.ndarray]:
    """Sharpen continuous probability along structural crests & select non-touching candidates.

    Guarantees ``touching == 0`` (minimum center-to-center Euclidean spacing > sqrt(2) px,
    default >= 2.3 px = 230 m) before calling unmodified ``gems57.emit.greedy_allocate``,
    eliminating 300 m kernel self-redundancy while preserving crisp fault-strand geometry.
    """
    h, w = score_2d.shape
    ys, xs = np.nonzero(allowed_2d & (score_2d > 0))
    if ys.size == 0:
        return score_2d.astype(np.float32), np.zeros_like(allowed_2d, dtype=bool)

    # Cross-strike crest boost: compare pixel score against +/- 2 px across structural normal
    ny_v = ny_2d[ys, xs]
    nx_v = nx_2d[ys, xs]
    y_p = np.clip(np.round(ys + 2.0 * ny_v).astype(np.int64), 0, h - 1)
    x_p = np.clip(np.round(xs + 2.0 * nx_v).astype(np.int64), 0, w - 1)
    y_m = np.clip(np.round(ys - 2.0 * ny_v).astype(np.int64), 0, h - 1)
    x_m = np.clip(np.round(xs - 2.0 * nx_v).astype(np.int64), 0, w - 1)

    s0 = score_2d[ys, xs]
    flank = 0.5 * (score_2d[y_p, x_p] + score_2d[y_m, x_m])
    crest_ratio = np.clip((s0 - 0.75 * flank) / (s0 + 1e-6), 0.0, 1.0)
    sharpened = np.zeros_like(score_2d, dtype=np.float32)
    sharpened[ys, xs] = (s0 * (0.72 + 0.56 * crest_ratio)).astype(np.float32)

    # Pre-thin candidate pool with exact Euclidean disk exclusion (r = min_dist_px >= 2.3 -> zero 3x3 touching!)
    vals = sharpened[ys, xs]
    order = np.argsort(-vals, kind="stable")
    if order.size > top_pool:
        order = order[:top_pool]
    ys_ord = ys[order]
    xs_ord = xs[order]

    r_int = int(np.floor(min_dist_px))
    dy_off, dx_off = np.mgrid[-r_int : r_int + 1, -r_int : r_int + 1]
    disk_mask = (dy_off * dy_off + dx_off * dx_off) <= (min_dist_px * min_dist_px)
    dy_k = dy_off[disk_mask]
    dx_k = dx_off[disk_mask]

    blocked = np.zeros((h, w), dtype=bool)
    cand_mask = np.zeros((h, w), dtype=bool)
    for y_i, x_i in zip(ys_ord.tolist(), xs_ord.tolist()):
        if blocked[y_i, x_i]:
            continue
        cand_mask[y_i, x_i] = True
        by = y_i + dy_k
        bx = x_i + dx_k
        ok = (by >= 0) & (by < h) & (bx >= 0) & (bx < w)
        blocked[by[ok], bx[ok]] = True

    return sharpened, cand_mask
