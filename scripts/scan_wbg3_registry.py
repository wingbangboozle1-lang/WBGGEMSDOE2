#!/usr/bin/env python3
"""Phase-B duplicate-stop scan of the WBG3 candidate against the pinned registry.

Scans every accessible registry raster (fetched by scripts/fetch_registry_rasters.py),
the nine focus-site rasters, and every raster stored in this repository, using the
pinned shared primitives gems57.uniqueness.dot_overlap / surface_rho.

Also measures the same scan for the GEMSDOE32-B2 raster as a *witness control*:
if the literal 70%-within-3-px rule rejects our candidate only via the documented
dense/blanket witnesses, the control shows whether the historical 0.2778 file is
rejected by the same witnesses (rule-degeneracy evidence, reported not exempted).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".cache" / "shared-template" / "src"))
from gems57 import uniqueness as uq  # noqa: E402

FOCUS_DIR = ROOT / "data_public" / "rasters_focus"
REG_DIR = ROOT / "data_public" / "rasters"
LOCAL_DIRS = [
    ROOT / "docs" / "downloads",
    ROOT / "submissions",
    ROOT / "artifacts",
    ROOT / "candidate",
]
BLANKET_DOTS = 500_000  # rasters with more positive cells than this are dense/blanket controls


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.nan_to_num(a.astype("float32"), nan=0.0)


def main() -> int:
    cand_path = Path(sys.argv[1]).resolve()
    control_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else (
        FOCUS_DIR / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    out_json = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else ROOT / "evidence" / "wbg3_registry_scan.json"

    with rasterio.open(cand_path) as ds:
        footprint = np.isfinite(ds.read(1))
    cand = read_raster(cand_path)
    control = read_raster(control_path)

    targets: list[tuple[str, Path]] = []
    for p in sorted(FOCUS_DIR.glob("*.tif")):
        targets.append((f"FOCUS::{p.stem}", p))
    for d in LOCAL_DIRS:
        for p in sorted(d.rglob("*.tif")):
            targets.append((f"LOCAL::{p.relative_to(ROOT)}", p))
    if REG_DIR.is_dir():
        state = json.loads((REG_DIR / "_fetch_state.json").read_text())
        for key, meta in state["done"].items():
            if meta.get("status") != "ok":
                continue
            p = REG_DIR / meta["file"]
            if p.is_file():
                src = (meta.get("sources") or ["REGISTRY"])[0]
                targets.append((f"REGISTRY::{src}", p))

    print(f"[scan] {len(targets)} registry targets", flush=True)
    rows = []
    ctrl_rows = []
    t0 = time.time()
    n_err = 0
    for i, (name, p) in enumerate(targets):
        try:
            with rasterio.open(p) as ds:
                if (ds.height, ds.width) != footprint.shape:
                    rows.append({"target": name, "status": "grid_mismatch"})
                    continue
            theirs = read_raster(p)
            n_their_dots = int((theirs > 0).sum())
            ov = uq.dot_overlap(cand, theirs)
            rho = uq.surface_rho(cand, theirs, footprint)["spearman_full_footprint"]
            row = {"target": name, "their_dots": n_their_dots,
                   "share_of_my_dots_within_3px": round(ov, 4),
                   "spearman_full_footprint": None if rho != rho else round(rho, 4),
                   "sha256": sha(p), "bytes": p.stat().st_size,
                   "blanket_witness": n_their_dots > BLANKET_DOTS}
            row["duplicate_by_overlap"] = bool(row["share_of_my_dots_within_3px"] > uq.OVERLAP_LIMIT)
            row["duplicate_by_rho"] = bool(row["spearman_full_footprint"] is not None
                                           and row["spearman_full_footprint"] > uq.RHO_LIMIT)
            rows.append(row)
            if n_their_dots > BLANKET_DOTS:
                cov = uq.dot_overlap(control, theirs)
                rho_c = uq.surface_rho(control, theirs, footprint)["spearman_full_footprint"]
                ctrl_rows.append({"target": name, "control": "GEMSDOE32-B2",
                                  "share_of_control_dots_within_3px": round(cov, 4),
                                  "spearman_full_footprint": None if rho_c != rho_c else round(rho_c, 4)})
            del theirs
        except Exception as exc:  # noqa: BLE001
            n_err += 1
            rows.append({"target": name, "status": f"error: {str(exc)[:120]}"})
        if i % 50 == 0:
            print(f"[{i+1}/{len(targets)}] elapsed={time.time()-t0:.0f}s err={n_err}", flush=True)

    dotted = [r for r in rows if r.get("their_dots") is not None and not r.get("blanket_witness")]
    sparse = [r for r in dotted if r.get("share_of_my_dots_within_3px") is not None]
    non_blanket_violations = [r for r in sparse
                              if r["duplicate_by_overlap"] or r["duplicate_by_rho"]]
    payload = {
        "schema": "wbggems.wbg3-registry-scan.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate": {"file": str(cand_path.relative_to(ROOT)), "sha256": sha(cand_path)},
        "control_witness": {"file": str(control_path.relative_to(ROOT)), "sha256": sha(control_path)},
        "targets_scanned": len(targets),
        "errors": n_err,
        "dense_blanket_witnesses": len(ctrl_rows),
        "non_blanket_rasters_scanned": len(sparse),
        "non_blanket_violations": non_blanket_violations,
        "non_blanket_max_overlap": max((r["share_of_my_dots_within_3px"] for r in sparse), default=None),
        "non_blanket_max_rho": max((r["spearman_full_footprint"] or 0 for r in sparse), default=None),
        "control_on_blanket_witnesses": ctrl_rows,
        "rows": rows,
        "gates": {"rho_limit": uq.RHO_LIMIT, "overlap_limit": uq.OVERLAP_LIMIT},
        "note": ("Literal dense/blanket witnesses (lattice/continuous-prior rasters) overlap every "
                 "non-empty dotted map, including the historical 0.2778 control; they are reported, "
                 "not silently exempted."),
    }
    out_json.write_text(json.dumps(payload, indent=1))
    print(f"[done] scanned={len(targets)} errors={n_err} "
          f"non-blanket max overlap={payload['non_blanket_max_overlap']} "
          f"violations={len(non_blanket_violations)} elapsed={time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
