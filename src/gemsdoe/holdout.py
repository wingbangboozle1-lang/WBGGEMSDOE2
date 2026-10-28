"""Prepare the shared, reusable evaluation substrate for the GEMS submission lane.

Outputs (all under ``data/work``, git-ignored):

* ``footprint.npy``      bool  (3730, 3292)  organizer-scored cells
* ``catalogue.npy``      bool                 mapped faults (labels == 1)
* ``segments.npy``       int32                connected-component id of each catalogue pixel (-1 else)
* ``folds.json``         fold definition + per-fold truth/visible bookkeeping
* ``fold{0..K}_truth.npy``/``fold{k}_visible.npy`` bool masks

Holdout protocol (documented, not a score): connected catalogue segments are
assigned to spatial blocks, blocks are grouped into K folds, and for fold k the
*truth* is every pixel of the held-out segments that lies further than
``BUFFER_PX`` from any visible segment pixel.  Catalogue-derived features must be
built from ``fold{k}_visible`` only.  This hides whole faults, not random pixels,
so a model cannot memorise a segment from its unmasked neighbours.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from . import grid

K_FOLDS = 4
BLOCK_ROWS = 8
BLOCK_COLS = 8
BUFFER_PX = 2


def build(check_only: bool = False) -> dict:
    grid.ensure_work()
    fp = grid.footprint()
    cat = grid.catalogue_mask()
    lab = grid.read_labels()
    if not np.array_equal(cat, lab == 1):
        raise RuntimeError("catalogue and labels disagree")

    labels, nseg = ndi.label(cat, structure=np.ones((3, 3), dtype=int))
    rows, cols = grid.SHAPE
    rr, cc = np.nonzero(cat)
    seg_of_px = labels[rr, cc]
    by = np.minimum((rr * BLOCK_ROWS) // rows, BLOCK_ROWS - 1)
    bx = np.minimum((cc * BLOCK_COLS) // cols, BLOCK_COLS - 1)

    # assign each segment to the block holding the majority of its pixels
    block_count = {}
    for s, b_y, b_x in zip(seg_of_px, by, bx):
        block_count.setdefault(int(s), {})[(int(b_y), int(b_x))] = \
            block_count.setdefault(int(s), {}).get((int(b_y), int(b_x)), 0) + 1
    seg_block = {s: max(c.items(), key=lambda kv: kv[1])[0] for s, c in block_count.items()}

    # balance fault pixels across folds deterministically
    px_per_block = {}
    for s, blk in seg_block.items():
        px_per_block[blk] = px_per_block.get(blk, 0) + sum(block_count[s].values())
    order = sorted(px_per_block.items(), key=lambda kv: (-kv[1], kv[0]))
    fold_load = [0] * K_FOLDS
    block_fold = {}
    for blk, npx in order:
        k = int(np.argmin(fold_load))
        block_fold[blk] = k
        fold_load[k] += npx

    seg_fold = {s: block_fold[blk] for s, blk in seg_block.items()}
    seg_img = np.full(grid.SHAPE, -1, dtype="int32")
    seg_img[rr, cc] = seg_of_px

    out = {"k_folds": K_FOLDS, "buffer_px": BUFFER_PX,
           "n_segments": int(nseg), "n_segments_used": len(seg_fold),
           "blocks": [BLOCK_ROWS, BLOCK_COLS],
           "fold_fault_pixels": [int(v) for v in fold_load], "folds": []}
    np.save(grid.WORK / "segments.npy", seg_img)
    np.save(grid.WORK / "catalogue.npy", cat)
    np.save(grid.WORK / "footprint.npy", fp)

    for k in range(K_FOLDS):
        hidden = np.isin(seg_img, [s for s, f in seg_fold.items() if f == k])
        visible = cat & ~hidden
        d_vis = ndi.distance_transform_edt(~visible)
        truth = hidden & (d_vis > BUFFER_PX)
        np.save(grid.WORK / f"fold{k}_truth.npy", truth)
        np.save(grid.WORK / f"fold{k}_visible.npy", visible)
        out["folds"].append({
            "fold": k,
            "hidden_segments": sum(1 for f in seg_fold.values() if f == k),
            "hidden_pixels": int(hidden.sum()),
            "truth_pixels_after_buffer": int(truth.sum()),
            "visible_pixels": int(visible.sum()),
            "dropped_by_buffer": int(hidden.sum() - truth.sum()),
        })

    truths = [np.load(grid.WORK / f"fold{k}_truth.npy") for k in range(K_FOLDS)]
    union = np.zeros(grid.SHAPE, dtype=bool)
    disjoint = True
    for t in truths:
        disjoint &= not bool((union & t).any())
        union |= t
    out["checks"] = {
        "footprint_matches_labels": bool(np.array_equal(fp, lab != -1)),
        "catalogue_pixels": int(cat.sum()),
        "footprint_pixels": int(fp.sum()),
        "fold_truths_disjoint": disjoint,
        "fold_truths_subset_of_catalogue": bool(np.all(cat | ~union)),
        "fold_truth_union_pixels": int(union.sum()),
        "buffer_dropped_total": int(sum(f["dropped_by_buffer"] for f in out["folds"])),
    }
    (grid.WORK / "folds.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(build(), indent=1))
