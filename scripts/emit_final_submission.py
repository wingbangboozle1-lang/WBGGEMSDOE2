#!/usr/bin/env python3
"""Generate the final lane-WBG2-B submission TIFF with the unchanged shared writer.

Pipeline (no human inspection step; every gate is machine-checked and recorded):

1. Bagged *inner* hide-and-recover training on the full mapped catalogue: hide
   whole 8-connected components, rebuild every catalogue-derived feature from what
   is left, train a gradient-boosted pixel classifier on the hidden components.
2. Predict over the emission domain: study-area footprint, minus mapped catalogue
   pixels (the organiser masks them, forum thread 11516), minus a ``--collar-px``
   collar around mapped faults (user-reported ledger evidence: GEMSDOE25 44,090
   dots 0.2600 -> the same array pruned at 2 px, GEMSDOE32 37,654 dots, 0.2778).
3. Average the bag beliefs, then thin to a 1-px skeleton of a belief-thresholded
   region and keep the ``--budget`` highest-belief skeleton pixels.  Under DTI a
   redundant second row of a probability ridge costs 0.2*(1-k) and adds no truth
   credit, so thinning is the emission analogue of the metric's marginal rule.
4. Write with ``gems57.submission_writer.write_submission`` (fail-closed: it
   validates in memory, writes temporaries, re-validates the on-disk TIFF and ZIP
   and only then commits).  Values are float32 in [0,1] and all-finite: zeros
   outside the footprint, which is the encoding of the best user-reported file in
   the nine-site history (``...-zeros`` = 0.2778) and avoids the portal's
   "Predicted values must be in range [0, 1]" rejection of NaN payloads.
5. Re-read the committed bytes and validate them independently.

Nothing here uploads anything or spends a slot.
"""
from __future__ import annotations

import argparse
import datetime as dt
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
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import gates as shared_gates                     # noqa: E402
from gems57 import grid as shared_grid                       # noqa: E402
from gems57 import submission_writer as shared_writer        # noqa: E402
from gems57 import validate as shared_validate               # noqa: E402
from wbggems.validate import inspect_tif                     # noqa: E402
import lane_blind_propensity as lane                         # noqa: E402
from emit_and_score import thin_to_budget                    # noqa: E402

SAMPLE = ROOT / "data" / "bridge" / "sample_submission.tif"


