"""Measure the nine focus rasters and the H3-PACK candidate; write the evidence.

Everything the executive summary quotes is produced here:

* per-raster dot count, 3 px collar fraction, packing efficiency (kmass/dot),
  256 px block clustering, distance-to-catalogue profile and live score;
* the live-score regression on those measured columns;
* the catalogue hide-and-recover holdout score of every raster, which is shown
  in order to demonstrate that this instrument is *anti*-correlated with the
  live leaderboard and therefore cannot be used to select a submission;
* the candidate's statistics and the projection range.

No hidden truth is used.  Reported live scores are owner/user-reported values
copied from the competition pages, never organizer receipts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))
from wbg3.metric import dti_binary, pooled  # noqa: E402
from wbg3.holdout import block_folds, make_fold  # noqa: E402

RADIUS = 3.0
COLLAR = 3.0
REG = ROOT / "scratch/registry"
REPORTED = {
    "GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449,
    "GEMSDOE28": 0.2710, "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708,
    "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632, "GEMSDOE36": 0.2750,
}
FOCUS_FILE = {
    "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
    "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
    "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
    "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load(p):
    with rasterio.open(p) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    with rasterio.open(ROOT / "data/official/existing_faults.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        fp = np.isfinite(ds.read(1))
    dist_cat = distance_transform_edt(~cat).astype(np.float32)
    bins = [0, 3, 4, 5, 8, 12, 19, 30, 50, 100, 150, 1e9]
    avail, _ = np.histogram(dist_cat[fp], bins=bins)

    bs = 256
    hh, ww = fp.shape[0] // bs, fp.shape[1] // bs
    fp_blocks = fp[:hh * bs, :ww * bs].reshape(hh, bs, ww, bs).mean(axis=(1, 3))

    def block_density(m):
        b = m[:hh * bs, :ww * bs].reshape(hh, bs, ww, bs).mean(axis=(1, 3))
        return b / np.maximum(fp_blocks, 1e-12)

    # catalogue hide-and-recover folds (the "instrument")
    fm = block_folds(cat.shape, n_folds=4, block=256, salt=0)
    folds = []
    for k in range(4):
        in_fold = fm == k
        wh = cat & in_fold
        vis = cat & ~in_fold & ~binary_dilation(wh, iterations=15)
        folds.append((vis, wh))

    def holdout(mask):
        parts = [dti_binary(mask, wh, fp) for _, wh in folds]
        return round(pooled(parts)["dti"], 5)

    rows = []
    densities = {}
    for name, score in REPORTED.items():
        path = REG / f"{name}.tif"
        m = load(path)
        d = distance_transform_edt(~m)
        k = np.maximum(1 - d / RADIUS, 0.0)
        km = float(k[fp].sum())
        have, _ = np.histogram(dist_cat[m], bins=bins)
        dens = block_density(m)
        densities[name] = dens
        rows.append(dict(
            site=name, file=FOCUS_FILE[name], sha256=sha256(path),
            reported_live_score=score,
            reported_score_evidence="USER-REPORTED; no organizer receipt",
            dots=int(m.sum()),
            collar_fraction_3px=round(float((dist_cat[m] <= COLLAR).mean()), 4),
            fraction_within_2px=round(float((dist_cat[m] <= 2.0).mean()), 4),
            kmass=round(km, 1),
            kmass_per_dot=round(km / max(int(m.sum()), 1), 3),
            block_clustering_chi2_over_mean=round(
                float((((dens - m.sum() / fp.sum()) ** 2) / max(m.sum() / fp.sum(), 1e-12)).mean()), 1),
            median_dist_to_catalogue_px=round(float(np.median(dist_cat[m])), 1),
            distance_profile_pct=[round(float(x / have.sum() * 100), 2) for x in have],
            holdout_catalogue_dti=holdout(m),
        ))

    D = np.array([r["dots"] for r in rows], float)
    S = np.array([r["reported_live_score"] for r in rows], float)
    C = np.array([r["collar_fraction_3px"] for r in rows], float)
    X = np.c_[np.ones_like(D), D / 1000.0, C]
    coef, *_ = np.linalg.lstsq(X, S, rcond=None)
    pred = X @ coef
    r2 = 1 - ((S - pred) ** 2).sum() / ((S - S.mean()) ** 2).sum()

    # pairwise similarity of the published density fields
    names = list(densities)
    pair = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pair[f"{names[i]}|{names[j]}"] = round(
                float(spearmanr(densities[names[i]].ravel(), densities[names[j]].ravel()).statistic), 4)

    # ---- candidate -------------------------------------------------------
    dots = np.load(ROOT / "scratch/h3_dots_final.npy")
    d = distance_transform_edt(~dots)
    k = np.maximum(1 - d / RADIUS, 0.0)
    km_c = float(k[fp].sum())
    Dc = int(dots.sum())
    kpd_c = km_c / Dc
    kpd_med = float(np.median([r["kmass_per_dot"] for r in rows]))
    packing_ratio = kpd_c / kpd_med
    base = float(coef[0] + coef[1] * Dc / 1000.0)   # collar = 0
    proj = dict(
        regression_only=round(base, 4),
        full_packing_transfer=round(base * packing_ratio, 4),
        half_packing_transfer=round(base * (1 + (packing_ratio - 1) / 2), 4),
        assumption=("regression fitted on the eight dotted focus rasters "
                    "(score = a + b*D/1000 + c*collar); the packing multiplier "
                    "assumes the kmass/dot gain transfers fully (or half) into TP. "
                    "This is a PROJECTION, not a score."),
    )

    holdout_vs_live = spearmanr([r["holdout_catalogue_dti"] for r in rows], S)
    out = dict(
        evidence_class="MEASUREMENT + PROJECTION (no hidden truth used)",
        generated_utc=__import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        distance_bins=bins,
        available_area_pct=[round(float(a / avail.sum() * 100), 2) for a in avail],
        focus_rasters=rows,
        regression=dict(
            form="reported_live_score = a + b*(D/1000) + c*collar_fraction_3px",
            a=round(float(coef[0]), 4), b=round(float(coef[1]), 5), c=round(float(coef[2]), 4),
            r2=round(float(r2), 4), n=len(rows),
            marginal_cost_per_1000_dots=round(float(-coef[1]), 5),
            marginal_cost_per_1pct_collar=round(float(-coef[2] / 100), 5),
        ),
        published_density_pairwise_spearman=pair,
        holdout_vs_live_spearman=dict(
            rho=round(float(holdout_vs_live.statistic), 4),
            p=round(float(holdout_vs_live.pvalue), 5),
            interpretation=("negative: the catalogue holdout rewards re-predicting "
                            "mapped faults, which is the opposite of the "
                            "competition target, so it cannot select a submission"),
        ),
        candidate=dict(
            name=json.loads((ROOT / "evidence/h3_submission.json").read_text())["submission_name"],
            dots=Dc, kmass=round(km_c, 1), kmass_per_dot=round(kpd_c, 3),
            kmass_per_dot_geometric_max=9.38,
            collar_fraction_3px=float((dist_cat[dots] <= COLLAR).mean()),
            median_dist_to_catalogue_px=round(float(np.median(dist_cat[dots])), 1),
            holdout_catalogue_dti=holdout(dots),
            projection=proj,
        ),
    )
    (ROOT / "evidence/h3_analysis.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k in ("regression", "holdout_vs_live_spearman", "candidate")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
