#!/usr/bin/env python3
"""Calibrate the shared hide-and-recover holdout against real submission history.

Problem: a HOLDOUT-DTI is a *proxy*.  It is not on the leaderboard's scale, and
writing one next to a leaderboard number invites exactly the confusion the protocol
forbids.  This script builds the missing link **empirically** instead of asserting a
projection:

1. Re-open every hash-verified registry raster (the nine focus-site files plus the
   lattice, the dense prior and two later research files).
2. Score each one on the *same* shared folds with the *same* unchanged evaluator
   (``gems57.evaluate_holdout``, pooled DTI, alpha 0.2, beta 0.8, 300 m triangular
   kernel) that lane candidates are scored on.
3. Regress the user-reported leaderboard value on that common-instrument holdout
   DTI (ordinary least squares + Spearman + leave-one-out), giving a documented
   transfer function with an honest residual spread.

Every input number is labelled.  ``user_reported_claim`` is USER-REPORTED and is
not an organiser receipt; the holdout column is HOLDOUT-DTI on this instrument.
The regression output is a CALIBRATED PROJECTION and is never written as a score.

Known biases, stated rather than hidden:
* registry rasters were built with the **full** catalogue available, while fold
  features are visible-only; they are scored here as opaque dot arrays, so no
  fold-local rebuild is possible or needed.
* the shared split forces withheld truth to lie >= 3.16 px from visible catalogue,
  which flatters catalogue-parallel placements relative to the live test set.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import evaluate_holdout as shared_eval   # noqa: E402
from gems57 import grid as shared_grid               # noqa: E402
from gems57 import holdout as shared_holdout         # noqa: E402
from emit_and_score import BLOCK_SIDE, bbox_of, detached_truth_folds  # noqa: E402
from restore_public_mirrors import verified          # noqa: E402


def score_raster_on_folds(values: np.ndarray, folds: list[dict], grid) -> dict:
    """Pooled HOLDOUT-DTI of an opaque [0,1] raster on the shared folds."""
    v = np.nan_to_num(np.asarray(values, np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    v = np.clip(v, 0.0, 1.0)
    terms, per_fold = [], {}
    for fold in folds:
        sl, (oy, ox) = bbox_of(fold["region"], pad=6)
        crop = dict(fold)
        for k in ("region", "truth", "masked_known", "visible"):
            crop[k] = fold[k][sl]
        res, term = shared_eval.evaluate(v[sl], crop, grid.footprint[sl],
                                         block_side=BLOCK_SIDE, origin=(oy, ox),
                                         global_shape=grid.shape)
        terms.append(term)
        per_fold[fold["name"]] = {k: res[k] for k in ("dti", "tp", "fp", "fn",
                                                      "n_truth", "n_emitted", "coverage")}
    stacked = np.stack(terms)
    block_terms = stacked.sum(axis=0)
    total = block_terms.sum(axis=0)
    return dict(holdout_dti=float(shared_eval.from_terms(total)),
                tpw=float(total[0]), fpw=float(total[1]), fnw=float(total[2]),
                withheld_positive_pixels=int(round(total[3])),
                emitted_in_scored_domain=int(sum(f["n_emitted"] for f in per_fold.values())),
                coverage=float(total[0] / total[3]) if total[3] else 0.0,
                per_fold=per_fold, block_terms=block_terms)


def ols(x: np.ndarray, y: np.ndarray) -> dict:
    if x.size < 3:
        return dict(n=int(x.size), slope=None, intercept=None, r2=None)
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return dict(n=int(x.size), slope=float(coef[0]), intercept=float(coef[1]),
                r2=float(1 - ss_res / ss_tot) if ss_tot > 0 else None,
                rmse=float(np.sqrt(ss_res / x.size)),
                max_abs_residual=float(np.abs(y - pred).max()))


def leave_one_out(x: np.ndarray, y: np.ndarray) -> list[dict]:
    out = []
    for i in range(x.size):
        keep = np.ones(x.size, bool); keep[i] = False
        fit = ols(x[keep], y[keep])
        if fit.get("slope") is None:
            continue
        pred = fit["slope"] * float(x[i]) + fit["intercept"]
        out.append(dict(index=int(i), held_out_reported=float(y[i]),
                        predicted_from_others=round(float(pred), 4),
                        residual=round(float(pred - y[i]), 4)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/registry_inputs.json")
    parser.add_argument("--registry-dir", type=Path, default=ROOT / "data/registry")
    parser.add_argument("--seed", type=int, default=20)
    parser.add_argument("--detach-px", type=float, nargs="+", default=[4.0, 6.0, 8.0, 12.0],
                        help="supplementary detached-truth instruments to report alongside "
                             "the unchanged shared buffered instrument")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/holdout_calibration.json")
    args = parser.parse_args()

    grid = shared_grid.load_grid()
    base_folds, _ = shared_holdout.buffered_component_draw(grid, seed=args.seed)
    manifest = json.loads(args.manifest.read_text())
    instruments = {"shared-buffered": base_folds}
    for d in args.detach_px:
        instruments[f"detached-{d:g}px"] = detached_truth_folds(base_folds, d)
    results = {}
    for label, folds in instruments.items():
        results[label] = _score_all(folds, grid, manifest, args)
        print(f"--- instrument {label}: "
              f"truth={results[label]['withheld_positive_pixels']}", flush=True)
    _finish(results, base_folds, grid, args)
    return 0


def _score_all(folds, grid, manifest, args):
    rows = []
    for entry in manifest["inputs"]:
        path = args.registry_dir / (entry["id"] + ".tif")
        if not verified(path, entry["bytes"], sha256=entry["sha256"], blob=entry["git_blob"]):
            print(f"SKIP {entry['id']}: bytes not hash-verified", flush=True)
            continue
        with rasterio.open(path) as src:
            if src.count != 1 or src.shape != grid.shape:
                print(f"SKIP {entry['id']}: not single-band on the pinned grid", flush=True)
                continue
            values = src.read(1)
        scored = score_raster_on_folds(values, folds, grid)
        rows.append(dict(id=entry["id"], sha256=entry["sha256"], source=entry.get("url"),
                         user_reported=entry.get("user_reported_claim"),
                         claim_evidence=entry.get("claim_evidence"),
                         **{k: v for k, v in scored.items() if k != "block_terms"},
                         block_terms=scored["block_terms"].tolist()))
        del values
        print(f"{entry['id']:24s} holdout={scored['holdout_dti']:.4f} "
              f"cov={scored['coverage']:.3f} emitted={scored['emitted_in_scored_domain']:7d} "
              f"reported={entry.get('user_reported_claim')}", flush=True)

    usable = [r for r in rows if isinstance(r["user_reported"], (int, float))]
    x = np.array([r["holdout_dti"] for r in usable], float)
    y = np.array([r["user_reported"] for r in usable], float)
    fit = ols(x, y)
    rho = float(spearmanr(x, y).statistic) if x.size >= 3 else None
    return dict(n_rasters_scored=len(rows), n_with_reported_value=len(usable),
                withheld_positive_pixels=int(sum(f["receipt"]["withheld_positive_pixels"]
                                                 for f in folds)),
                spearman_holdout_vs_reported=rho, fit=fit,
                leave_one_out=leave_one_out(x, y), rows=rows)


def _finish(results, base_folds, grid, args):
    out = dict(schema="wbggems.holdout-calibration.v2",
               generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               instrument=dict(evaluator=shared_eval.VERSION,
                               implementation_sha256=shared_eval.implementation_hashes(),
                               holdout="gems57.holdout.buffered_component_draw",
                               seed=args.seed, folds=[f["name"] for f in base_folds],
                               withheld_positive_pixels=int(sum(f["receipt"]["withheld_positive_pixels"]
                                                                for f in base_folds)),
                               alpha=0.2, beta=0.8, kernel_radius_m=300.0,
                               block_side_m=BLOCK_SIDE * 100),
               label_policy=dict(holdout_column="HOLDOUT-DTI (this instrument)",
                                 reported_column="USER-REPORTED, NOT ORGANIZER-CONFIRMED",
                                 regression_output="CALIBRATED PROJECTION, never a score"),
               known_bias=[
                   "PRIVILEGED-CATALOGUE BIAS: registry rasters were built with the FULL mapped "
                   "catalogue, and the proxy truth is a random 20% subset of that same catalogue, "
                   "so catalogue-hugging dots score as direct hits here. The live truth is "
                   "disjoint from the catalogue, so those dots are false positives there. This "
                   "makes cross-family comparison on this instrument invalid.",
                   "SHELL BIAS: the shared split forces withheld truth to lie >=3.16 px from "
                   "visible catalogue, so proxy truth piles up in a thin shell around mapped "
                   "traces; the detached-* instruments narrow truth to pixels far from any "
                   "visible trace to reduce it.",
                   "Fold-local candidates (this lane) never see the withheld components, so their "
                   "numbers are not inflated by the privileged-catalogue bias; registry rasters' "
                   "numbers are."],
               decisive_counterexample=(
                   "GEMSDOE32 (B2) is GEMSDOE25 with every dot within 2 px of the mapped "
                   "catalogue removed. User-reported leaderboard: 0.2600 -> 0.2778 (pruning "
                   "HELPED). On this instrument the same pruning collapses pooled DTI "
                   "0.0919 -> 0.0037 (coverage 0.142 -> 0.005), i.e. 96% of the proxy credit "
                   "came from dots hugging the mapped catalogue. The instrument's ranking of "
                   "these two files is the inverse of the organiser-reported ranking."),
               instruments=results)
    args.out.write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    for label, res in results.items():
        print(f"{label:18s} truth={res['withheld_positive_pixels']:6d} "
              f"spearman={res['spearman_holdout_vs_reported']:+.4f} "
              f"slope={res['fit']['slope']:+.3f} r2={res['fit']['r2']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    raise SystemExit(main())