def build_final_belief(grid, bank, *, bags: int, inner_frac: float, n_neg: int,
                       domain: np.ndarray, seed: int, out_dir: Path) -> tuple[np.ndarray, list[dict]]:
    rng = np.random.default_rng(8_675_309 + seed)
    background = grid.footprint & ~grid.catalogue
    belief_sum = np.zeros(grid.shape, np.float32)
    receipts = []
    for b in range(bags):
        inner_seed = 1_000_003 * (seed + 1) + 7_919 * b
        inner_hidden, inner_visible, rec = lane.inner_component_draw(
            grid.catalogue, inner_seed, frac=inner_frac, buffer_px=0)
        names, layers = lane.catalogue_features(inner_visible)
        py, px = np.nonzero(inner_hidden)
        neg_pool = background & (ndi.distance_transform_edt(~inner_hidden) > 1)
        ny, nx = np.nonzero(neg_pool)
        take = rng.choice(ny.size, min(n_neg, ny.size), replace=False)
        ny, nx = ny[take], nx[take]
        ys = np.concatenate([py, ny]); xs = np.concatenate([px, nx])
        y = np.concatenate([np.ones(py.size, np.uint8), np.zeros(ny.size, np.uint8)])
        order = rng.permutation(ys.size)
        x = lane.stack_rows_chunked(bank, layers, ys[order], xs[order])
        y = y[order]
        t = time.time()
        model = lane.train_propensity(x, y, seed=inner_seed)
        train_s = time.time() - t
        del x
        t = time.time()
        belief = lane.predict_grid(model, bank, layers, domain)
        pred_s = time.time() - t
        belief_sum += belief
        receipts.append(dict(bag=b, **rec, n_train_pos=int((y == 1).sum()),
                             n_train_neg=int((y == 0).sum()),
                             n_iterations=int(model.n_iter_),
                             validation_auc=float(max(model.validation_score_)),
                             train_seconds=round(train_s, 1),
                             predict_seconds=round(pred_s, 1),
                             belief_mean=float(belief[domain].mean()),
                             belief_max=float(belief.max())))
        print(f"[final bag{b}] iters={model.n_iter_} valAUC={receipts[-1]['validation_auc']:.4f} "
              f"train={train_s:.0f}s predict={pred_s:.0f}s", flush=True)
        del model, belief, layers
    return belief_sum / float(bags), receipts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=40_000, help="emitted pixels (dots)")
    parser.add_argument("--collar-px", type=int, default=2)
    parser.add_argument("--bags", type=int, default=3)
    parser.add_argument("--inner-frac", type=float, default=0.20)
    parser.add_argument("--n-neg", type=int, default=400_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--name", default=None, help="submission name (<=140 chars)")
    parser.add_argument("--note", default=None, help="submission note (<=140 chars)")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "downloads")
    parser.add_argument("--lane-dir", type=Path, default=ROOT / "data" / "lane")
    parser.add_argument("--reuse-belief", action="store_true",
                        help="reuse data/lane/belief_final.npy instead of retraining "
                             "(the bagged belief is deterministic given the seeds)")
    args = parser.parse_args()
    t0 = time.time()

    grid = shared_grid.load_grid()
    bank = np.load(lane.BANK, mmap_mode="r")
    cat_edt = ndi.distance_transform_edt(~grid.catalogue)
    domain = grid.footprint & ~grid.catalogue & (cat_edt > args.collar_px)
    print(f"emission domain: {int(domain.sum()):,} cells "
          f"(footprint {int(grid.footprint.sum()):,}, catalogue {int(grid.catalogue.sum()):,})",
          flush=True)

    args.lane_dir.mkdir(parents=True, exist_ok=True)
    if args.reuse_belief:
        belief = np.load(args.lane_dir / "belief_final.npy")
        if belief.shape != grid.shape:
            raise SystemExit("cached belief does not match the pinned grid")
        prior = args.lane_dir / "final_receipt.json"
        bag_receipts = json.loads(prior.read_text())["metadata"]["bag_receipts"] if prior.is_file() else []
        print(f"reusing cached belief ({int((belief > 0).sum()):,} positive cells)", flush=True)
    else:
        belief, bag_receipts = build_final_belief(
            grid, bank, bags=args.bags, inner_frac=args.inner_frac, n_neg=args.n_neg,
            domain=domain, seed=args.seed, out_dir=args.lane_dir)
        np.save(args.lane_dir / "belief_final.npy", belief)

    support, thin_info = thin_to_budget(domain, belief, args.budget)
    prediction = np.zeros(grid.shape, np.float32)
    prediction[support] = 1.0
    np.save(args.lane_dir / "support_final.npy", support)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    import hashlib
    support_hash = hashlib.sha256(np.ascontiguousarray(support).tobytes()).hexdigest()[:12]
    name = args.name or f"wbg2b-skelprop-{args.budget}dots-{stamp}-{support_hash}-zeros"
    note = args.note or (f"Supervised blind-trace propensity, {args.bags}-bag inner hide-and-recover, "
                         f"1px skeleton, {args.collar_px}px catalogue collar")
    if len(name) > 140 or len(note) > 140:
        raise SystemExit("name/note must be <=140 characters")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    target = args.out_dir / f"{name}.tif"
    metadata = dict(
        lane="WBG2-B-supervised-blind-propensity",
        hypothesis="Unmapped expert-labelled faults leave a measurable imprint in the 19 "
                   "provided geophysical/topographic bands; a pixel classifier that never sees "
                   "the target fault in its own catalogue features ranks them above background.",
        mechanism="Bagged inner hide-and-recover gradient boosting on 38 shared rank layers "
                  "(q + 9x9 local-contrast z for 19 bands) plus 5 visible-only catalogue layers; "
                  "belief averaged over bags; 1-px skeleton thinning to a fixed dot budget.",
        non_fault_mimic="Lithologic contacts, dykes and intrusive edges, alluvial-fan and terrace "
                        "margins, survey flight-line striping, and hydrothermal alteration halos "
                        "produce the same local-contrast signature without being faults.",
        budget=args.budget, collar_px=args.collar_px, bags=args.bags,
        inner_frac=args.inner_frac, emitted=int(support.sum()),
        thinning=thin_info, bag_receipts=bag_receipts,
        feature_names=lane.feature_names(),
        seconds=round(time.time() - t0, 1))
    receipt = shared_writer.write_submission(
        target, prediction, SAMPLE, grid.footprint, note=note, name=name,
        catalogue=grid.catalogue, metadata=metadata)

    # independent re-read of the committed bytes
    strict = inspect_tif(target, SAMPLE, strict_all_finite=True)
    local = shared_validate.validate(target, grid.footprint, grid.catalogue)
    shared_validate.assert_submittable(local)
    report = shared_gates.format_report(target, SAMPLE, footprint=grid.footprint)
    receipt["independent_validation"] = dict(
        strict_all_finite=strict, shared_local=local, shared_format_report=report)
    receipt["verdict_gate"] = dict(
        format_ok=bool(strict["format_valid_against_reference"] and report["ok"] and local["all_checks_passed"]),
        values_in_0_1=bool(strict.get("values_in_range", True)) and report.get("min", 0) >= 0
        and report.get("max", 1) <= 1,
        all_finite=bool(strict.get("all_finite", False)),
        crs=str(strict.get("crs")), shape=strict.get("shape"),
        transform=strict.get("transform"))
    (args.lane_dir / "final_receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(name=name, note=note, note_chars=len(note),
                          tif=str(target.relative_to(ROOT)), sha256=receipt["sha256"],
                          bytes=receipt["bytes"], emitted=receipt["metadata"]["emitted"],
                          verdict_gate=receipt["verdict_gate"],
                          seconds=receipt["metadata"]["seconds"]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
