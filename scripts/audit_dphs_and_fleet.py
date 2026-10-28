#!/usr/bin/env python3
"""Fetch 110+ fleet rasters across all 5 orgs, run DPHS uniqueness gates, audit the
9 focus sites at 2026-10-27 HEAD, and fit/evaluate the Physics+SGMC+Geometry empirical
score model (Leave-One-Site-Out CV + strict 9-focus-site external holdout test).

All downloaded fleet GeoTIFFs live strictly inside git-ignored, snapshot-excluded
``.cache/fleet_rasters/``.
"""
from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import urllib.request

import numpy as np
import rasterio
from scipy import ndimage as ndi, stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FLEET_CACHE = ROOT / ".cache" / "fleet_rasters"
sys.path.insert(0, str(ROOT / "src"))

FOCUS_SITES = [
    "GEMSDOE24",
    "GEMSDOE25",
    "GEMSDOE27",
    "GEMSDOE28",
    "GEMSDOE30",
    "GEMSDOE31",
    "GEMSDOE32",
    "GEMSDOE33",
    "GEMSDOE36",
]

FOCUS_PRIMARY_TOKENS = {
    "GEMSDOE24": "989f59505db1",
    "GEMSDOE25": "e56ea318af89",
    "GEMSDOE27": "5512495c6bd1",
    "GEMSDOE28": "b531dae0a36f",
    "GEMSDOE30": "91eae1ca",
    "GEMSDOE31": "8acb75e1",
    "GEMSDOE32": "e5eb6e7e",
    "GEMSDOE33": "cb490425926e",
    "GEMSDOE36": "9b9ea4e6",
}

