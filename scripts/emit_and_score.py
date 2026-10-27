#!/usr/bin/env python3
"""Emission + pooled hide-and-recover scoring for lane WBG2-B (and its control).

Arms scored on the *same* shared folds, the same scored domain and the same
per-fold budget, so the paired block bootstrap compares like with like:

``control_contrast``   in-repo reconstruction of the unsupervised "dotted ridge /
                       contrast-rank" family that produced the 0.2449-0.2778
                       user-reported history: rank pixels by the mean local-contrast
                       (z) rank of the six provided edge/gradient bands and take the
                       top-N.  It is *not* the historical bytes.
``candidate_topN``     supervised belief, plain top-N (isolates the value of
                       supervision alone).
``candidate_thin``     supervised belief, 1-px skeleton of a belief-thresholded
                       region, then top-N by belief inside the skeleton
                       (supervision + redundancy-free thinning).

Scoring is the unchanged shared ``gems57.evaluate_holdout.evaluate`` (pooled DTI,
alpha 0.2, beta 0.8, 300 m triangular kernel, per-20 km block terms) and the
paired CI comes from the unchanged shared ``pooled_summary``.

Emission domain (both arms): the fold's scored domain minus mapped catalogue
pixels minus a 2 px collar around **visible** mapped faults.  The collar mirrors
the organiser's masking of mapped pixels (forum thread 11516) and the user-reported
ledger evidence that pruning dots within 2 px of the catalogue raised the score
(GEMSDOE25 44,090 dots 0.2600 -> GEMSDOE32 pruned 37,654 dots 0.2778).  No
withheld truth lies inside that collar (the shared split enforces >= 3.16 px), so
the collar cannot hide a true positive here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import evaluate_holdout as shared_eval   # noqa: E402  (pinned shared)
from gems57 import grid as shared_grid               # noqa: E402  (pinned shared)
from gems57 import holdout as shared_holdout         # noqa: E402  (pinned shared)

BANK = ROOT / "data" / "features" / "bank_u8.npy"
LANE_DIR = ROOT / "data" / "lane"
NODATA_U8 = 255
# provided bands whose local-contrast rank defines the unsupervised control
CONTRAST_BANDS = ("iso_grav_anom_hg", "tmi_hg", "tc", "det_elev_slope",
                  "geod_2ndinv", "iso_grav_anom_slope")
BLOCK_SIDE = 200          # 20 km shared spatial bootstrap cluster


def band_names() -> list[str]:
    import rasterio
    with rasterio.open(ROOT / "data" / "training_features_mirror.tif") as src:
        return [src.descriptions[i].split(" - ")[0] for i in range(src.count)]


def contrast_surface(bank, names: list[str], footprint: np.ndarray) -> np.ndarray:
    """Mean local-contrast rank over the six edge bands; NaN nodata -> 0."""
    layers = []
    for nm in CONTRAST_BANDS:
        i = names.index(nm)
        z = np.asarray(bank[2 * i + 1], np.float32)
        z[z == NODATA_U8] = 0.0
        layers.append(z)
    out = np.mean(np.stack(layers), axis=0)
    out[~footprint] = 0.0
    return out


def detached_truth_folds(folds: list[dict], detach_px: float) -> list[dict]:
    """Same shared folds, truth narrowed to pixels far from any visible mapped fault.

    The shared split forces every withheld pixel to lie >= 3.16 px from a visible
    catalogue pixel, so proxy truth piles up in a thin shell around mapped traces
    and dots hugging those traces collect credit they cannot collect live.  This
    narrowing keeps the evaluator, split, masks and metric unchanged; only the
    scored truth subset changes, and the change is reported with the result.
    """
    out = []
    for fold in folds:
        dist = ndi.distance_transform_edt(~fold["visible"])
        truth = fold["truth"] & (dist > detach_px)
        f2 = dict(fold)
        f2["truth"] = truth
        f2["receipt"] = dict(fold["receipt"], detached_truth_pixels=int(truth.sum()),
                             detach_px=detach_px, withheld_positive_pixels=int(truth.sum()))
        out.append(f2)
    return out


def bbox_of(mask: np.ndarray, pad: int = 6):
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    return (slice(max(0, ys.min() - pad), min(h, ys.max() + pad + 1)),
            slice(max(0, xs.min() - pad), min(w, xs.max() + pad + 1))), (int(ys.min()), int(xs.min()))


def top_n(domain: np.ndarray, score: np.ndarray, n: int) -> np.ndarray:
    """Boolean support: the ``n`` highest-scoring pixels inside ``domain``."""
    out = np.zeros(domain.shape, bool)
    idx = np.flatnonzero(domain.ravel())
    if idx.size == 0 or n <= 0:
        return out
    vals = score.ravel()[idx]
    k = min(int(n), idx.size)
    if k >= idx.size:
        out.ravel()[idx] = True
        return out
    cut = np.argpartition(-vals, k - 1)[:k]
    out.ravel()[idx[cut]] = True
    return out


def thin_to_budget(domain: np.ndarray, belief: np.ndarray, n: int,
                   ratio: float = 3.0, rounds: int = 14) -> tuple[np.ndarray, dict]:
    """1-px skeleton of a belief-thresholded region, trimmed to ``n`` by belief.

    The threshold is bisected so that the *region* carries about ``ratio`` x budget
    pixels (a ridge a few pixels wide), which is what a 1-px skeleton of a linear
    target needs.  Under DTI the second and third rows of a probability ridge cost
    0.2*(1-k) each and add no truth credit, so thinning is the emission analogue of
    the metric's marginal rule.  If the skeleton is shorter than the budget, the
    remainder is filled with the highest-belief region pixels adjacent to it, so no
    cheap budget is wasted.  The best (closest-to-target) iterate is kept, not the
    last one -- an earlier version kept the last and could emit nothing.
    """
    vals = belief[domain]
    if vals.size == 0 or n <= 0:
        return np.zeros(domain.shape, bool), dict(threshold=None, skeleton_pixels=0,
                                                  region_pixels=0, emitted=0,
                                                  budget=int(n),
                                                  domain_cells=int(domain.sum()),
                                                  shortfall_filled_from_domain=0,
                                                  target_region_pixels=0,
                                                  bisection_rounds=0)
    sl, _origin = bbox_of(domain, pad=2)
    d_sub, b_sub = domain[sl], belief[sl]
    order = np.sort(vals)
    target_region = int(ratio * n)
    lo_t = float(order[min(order.size - 1, max(0, order.size - target_region * 4))])
    hi_t = float(order[-1]) + 1e-9
    best = None
    for _ in range(rounds):
        t = 0.5 * (lo_t + hi_t)
        region_sub = d_sub & (b_sub >= t)
        region_count = int(region_sub.sum())
        if region_count == 0:
            hi_t = t
            continue
        skel_sub = skeletonize(region_sub) & d_sub
        count = int(skel_sub.sum())
        err = abs(region_count - target_region)
        if best is None or err < best[0]:
            best = (err, float(t), count, region_count, skel_sub.copy())
        if region_count > target_region:
            lo_t = t
        else:
            hi_t = t
        if err <= max(50, 0.05 * target_region):
            break
    _err, t, skel_count, region_count, skel_sub = best
    support = np.zeros(domain.shape, bool)
    support[sl] = skel_sub
    shortfall = 0
    if skel_count > n:
        support = top_n(support, belief, n)
    elif skel_count < n:
        extra = top_n(domain & (belief >= t) & ~support, belief, n - skel_count)
        support = support | extra
        # The thresholded region can hold fewer spare pixels than the budget
        # asks for (a thin corridor, or a budget near the domain size).  Spend
        # the remainder on the highest-belief admissible pixels anyway: an
        # unspent dot is a guaranteed false negative, never a false positive.
        if int(support.sum()) < n:
            shortfall = n - int(support.sum())
            support = support | top_n(domain & ~support, belief, shortfall)
    emitted = int(support.sum())
    return support, dict(threshold=float(t), skeleton_pixels=int(skel_count),
                         region_pixels=int(region_count), emitted=emitted,
                         budget=int(n), domain_cells=int(domain.sum()),
                         shortfall_filled_from_domain=shortfall,
                         target_region_pixels=target_region, bisection_rounds=rounds)


def emit_and_score(beliefs: dict[str, np.ndarray], folds: list[dict], grid,
                   contrast: np.ndarray, budgets: list[int], collar_px: int = 2,
                   arms: tuple[str, ...] = ("control_contrast", "candidate_topN",
                                            "candidate_thin", "candidate_thin_ring"),
                 ring_value: float = 0.5) -> dict:
    names = band_names()
    total_active = 0
    domains = {}
    for fold in folds:
        active = fold["region"] & ~fold["masked_known"]
        vis_edt = ndi.distance_transform_edt(~fold["visible"])
        domain = grid.footprint & active & (vis_edt > collar_px)
        domains[fold["name"]] = domain
        total_active += int(domain.sum())
    results = {}
    for budget in budgets:
        key = f"budget_{budget}"
        terms = {arm: [] for arm in arms}
        per_fold = {arm: {} for arm in arms}
        for fold in folds:
            fname = fold["name"]
            domain = domains[fname]
            share = int(domain.sum()) / total_active
            n_fold = max(1, int(round(budget * share)))
            belief = beliefs[fname]
            sl, (oy, ox) = bbox_of(fold["region"], pad=6)
            origin = (oy, ox)
            emissions = {}
            values = {}
            if "control_contrast" in arms:
                emissions["control_contrast"] = top_n(domain, contrast, n_fold)
            if "candidate_topN" in arms:
                emissions["candidate_topN"] = top_n(domain, belief, n_fold)
            if "candidate_thin" in arms or "candidate_thin_ring" in arms:
                sup, info = thin_to_budget(domain, belief, n_fold)
                emissions["candidate_thin"] = sup
                per_fold["candidate_thin"].setdefault("thinning", {})[fname] = info
                if "candidate_thin_ring" in arms:
                    ring = ndi.binary_dilation(sup, np.ones((3, 3), bool)) & domain & ~sup
                    emissions["candidate_thin_ring"] = sup | ring
                    values["candidate_thin_ring"] = (sup, ring)
            crop_fold = dict(fold)
            for k in ("region", "truth", "masked_known", "visible"):
                crop_fold[k] = fold[k][sl]
            valid_sub = grid.footprint[sl]
            for arm, sup in emissions.items():
                pred = np.zeros(grid.shape, np.float32)
                if arm in values:
                    core, ring = values[arm]
                    pred[core] = 1.0
                    pred[ring] = np.float32(ring_value)
                else:
                    pred[sup] = 1.0
                res, term = shared_eval.evaluate(pred[sl], crop_fold, valid_sub,
                                                 block_side=BLOCK_SIDE, origin=origin,
                                                 global_shape=grid.shape)
                terms[arm].append(term)
                per_fold[arm][fname] = {k: res[k] for k in
                                        ("dti", "tp", "fp", "fn", "n_truth", "n_emitted", "coverage")}
                del pred
        pooled = {arm: float(shared_eval.from_terms(np.stack(t).sum(axis=(0, 1))))
                  for arm, t in terms.items()}
        block_terms = {arm: np.stack(t).sum(axis=0) for arm, t in terms.items()}
        results[key] = dict(budget=budget, pooled_dti=pooled,
                            ring_value=ring_value,
                            emitted_per_fold={arm: sum(f["n_emitted"] for f in per_fold[arm].values()
                                                       if isinstance(f, dict) and "n_emitted" in f)
                                              for arm in arms},
                            per_fold=per_fold,
                            block_terms={arm: block_terms[arm].tolist() for arm in arms})
        print(f"{key}: " + " ".join(f"{a}={pooled[a]:.4f}" for a in arms), flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20)
    parser.add_argument("--budgets", type=int, nargs="+", default=[25_000, 40_000, 60_000, 85_000])
    parser.add_argument("--collar-px", type=int, default=2)
    parser.add_argument("--ring-value", type=float, default=0.5)
    parser.add_argument("--detach-px", type=float, default=0.0,
                        help="0 = unchanged shared buffered instrument; >0 narrows scored "
                             "truth to pixels farther than this from any visible mapped fault")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence" / "lane_b_sweep.json")
    args = parser.parse_args()
    t0 = time.time()
    grid = shared_grid.load_grid()
    folds, _ = shared_holdout.buffered_component_draw(grid, seed=args.seed)
    instrument = "shared-buffered"
    if args.detach_px > 0:
        folds = detached_truth_folds(folds, args.detach_px)
        instrument = f"detached-{args.detach_px:g}px"
    bank = np.load(BANK, mmap_mode="r")
    names = band_names()
    contrast = contrast_surface(bank, names, grid.footprint)
    beliefs = {f["name"]: np.load(LANE_DIR / f"belief_{f['name']}.npy") for f in folds}
    sweep = emit_and_score(beliefs, folds, grid, contrast, args.budgets, args.collar_px,
                           ring_value=args.ring_value)
    out = dict(instrument="gems57.holdout.buffered_component_draw (unchanged shared)",
               instrument_variant=instrument,
               evaluator=shared_eval.VERSION,
               evaluator_implementation_sha256=shared_eval.implementation_hashes(),
               block_side_px=BLOCK_SIDE, collar_px=args.collar_px,
               contrast_bands=list(CONTRAST_BANDS),
               seconds=round(time.time() - t0, 1), sweep=sweep)
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out} in {out['seconds']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
