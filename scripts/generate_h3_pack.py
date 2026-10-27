"""Historical H3 placement method, DISABLED. Its saved raster fails the literal lattice gate. Original causal, uniqueness and score-projection claims are superseded by evidence/local_artifact_audit_20261027.json; code is retained only for research provenance."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))

RADIUS = 3.0            # 300 m kernel = 3 px at 100 m
COLLAR_PX = 3.0         # measured-negative zone around every mapped fault
BUDGET = 34000          # dots
MIN_SEP_PX = 5.0        # Poisson-disk radius; >= 5 gives kmass/dot ~ 9.38
SHOULDER = 0.30         # measured 3-12 px enrichment (B2 is 1.2-2.0x there)


def region_masks():
    with rasterio.open(ROOT / "data/official/existing_faults.tif") as ds:
        cat = ds.read(1) == 1
    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    return cat, footprint


#: Target enrichment of dot density relative to the *available area* in each
#: distance-to-catalogue band.  The only design freedom left once the collar is
#: excluded and the budget is fixed; anchored on the measured GEMSDOE32 B2
#: profile (1.2-2.0x inside 3-12 px, ~1.0x beyond) which is the only raster with
#: a reported score of 0.2778.
TARGET_ENRICHMENT = {
    (0.0, 3.0): 0.00,
    (3.0, 4.0): 1.55,
    (4.0, 5.0): 1.45,
    (5.0, 8.0): 1.30,
    (8.0, 12.0): 1.15,
    (12.0, 19.0): 1.00,
    (19.0, 30.0): 1.00,
    (30.0, 50.0): 1.00,
    (50.0, 100.0): 1.00,
    (100.0, 150.0): 1.00,
    (150.0, 1e9): 1.00,
}


def regional_modulation(footprint, dist_cat, bands_path="scratch/fbank/bands.f32"):
    """Block-scale geological modulation, made independent of distance.

    The nine published rasters share one regional density field (pairwise
    Spearman 0.996-0.999 of 256 px block densities) and that field correlates
    +0.79 with a simple scarp/magnetics score.  It is therefore reproduced here
    at block scale only -- fine-scale structure is what pushed the earlier
    drafts into the collar the evidence says to avoid.
    """
    path = ROOT / bands_path
    if not path.exists():
        return np.ones(footprint.shape, dtype=np.float32)
    from scipy.ndimage import gaussian_filter
    stats = json.loads((ROOT / "scratch/fbank/stats.json").read_text())
    mm = np.memmap(path, dtype=np.float32, mode="r",
                   shape=(19, *footprint.shape))

    def band(i):
        a = np.array(mm[i - 1], dtype=np.float32)
        s = stats[i - 1]
        a = (a - s["p50"]) / (s["iqr"] if s["iqr"] else 1.0)
        return np.where(np.isfinite(a), a, 0.0)

    det_elev, det_slope, tmi_hg, tilt = band(12), band(19), band(3), band(6)
    smooth = gaussian_filter(det_elev, 1.2)
    gy, gx = np.gradient(smooth)
    curv = -(gaussian_filter(gy, 1.5, order=(1, 0)) + gaussian_filter(gx, 1.5, order=(0, 1)))
    scarp = np.maximum(det_slope, 0.0) * (1.0 + np.maximum(curv, 0.0))
    mag = np.maximum(gaussian_filter(np.maximum(tmi_hg, 0.0), 1.0) *
                     (1.0 + gaussian_filter(np.abs(tilt), 1.0)), 0.0)
    rough = np.abs(det_elev - gaussian_filter(det_elev, 4.0))
    score = np.ones(footprint.shape, dtype=np.float32)
    for term, w in ((scarp, 0.70), (mag, 0.45), (rough, 0.20)):
        q = np.nanpercentile(term[footprint], 99.0) or 1.0
        score += w * np.clip(term / q, 0.0, 3.0)
    score = gaussian_filter(score, 56.0)          # block scale only

    # remove any residual distance dependence, then normalise
    dbins = np.concatenate([np.arange(0, 21), [24, 28, 34, 42, 55, 75, 100, 140, 200, 300, 1000]])
    idx = np.digitize(dist_cat, dbins) - 1
    num = np.zeros(len(dbins) + 1)
    cnt = np.zeros(len(dbins) + 1)
    np.add.at(num, idx[footprint], score[footprint].astype(np.float64))
    np.add.at(cnt, idx[footprint], 1.0)
    mean = np.maximum(num / np.maximum(cnt, 1), 1e-9)
    rel = score / mean[idx]
    rel = rel / np.median(rel[footprint])
    return np.clip(rel, 0.40, 2.50).astype(np.float32)


def place_dots(footprint, dist_cat, regional, budget, min_sep=MIN_SEP_PX, seed=20261027):
    """Quota-stratified weighted Poisson-disk placement.

    Each distance band receives exactly the number of dots implied by
    ``TARGET_ENRICHMENT``; inside a band, dots are drawn with probability
    proportional to the regional modulation and thinned to a ``min_sep``
    Poisson-disk, which is what lifts ``kmass/dot`` from the published 8.0 to
    the geometric maximum of 9.38.
    """
    rng = np.random.default_rng(seed)
    edges = sorted(TARGET_ENRICHMENT)
    avail = {}
    for lo, hi in edges:
        avail[(lo, hi)] = int(((dist_cat > max(lo, COLLAR_PX)) & (dist_cat <= hi) & footprint).sum())
    weight = {k: avail[k] * TARGET_ENRICHMENT[k] for k in edges}
    total = sum(weight.values())
    quotas = {k: int(round(budget * weight[k] / total)) for k in edges}

    dots = np.zeros(footprint.shape, dtype=bool)
    h, w = footprint.shape
    r = int(np.ceil(min_sep))
    for (lo, hi), quota in quotas.items():
        if quota <= 0:
            continue
        mask = (dist_cat > max(lo, COLLAR_PX)) & (dist_cat <= hi) & footprint
        idx = np.flatnonzero(mask.ravel())
        if idx.size == 0:
            continue
        wgt = regional.ravel()[idx].astype(np.float64)
        # Efraimidis-Spirakis weighted sampling without replacement, then
        # sequential thinning for the Poisson-disk spacing.
        keys = rng.random(idx.size) ** (1.0 / np.maximum(wgt, 1e-6))
        order = idx[np.argsort(-keys)]
        taken = 0
        for j in order:
            y, x = divmod(int(j), w)
            if dots[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].any():
                continue
            dots[y, x] = True
            taken += 1
            if taken >= quota:
                break
    return dots


def budget_curve(margins, n_truth_candidates=(10000, 20000, 40000, 80000)):
    """Upper-bound proxy TP(D)/(0.2 D + 0.8 N) over a range of hidden-truth sizes.

    This is an UPPER bound on the true DTI (drops the 0.2*TP term in the
    denominator), used only to compare budgets, never reported as a score.
    """
    tp = np.cumsum(margins)
    d = np.arange(1, margins.size + 1, dtype=float)
    out = {}
    for n in n_truth_candidates:
        curve = tp / (0.2 * d + 0.8 * n)
        out[n] = dict(argmax_D=int(np.argmax(curve) + 1),
                      best=float(curve.max()),
                      at_budget=float(curve[min(BUDGET, len(curve)) - 1]))
    return out


def main() -> int:
    raise RuntimeError("STOP: historical lane fails the literal registry gate or lacks pre-placement evidence; see evidence/local_artifact_audit_20261027.json. Do not generate or approve a submission.")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--min-sep", type=float, default=MIN_SEP_PX)
    ap.add_argument("--out", default="scratch/h3_dots_final.npy")
    ap.add_argument("--report", default="evidence/h3_generation.json")
    args = ap.parse_args()
    t0 = time.time()

    cat, footprint = region_masks()
    dist_cat = distance_transform_edt(~cat).astype(np.float32)
    regional = regional_modulation(footprint, dist_cat)
    np.save(ROOT / "scratch/h3_regional.npy", regional)
    dots = place_dots(footprint, dist_cat, regional, args.budget, min_sep=args.min_sep)
    dots = np.asarray(dots, dtype=bool)
    np.save(ROOT / args.out, dots)
    print(f"[place] {int(dots.sum())} dots ({time.time()-t0:.1f}s)", flush=True)

    d = distance_transform_edt(~dots)
    k = np.maximum(1.0 - d / RADIUS, 0.0)
    kmass = float(k[footprint].sum())
    D = int(dots.sum())
    bins = [0, 3, 4, 5, 8, 12, 19, 30, 50, 100, 150, 1e9]
    avail, _ = np.histogram(dist_cat[footprint], bins=bins)
    have, _ = np.histogram(dist_cat[dots], bins=bins)
    profile = {f"{bins[i]}-{bins[i+1]}":
               dict(available_pct=round(float(avail[i] / avail.sum() * 100), 2),
                    dots_pct=round(float(have[i] / have.sum() * 100), 2),
                    enrichment=round(float(have[i] / max(avail[i], 1e-9) *
                                           avail.sum() / max(have.sum(), 1)), 2))
               for i in range(len(bins) - 1)}
    report = dict(
        evidence_class="DESIGN-MEASUREMENT (no hidden truth used)",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        budget=D, min_sep=args.min_sep, collar_px=COLLAR_PX, radius_px=RADIUS,
        kmass=kmass, kmass_per_dot=kmass / max(D, 1),
        kmass_per_dot_geometric_max=9.38,
        collar_fraction=float((dist_cat[dots] <= COLLAR_PX).mean()),
        median_dist_to_catalogue=float(np.median(dist_cat[dots])),
        distance_profile=profile,
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / args.report).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