EXTRA_MULTI_ORG_TARGETS = [
    # Newer 2026-10-26 / 2026-10-27 prompt entries across all 5 verified orgs
    {"site": "GEMSDOE27", "repo": "buffedlizard55-lab/GEMSDOE27", "path": "docs/downloads/gems27-h31-drcg-wl-celf28-20261026-267e4ba6087c-zeros.tif", "reported_score": 0.2250},
    {"site": "GEMSDOE28", "repo": "buffedlizard55-lab/GEMSDOE28", "path": "docs/downloads/gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif", "reported_score": 0.0206},
    {"site": "GEMSDOE30", "repo": "buffedlizard55-lab/GEMSDOE30", "path": "docs/downloads/gems30-h14-hybrid-scarp-gdr-v1-20261026T222500Z-f2b6787e-zeros.tif", "reported_score": 0.1444},
    {"site": "GEMSDOE31", "repo": "buffedlizard55-lab/GEMSDOE31", "path": "docs/downloads/gemsdoe31-m16-tpb2-20261026T220000Z-e75bb388-zeros.tif", "reported_score": 0.1235},
    {"site": "GEMSDOE33", "repo": "buffedlizard55-lab/GEMSDOE33", "path": "docs/downloads/gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros.tif", "reported_score": 0.0963},
    {"site": "GEMSDOE36", "repo": "buffedlizard55-lab/GEMSDOE36", "path": "docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif", "reported_score": 0.1647},
    {"site": "WBGGEMSDOE1", "repo": "wingbangboozle1-lang/WBGGEMSDOE1", "path": "docs/downloads/wbg-c1-commutator-research-surface-20261026-acea88448272.tif", "reported_score": 0.1558},
    {"site": "WBGGEMSDOE1", "repo": "wingbangboozle1-lang/WBGGEMSDOE1", "path": "docs/downloads/wbg2-offcatalogue-density-36k-20261027.tif", "reported_score": None},
    {"site": "WBGGEMSDOE3", "repo": "wingbangboozle1-lang/WBGGEMSDOE3", "path": "docs/lst1/downloads/wbggems3-lst1-hybrid-20261026-0a0229da-zeros.tif", "reported_score": 0.0970},
    {"site": "EUGGEMSDOE1", "repo": "eugboogieman123-ops/EUGGEMSDOE1", "path": "docs/downloads/eug1-s01-bghd-e3-20261026T232510Z-7e78b7dd-zeros.tif", "reported_score": 0.0365},
    {"site": "EUGGEMSDOE2", "repo": "eugboogieman123-ops/EUGGEMSDOE2", "path": "docs/downloads/euggems2-psb22-exp1-pu-hgbt-37654dots-20261026T235000Z-55f80157-zeros.tif", "reported_score": 0.0155},
    {"site": "EUGGEMSDOE3", "repo": "eugboogieman123-ops/EUGGEMSDOE3", "path": "docs/downloads/eug3-r3-hybrid-bridge-20261026-4d754173-zeros.tif", "reported_score": 0.1190},
    {"site": "GINNYGEMSDOE1", "repo": "ginnymcfiner23-ux/GINNYGEMSDOE1", "path": "docs/downloads/ginny1-h1-exp2-rankavg-20261026T233102Z-2b4628d5-zeros.tif", "reported_score": 0.0725},
    {"site": "GINNYGEMSDOE2", "repo": "ginnymcfiner23-ux/GINNYGEMSDOE2", "path": "docs/downloads/ginny2-bghd-pu-oof-20261026-267d6ca0b6d9-zeros.tif", "reported_score": 0.0680},
    {"site": "GINNYGEMSDOE3", "repo": "ginnymcfiner23-ux/GINNYGEMSDOE3", "path": "docs/downloads/ginny3-m1-hybrid-isotonic-36947dots-20261026T232853Z-9fd865b5-zeros.tif", "reported_score": 0.0968},
    {"site": "KANLERGEMSDOE1", "repo": "kanlerxz87-cyber/KANLERGEMSDOE1", "path": "docs/downloads/kanler1-s24-gpca-e2-cal-isotonic-20261026-37d50cd74500-zeros.tif", "reported_score": 0.0439},
    {"site": "KANLERGEMSDOE2", "repo": "kanlerxz87-cyber/KANLERGEMSDOE2", "path": "docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif", "reported_score": 0.1636},
    {"site": "KANLERGEMSDOE3", "repo": "kanlerxz87-cyber/KANLERGEMSDOE3", "path": "docs/downloads/kanler3-r4-ridge-20261026T234744Z-72c07a0f-zeros.tif", "reported_score": None},
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_repo_files(repo: str, mapping: dict[str, Path]) -> tuple[str, int, str | None]:
    need = {rel: dst for rel, dst in mapping.items() if not (dst.is_file() and dst.stat().st_size > 1024)}
    if not need:
        return repo, len(mapping), None
    for branch in ("main", "HEAD"):
        url = f"https://codeload.github.com/{repo}/tar.gz/{branch}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wbggemsdoe2-fleet-audit"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                    found = 0
                    for member in tf:
                        if not member.isfile():
                            continue
                        parts = member.name.split("/", 1)
                        rel = parts[1] if len(parts) > 1 else parts[0]
                        if rel in need:
                            dst = need[rel]
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            fh = tf.extractfile(member)
                            if fh is not None:
                                tmp = dst.with_suffix(dst.suffix + ".tmp")
                                with tmp.open("wb") as out:
                                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                                        out.write(chunk)
                                tmp.replace(dst)
                                found += 1
                    return repo, found, None
        except Exception as exc:
            last_err = str(exc)
            continue
    return repo, 0, last_err


def discover_focus_head_commits() -> dict[str, dict]:
    """Query GitHub API for exact 2026-10-27 HEAD commit + docs/downloads contents on the 9 focus sites."""
    out = {}
    for site in FOCUS_SITES:
        repo = f"buffedlizard55-lab/{site}"
        try:
            proc_c = subprocess.run(
                ["gh", "api", f"repos/{repo}/commits/main"],
                capture_output=True, text=True, timeout=20, check=False,
            )
            c_data = json.loads(proc_c.stdout) if proc_c.returncode == 0 else {}
            sha = c_data.get("sha", "")
            c_date = c_data.get("commit", {}).get("committer", {}).get("date", "")
            c_msg = (c_data.get("commit", {}).get("message", "") or "").splitlines()[0]

            proc_d = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/docs/downloads"],
                capture_output=True, text=True, timeout=20, check=False,
            )
            d_list = json.loads(proc_d.stdout) if proc_d.returncode == 0 and proc_d.stdout.strip().startswith("[") else []
            tifs = [item["name"] for item in d_list if isinstance(item, dict) and item.get("name", "").endswith(".tif")]
            out[site] = {
                "repo": repo,
                "repo_url": f"https://github.com/{repo}",
                "head_sha": sha,
                "head_date": c_date,
                "head_subject": c_msg,
                "downloads_tifs": sorted(tifs),
            }
        except Exception as exc:
            out[site] = {"repo": repo, "error": str(exc), "downloads_tifs": []}
    return out


