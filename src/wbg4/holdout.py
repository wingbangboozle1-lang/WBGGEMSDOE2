"""Spatially-blocked hide-and-recover holdout for the WBG4 lane.

Protocol (per the project charter, adapted only where the charter's inputs are
absent -- every deviation is named):

1. Cut the label raster into connected fault **segments** (8-connectivity).
2. Withhold a deterministic subset of whole segments (``holdout_frac``), so no
   part of a withheld segment is visible to training.
3. Buffer the withheld segments by ``buffer_px`` and remove the buffer from the
   training domain, so a model cannot learn "be near a withheld segment".
4. Score **pooled** DTI (never averaged) with the official alpha=0.2, beta=0.8,
   300 m triangular kernel, using the shared evaluator ``wbg2.metric``.

Deviation from the charter's literal wording, stated explicitly: the charter's
holdout requires catalogue-based features to be *derived from the visible faults
only*.  This lane uses **no catalogue-derived features at all** (see
``wbg4.features``), so there is no catalogue feature to re-derive; the
visible-fault restriction is satisfied by construction rather than by
re-computation.  Visible-fault *masking* is still applied in the ``masked``
variant so the organizer's catalogue-masking behaviour is emulated.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi


def segments(truth: np.ndarray, min_px: int = 1) -> tuple[np.ndarray, int]:
    """Label connected fault segments (8-connectivity)."""
    lab, n = ndi.label(np.asarray(truth, bool), structure=np.ones((3, 3), bool))
    if min_px > 1:
        sizes = np.bincount(lab.ravel())
        small = np.flatnonzero(sizes < min_px)
        small = small[small > 0]
        if len(small):
            lab[np.isin(lab, small)] = 0
            lab, n = ndi.label(lab > 0, structure=np.ones((3, 3), bool))
    return lab, int(lab.max())


def split_segments(lab: np.ndarray, n: int, holdout_frac: float = 0.2,
                   seed: int = 20261028, min_px: int = 20) -> tuple[np.ndarray, dict]:
    """Deterministically withhold whole segments; return the withheld mask."""
    rng = np.random.default_rng(seed)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    eligible = np.flatnonzero(sizes >= min_px)
    eligible = eligible[eligible > 0]
    if len(eligible) == 0:
        raise ValueError("no segments large enough to hold out")
    order = rng.permutation(eligible)
    # Greedy: hit the target *pixel* fraction, not the segment count, so a few
    # huge segments cannot swallow the whole holdout.
    total = sizes[eligible].sum()
    chosen, acc = [], 0
    for s in order:
        if acc >= holdout_frac * total:
            break
        chosen.append(int(s)); acc += int(sizes[s])
    withheld = np.isin(lab, chosen)
    info = dict(n_segments=n, n_eligible=len(eligible), n_withheld=len(chosen),
                withheld_pixels=int(withheld.sum()),
                withheld_fraction=float(withheld.sum() / max(1, sizes[eligible].sum())),
                seed=seed, holdout_frac=holdout_frac, min_px=min_px)
    return withheld, info


def build_folds(truth: np.ndarray, footprint: np.ndarray, holdout_frac: float = 0.2,
                buffer_px: int = 5, seed: int = 20261028) -> dict:
    """One buffered segment holdout: withheld truth, train domain, visible mask."""
    lab, n = segments(truth)
    withheld, info = split_segments(lab, n, holdout_frac, seed)
    visible = truth & ~withheld
    if buffer_px > 0:
        buf = ndi.binary_dilation(withheld, ndi.generate_binary_structure(2, 1),
                                  iterations=buffer_px)
    else:
        buf = withheld
    train_domain = footprint & ~buf
    info.update(dict(buffer_px=buffer_px,
                     train_domain_pixels=int(train_domain.sum()),
                     visible_positive_pixels=int(visible.sum())))
    return dict(withheld=withheld & footprint, visible=visible & footprint,
                train_domain=train_domain, footprint=footprint,
                label_map=lab, info=info)


def score_holdout(pred: np.ndarray, fold: dict, mask_visible: bool = False) -> dict:
    """Pooled DTI of ``pred`` against the withheld segments.

    ``mask_visible=True`` additionally removes visible catalogue pixels from the
    active region, emulating the organizer's catalogue masking.  This *raises*
    the score slightly (it removes easy false-positive cells), so both variants
    are reported.
    """
    from wbg2.metric import weighted_components
    active = fold["footprint"].copy()
    if mask_visible:
        active &= ~fold["visible"]
    p = np.where(active, np.clip(np.nan_to_num(np.asarray(pred, np.float64)), 0.0, 1.0), 0.0)
    g = (fold["withheld"] & active).astype(np.float64)
    T, F, _, N = weighted_components(p, g, radius=3)
    if N == 0:
        raise ValueError("no withheld truth in the active region")
    dti = T / (T + 0.2 * F + 0.8 * N)
    return dict(T=T, F=F, N=int(N), c=T / N, f=F / N, dti=dti,
                n_pred=int((p > 0).sum()), mask_visible=mask_visible)


def block_folds(footprint: np.ndarray, n_row: int = 5, n_col: int = 5,
                n_hold: int = 5) -> list[dict]:
    """Secondary check: rectangular spatial blocks (no segment structure used)."""
    h, w = footprint.shape
    rid = (np.arange(h) * n_row) // h
    cid = (np.arange(w) * n_col) // w
    bid = rid[:, None] * n_col + cid[None, :]
    rng = np.random.default_rng(7)
    hold = rng.choice(n_row * n_col, size=n_hold, replace=False)
    out = []
    for b in hold:
        test = footprint & (bid == b)
        out.append(dict(block=int(b), test=test, train=footprint & (bid != b)))
    return out
