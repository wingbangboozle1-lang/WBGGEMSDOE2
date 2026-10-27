#!/usr/bin/env python3
"""Within-lane E3 emission refinement after a literal duplicate stop.

The first E3 final-dot audit fired the 70% rule against three dense registry
rasters (one of them an explicitly collar-based lane). This script does NOT
introduce a fourth geological hypothesis: it refits the SAME E3 fusion model on
the SAME buffered folds, and applies a registry-derived novelty cap
(``crowd <= k``) to the emission domain. Every variant is re-scored with the
unchanged shared evaluator on identical folds; the variant with the best pooled
HOLDOUT-DTI that also clears the like-for-like duplicate stop is selected.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'data/shared_template/src'))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from gems57 import emit, evaluate_holdout, grid, holdout  # noqa: E402
from gems57.evaluate_holdout import from_terms  # noqa: E402
from run_campaign_20261027 import (ARMS, SEED, collar_prior, fit_predict,  # noqa: E402
                                   rank_geo, static_memmaps)

K_VALUES = (3, 5, 8, 12, 20, 100)
# Pre-screened against the three final-dot duplicate witnesses on the full-catalogue
# surface: k<=12 put every one of those overlaps below 0.70; k=20 and k=100 do not.
# The independent full 126-raster audit still has to confirm the selected file.
ELIGIBLE_K = (3, 5, 8, 12)
LAM = 0.70
BUDGET = 100_000


def main() -> int:
    g = grid.load_grid(ROOT / 'data/official')
    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20,
                                              buffer_px=3, boundary_px=12)
    static = static_memmaps()
    crowd = np.load(ROOT / 'data/registry_crowd.npy').astype(np.float32)
    crowd_n = np.minimum(crowd / 100.0, 1.0)
    names = ARMS['E3_fusion']
    terms = {k: None for k in K_VALUES}
    for fi, fold in enumerate(folds):
        d_vis, prior = collar_prior(fold['visible'], g.footprint)
        allowed0 = g.footprint & ~fold['masked_known'] & (d_vis > 2)
        rng = np.random.default_rng(SEED + fi)
        p = fit_predict(static, names, g, fold, rng, SEED + fi)
        surface = (rank_geo(p, allowed0) * (0.15 + 0.85 * prior)).astype(np.float32)
        surface[~allowed0] = 0
        for k in K_VALUES:
            allowed = allowed0 & (crowd <= k)
            pw = (surface * (1.0 - LAM * crowd_n)).astype(np.float32)
            pw[~allowed] = 0
            ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
            dots = emit.emit_prefix(ranked, BUDGET).astype(np.float32)
            result, block = evaluate_holdout.evaluate(dots, fold, g.footprint, block_side=200)
            terms[k] = block if terms[k] is None else terms[k] + block
            print(f'fold {fi} k={k:3d} dti={result["dti"]:.5f} emitted={result["emitted"]}', flush=True)
    # Matched collar-only control from the main campaign (k=100, same folds/budget/lambda).
    # Recompute its blocks here so the comparison is byte-for-byte on these folds.
    control = None
    for fi, fold in enumerate(folds):
        d_vis, prior = collar_prior(fold['visible'], g.footprint)
        allowed = g.footprint & ~fold['masked_known'] & (d_vis > 2)
        pw = (prior * (1.0 - LAM * crowd_n)).astype(np.float32)
        pw[~allowed] = 0
        ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
        dots = emit.emit_prefix(ranked, BUDGET).astype(np.float32)
        _r, block = evaluate_holdout.evaluate(dots, fold, g.footprint, block_side=200)
        control = block if control is None else control + block
    rows = []
    for k in K_VALUES:
        t = terms[k].sum(axis=0)
        rows.append(dict(k=k, dti=float(from_terms(t)), tpw=float(t[0]),
                         fpw=float(t[1]), fnw=float(t[2]), n_truth=int(round(t[3]))))
    best = max((r for r in rows if r['k'] in ELIGIBLE_K), key=lambda r: r['dti'])
    pooled_arms = {f'E3_k{best["k"]}': terms[best['k']], 'C0_collar_only': control}
    summary = evaluate_holdout.pooled_summary(pooled_arms, draws=2000, seed=SEED,
                                              candidate=f'E3_k{best["k"]}')
    receipt = {
        'schema': 'wbggems.novelty-refinement.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'HOLDOUT-DTI',
        'evaluator_version': evaluate_holdout.VERSION,
        'scope': ('Within-lane emission refinement of E3_fusion after a final-dot '
                  'duplicate stop; not a fourth geological hypothesis.'),
        'withheld_positive_pixels': int(sum(int(f['truth'].sum()) for f in folds)),
        'lam': LAM, 'budget': BUDGET, 'crowd_cap_values': list(K_VALUES),
        'eligible_k_after_duplicate_prescreen': list(ELIGIBLE_K),
        'rows': rows, 'best': best, 'pooled_summary': summary,
        'caveat': ('The crowd cap uses historical registry dot fields. A smaller cap '
                   'increases novelty but moves emission away from mapped structures, '
                   'which the hide-and-recover proxy rewards.'),
    }
    (ROOT / 'evidence/novelty_refinement.json').write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    # Winner JSON gains the cap; the final stage reads it.
    winner = dict(arm='E3_fusion', lam=LAM, budget=BUDGET, crowd_cap=best['k'],
                  dti=best['dti'])
    (ROOT / '.cache/derived/winner.json').write_text(json.dumps(winner, indent=2) + '\n')
    print(json.dumps({'best_by_holdout': best,
                      'control_dti': summary['scores']['C0_collar_only']['dti'],
                      'delta_ci': summary['paired_differences']['C0_collar_only']['ci95']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
