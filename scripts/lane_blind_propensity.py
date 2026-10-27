#!/usr/bin/env python3
"""Lane WBG2-B: supervised blind-trace propensity, hide-and-recover instrument.

Hypothesis (this lane's single method paragraph)
-----------------------------------------------
Expert-labelled *new* faults in the GeoDAWN region are physical discontinuities
that leave a measurable imprint in the 19 provided bands (magnetic and gravity
edges, detrended-elevation scarps, geodetic strain concentration, seismicity
proximity, cover thickness and conductivity contrast) even where no trace has been
mapped.  A pixel classifier that learns to recognise fault pixels **from features
that do not include the fault itself** should therefore rank unmapped fault-like
pixels above background.  The organiser masks mapped catalogue pixels out of
scoring (forum thread 11516), so the useful output is the off-catalogue part of
that ranking, emitted as a thin, redundancy-free support: each emitted pixel must
cover new truth rather than duplicate a neighbour's 300 m kernel credit.

Why the obvious construction fails (verified in this sandbox)
------------------------------------------------------------
Training positives = mapped catalogue pixels together with a
``distance_to_visible_catalogue`` feature is a **direct label encoder**: every
positive has dcat == 0, the internal validation AUC saturates at 1.000, and the
fitted model returns a constant belief on the scored domain (holdout AUC 0.500).
Measured, not assumed.  The repair is an *inner* hide-and-recover draw: hide whole
components of the visible catalogue, build every catalogue-derived feature from
what is left, and train on the hidden components.  The model then learns
"fault-like given that this pixel is not itself mapped", which is the target task,
and train/prediction catalogue context are matched by construction.

Instrument (parallel-run protocol rule 2, unchanged shared tools)
----------------------------------------------------------------
* ``gems57.holdout.buffered_component_draw`` -- withhold whole catalogue
  components per quadrant with a 3 px feature-context buffer.
* every catalogue-derived feature is rebuilt **fold-locally from visible faults
  only**; the shared full-catalogue ``geo_f32``/``dtip_f32`` caches are never used.
* ``gems57.evaluate_holdout.evaluate`` (called by ``emit_and_score.py``) -- pooled
  DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) + per-20 km-block terms.
* rule 4 leakage canary: every feature is scored alone on the outer holdout.

Only *beliefs* and receipts are written here; emission and scoring live in
``scripts/emit_and_score.py`` so the sweep never retrains.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import grid as shared_grid            # noqa: E402  (pinned shared)
from gems57 import holdout as shared_holdout      # noqa: E402  (pinned shared)
from wbggems.novelty import single_feature_auc    # noqa: E402

BANK = ROOT / "data" / "features" / "bank_u8.npy"
FEATURES_TIF = ROOT / "data" / "training_features_mirror.tif"
LANE_DIR = ROOT / "data" / "lane"
NODATA_U8 = 255
CLIP_PX = 60.0          # saturate distance features (6 km)
DENS_RADII = (5, 15)    # shared builder's catalogue-density disc radii
STRUCT3 = np.ones((3, 3), bool)


# --------------------------------------------------------------------------- #
# fold-local, visible-faults-only catalogue features
# --------------------------------------------------------------------------- #
def disc_count(mask: np.ndarray, radius: int) -> np.ndarray:
    """Exact count of ``mask`` pixels in a closed disc of ``radius`` pixels.

    Row-span prefix sums (2r+1 shifts) instead of a 707-tap convolution.  Verified
    equal to ``ndi.convolve`` with the shared disc kernel on random fixtures
    (``tests/test_lane_components.py``).
    """
    m = np.pad(mask.astype(np.float32), radius, mode="constant")
    csum = np.concatenate([np.zeros((m.shape[0], 1), np.float32),
                           np.cumsum(m, axis=1, dtype=np.float32)], axis=1)
    h, w = mask.shape
    out = np.zeros((h, w), np.float32)
    for j in range(-radius, radius + 1):
        half = int(np.floor(np.sqrt(radius * radius - j * j)))
        rows = slice(radius + j, radius + j + h)
        out += csum[rows, radius + half + 1: radius + half + 1 + w]
        out -= csum[rows, radius - half: radius - half + w]
    return out


def tip_mask(cat: np.ndarray) -> np.ndarray:
    """Vectorised equivalent of the shared builder's per-component tip rule.

    Shared rule: per 8-connected component ``m`` take ``m & ~erode3x3(m)``, or all
    of ``m`` when that is empty.  Erosion distributes over 8-disconnected
    components, so one full-grid erosion plus a bincount reproduces it exactly
    (verified against the literal loop on 250 random real components).
    """
    cat = np.asarray(cat, bool)
    interior = ndi.binary_erosion(cat, structure=STRUCT3)
    boundary = cat & ~interior
    lab, n = ndi.label(cat, structure=STRUCT3)
    if n == 0:
        return boundary
    has_boundary = np.bincount(lab[boundary].ravel(), minlength=n + 1) > 0
    orphan_labels = np.flatnonzero(~has_boundary)
    if orphan_labels.size:
        ys, xs = np.nonzero(cat & ~boundary)
        keep = np.isin(lab[ys, xs], orphan_labels)
        boundary[ys[keep], xs[keep]] = True
    return boundary


def catalogue_features(visible: np.ndarray) -> tuple[list[str], list[np.ndarray]]:
    """Five catalogue-derived layers built from ``visible`` faults only."""
    dcat = ndi.distance_transform_edt(~visible).astype(np.float32)
    dtip = ndi.distance_transform_edt(~tip_mask(visible)).astype(np.float32)
    names = ["dcat_vis", "log1p_dcat_vis", "dtip_vis"]
    layers = [np.minimum(dcat, CLIP_PX), np.log1p(np.minimum(dcat, CLIP_PX)),
              np.minimum(dtip, CLIP_PX)]
    for r in DENS_RADII:
        names.append(f"cdens{r}_vis")
        layers.append(disc_count(visible, r))
    del dcat, dtip
    return names, layers


# --------------------------------------------------------------------------- #
# inner hide-and-recover draw (removes the dcat label encoder)
# --------------------------------------------------------------------------- #
def inner_component_draw(catalogue: np.ndarray, seed: int, frac: float = 0.20,
                         buffer_px: int = 3) -> tuple[np.ndarray, np.ndarray, dict]:
    """Hide whole 8-connected components until ``frac`` of the pixels are hidden.

    Mirrors ``gems57.holdout._pick_segments`` semantics (random component order,
    cumulative size to target) but globally rather than per quadrant, and returns
    the *visible* context with a ``buffer_px`` collar removed so no feature sees a
    truth-shaped halo.
    """
    cat = np.asarray(catalogue, bool)
    lab, n = ndi.label(cat, structure=STRUCT3)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    rng = np.random.default_rng(seed)
    ids = np.arange(1, n + 1)
    perm = rng.permutation(ids)
    cum = np.cumsum(sizes[perm])
    k = int(np.searchsorted(cum, frac * float(cat.sum()))) + 1
    chosen = perm[: min(k, perm.size)]
    hidden = np.isin(lab, chosen) & cat
    collar = ndi.distance_transform_edt(~hidden) <= buffer_px
    visible = cat & ~collar
    receipt = dict(inner_seed=int(seed), inner_frac=frac, buffer_px=buffer_px,
                   hidden_components=int(chosen.size), eligible_components=int(n),
                   hidden_positive_pixels=int(hidden.sum()),
                   visible_context_pixels=int(visible.sum()),
                   catalogue_pixels=int(cat.sum()))
    return hidden, visible, receipt


# --------------------------------------------------------------------------- #
# feature assembly
# --------------------------------------------------------------------------- #
def band_names() -> list[str]:
    with rasterio.open(FEATURES_TIF) as src:
        return [src.descriptions[i].split(" - ")[0] for i in range(src.count)]


def feature_names() -> list[str]:
    names = band_names()
    return ([f"q_{n}" for n in names] + [f"z_{n}" for n in names]
            + ["dcat_vis", "log1p_dcat_vis", "dtip_vis", "cdens5_vis", "cdens15_vis"])


def stack_rows(bank, cat_layers, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    n = ys.size
    nb = bank.shape[0]
    out = np.empty((n, nb + len(cat_layers)), np.float32)
    for i in range(nb):
        v = bank[i][ys, xs].astype(np.float32)
        v[v == NODATA_U8] = np.nan
        out[:, i] = v
    for j, layer in enumerate(cat_layers):
        out[:, nb + j] = layer[ys, xs]
    return out


def stack_rows_chunked(bank, cat_layers, ys: np.ndarray, xs: np.ndarray,
                       chunk: int = 400_000) -> np.ndarray:
    bounds = list(zip(range(0, ys.size, chunk), range(chunk, ys.size + chunk, chunk)))
    parts = [stack_rows(bank, cat_layers, ys[a:b], xs[a:b]) for a, b in bounds]
    return np.concatenate(parts) if len(parts) > 1 else parts[0]


# --------------------------------------------------------------------------- #
# model
# --------------------------------------------------------------------------- #
def train_propensity(x: np.ndarray, y: np.ndarray, seed: int, max_iter: int = 300):
    from sklearn.ensemble import HistGradientBoostingClassifier
    model = HistGradientBoostingClassifier(
        loss="log_loss", learning_rate=0.06, max_iter=max_iter, max_leaf_nodes=31,
        min_samples_leaf=80, l2_regularization=1.0, max_bins=128,
        early_stopping=True, validation_fraction=0.2, n_iter_no_change=30,
        scoring="roc_auc", random_state=seed)
    model.fit(x, y)
    return model


def predict_grid(model, bank, cat_layers, domain: np.ndarray,
                 rows_per_chunk: int = 128) -> np.ndarray:
    """Belief over ``domain`` (bool, full grid), zero elsewhere; float32."""
    h, w = domain.shape
    belief = np.zeros((h, w), np.float32)
    nb = bank.shape[0]
    ncat = len(cat_layers)
    for y0 in range(0, h, rows_per_chunk):
        y1 = min(h, y0 + rows_per_chunk)
        sub = domain[y0:y1]
        if not sub.any():
            continue
        ys, xs = np.nonzero(sub)
        ys = ys + y0
        x = np.empty((ys.size, nb + ncat), np.float32)
        for i in range(nb):
            v = bank[i][ys, xs].astype(np.float32)
            v[v == NODATA_U8] = np.nan
            x[:, i] = v
        for j, layer in enumerate(cat_layers):
            x[:, nb + j] = layer[ys, xs]
        belief[ys, xs] = model.predict_proba(x)[:, 1].astype(np.float32)
    return belief


# --------------------------------------------------------------------------- #
# lane run
# --------------------------------------------------------------------------- #
def run(seed: int = 20, hide_frac: float = 0.20, buffer_px: int = 3,
        bags: int = 2, inner_frac: float = 0.20, inner_buffer_px: int = 0,
        n_neg: int = 400_000, out_dir: Path = LANE_DIR) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    grid = shared_grid.load_grid()
    folds, _quad = shared_holdout.buffered_component_draw(
        grid, seed=seed, hide_frac=hide_frac, buffer_px=buffer_px)
    bank = np.load(BANK, mmap_mode="r")
    names = feature_names()
    rng = np.random.default_rng(9_753_210 + seed)
    background_pool = grid.footprint & ~grid.catalogue

    receipt = dict(lane="WBG2-B-supervised-blind-propensity",
                   shared_holdout="gems57.holdout.buffered_component_draw",
                   shared_evaluator="gems57.evaluate_holdout (used by emit_and_score.py)",
                   seed=seed, hide_frac=hide_frac, buffer_px=buffer_px,
                   inner_frac=inner_frac, inner_buffer_px=inner_buffer_px,
                   bags=bags, n_neg=n_neg,
                   feature_names=names, folds=[], seconds=None)

    for fold in folds:
        key = fold["name"]
        visible = fold["visible"]              # outer catalogue minus withheld minus collar
        masked_known = fold["masked_known"]    # organiser-style mask: all mapped pixels
        hidden_outer = fold["hidden_all"]
        region = fold["region"]
        active = region & ~masked_known
        truth = fold["truth"]

        # ---- rule 4 canaries use the evaluation-time (outer visible) features
        can_names, can_layers = catalogue_features(visible)
        canaries = {}
        for i, nm in enumerate(names):
            if i < bank.shape[0]:
                v = np.asarray(bank[i], np.float32)[active]
                v[v == NODATA_U8] = np.nan
            else:
                v = can_layers[i - bank.shape[0]][active]
            median = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
            full = np.zeros(active.shape, np.float32)
            full[active] = np.where(np.isfinite(v), v, median)
            res = single_feature_auc(full, truth, active)
            canaries[nm] = dict(auc=res["auc"], two_sided_auc=res["two_sided_auc"],
                                canary_pass=bool(res["canary_pass"]),
                                nodata_filled_median=median,
                                withheld_positives=res["withheld_positives"],
                                negatives=res["negative_examples"])
        del can_layers

        # ---- bagged inner hide-and-recover training
        belief_sum = np.zeros(active.shape, np.float32)
        bag_receipts = []
        for b in range(bags):
            inner_seed = 424_243 * (seed + 1) + 7_919 * fold["fold"] + 31 * b
            inner_hidden, inner_visible, inner_receipt = inner_component_draw(
                visible, inner_seed, frac=inner_frac, buffer_px=inner_buffer_px)
            cat_names, cat_layers = catalogue_features(inner_visible)
            py, px = np.nonzero(inner_hidden)
            neg_pool = background_pool & (ndi.distance_transform_edt(~inner_hidden) > max(inner_buffer_px, 1))
            ny, nx = np.nonzero(neg_pool)
            take = rng.choice(ny.size, min(n_neg, ny.size), replace=False)
            ny, nx = ny[take], nx[take]
            ys = np.concatenate([py, ny]); xs = np.concatenate([px, nx])
            y = np.concatenate([np.ones(py.size, np.uint8), np.zeros(ny.size, np.uint8)])
            order = rng.permutation(ys.size)
            ys, xs, y = ys[order], xs[order], y[order]
            x = stack_rows_chunked(bank, cat_layers, ys, xs)
            t = time.time()
            model = train_propensity(x, y, seed=inner_seed)
            train_s = time.time() - t
            del x
            t = time.time()
            belief = predict_grid(model, bank, cat_layers, active)
            pred_s = time.time() - t
            belief_sum += belief
            auc = single_feature_auc(belief, truth, active)
            bag_receipts.append(dict(bag=b, **inner_receipt,
                                     n_train_pos=int((y == 1).sum()),
                                     n_train_neg=int((y == 0).sum()),
                                     n_iterations=int(model.n_iter_),
                                     validation_auc=float(max(model.validation_score_)),
                                     train_seconds=round(train_s, 1),
                                     predict_seconds=round(pred_s, 1),
                                     holdout_auc=auc["auc"],
                                     holdout_two_sided_auc=auc["two_sided_auc"],
                                     belief_mean_on_truth=float(belief[truth].mean()),
                                     belief_mean_off_truth=float(belief[active & ~truth].mean())))
            print(f"[{key} bag{b}] inner_hidden={inner_receipt['hidden_positive_pixels']} "
                  f"iters={model.n_iter_} valAUC={bag_receipts[-1]['validation_auc']:.4f} "
                  f"holdoutAUC={auc['auc']:.4f} train={train_s:.0f}s pred={pred_s:.0f}s", flush=True)
            del model, belief, cat_layers

        belief_mean = belief_sum / float(bags)
        np.save(out_dir / f"belief_{key}.npy", belief_mean)
        fold_entry = {k: v for k, v in fold["receipt"].items()}
        fold_entry.update(
            fold_name=key,
            n_active=int(active.sum()), n_truth=int(truth.sum()),
            n_emitted_domain=int((belief_mean > 0).sum()),
            bags=bag_receipts, canaries=canaries)
        receipt["folds"].append(fold_entry)
        del belief_sum, belief_mean
    receipt["seconds"] = round(time.time() - t0, 1)
    (ROOT / "evidence" / "lane_b_training.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(f"lane training finished in {receipt['seconds']} s", flush=True)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20)
    parser.add_argument("--hide-frac", type=float, default=0.20)
    parser.add_argument("--buffer-px", type=int, default=3)
    parser.add_argument("--bags", type=int, default=2)
    parser.add_argument("--inner-frac", type=float, default=0.20)
    parser.add_argument("--inner-buffer-px", type=int, default=0,
                        help="collar removed from the inner feature catalogue; 0 keeps "
                             "mapped faults adjacent to the training targets so the model "
                             "does not learn the shared split's >=3.16 px artefact")
    parser.add_argument("--n-neg", type=int, default=400_000)
    parser.add_argument("--out-dir", type=Path, default=LANE_DIR)
    args = parser.parse_args()
    run(seed=args.seed, hide_frac=args.hide_frac, buffer_px=args.buffer_px,
        bags=args.bags, inner_frac=args.inner_frac, inner_buffer_px=args.inner_buffer_px,
        n_neg=args.n_neg, out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