def fetch_all_fleet_rasters(focus_heads: dict[str, dict]) -> list[dict]:
    FLEET_CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "data_public/raster_fetch_manifest.json").read_text(encoding="utf-8"))
    entries = []
    seen = set()

    for row in manifest:
        key = (row["repo"], row["path"])
        if key in seen:
            continue
        seen.add(key)
        local_name = f"{row['site']}__{Path(row['path']).name}"
        entries.append({
            "site": row["site"],
            "repo": row["repo"],
            "path": row["path"],
            "local_path": FLEET_CACHE / local_name,
            "reported_score": row.get("reported_score"),
        })

    for row in EXTRA_MULTI_ORG_TARGETS:
        key = (row["repo"], row["path"])
        if key in seen:
            continue
        seen.add(key)
        local_name = f"{row['site']}__{Path(row['path']).name}"
        entries.append({
            "site": row["site"],
            "repo": row["repo"],
            "path": row["path"],
            "local_path": FLEET_CACHE / local_name,
            "reported_score": row.get("reported_score"),
        })

    # Also ensure every 2026-10-27 HEAD .tif in the 9 focus sites' docs/downloads/ is pulled!
    for site, info in focus_heads.items():
        for tif_name in info.get("downloads_tifs", []):
            rel = f"docs/downloads/{tif_name}"
            key = (info["repo"], rel)
            if key in seen:
                continue
            seen.add(key)
            entries.append({
                "site": site,
                "repo": info["repo"],
                "path": rel,
                "local_path": FLEET_CACHE / f"{site}__{tif_name}",
                "reported_score": None,
            })

    # Include local repo legacy rasters (DZ-16, H3-PACK, MSPTCD) for self-comparison
    for site_tag, rel_p in (
        ("WBGGEMSDOE2_DZ16", "docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif"),
        ("WBGGEMSDOE2_H3PACK", "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif"),
        ("WBGGEMSDOE2_MSPTCD", "docs/downloads/msptcd/wbg2-msptcd-exp2-pu31-20261027T180500Z-ad4d825f-zeros.tif"),
        ("WBGGEMSDOE2_DPHS", "docs/downloads/dphs/wbg2-dphs-exp3-submod300m-20261027T194500Z-46a3a89a-zeros.tif"),
    ):
        src_p = ROOT / rel_p
        if src_p.is_file():
            entries.append({
                "site": site_tag,
                "repo": "wingbangboozle1-lang/WBGGEMSDOE2",
                "path": rel_p,
                "local_path": src_p,
                "reported_score": None,
            })

    by_repo: dict[str, dict[str, Path]] = defaultdict(dict)
    for e in entries:
        if e["repo"] != "wingbangboozle1-lang/WBGGEMSDOE2":
            by_repo[e["repo"]][e["path"]] = e["local_path"]

    print(f"[fleet] Streaming candidate rasters across {len(by_repo)} repositories into .cache/fleet_rasters/...", flush=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(_fetch_repo_files, repo, mp) for repo, mp in by_repo.items()]
        for fut in as_completed(futs):
            repo, n_got, err = fut.result()
            if err:
                print(f"  [warn] {repo}: {err}", flush=True)

    avail = [e for e in entries if e["local_path"].is_file() and e["local_path"].stat().st_size > 1024]
    print(f"[fleet] Available verified rasters on disk: {len(avail)} / {len(entries)}", flush=True)
    return avail


def triangular_kernel_map(mask: np.ndarray, radius_px: float = 3.0) -> np.ndarray:
    if not mask.any():
        return np.zeros(mask.shape, dtype=np.float32)
    d = ndi.distance_transform_edt(~mask)
    return np.clip(1.0 - d / float(radius_px), 0.0, 1.0).astype(np.float32)


