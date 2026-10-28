#!/usr/bin/env python3
"""Calibrate 'surface-weighted coverage' against the reported fleet scores.

Idea
----
The structural model (``gemsdoe_metric_model.py``) turns each USER-REPORTED score
into an implied coverage of the scored truth, ``f = T / N``.  If a common
fault-probability surface carries real information, then ``f`` should rise with the
share of that surface's mass lying inside a file's 300 m halo,

    J = sum_x w(x) * covered(x) / sum_x w(x),

because a dot field placed where the surface is high should claim more of the truth.

This script measures ``(f_i, J_i, reach_i, mass_i)`` for every fleet raster that is
present locally, then fits ``f = beta J`` (through the origin, weighted by mass) and
reports the fit quality.  ``beta`` is the only free parameter, so the fit is a genuine
one-parameter test of whether the surface is informative.

The fitted relation is then used to estimate *our* candidate's coverage and score:

    f_hat = beta J,   score_hat = f_hat N / (f_hat N + 0.2 M + 0.8 (1 - f_hat) N)

Every output is labelled: scores are USER-REPORTED, the surface is a consensus of
third-party rasters, and the estimate is an EMPIRICAL-BAND ESTIMATE, not a receipt.

CAVEAT (do not publish the fit as validation): the surface is built from the same fleet
whose scores are the labels, so a high ``beta`` partly measures *agreement with the
crowd*. It cannot validate a candidate that is deliberately unlike the crowd, and it was
therefore not used to choose the delivered file. Treat it as a diagnostic only.

Usage
-----
    python scripts/gemsdoe_calibrate.py --surface data/work/consensus_surface.npy
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "work"
PUB = ROOT / "data_public"
R = 3
ALPHA, BETA = 0.2, 0.8


def load_mask(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as d:
        a = d.read(1)
    a = np.nan_to_num(a.astype("float32"), nan=0.0, posinf=0.0, neginf=0.0)
    return (a > 0) & footprint


def coverage(mask: np.ndarray) -> np.ndarray:
    d = ndi.distance_transform_edt(~mask)
    return np.maximum(1.0 - d / R, 0.0).astype("float32")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", default=str(WORK / "consensus_surface.npy"))
    ap.add_argument("--fleet", default="/tmp/fleet")
    ap.add_argument("--n-truth", type=float, default=None)
    ap.add_argument("--candidates", nargs="*", default=[])
    args = ap.parse_args()

    model = json.loads((PUB / "gemsdoe_metric_model.json").read_text())
    n_truth = args.n_truth or model["n_truth_pixels_solved"]
    feats = json.loads((PUB / "fleet_features.json").read_text())["rows"]
    fp = np.load(WORK / "footprint.npy").astype(bool)

    surf = np.load(args.surface).astype("float32")
    surf = np.nan_to_num(surf, nan=0.0)
    s = (surf - surf[fp].min()) / max(float(np.ptp(surf[fp])), 1e-9)
    w = np.where(fp, s, 0.0).astype("float32")
    total_w = float(w.sum())
    area = int(fp.sum())

    def norm(x: str) -> str:
        return "".join(ch for ch in x.lower() if ch.isalnum())

    files = {}
    for p in glob.glob(str(Path(args.fleet) / "**" / "*.tif"), recursive=True):
        stem = Path(p).stem
        if stem.endswith(("-nan", "-allfinite")):
            continue
        files.setdefault(stem.replace("-zeros", ""), p)
    norm_index = {norm(k): k for k in files}

    def find(stem: str):
        for cand in (stem, stem.replace("-zeros", ""), stem.replace("-nan", "")):
            if cand in files:
                return files[cand]
        key = norm(stem)
        for nk, original in norm_index.items():
            if len(key) >= 24 and (nk.startswith(key) or key.startswith(nk) or key in nk):
                return files[original]
        return None

    rows = []
    for r in feats:
        stem = Path(r["path"]).stem
        score = r.get("reported_score")
        mass = r.get("mass")
        path = find(stem)
        if path is None or score is None or not mass:
            continue
        mask = load_mask(Path(path), fp)
        cov = coverage(mask)
        rows.append({
            "site": r["site"], "file": stem, "score": float(score), "mass": float(mass),
            "cells": int(mask.sum()),
            "reach": float((cov > 0)[fp].mean()),
            "J": float((w * cov).sum() / total_w),
            "implied_T": float(score * (ALPHA * mass + BETA * n_truth) / (1 - ALPHA * score)),
        })
        rows[-1]["f"] = rows[-1]["implied_T"] / n_truth

    if len(rows) < 5:
        raise SystemExit(f"only {len(rows)} fleet rasters matched; need at least 5")

    f = np.array([r["f"] for r in rows])
    J = np.array([r["J"] for r in rows])
    m = np.array([r["mass"] for r in rows])
    beta_hat = float((J * f).sum() / (J * J).sum())
    pred = beta_hat * J
    ss_res = float(((f - pred) ** 2).sum())
    ss_tot = float(((f - f.mean()) ** 2).sum())
    # rank correlation, no scipy.stats dependency needed
    rf = np.argsort(np.argsort(f))
    rj = np.argsort(np.argsort(J))
    rho = float(np.corrcoef(rf, rj)[0, 1])

    out = {
        "schema": "wbggems.surface-calibration.v1",
        "evidence_class": ("EMPIRICAL-BAND ESTIMATE (USER-REPORTED scores; "
                           "consensus of third-party rasters; no organizer receipt)"),
        "surface": args.surface,
        "n_truth_pixels": n_truth,
        "n_files": len(rows),
        "beta_hat": beta_hat,
        "r2": 1.0 - ss_res / ss_tot if ss_tot else None,
        "spearman_J_vs_f": rho,
        "rows": rows,
        "candidates": [],
    }

    for path in args.candidates:
        mask = load_mask(Path(path), fp)
        cov = coverage(mask)
        Jc = float((w * cov).sum() / total_w)
        reach = float((cov > 0)[fp].mean())
        mass = float(mask.sum())
        f_hat = min(1.0, beta_hat * Jc)
        score = f_hat * n_truth / (f_hat * n_truth + ALPHA * mass + BETA * (1 - f_hat) * n_truth)
        out["candidates"].append({"file": Path(path).name, "mass": mass,
                                  "cells": int(mask.sum()), "J": Jc, "reach": reach,
                                  "f_hat": f_hat, "score_hat": score})

    (PUB / "gemsdoe_surface_calibration.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n_files", "beta_hat", "r2", "spearman_J_vs_f",
                                         "n_truth_pixels")}, indent=1))
    for c in out["candidates"]:
        print(f"  {c['file'][:56]:58s} mass={c['mass']:>7,.0f} reach={c['reach']:.4f} "
              f"J={c['J']:.4f} f_hat={c['f_hat']:.3f} score_hat={c['score_hat']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
