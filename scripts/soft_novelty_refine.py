#!/usr/bin/env python3
"""Within-lane E3 refinement: graded (not hard) separation from dense prior lanes.

Hard crowd caps were tested first (`scripts/novelty_refine.py`): they collapse
HOLDOUT-DTI to ~0.009 and are a decisive negative. Here the SAME E3 fusion model
and SAME buffered folds are used with a *graded* penalty inside the 3 px halo of
the three dense registry rasters that fired the duplicate rule. The penalty is
derived only from public historical rasters, never from holdout labels. Every
variant is re-scored with the unchanged shared evaluator and the final full-raster
overlaps are measured before one is selected.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'data/shared_template/src'))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from gems57 import emit, evaluate_holdout, grid, holdout  # noqa: E402
from gems57.evaluate_holdout import from_terms  # noqa: E402
from run_campaign_20261027 import (ARMS, SEED, collar_prior, fit_predict,  # noqa: E402
                                   rank_geo, static_memmaps)

BETAS = (0.0, 0.80, 0.88, 0.90, 0.92, 0.95)
LAM = 0.70
BUDGET = 100_000


def disk3() -> np.ndarray:
    y, x = np.mgrid[-3:4, -3:4]
    return (x * x + y * y) <= 9


def firing_halos(fp: np.ndarray) -> tuple[list[tuple[str, np.ndarray]], np.ndarray]:
    audit = json.loads((ROOT / 'evidence/final_uniqueness.json').read_text())
    rows = [r for r in audit['rows']
            if r.get('duplicate_by_overlap') and r.get('representation') == 'dot_field']
    struct = disk3()
    halos, union = [], np.zeros(fp.shape, bool)
    for r in rows:
        with rasterio.open(ROOT / r['local']) as src:
            a = src.read(1)
        h = ndi.binary_dilation(np.isfinite(a) & (a > 0) & fp, structure=struct)
        halos.append((r['submission'], h))
        union |= h
    return halos, union


def main() -> int:
    g = grid.load_grid(ROOT / 'data/official')
    folds, _ = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20,
                                              buffer_px=3, boundary_px=12)
    static = static_memmaps()
    crowd = np.load(ROOT / 'data/registry_crowd.npy').astype(np.float32)
    crowd_n = np.minimum(crowd / 100.0, 1.0)
    halos, union = firing_halos(g.footprint)
    names = ARMS['E3_fusion']
    terms = {b: None for b in BETAS}
    for fi, fold in enumerate(folds):
        d_vis, prior = collar_prior(fold['visible'], g.footprint)
        allowed = g.footprint & ~fold['masked_known'] & (d_vis > 2)
        rng = np.random.default_rng(SEED + fi)
        p = fit_predict(static, names, g, fold, rng, SEED + fi)
        surface = (rank_geo(p, allowed) * (0.15 + 0.85 * prior)).astype(np.float32)
        surface[~allowed] = 0
        base = (surface * (1.0 - LAM * crowd_n)).astype(np.float32)
        for beta in BETAS:
            pw = (base * (1.0 - beta * union)).astype(np.float32)
            pw[~allowed] = 0
            ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
            dots = emit.emit_prefix(ranked, BUDGET).astype(np.float32)
            result, block = evaluate_holdout.evaluate(dots, fold, g.footprint, block_side=200)
            terms[beta] = block if terms[beta] is None else terms[beta] + block
            print(f'fold {fi} beta={beta:.2f} dti={result["dti"]:.5f}', flush=True)
    # Matched collar-only control on the SAME folds / budget / lambda, so the
    # promoted arm can be compared with a paired spatial-block CI.
    control_terms = None
    for fi, fold in enumerate(folds):
        d_vis, prior = collar_prior(fold['visible'], g.footprint)
        allowed = g.footprint & ~fold['masked_known'] & (d_vis > 2)
        pw = (prior * (1.0 - LAM * crowd_n)).astype(np.float32)
        pw[~allowed] = 0
        ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
        dots = emit.emit_prefix(ranked, BUDGET).astype(np.float32)
        _r, block = evaluate_holdout.evaluate(dots, fold, g.footprint, block_side=200)
        control_terms = block if control_terms is None else control_terms + block
    np.savez_compressed(ROOT / '.cache/derived/soft_terms.npz',
                        **{f'beta_{int(b*100)}': terms[b] for b in BETAS},
                        control=control_terms)
    # Final-surface overlaps on the full-catalogue surface (no hidden labels involved).
    d_full, prior_full = collar_prior(g.catalogue, g.footprint)
    allowed_full = g.footprint & ~g.catalogue & (d_full > 2)
    full_fold = dict(region=np.zeros(g.shape, bool), hidden_all=np.zeros(g.shape, bool),
                     visible=g.catalogue, masked_known=g.catalogue)
    p_full = fit_predict(static, names, g, full_fold, np.random.default_rng(SEED + 999), SEED + 999)
    surf_full = (rank_geo(p_full, allowed_full) * (0.15 + 0.85 * prior_full)).astype(np.float32)
    surf_full[~allowed_full] = 0
    base_full = (surf_full * (1.0 - LAM * crowd_n)).astype(np.float32)
    rows = []
    for beta in BETAS:
        t = terms[beta].sum(axis=0)
        pw = (base_full * (1.0 - beta * union)).astype(np.float32)
        pw[~allowed_full] = 0
        ranked, _ = emit.emit_decimated(pw, allowed_full, tile_px=3)
        dots = emit.emit_prefix(ranked, BUDGET)
        overlaps = {name: float(h[dots].mean()) for name, h in halos}
        rows.append(dict(beta=beta, dti=float(from_terms(t)), tpw=float(t[0]),
                         fpw=float(t[1]), fnw=float(t[2]), n_truth=int(round(t[3])),
                         final_surface_overlaps=overlaps,
                         worst_final_overlap=max(overlaps.values()),
                         passes_duplicate_stop=max(overlaps.values()) <= 0.70))
    eligible = [r for r in rows if r['passes_duplicate_stop']]
    best = max(eligible, key=lambda r: r['dti']) if eligible else None
    control = json.loads((ROOT / 'evidence/holdout_20261027.json').read_text())
    control_entry = min(control['estimates'], key=lambda r: 0 if r['arm'] == 'C0_collar_only' and
                        r['lam'] == LAM and r['budget'] == BUDGET else 1)
    control_t = control_terms.sum(axis=0)
    summary = None
    if best is not None:
        summary = evaluate_holdout.pooled_summary(
            {f'E3_soft{int(best["beta"]*100)}': terms[best['beta']],
             'C0_collar_only': control_terms},
            draws=2000, seed=SEED, candidate=f'E3_soft{int(best["beta"]*100)}')
    receipt = {
        'schema': 'wbggems.soft-novelty-refinement.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'HOLDOUT-DTI',
        'evaluator_version': evaluate_holdout.VERSION,
        'scope': ('Within-lane graded emission refinement of E3_fusion, not a fourth '
                  'geological hypothesis. Hard crowd caps were tested and rejected first.'),
        'withheld_positive_pixels': int(sum(int(f['truth'].sum()) for f in folds)),
        'lam': LAM, 'budget': BUDGET, 'betas': list(BETAS),
        'dense_witness_halo_fraction_of_footprint': float(union[g.footprint].mean()),
        'dense_witnesses': [n for n, _h in halos],
        'rows': rows, 'best_passing': best,
        'matched_control_from_main_campaign': control_entry,
        'matched_control_recomputed_dti': float(from_terms(control_t)),
        'pooled_summary': summary,
        'caveat': ('Overlaps are measured on the final full-catalogue surface; the '
                   'independent 126-raster audit must confirm the promoted file.'),
    }
    (ROOT / 'evidence/soft_novelty_refinement.json').write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    if best is None:
        print('NO beta clears the duplicate stop with these witnesses; STOP.', flush=True)
        return 1
    winner = dict(arm='E3_fusion', lam=LAM, budget=BUDGET, crowd_cap=100,
                  soft_beta=best['beta'], dti=best['dti'])
    (ROOT / '.cache/derived/winner.json').write_text(json.dumps(winner, indent=2) + '\n')
    print(json.dumps({'best_passing': best,
                      'pooled_dti': summary['scores'][f'E3_soft{int(best["beta"]*100)}']['dti'],
                      'ci95': summary['scores'][f'E3_soft{int(best["beta"]*100)}']['ci95']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
