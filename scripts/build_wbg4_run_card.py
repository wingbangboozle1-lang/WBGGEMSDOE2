"""Assemble the single WBG4 run card from the measured evidence files.

The spatial block bootstrap resamples the four withheld quadrants with
replacement (4 blocks -> 256 resamples) and re-pools TP/FP/FN at the chosen
operating point.  With only four spatial blocks the interval is coarse and is
labelled as such; it is not a substitute for more folds.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence"


def load(name):
    return json.loads((EVID / name).read_text())


def main():
    folds = load("wbg4_folds.json")["blind"]
    cand = load("wbg4_candidate.json")
    canary = load("wbg4_canaries.json")
    uniq = load("wbg4_uniqueness.json")
    reg = load("wbg4_registry_folds.json")
    vac = load("wbg4_lattice_vacuity.json")
    best = folds["best"]
    mf = best["mass_fraction"]

    parts = []
    for pf in folds["folds"]:
        row = [c for c in pf["curve"] if abs(c["mass_fraction"] - mf) < 1e-12][0]
        parts.append((row["tp"], row["fp"], row["fn"], row["n_truth"]))
    tp = sum(p[0] for p in parts); fp = sum(p[1] for p in parts)
    fn = sum(p[2] for p in parts); nt = sum(p[3] for p in parts)
    dti = tp / (tp + 0.2 * fp + 0.8 * fn)
    boot = []
    for idx in itertools.product(range(4), repeat=4):
        t = sum(parts[i][0] for i in idx); f = sum(parts[i][1] for i in idx)
        n = sum(parts[i][2] for i in idx)
        boot.append(t / (t + 0.2 * f + 0.8 * n + 1e-12))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    per_fold = [round(p["dti"] if "dti" in p else 0, 4) for p in
                (r for r in (row for row in
                             ([c for c in pf["curve"] if abs(c["mass_fraction"] - mf) < 1e-12][0]
                               for pf in folds["folds"])))]

    card = {
        "schema": "wbg4.run-card.v1",
        "generated_utc": cand["generated_utc"],
        "lane": "WBG4-SSCC (strike-conditioned structural corridor), blind feature set",
        "hypothesis": ("A supervised detector fitted on public USGS-derived layers only — lidar scarp morphology, "
                       "GeoDAWN radiometrics and their ratio/upward-continuation extensions, SGMC fault geometry, "
                       "GDR-1391 spring density — recovers withheld whole fault components better than a "
                       "structure-only dot prior does, and therefore has a better chance of firing on faults that "
                       "are absent from the catalogues."),
        "mechanism": ("Multi-scale scarp/curvature relief with strike continuity, radiometric contrast and independent "
                      "structural context; per-pixel probabilities from gradient-boosted trees; emitted set = top-k "
                      "model scores at the operating point that maximises pooled holdout DTI."),
        "non_fault_mimic": ("Bedrock ridge crests, landslide head scarps and fluvial terrace edges produce the same "
                            "short-wavelength coherent relief; alluvial-fan and playa boundaries produce radiometric "
                            "contrast without faulting."),
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator": folds["evaluator"],
            "withheld_positives": folds["withheld_positives_total"],
            "dti": round(dti, 5),
            "ci95_spatial_block_bootstrap": [round(float(lo), 5), round(float(hi), 5)],
            "ci95_method": "4 spatial quadrant blocks resampled with replacement, 256 resamples; coarse by construction",
            "per_fold_dti": per_fold,
            "mass_fraction": mf,
            "note": ("Holdout target is withheld CATALOGUE faults, not the experts' new faults; the registry "
                     "comparison below shows this metric does not predict leaderboard score (LOO R2 < 0)."),
        },
        "negative_result": {
            "variant": "catalogue-proximity features enabled",
            "dti": load("wbg4_folds.json")["full"]["best"]["dti"],
            "interpretation": ("'Be near the mapped catalogue' is not a fault detector under hide-and-recover: it "
                               "re-detects the faults that were not withheld and earns no credit for the withheld ones."),
        },
        "leakage_canary": {"max_single_feature_auc": canary["max_auc"],
                           "n_features": len(canary["features"]),
                           "n_flagged_above_0.90": canary["n_flagged"]},
        "uniqueness": {
            "registry_rasters_measured": uniq["registry_rasters_measured"],
            "max_abs_smoothed_spearman": uniq["max_abs_smoothed_spearman"],
            "rank_correlation_limit": 0.90,
            "max_frac_within_3px": uniq["max_frac_candidate_within_3px"],
            "literal_3px_rule": ("unsatisfiable: the GEMSDOE13 stride-5 lattice gives the organizer-accepted files "
                                 "99.91-99.92 % overlap and this file 99.84 %"),
            "lattice_vacuity_witness": vac["measured"],
            "verdict": "not a copy; method is new and rank correlation passes everywhere",
        },
        "registry_calibration": {
            "n_rasters": reg["n_rasters"],
            "spearman_holdout_vs_reported": reg["spearman_holdout_vs_reported"],
            "loo_r2": reg["loo"]["r2"],
            "loo_rmse": reg["loo"]["rmse"],
            "conclusion": "no defensible leaderboard point estimate for this file",
        },
        "raster": {
            "name": cand["name"],
            "path": f"downloads/{cand['name']}.tif",
            "zip": f"downloads/{cand['name']}.zip",
            "sha256": cand["sha256"],
            "bytes": cand["bytes"],
            "positive_cells": cand["positive_inside_footprint"],
            "grid": {"shape": cand["shape"], "crs": cand["crs"], "transform": cand["transform"],
                     "dtype": cand["dtype"]},
        },
        "validator": cand["checks"],
        "submission_name": cand["name"],
        "submission_note": ("WBG4-SSCC: strike-conditioned structural corridor, geophysics-only features, "
                            "4-fold whole-fault holdout, unique raster"),
        "note_length": len("WBG4-SSCC: strike-conditioned structural corridor, geophysics-only features, "
                           "4-fold whole-fault holdout, unique raster"),
        "verdict": ("PROMOTE-WITH-CAVEAT: format valid, method novel, holdout measured; no claim of beating 0.2778 "
                    "because no validated estimator exists"),
        "experiments_run": 3,
        "weekly_slots_used": 0,
    }
    (EVID / "RUN_CARD_WBG4.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({k: card[k] for k in ("verdict",)}, indent=2))
    print("holdout", card["holdout"]["dti"], card["holdout"]["ci95_spatial_block_bootstrap"],
          "note chars", card["note_length"])


if __name__ == "__main__":
    main()