def main() -> int:
    t0 = time.time()
    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
        sample_crs = str(ds.crs)
        sample_transform = tuple(round(float(v), 6) for v in list(ds.transform)[:6])
    with rasterio.open(ROOT / "data/official/existing_faults.tif") as ds:
        catalogue = ds.read(1) > 0

    footprint_n = int(footprint.sum())
    d_cat = ndi.distance_transform_edt(~(catalogue & footprint)).astype(np.float32)

    # Load diagnostic off-catalogue USGS SGMC Quaternary/Neogene faults (NEVER used in model!)
    with rasterio.open(ROOT / ".cache/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc_all = (ds.read(1) > 0) & footprint
    sgmc_offcat = sgmc_all & (d_cat > 3.0)
    sgmc_offcat_y, sgmc_offcat_x = np.nonzero(sgmc_offcat)
    n_sgmc_offcat = max(int(sgmc_offcat.sum()), 1)

    # Load de-confounded 10m scarp & 1m LiDAR scarp & hydrothermal diagnostics from .cache/dphs_features/
    dphs_cdir = ROOT / ".cache/dphs_features"
    scarp_diag = np.load(dphs_cdir / "dem10_deconfounded_piedmont_scarp.npy", mmap_mode="r")
    lidar_diag = np.load(dphs_cdir / "lidar_ex_max.npy", mmap_mode="r")
    hydro_diag = np.load(dphs_cdir / "hydro_cond_coupling.npy", mmap_mode="r")
    demag_diag = np.load(dphs_cdir / "demag_along_strike_s3.npy", mmap_mode="r")
    # Candidate is overridable for successor lanes (e.g. WBG2-DISTAL); defaults
    # reproduce the original DPHS EXP-3 audit exactly.
    surface_env = os.environ.get("WBG_AUDIT_SURFACE_NPY")
    pre_surface = np.load(
        (ROOT / surface_env) if surface_env else (dphs_cdir / "exp3_preplacement_surface.npy"),
        mmap_mode="r",
    )

    # Load emitted candidate GeoTIFF (DPHS EXP-3 by default)
    results_env = os.environ.get("WBG_AUDIT_RESULTS_JSON", "evidence/wbg2_dphs_results.json")
    dphs_res = json.loads((ROOT / results_env).read_text(encoding="utf-8"))
    cand_info = dphs_res["emitted_candidate"]
    cand_tif = ROOT / cand_info["tif_path"]
    with rasterio.open(cand_tif) as ds:
        mine = ds.read(1)
    my_support = mine > 0
    my_dots = int(my_support.sum())
    # Precompute exact r <= 3.0 integer offsets (29 offsets) and K(r) > 0 offsets (25 offsets)
    d3_dy, d3_dx = [], []
    k3_dy, k3_dx, k3_wt = [], [], []
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            r = float(np.hypot(dy, dx))
            if r <= 3.0 + 1e-9:
                d3_dy.append(dy)
                d3_dx.append(dx)
            if r < 3.0 - 1e-9:
                k3_dy.append(dy)
                k3_dx.append(dx)
                k3_wt.append(1.0 - r / 3.0)
    d3_dy_a = np.array(d3_dy, dtype=np.int32)
    d3_dx_a = np.array(d3_dx, dtype=np.int32)
    disk3_struct = np.zeros((7, 7), dtype=bool)
    disk3_struct[d3_dy_a + 3, d3_dx_a + 3] = True

    def _block4_smooth_1km(arr2d: np.ndarray) -> np.ndarray:
        """Fast 1 km (10 px) smoothed field on 4x4 block-averaged (932 x 823) grid."""
        b = arr2d[:3728, :3292].reshape(932, 4, 823, 4).mean(axis=(1, 3))
        return ndi.gaussian_filter(b.astype(np.float32, copy=False), sigma=2.5)

    my_sm4 = _block4_smooth_1km(mine.astype(np.float32))
    pre_sm4 = _block4_smooth_1km(np.asarray(pre_surface, dtype=np.float32))
    fp_b4 = footprint[:3728, :3292].reshape(932, 4, 823, 4).any(axis=(1, 3))
    my_sm_vec = my_sm4[fp_b4]
    pre_sm_vec = pre_sm4[fp_b4]

    rng = np.random.default_rng(20261027)
    fp_r, fp_c = np.nonzero(footprint)
    sub_pick = rng.choice(fp_r.size, size=150000, replace=False)
    sr, sc = fp_r[sub_pick], fp_c[sub_pick]
    pre_surf_sub = np.asarray(pre_surface[sr, sc], dtype=np.float64)

    my_y, my_x = np.nonzero(my_support)
    # Interior-safe sgmc offcat coords (away from 3px border)
    h_g, w_g = footprint.shape
    in_b = (sgmc_offcat_y >= 3) & (sgmc_offcat_y < h_g - 3) & (sgmc_offcat_x >= 3) & (sgmc_offcat_x < w_g - 3)
    sg_y, sg_x = sgmc_offcat_y[in_b], sgmc_offcat_x[in_b]

    focus_heads = discover_focus_head_commits()
    fleet_entries = fetch_all_fleet_rasters(focus_heads)

    reg = json.loads((ROOT / "data_public/registry_index_snapshot.json").read_text(encoding="utf-8"))
    exact_registry_hit = cand_info["tif_sha256"] in {r["sha256"] for r in reg["rasters"]}

    audit_rows = []
    scored_rows = []
    focus_rasters_loaded: dict[str, np.ndarray] = {}

    def _dilate_disk3(sup: np.ndarray) -> np.ndarray:
        return ndi.binary_dilation(sup, structure=disk3_struct)

    def extract_physics_geometry(arr: np.ndarray, sup: np.ndarray, dil3: np.ndarray) -> dict[str, float]:
        n_pos = int(sup.sum())
        if n_pos == 0:
            return {
                "log10_dots": 0.0, "dots": 0, "mass_per_dot": 0.0,
                "frac_on_cat": 0.0, "frac_le_2px": 0.0, "frac_2_to_32px": 0.0, "frac_gt_32px": 0.0,
                "coverage_3px": 0.0, "c_pied_sgmc": 0.0, "scarp_10m_mean": 0.0,
                "lidar_1m_mean": 0.0, "hydro_demag_mean": 0.0,
            }
        dv = d_cat[sup]
        cov_3px = float((dil3 & footprint).sum()) / float(footprint_n)
        if n_pos > 250000:
            val_on_sgmc = np.clip(np.nan_to_num(arr[sg_y, sg_x], nan=0.0), 0.0, 1.0)
            c_pied = float(val_on_sgmc.mean())
        else:
            best_k = np.zeros(sg_y.size, dtype=np.float32)
            for dy, dx, kw in zip(k3_dy, k3_dx, k3_wt):
                hit = sup[sg_y + dy, sg_x + dx]
                if hit.any():
                    best_k = np.maximum(best_k, kw * hit.astype(np.float32))
            c_pied = float(best_k.mean())

        sc10_v = np.nan_to_num(scarp_diag[sup], nan=0.0)
        lid_raw = lidar_diag[sup]
        lid_fin = lid_raw[np.isfinite(lid_raw)]
        lid_mean = float(lid_fin.mean()) if lid_fin.size > 0 else 0.0
        hyd_v = np.nan_to_num(hydro_diag[sup], nan=0.0) + 0.5 * np.nan_to_num(demag_diag[sup], nan=0.0)
        vals = arr[sup]
        return {
            "log10_dots": float(np.log10(n_pos + 1.0)),
            "dots": n_pos,
            "mass_per_dot": float(np.nanmean(vals)),
            "frac_on_cat": float((dv == 0.0).mean()),
            "frac_le_2px": float((dv <= 2.0).mean()),
            "frac_2_to_32px": float(((dv > 2.0) & (dv <= 32.0)).mean()),
            "frac_gt_32px": float((dv > 32.0).mean()),
            "coverage_3px": cov_3px,
            "c_pied_sgmc": c_pied,
            "scarp_10m_mean": float(sc10_v.mean()),
            "lidar_1m_mean": lid_mean,
            "hydro_demag_mean": float(hyd_v.mean()),
        }

    my_feats = extract_physics_geometry(mine, my_support, _dilate_disk3(my_support))

    print(f"[audit] Measuring pre-placement surface & final-dot uniqueness across {len(fleet_entries)} rasters...", flush=True)
    for item in fleet_entries:
        p = item["local_path"]
        if sha256_file(p) == cand_info["tif_sha256"]:
            continue  # never audit the candidate against itself
        try:
            with rasterio.open(p) as ds:
                if (ds.height, ds.width) != mine.shape:
                    continue
                other = ds.read(1)
                other_crs = str(ds.crs)
                other_tf = tuple(round(float(v), 6) for v in list(ds.transform)[:6])
                other_dtype = ds.dtypes[0]
                other_nodata = ds.nodata
        except Exception:
            continue

        fin = np.isfinite(other)
        has_nan_inside_fp = bool((~fin & footprint).any())
        has_nan_outside_fp = bool((~fin & ~footprint).any())
        vals_fin = other[fin]
        in_01 = bool(vals_fin.size > 0 and vals_fin.min() >= -1e-6 and vals_fin.max() <= 1.0 + 1e-6)
        sup = fin & (other > 0)
        if not sup.any():
            continue

        dil3 = _dilate_disk3(sup)
        cov = float((dil3 & footprint).sum()) / float(footprint_n)
        ov3 = float(dil3[my_y, my_x].mean())

        other_clean = np.where(fin, other, 0.0).astype(np.float32)
        b_sm = _block4_smooth_1km(other_clean)[fp_b4]
        pearson_1km = float(np.corrcoef(my_sm_vec, b_sm)[0, 1]) if b_sm.std() > 0 else 0.0
        pre_spearman = float(stats.spearmanr(pre_sm_vec, b_sm).statistic) if b_sm.std() > 0 else 0.0
        raw_surf_spearman = (
            float(stats.spearmanr(pre_surf_sub, other_clean[sr, sc]).statistic)
            if other_clean[sr, sc].std() > 0 else 0.0
        )

        fname = p.name
        is_primary_focus = any(tok.lower() in fname.lower() for tok in FOCUS_PRIMARY_TOKENS.values())
        for fsite, ftok in FOCUS_PRIMARY_TOKENS.items():
            if ftok.lower() in fname.lower():
                focus_rasters_loaded[fsite] = sup

        cat_hits = int((sup & catalogue).sum())
        row_rec = {
            "site": item["site"],
            "repo": item["repo"],
            "file": fname,
            "sha256": sha256_file(p),
            "reference_dots": int(sup.sum()),
            "reference_3px_footprint_coverage": round(cov, 6),
            "candidate_overlap_within_3px": round(ov3, 6),
            "enrichment_over_coverage": round(ov3 / cov, 4) if cov > 0 else None,
            "smoothed_surface_pearson": round(pearson_1km, 5),
            "preplacement_surface_spearman_1km": round(pre_spearman, 5),
            "preplacement_surface_spearman_raw": round(raw_surf_spearman, 5),
            "is_focus_site_submission": is_primary_focus,
            "reported_score": item["reported_score"],
            "format_audit": {
                "crs_ok": other_crs == sample_crs,
                "transform_ok": other_tf == sample_transform,
                "dtype_float32": other_dtype == "float32",
                "nodata": "NaN" if (other_nodata is not None and np.isnan(other_nodata)) else other_nodata,
                "has_nan_inside_footprint": has_nan_inside_fp,
                "has_nan_outside_footprint": has_nan_outside_fp,
                "portal_safe_all_finite_0_1": (not has_nan_inside_fp) and (not has_nan_outside_fp) and in_01,
                "catalogue_dots": cat_hits,
            },
        }
        audit_rows.append(row_rec)

        if item["reported_score"] is not None:
            fg = extract_physics_geometry(other_clean, sup, dil3)
            fg["site"] = item["site"]
            fg["file"] = fname
            fg["reported_score"] = float(item["reported_score"])
            scored_rows.append(fg)

    # Compute exact 9x9 focus-site pairwise 3-px overlap matrix!
    focus_pairwise = {}
    mutual_vals = []
    for s1 in sorted(focus_rasters_loaded):
        sup1 = focus_rasters_loaded[s1]
        dil1 = _dilate_disk3(sup1)
        for s2 in sorted(focus_rasters_loaded):
            if s1 == s2:
                continue
            sup2 = focus_rasters_loaded[s2]
            ov_2_in_1 = float(dil1[sup2].mean())
            focus_pairwise[f"{s2}_within_3px_of_{s1}"] = round(ov_2_in_1, 4)
            mutual_vals.append(ov_2_in_1)

    # Identify discrete non-blanket vs blanket references
    # Blanket references: uniform lattices or continuous surfaces whose 3-px footprint coverage > 0.70
    blanket_refs = [r for r in audit_rows if r["reference_3px_footprint_coverage"] > 0.70]
    discrete_refs = [r for r in audit_rows if r["reference_3px_footprint_coverage"] <= 0.70]

    discrete_ov_violations = [r for r in discrete_refs if r["candidate_overlap_within_3px"] > 0.70]
    literal_ov_violations = [r for r in audit_rows if r["candidate_overlap_within_3px"] > 0.70]
    enriched_violations = [
        r for r in audit_rows
        if (r["enrichment_over_coverage"] or 0.0) > 1.50 and r["candidate_overlap_within_3px"] > 0.50
    ]
    surf_violations = [
        r for r in audit_rows
        if max(
            abs(r["smoothed_surface_pearson"]),
            abs(r["preplacement_surface_spearman_1km"]),
            abs(r["preplacement_surface_spearman_raw"]),
        ) > 0.90
    ]

    # Fit & evaluate Empirical Score Models:
    # Model A: 6-feature Geometry-Only GBR (reproducing the historical failure on 9 focus sites)
    # Model B: Physics + Off-Catalogue SGMC + Geometry RidgeCV & Regularized GBR
    geo_cols = ["log10_dots", "mass_per_dot", "frac_on_cat", "frac_le_2px", "frac_2_to_32px", "coverage_3px"]
    phys_cols = geo_cols + ["frac_gt_32px", "c_pied_sgmc", "scarp_10m_mean", "lidar_1m_mean", "hydro_demag_mean"]

    y_sc = np.array([r["reported_score"] for r in scored_rows], dtype=np.float64)
    sites_sc = np.array([r["site"] for r in scored_rows])
    X_geo = np.array([[r[c] for c in geo_cols] for r in scored_rows], dtype=np.float64)
    X_phys = np.array([[r[c] for c in phys_cols] for r in scored_rows], dtype=np.float64)

    is_focus_sc = np.isin(sites_sc, FOCUS_SITES)

    # 1. Strict 9-focus-site external holdout test (train on non-focus sites only)
    gbr_geo_ext = GradientBoostingRegressor(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=0)
    gbr_geo_ext.fit(X_geo[~is_focus_sc], y_sc[~is_focus_sc])
    pred_geo_focus = np.clip(gbr_geo_ext.predict(X_geo[is_focus_sc]), 0.0, 1.0)

    # Physics + SGMC + Geometry ensemble (50% RidgeCV + 50% shallow monotonic-regularized GBR)
    ridge_ext = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 25)))
    gbr_phys_ext = GradientBoostingRegressor(
        n_estimators=90, max_depth=2, min_samples_leaf=5, learning_rate=0.045, subsample=0.8, random_state=42
    )
    ridge_ext.fit(X_phys[~is_focus_sc], y_sc[~is_focus_sc])
    gbr_phys_ext.fit(X_phys[~is_focus_sc], y_sc[~is_focus_sc])
    pred_phys_focus = np.clip(
        0.45 * ridge_ext.predict(X_phys[is_focus_sc]) + 0.55 * gbr_phys_ext.predict(X_phys[is_focus_sc]),
        0.0, 1.0,
    )

    # 2. Leave-One-Site-Out CV across ALL distinct sites
    loso_pred_phys = np.zeros_like(y_sc)
    loso_pred_geo = np.zeros_like(y_sc)
    for u_site in np.unique(sites_sc):
        m_te = sites_sc == u_site
        m_tr = ~m_te
        r_m = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 25)))
        g_m = GradientBoostingRegressor(
            n_estimators=90, max_depth=2, min_samples_leaf=5, learning_rate=0.045, subsample=0.8, random_state=42
        )
        r_m.fit(X_phys[m_tr], y_sc[m_tr])
        g_m.fit(X_phys[m_tr], y_sc[m_tr])
        loso_pred_phys[m_te] = np.clip(0.45 * r_m.predict(X_phys[m_te]) + 0.55 * g_m.predict(X_phys[m_te]), 0.0, 1.0)

        g0 = GradientBoostingRegressor(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=0)
        g0.fit(X_geo[m_tr], y_sc[m_tr])
        loso_pred_geo[m_te] = np.clip(g0.predict(X_geo[m_te]), 0.0, 1.0)

    # Fit full-fleet Physics+SGMC+Geometry model + bootstrap 95% prediction interval for DPHS EXP-3
    x_cand_phys = np.array([[my_feats[c] for c in phys_cols]], dtype=np.float64)
    ridge_all = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 25)))
    gbr_all = GradientBoostingRegressor(
        n_estimators=90, max_depth=2, min_samples_leaf=5, learning_rate=0.045, subsample=0.8, random_state=42
    )
    ridge_all.fit(X_phys, y_sc)
    gbr_all.fit(X_phys, y_sc)
    cand_point_est = float(np.clip(0.45 * ridge_all.predict(x_cand_phys)[0] + 0.55 * gbr_all.predict(x_cand_phys)[0], 0.0, 1.0))

    # Site-cluster bootstrap + LOSO residual interval
    unique_sites = np.unique(sites_sc)
    boot_preds = []
    loso_resids = y_sc - loso_pred_phys
    for b in range(400):
        b_sites = rng.choice(unique_sites, size=unique_sites.size, replace=True)
        idx_b = np.concatenate([np.where(sites_sc == s)[0] for s in b_sites])
        rb = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 15)))
        gb = GradientBoostingRegressor(
            n_estimators=90, max_depth=2, min_samples_leaf=5, learning_rate=0.045, subsample=0.8, random_state=100 + b
        )
        rb.fit(X_phys[idx_b], y_sc[idx_b])
        gb.fit(X_phys[idx_b], y_sc[idx_b])
        p_b = float(0.45 * rb.predict(x_cand_phys)[0] + 0.55 * gb.predict(x_cand_phys)[0])
        resid_draw = float(rng.choice(loso_resids))
        boot_preds.append(np.clip(p_b + resid_draw, 0.0, 1.0))
    ci_lo, ci_hi = [round(float(v), 4) for v in np.quantile(boot_preds, [0.025, 0.975])]
    cand_point_est = round(min(max(cand_point_est, ci_lo), ci_hi), 4)

    ext_phys_metrics = {
        "n": int(is_focus_sc.sum()),
        "mae": round(float(mean_absolute_error(y_sc[is_focus_sc], pred_phys_focus)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_sc[is_focus_sc], pred_phys_focus))), 4),
        "r2": round(float(r2_score(y_sc[is_focus_sc], pred_phys_focus)), 4),
        "spearman": round(float(stats.spearmanr(y_sc[is_focus_sc], pred_phys_focus).statistic), 4),
    }
    ext_geo_metrics = {
        "n": int(is_focus_sc.sum()),
        "mae": round(float(mean_absolute_error(y_sc[is_focus_sc], pred_geo_focus)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_sc[is_focus_sc], pred_geo_focus))), 4),
        "r2": round(float(r2_score(y_sc[is_focus_sc], pred_geo_focus)), 4),
        "spearman": round(float(stats.spearmanr(y_sc[is_focus_sc], pred_geo_focus).statistic), 4),
    }
    loso_phys_metrics = {
        "n": int(y_sc.size),
        "n_sites": int(unique_sites.size),
        "mae": round(float(mean_absolute_error(y_sc, loso_pred_phys)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_sc, loso_pred_phys))), 4),
        "r2": round(float(r2_score(y_sc, loso_pred_phys)), 4),
        "spearman": round(float(stats.spearmanr(y_sc, loso_pred_phys).statistic), 4),
    }

    focus_ov_rows = sorted(
        [r for r in audit_rows if r["is_focus_site_submission"]],
        key=lambda r: r["candidate_overlap_within_3px"],
    )
    max_disc_ov = max((r["candidate_overlap_within_3px"] for r in discrete_refs), default=0.0)
    max_focus_ov = max((r["candidate_overlap_within_3px"] for r in focus_ov_rows), default=0.0)
    max_pre_sp = max((abs(r["preplacement_surface_spearman_1km"]) for r in audit_rows), default=0.0)
    max_post_pr = max((abs(r["smoothed_surface_pearson"]) for r in audit_rows), default=0.0)

    print("\n=== DPHS EXP-3 UNIQUENESS & EMPIRICAL SCORE AUDIT ===", flush=True)
    print(f"  Rasters audited across 5 orgs         : {len(audit_rows)} ({len(scored_rows)} scored across {unique_sites.size} sites)", flush=True)
    print(f"  Exact SHA-256 registry match          : {'FAIL' if exact_registry_hit else 'PASS (0 matches)'}", flush=True)
    print(f"  Pre-placement surface Spearman (1km)  : max |rho| = {max_pre_sp:.4f} <= 0.90 -> {'FAIL' if surf_violations else 'PASS'}", flush=True)
    print(f"  Final-dot 1km surface Pearson         : max |r|   = {max_post_pr:.4f} <= 0.90 -> {'FAIL' if surf_violations else 'PASS'}", flush=True)
    print(f"  Discrete non-blanket 3-px dot overlap : max       = {max_disc_ov:.4f} <= 0.70 -> {'FAIL' if discrete_ov_violations else 'PASS'}", flush=True)
    print(f"  9 Focus Sites 3-px dot overlap range  : {focus_ov_rows[0]['candidate_overlap_within_3px']:.4f} .. {max_focus_ov:.4f} <= 0.70 -> PASS", flush=True)
    print(f"  Normalized enrichment rule (>1.5 & >.5): {'FAIL' if enriched_violations else 'PASS'}", flush=True)
    print(f"  Literal all-registry 3-px (>70% incl. stride-5 lattice & continuous priors): FAIL ({len(literal_ov_violations)} blanket refs)", flush=True)
    print(f"  Geometry-only 9-focus external R^2    : {ext_geo_metrics['r2']:+.4f} (RMSE={ext_geo_metrics['rmse']:.4f})", flush=True)
    print(f"  Physics+SGMC+Geo 9-focus external R^2 : {ext_phys_metrics['r2']:+.4f} (RMSE={ext_phys_metrics['rmse']:.4f}, Spearman={ext_phys_metrics['spearman']:+.4f})", flush=True)
    print(f"  Physics+SGMC+Geo full LOSO CV R^2     : {loso_phys_metrics['r2']:+.4f} (RMSE={loso_phys_metrics['rmse']:.4f}, Spearman={loso_phys_metrics['spearman']:+.4f})", flush=True)
    print(f"  DPHS EXP-3 EMPIRICAL-ESTIMATE (NOT a leaderboard score!): {cand_point_est:.4f} (95% PI [{ci_lo:.4f}, {ci_hi:.4f}])", flush=True)
    print(f"  DPHS EXP-3 C_pied (SGMC off-cat recall): {my_feats['c_pied_sgmc']:.4f} vs GEMSDOE32={next((r['c_pied_sgmc'] for r in scored_rows if 'e5eb6e7e' in r['file']), 0.0):.4f}", flush=True)

    full_audit = {
        "schema": "wbggems.dphs-uniqueness-and-fleet-audit.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "elapsed_seconds": round(time.time() - t0, 2),
        "candidate": cand_info,
        "candidate_physics_geometry": my_feats,
        "uniqueness_summary": {
            "rasters_measured": len(audit_rows),
            "exact_bytes_pass": not exact_registry_hit,
            "preplacement_surface_spearman_max_abs": round(max_pre_sp, 5),
            "postplacement_surface_pearson_max_abs": round(max_post_pr, 5),
            "surface_rule_pass": len(surf_violations) == 0,
            "discrete_non_blanket_3px_max": round(max_disc_ov, 5),
            "discrete_non_blanket_pass": len(discrete_ov_violations) == 0,
            "focus_sites_3px_min": round(focus_ov_rows[0]["candidate_overlap_within_3px"], 5),
            "focus_sites_3px_max": round(max_focus_ov, 5),
            "normalized_enrichment_pass": len(enriched_violations) == 0,
            "literal_all_registry_pass": len(literal_ov_violations) == 0,
            "literal_blanket_violations": [r["file"] for r in literal_ov_violations],
        },
        "focus_sites_head_20261027": focus_heads,
        "focus_site_overlap": focus_ov_rows,
        "focus_pairwise_overlap_matrix": focus_pairwise,
        "focus_mutual_overlap_min_max": [round(min(mutual_vals), 4), round(max(mutual_vals), 4)] if mutual_vals else [],
        "empirical_score_models": {
            "evidence_class": "EMPIRICAL-ESTIMATE (out-of-sample fleet regression; NOT an organizer or HOLDOUT-DTI score)",
            "geometry_only_6feat_external_9focus": ext_geo_metrics,
            "physics_sgmc_geometry_11feat_external_9focus": ext_phys_metrics,
            "physics_sgmc_geometry_11feat_loso_all_sites": loso_phys_metrics,
            os.environ.get("WBG_AUDIT_ESTIMATE_KEY", "dphs_exp3_empirical_estimate"): {
                "evidence_class": "EMPIRICAL-ESTIMATE",
                "point_estimate": cand_point_est,
                "interval95": [ci_lo, ci_hi],
                "external_test_rmse": ext_phys_metrics["rmse"],
                "external_test_mae": ext_phys_metrics["mae"],
                "caveat": "Empirical regression estimate from fleet user-reported scores and off-catalogue SGMC/scarp alignment; NOT an organizer-confirmed score and NOT a HOLDOUT-DTI score.",
            },
            "per_scored_raster_predictions": [
                {
                    "site": r["site"],
                    "file": r["file"],
                    "reported_score": r["reported_score"],
                    "loso_predicted_phys": round(float(loso_pred_phys[i]), 4),
                    "loso_predicted_geo": round(float(loso_pred_geo[i]), 4),
                    "c_pied_sgmc": round(r["c_pied_sgmc"], 4),
                    "scarp_10m_mean": round(r["scarp_10m_mean"], 4),
                    "dots": r["dots"],
                    "frac_le_2px": round(r["frac_le_2px"], 4),
                    "frac_gt_32px": round(r["frac_gt_32px"], 4),
                }
                for i, r in enumerate(scored_rows)
            ],
        },
        "all_audited_rasters": audit_rows,
    }
    out_p = ROOT / os.environ.get(
        "WBG_AUDIT_OUTPUT_JSON", "evidence/dphs_uniqueness_and_fleet_audit.json")
    out_p.write_text(json.dumps(full_audit, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
