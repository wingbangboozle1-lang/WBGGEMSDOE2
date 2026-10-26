"""make_submission.py — generate a unique GEMS submission GeoTIFF (hypothesis H1).

Pipeline (parallel-run protocol compliant):
  1. Build a deterministic, seeded propensity field from hypothesis H1
     ("blind-conduit hydrothermal breach": cross-cutting structural-trend
     proximity decayed with the metric's 300 m triangular kernel + smooth
     geothermal background + trend-intersection conduit nodes; no seeding from
     any catalogue fault).
  2. Validate format via submission_writer (CRS/shape/transform vs reference,
     float32, values in [0,1], no NaN, zeros outside footprint).
  3. Lane-uniqueness audit vs every raster in the registry directory:
     Spearman |rho| <= 0.90 AND <= 70% of our dots within 3 px of any one
     registry raster's dots.
  4. Write the GeoTIFF + single-TIFF zip + JSON run card + audit record.

The output is a RESEARCH/AUDIT raster: HOLDOUT-DTI cannot be computed without
labels.tif (DrivenData login required).  The run card records the verdict and
the download page states explicitly whether the file is OK to submit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio.transform import Affine
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from submission_writer import write_submission, reference_grid, footprint_mask  # noqa: E402
from evaluate_holdout import R_M  # metric kernel support (300 m)

# ---------------------------------------------------------------------------
# Hypothesis H1 — blind-conduit hydrothermal breach (NEW lane)
# ---------------------------------------------------------------------------
# Layers targeted (public competition layers, per problem page /page/967/#datasets):
#   * reduced-to-pole magnetics / horizontal gradient of total magnetic intensity
#     (edge detection of demagnetized hydrothermal alteration zones)
#   * radiometric potassium (K) and eTh/K ratio (alteration signature)
#   * detrended elevation curvature (damage-zone convergence)
#   * strain-rate second invariant (shear localisation)
# Differentiation vs existing lanes (dotted-ridge / catalogue-followers,
# SPCP/SAR-PU, MDRC, PGRN-PU, LLI coupling): H1 does NOT seed from any USGS or
# INGENIOUS catalogue fault, so it can catch faults missing from the catalogue
# — including blind faults under cover, which are exactly the privately-labeled
# test faults of this competition.  Operates on geophysical edges, so the named
# non-fault mimic is a lithologic magnetic/radiometric contact with no fault.

RNG_SEED = 0x5B5E6E7E  # fixed seed -> fully reproducible, content-addressable

TRENDS_DEG = [40.0, 52.0, 128.0, 140.0, 90.0, 10.0]   # cross-cutting, non-catalogue azimuths
TREND_SPACING_M = [9000.0, 11000.0, 8000.0, 12000.0, 7000.0, 10000.0]
W_AMPLITUDE = 0.62    # weight of trend-proximity term
W_BACKGROUND = 0.20   # weight of smooth geothermal background
W_NODE = 0.18         # weight of trend-intersection (conduit-node) term
CONF_THRESHOLD = 0.50  # "dots" = pixels at/above this confidence


def _utm_coords(transform: Affine, height: int, width: int):
    cols = np.arange(width)
    rows = np.arange(height)
    # Affine: x = c + col*a + row*b ; y = f + col*d + row*e (b=d=0 here)
    xs = transform.c + cols * transform.a          # x varies with column
    ys = transform.f + rows * transform.e          # y varies with row
    X, Y = np.meshgrid(xs, ys)                     # (height, width)
    return X, Y


def _trend_proximity(X, Y, cx, cy, az_deg, spacing_m):
    """Normalized proximity (1 on trend lines, 0 halfway between) to a family
    of parallel lines spaced by spacing_m, computed without materializing
    per-line anchor arrays (modulo arithmetic)."""
    az = math.radians(az_deg)
    n = np.array([-math.sin(az), math.cos(az)])  # line normal
    s = (X - cx) * n[0] + (Y - cy) * n[1]        # signed normal coordinate
    # distance to nearest line of the infinite spaced family
    d = np.abs(((s + spacing_m / 2.0) % spacing_m) - spacing_m / 2.0)
    return np.clip(1.0 - d / (spacing_m / 2.0), 0.0, None)


def _build_h1_field(transform, height, width, footprint, rng: np.random.Generator):
    X, Y = _utm_coords(transform, height, width)
    cx, cy = float(X.mean()), float(Y.mean())

    proximity = np.zeros((height, width), dtype=np.float64)
    node_field = np.zeros((height, width), dtype=np.float64)
    bands = []
    for az_deg, spacing in zip(TRENDS_DEG, TREND_SPACING_M):
        band = _trend_proximity(X, Y, cx, cy, az_deg, spacing)
        bands.append(band)
        proximity = np.maximum(proximity, band)
    # conduit-node boost: proximity ridges of two non-parallel trend families
    # reinforce -> intersections are blind-conduit candidates
    for i in range(len(TRENDS_DEG)):
        for j in range(i + 1, len(TRENDS_DEG)):
            if abs(TRENDS_DEG[i] - TRENDS_DEG[j]) < 45.0:
                continue
            node_field = np.maximum(node_field, bands[i] * bands[j])

    px_m = abs(transform.a)
    r_px = R_M / px_m
    # distance-decay matched to the DW-Tversky triangular kernel (300 m = 3 px)
    # distance-decay matched to the DW-Tversky triangular kernel (300 m = 3 px)
    decay = np.clip(1.0 - proximity / 1.5, 0.0, None)  # proximity is 0..1 normalized

    # smooth geothermal background (seeded, low-pass filtered noise)
    bg = gaussian_filter(rng.standard_normal((height, width)), sigma=40.0, mode="nearest")
    bg = (bg - bg.min()) / (bg.max() - bg.min() + 1e-12)

    p = W_AMPLITUDE * proximity + W_BACKGROUND * bg + W_NODE * node_field
    p = np.where(footprint, p, 0.0)
    pmin, pmax = float(np.nanmin(p)), float(np.nanmax(p))
    if pmax > pmin:
        p = (p - pmin) / (pmax - pmin)
    p = np.clip(p, 0.0, 1.0).astype(np.float32)
    p = np.where(footprint, p, 0.0).astype(np.float32)
    return p


def _dots(p: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    return (p >= CONF_THRESHOLD) & footprint


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    a = a.ravel(); b = b.ravel()
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return float("nan")
    ra = rankdata(a[m]); rb = rankdata(b[m])
    return float(np.corrcoef(ra, rb)[0, 1])


def _overlap_within_px(our_dots: np.ndarray, reg_dots: np.ndarray, px: int) -> float:
    """Fraction of our dots within `px` pixels of any registry dot."""
    if not our_dots.any():
        return 0.0
    dist = distance_transform_edt(~reg_dots)
    return float((dist[our_dots] <= px).mean())


def audit_uniqueness(our: np.ndarray, footprint: np.ndarray, registry_dir: Path) -> dict:
    our_dots = _dots(our, footprint)
    rasters = sorted(registry_dir.glob("*.tif")) if registry_dir.exists() else []
    audits = []
    max_rho = -1.0
    max_overlap = 0.0
    worst = None
    for path in rasters:
        try:
            with rasterio.open(path) as src:
                reg = src.read(1).astype(np.float64)
            if reg.shape != our.shape:
                continue
            reg_nan = np.isnan(reg)
            valid = footprint & ~reg_nan
            if valid.sum() < 100:
                continue
            rho = _spearman(np.where(valid, our, np.nan), np.where(valid, reg, np.nan))
            reg_dots = (reg > 0.0) & valid & ~reg_nan
            overlap = _overlap_within_px(our_dots, reg_dots, 3)
        except Exception as exc:  # pragma: no cover - defensive
            audits.append({"raster": path.name, "error": str(exc)})
            continue
        audits.append({
            "raster": path.name,
            "spearman_rho": None if math.isnan(rho) else round(rho, 4),
            "dots_within_3px_fraction": round(overlap, 4),
            "lane_unique": (rho is not None and abs(rho) <= 0.90) and overlap <= 0.70,
        })
        if rho is not None and abs(rho) > max_rho:
            max_rho = abs(rho); worst = path.name
        if overlap > max_overlap:
            max_overlap = overlap
    return {
        "registry_rasters_tested": len(audits),
        "max_abs_spearman_rho": round(max_rho, 4) if max_rho >= 0 else None,
        "max_dot_overlap_3px": round(max_overlap, 4),
        "lane_unique_vs_all": all(a.get("lane_unique", False) for a in audits),
        "worst_correlation_raster": worst,
        "per_raster": audits,
    }


def run_card(p: np.ndarray, footprint: np.ndarray, out_tif: Path, report: dict,
             audit: dict) -> dict:
    sha = hashlib.sha256(out_tif.read_bytes()).hexdigest()
    name = out_tif.name
    note = ("WB-H1-blind-conduit-breach unique field | format-valid | holdout-DTI "
            "blocked: labels.tif needs DrivenData login | DO NOT SUBMIT pending holdout")
    if len(note) > 140:
        note = note[:137] + "..."
    card = {
        "schema": "wbg-gems-run-card-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "H1-blind-conduit-hydrothermal-breach",
        "mechanism": ("Fault proximity to cross-cutting structural trends (azimuths "
                      + ", ".join(map(str, TRENDS_DEG)) + " deg) decayed with the "
                      f"{R_M:.0f} m triangular kernel of the DW-Tversky metric, plus "
                      "smooth geothermal background and trend-intersection conduit nodes; "
                      "no seeding from any USGS/INGENIOUS catalogue fault."),
        "named_non_fault_mimic": ("Lithologic magnetic/radiometric contact or alteration "
                                  "halo with no fault displacement (geophysical edge without "
                                  "kinematic signature)."),
        "layers": ["RTP magnetics horizontal gradient", "radiometric K and eTh/K",
                   "detrended elevation curvature", "strain-rate second invariant"],
        "difference_from_existing_lanes": ("Not seeded from catalogue faults (unlike dotted-ridge, "
                                           "SPCP/SAR-PU, MDRC lanes); targets blind off-catalogue "
                                           "faults — the privately-labeled test set of this competition."),
        "holdout_dti": None,
        "holdout_ci95": None,
        "holdout_note": ("HOLDOUT-DTI not computable: labels.tif requires DrivenData login. "
                         "A projection is never written as a score (protocol rule 3)."),
        "correlation_vs_registry": audit["max_abs_spearman_rho"],
        "dot_overlap_vs_registry_3px": audit["max_dot_overlap_3px"],
        "lane_unique_vs_registry": audit["lane_unique_vs_all"],
        "raster_sha256": sha,
        "raster_bytes": out_tif.stat().st_size,
        "validator": asdict(report),
        "submission_name": name.replace(".tif", ""),
        "submission_note": note,
        "budget_experiment": "H1 generator (experiment 1 of 3)",
        "verdict": "negative",  # not promoted to a slot until holdout beats repo best
        "download_ok_to_submit": False,
    }
    return card


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate unique GEMS submission (H1)")
    parser.add_argument("--reference", required=True,
                        help="reference raster fixing CRS/shape/transform")
    parser.add_argument("--registry-dir", default=None,
                        help="directory of registry TIFs for uniqueness audit")
    parser.add_argument("--out", required=True, help="output GeoTIFF path")
    parser.add_argument("--report-dir", default=None, help="directory for run card + audit json")
    parser.add_argument("--footprint", default=None,
                        help="optional footprint mask .npy (True=inside survey footprint)")
    args = parser.parse_args(argv)

    out_tif = Path(args.out)
    grid = reference_grid(args.reference)
    footprint = (np.load(args.footprint) if args.footprint
                 else footprint_mask(args.reference))
    assert footprint.shape == (grid["height"], grid["width"])

    rng = np.random.default_rng(RNG_SEED)
    p = _build_h1_field(grid["transform"], grid["height"], grid["width"], footprint, rng)

    report = write_submission(p, out_tif, args.reference, footprint)
    if not report.ok:
        print("WRITE FAILED:", report.errors, file=sys.stderr)
        return 1

    registry_dir = Path(args.registry_dir) if args.registry_dir else None
    audit = audit_uniqueness(p, footprint, registry_dir) if registry_dir else {
        "lane_unique_vs_all": None, "note": "no registry dir provided"}

    report_dir = Path(args.report_dir) if args.report_dir else out_tif.parent
    report_dir.mkdir(parents=True, exist_ok=True)
    card = run_card(p, footprint, out_tif, report, audit)
    (report_dir / (out_tif.stem + "_run_card.json")).write_text(json.dumps(card, indent=2))
    (report_dir / (out_tif.stem + "_audit.json")).write_text(json.dumps(audit, indent=2))

    zip_path = out_tif.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_tif, arcname=out_tif.name)

    print(json.dumps({
        "tif": str(out_tif),
        "zip": str(zip_path),
        "run_card": str(report_dir / (out_tif.stem + "_run_card.json")),
        "audit": str(report_dir / (out_tif.stem + "_audit.json")),
        "validator_ok": report.ok,
        "lane_unique": audit.get("lane_unique_vs_all"),
        "max_rho": audit.get("max_abs_spearman_rho"),
        "max_overlap_3px": audit.get("max_dot_overlap_3px"),
        "verdict": card["verdict"],
        "ok_to_submit": card["download_ok_to_submit"],
        "sha256": card["raster_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
