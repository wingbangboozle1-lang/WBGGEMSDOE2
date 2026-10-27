#!/usr/bin/env python3
"""2026-10-27 campaign: three preregistered geological lanes, one shared evaluator.

Protocol compliance (no private evaluator/writer/metric):
* ``gems57.holdout.buffered_component_draw`` -- whole connected catalogue
  components withheld, 3 px feature-context buffer, 12 px label-blind region
  erosion, visible faults masked pixel-exactly in scoring.
* ``gems57.evaluate_holdout.evaluate`` + ``pooled_summary`` -- exact DTI,
  alpha 0.2 / beta 0.8 / 300 m triangular kernel, pooled over 4 spatial folds
  with a paired 20 km spatial-block bootstrap 95% CI.
* ``gems57.emit.emit_decimated`` / ``emit_prefix`` -- shared dot allocation.
* ``gems57.submission_writer.write_submission`` -- shared TIFF/ZIP writer.

LEAKAGE FIX (documented in evidence/campaign_20261027.json): a first pass trained
with ``ctx_dist_visible`` learned the trivial identity "visible catalogue pixel ->
distance 0" and emitted zero-coverage dots. It was discarded before any result was
trusted. Here the model sees ONLY label-free geophysical features. The fold-visible
catalogue is used once, at emission, as a fixed physical collar prior; it is never
a training column. Single-feature canaries cover both the geophysics and the prior.
No competition slot is spent: selector and weekly cap remain with the human.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'data/shared_template/src'))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))

from gems57 import emit, evaluate_holdout, grid, holdout, submission_writer  # noqa: E402
from gems57.evaluate_holdout import from_terms  # noqa: E402

FEATURES = json.loads((ROOT / 'evidence/derived_features.json').read_text())['features']
STATIC_NAMES = list(FEATURES)
ARMS = {
    'E1_flexure': [n for n in STATIC_NAMES if n.startswith('flex_')],
    'E2_alteration': [n for n in STATIC_NAMES if n.startswith('alt_')],
    'E3_fusion': STATIC_NAMES,
}
CONTROL_ARMS = {'C0_collar_only': []}
LAMBDAS = (0.35, 0.70)
BUDGETS = (20_000, 37_654, 60_000, 100_000)
SEED = 20261027
NAME = 'wbg2-20261027-blind-discontinuity-unique'


def log(msg: str) -> None:
    print(f'[{dt.datetime.now(dt.timezone.utc):%H:%M:%S}] {msg}', flush=True)


def static_memmaps() -> dict[str, np.ndarray]:
    return {n: np.load(ROOT / FEATURES[n]['file'], mmap_mode='r') for n in STATIC_NAMES}


def collar_prior(visible: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Distance to the VISIBLE catalogue and a fixed 6 px (600 m) collar prior."""
    d = ndi.distance_transform_edt(~np.asarray(visible, bool))
    prior = np.exp(-0.5 * ((d - 6.0) / 4.0) ** 2).astype(np.float32)
    prior[~footprint] = 0
    return d, prior


def training_rows(g, fold, rng) -> tuple[np.ndarray, np.ndarray]:
    """Visible-fault positives OUTSIDE the scored region; no hidden labels."""
    excl = ndi.binary_dilation(fold['hidden_all'], iterations=3)
    zone = g.footprint & ~fold['region'] & ~excl
    pos = np.flatnonzero((fold['visible'] & zone).ravel())
    negpool = np.flatnonzero((zone & ~g.catalogue & ~excl).ravel())
    neg = rng.choice(negpool, min(3 * len(pos), len(negpool)), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(len(pos), np.int8), np.zeros(len(neg), np.int8)])
    return idx, y


def fit_predict(feats: dict[str, np.ndarray], names: list[str], g, fold,
                rng, seed: int) -> np.ndarray:
    idx, y = training_rows(g, fold, rng)
    iy, ix = np.unravel_index(idx, g.shape)
    X = np.column_stack([np.asarray(feats[n][iy, ix], np.float32) for n in names])
    model = HistGradientBoostingClassifier(
        max_iter=90, learning_rate=0.09, max_leaf_nodes=31, max_bins=128,
        l2_regularization=2.0, early_stopping=False, random_state=seed)
    model.fit(X, y)
    fp_idx = np.flatnonzero(g.footprint.ravel())
    fy, fx = np.unravel_index(fp_idx, g.shape)
    out = np.empty(fp_idx.size, np.float32)
    for start in range(0, fp_idx.size, 400_000):
        sl = slice(start, min(start + 400_000, fp_idx.size))
        Z = np.column_stack([np.asarray(feats[n][fy[sl], fx[sl]], np.float32) for n in names])
        out[sl] = model.predict_proba(Z)[:, 1]
    p = np.zeros(g.shape, np.float32)
    p.flat[fp_idx] = np.clip(out, 0, 1)
    return p


def rank_geo(p: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """Spread the model's compressed probabilities into a usable [0,1] score."""
    hi = max(float(np.percentile(p[allowed], 99.5)), 1e-6)
    return np.sqrt(np.clip(p / hi, 0, 1)).astype(np.float32)


def canaries(g, folds, feats_by_fold, priors) -> dict:
    rng = np.random.default_rng(SEED)
    names = STATIC_NAMES + ['collar_prior']
    scores: dict[str, list[float]] = {n: [] for n in names}
    for fold, feats, prior in zip(folds, feats_by_fold, priors):
        active = g.footprint & fold['region'] & ~fold['masked_known']
        truth = (fold['truth'] & active).ravel()
        ti = np.flatnonzero(truth)
        pool = np.flatnonzero(active.ravel() & ~truth)
        ni = rng.choice(pool, min(4 * len(ti), len(pool)), replace=False)
        idx = np.concatenate([ti, ni])
        labels = np.concatenate([np.ones(len(ti), np.int8), np.zeros(len(ni), np.int8)])
        iy, ix = np.unravel_index(idx, g.shape)
        for n in names:
            a = prior if n == 'collar_prior' else feats[n]
            auc = roc_auc_score(labels, np.asarray(a[iy, ix], np.float64))
            scores[n].append(round(float(max(auc, 1 - auc)), 6))
    rows = {n: {'per_fold_directed_auc': v, 'max_directed_auc': max(v),
                'leakage_alarm': max(v) > 0.90} for n, v in scores.items()}
    alarmed = sorted(n for n, r in rows.items() if r['leakage_alarm'])
    receipt = {
        'schema': 'wbggems.leakage-canary.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'LEAKAGE-CANARY',
        'method': ('Single-feature directed AUC = max(AUC, 1-AUC) on each fold\'s '
                   'label-blind scored region; withheld component pixels vs 4x random '
                   'active non-truth pixels. >0.90 is an alarm.'),
        'folds': len(folds), 'withheld_positive_pixels': int(sum(int(f['truth'].sum()) for f in folds)),
        'alarm_threshold': 0.90, 'alarmed_features': alarmed, 'features': rows,
        'code_path_note': ('collar_prior is a deterministic function of the fold-visible '
                           'catalogue only; no hidden label array is read. The discarded '
                           'first pass trained on ctx_dist_visible and learned a trivial '
                           'self-identity; that column is no longer used anywhere.'),
    }
    (ROOT / 'evidence/canaries_20261027.json').write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    log(f'canaries: max directed AUC {max(r["max_directed_auc"] for r in rows.values()):.4f}; '
        f'alarms {alarmed}')
    return receipt


def historical_controls(g) -> dict[str, np.ndarray]:
    manifest = json.loads((ROOT / 'config/registry_inputs.json').read_text())
    out = {}
    for e in manifest['inputs'][:9]:
        path = ROOT / 'data/registry' / f"{e['id']}.tif"
        with rasterio.open(path) as src:
            a = src.read(1)
        out[f"H_{e['id']}"] = np.where(np.isfinite(a) & (a > 0) & g.footprint, 1, 0).astype(np.float32)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['canaries', 'holdout', 'final', 'all'], default='all')
    args = parser.parse_args()
    t0 = time.time()
    g = grid.load_grid(ROOT / 'data/official')
    folds, quad = holdout.buffered_component_draw(g, seed=20, hide_frac=0.20,
                                                  buffer_px=3, boundary_px=12)
    n_withheld = int(sum(int(f['truth'].sum()) for f in folds))
    log(f'grid {g.shape}; footprint {int(g.footprint.sum())}; catalogue {int(g.catalogue.sum())}; '
        f'withheld positives {n_withheld}; folds {len(folds)}')
    static = static_memmaps()
    dist_prior = [collar_prior(f['visible'], g.footprint) for f in folds]
    priors = [p for _d, p in dist_prior]

    if args.stage in ('canaries', 'all'):
        canaries(g, folds, [static] * len(folds), priors)
        if args.stage == 'canaries':
            return 0

    if args.stage in ('holdout', 'all'):
        crowd = np.load(ROOT / 'data/registry_crowd.npy').astype(np.float32)
        crowd_n = np.minimum(crowd / 100.0, 1.0)
        valid = g.footprint
        terms: dict[str, dict] = {}
        per_fold: dict[str, dict] = {}
        for arm, names in {**ARMS, **CONTROL_ARMS}.items():
            terms[arm] = {lam: {b: None for b in BUDGETS} for lam in LAMBDAS}
            per_fold[arm] = {}
            for fi, fold in enumerate(folds):
                d_vis, prior = dist_prior[fi]
                allowed = valid & ~fold['masked_known'] & (d_vis > 2)
                if names:
                    rng = np.random.default_rng(SEED + fi)
                    p = fit_predict(static, names, g, fold, rng, SEED + fi)
                    surface = (rank_geo(p, allowed) * (0.15 + 0.85 * prior)).astype(np.float32)
                else:
                    surface = prior.copy()
                surface[~allowed] = 0
                for lam in LAMBDAS:
                    pw = (surface * (1.0 - lam * crowd_n)).astype(np.float32)
                    pw[~allowed] = 0
                    ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
                    for b in BUDGETS:
                        dots = emit.emit_prefix(ranked, b).astype(np.float32)
                        result, block = evaluate_holdout.evaluate(dots, fold, valid, block_side=200)
                        key = f'fold{fi}_lam{lam}_b{b}'
                        per_fold[arm][key] = dict(dti=result['dti'], tpw=result['tpw'],
                                                  fpw=result['fpw'], fnw=result['fnw'],
                                                  n_truth=result['n_truth'], emitted=result['emitted'])
                        terms[arm][lam][b] = block if terms[arm][lam][b] is None else terms[arm][lam][b] + block
                log(f'{arm} fold {fi} done')
        for name, a in historical_controls(g).items():
            blocks = None
            for fold in folds:
                result, block = evaluate_holdout.evaluate(a, fold, valid, block_side=200)
                blocks = block if blocks is None else blocks + block
            terms[name] = {0.0: {0: blocks}}
            per_fold[name] = {'dots': int((a > 0).sum())}
        estimates = []
        for arm, by_lam in terms.items():
            for lam, by_b in by_lam.items():
                for b, block in by_b.items():
                    if block is None:
                        continue
                    t = block.sum(axis=0)
                    estimates.append(dict(arm=arm, lam=lam, budget=b,
                                          dti=float(from_terms(t)),
                                          tpw=float(t[0]), fpw=float(t[1]),
                                          fnw=float(t[2]), n_truth=int(round(t[3]))))
        estimates.sort(key=lambda r: -r['dti'])
        controls = [e for e in estimates if e['arm'].startswith('H_') or e['arm'] in CONTROL_ARMS]
        candidates = [e for e in estimates if e['arm'] in ARMS]
        winner = candidates[0]
        best_control = controls[0]
        pooled_arms = {
            winner['arm']: terms[winner['arm']][winner['lam']][winner['budget']],
            best_control['arm']: terms[best_control['arm']][best_control['lam']][best_control['budget']],
        }
        summary = evaluate_holdout.pooled_summary(pooled_arms, draws=2000, seed=SEED,
                                                  candidate=winner['arm'])
        receipt = {
            'schema': 'wbggems.holdout-campaign.v1',
            'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'evidence_class': 'HOLDOUT-DTI',
            'evaluator_version': evaluate_holdout.VERSION,
            'implementation_sha256': evaluate_holdout.implementation_hashes(),
            'folds': [f['receipt'] for f in folds],
            'withheld_positive_pixels': n_withheld,
            'n_folds': len(folds), 'alpha': 0.2, 'beta': 0.8,
            'triangular_radius_m': 300, 'block_side_px': 200,
            'arms': ARMS, 'control_arms': CONTROL_ARMS,
            'lambdas': list(LAMBDAS), 'budgets': list(BUDGETS),
            'emission_rule': ('rank_geo(model) * (0.15 + 0.85 * collar_prior(visible)); '
                              'novelty multiplier 1 - lambda*crowd/100; 3 px decimated tiles'),
            'discarded_first_pass': ('Trained with ctx_dist_visible; learned the trivial '
                                     'self-identity and emitted 0.0 DTI. No result trusted.'),
            'canary_file': 'evidence/canaries_20261027.json',
            'estimates': estimates, 'winner': winner, 'best_control': best_control,
            'pooled_summary': summary, 'per_fold': per_fold,
            'caveat': ('Hide-and-recover withheld mapped catalogue components are a proxy, '
                       'not the organizer public/private fault set. Historical control rasters '
                       'were built with the full catalogue and may be optimistically biased.'),
        }
        (ROOT / 'evidence/holdout_20261027.json').write_text(
            json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        (ROOT / '.cache/derived/winner.json').write_text(json.dumps(winner, indent=2) + '\n')
        log(f'winner {winner}; best control {best_control}; '
            f'pooled DTI {summary["scores"][winner["arm"]]["dti"]:.5f} '
            f'CI {summary["scores"][winner["arm"]]["ci95"]}')
        if args.stage == 'holdout':
            return 0

    # ---------------- final candidate ----------------
    winner = json.loads((ROOT / '.cache/derived/winner.json').read_text())
    names = ARMS[winner['arm']]
    crowd = np.load(ROOT / 'data/registry_crowd.npy').astype(np.float32)
    cap = int(winner.get('crowd_cap', 100))
    d_full, prior_full = collar_prior(g.catalogue, g.footprint)
    allowed = g.footprint & ~g.catalogue & (d_full > 2) & (crowd <= cap)
    full_fold = dict(region=np.zeros(g.shape, bool), hidden_all=np.zeros(g.shape, bool),
                     visible=g.catalogue, masked_known=g.catalogue)
    rng = np.random.default_rng(SEED + 999)
    p = fit_predict(static, names, g, full_fold, rng, SEED + 999)
    surface = (rank_geo(p, allowed) * (0.15 + 0.85 * prior_full)).astype(np.float32)
    surface[~allowed] = 0
    beta = float(winner.get('soft_beta', 0.0))
    union_path = ROOT / '.cache/derived/dense_witness_union.npy'
    dense_union = np.load(union_path) if beta > 0 else np.zeros(g.shape, bool)
    preplacement = (surface * (1.0 - beta * dense_union)).astype(np.float32)
    preplacement[~allowed] = 0
    np.save(ROOT / '.cache/derived/final_preplacement_surface.npy', preplacement)
    np.save(ROOT / '.cache/derived/catalogue.npy', g.catalogue)
    np.save(ROOT / '.cache/derived/footprint.npy', g.footprint)
    preview_ranked, _ = emit.emit_decimated(preplacement, allowed, tile_px=3)
    preview = emit.emit_prefix(preview_ranked, int(winner['budget']))
    np.save(ROOT / '.cache/derived/preview_dots.npy', preview)
    lam = float(winner['lam'])
    crowd_n = np.minimum(crowd / 100.0, 1.0)
    pw = (preplacement * (1.0 - lam * crowd_n)).astype(np.float32)
    pw[~allowed] = 0
    ranked, _ = emit.emit_decimated(pw, allowed, tile_px=3)
    dots = emit.emit_prefix(ranked, int(winner['budget']))
    values = np.where(dots, 1.0, 0.0).astype(np.float32)
    np.save(ROOT / '.cache/derived/final_dots.npy', values)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    digest = hashlib.sha256(values.tobytes()).hexdigest()[:10]
    filename = (f'wbg2-blind-discontinuity-{winner["arm"].split("_")[0]}-soft{int(round(beta*100))}-'
                f'{stamp}-{digest}-zeros.tif')
    target = ROOT / 'docs/downloads' / filename
    note = (f'Blind-discontinuity {winner["arm"]} soft{int(round(beta*100))}; '
            f'HOLDOUT-DTI proxy only; 126-raster audit; no organizer score.')
    assert len(note) <= 140, len(note)
    receipt = submission_writer.write_submission(
        target, values, ROOT / 'data/official/sample_submission.tif', g.footprint,
        note=note, name=NAME, catalogue=g.catalogue,
        metadata={'arm': winner['arm'], 'lam': lam, 'budget': winner['budget'],
                  'crowd_cap': cap, 'soft_beta': beta,
                  'hard_cap_refinement': 'evidence/novelty_refinement.json',
                  'soft_refinement': 'evidence/soft_novelty_refinement.json',
                  'holdout_evaluator': evaluate_holdout.VERSION,
                  'source': 'hash-pinned owner mirror; not organizer authenticated'})
    local = ROOT / 'downloads' / filename
    shutil.copyfile(target, local)
    for suffix in ('.zip', '.json'):
        shutil.copyfile(target.with_suffix(suffix), local.with_suffix(suffix))
    log(f'wrote {target} ({target.stat().st_size} bytes), sha256 {receipt["sha256"]}')
    campaign = {
        'schema': 'wbggems.campaign.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'winner': winner, 'filename': filename, 'file': str(target.relative_to(ROOT)),
        'local_copy': str(local.relative_to(ROOT)),
        'note': note, 'submission_name': NAME,
        'tif_sha256': receipt['sha256'], 'zip_sha256': receipt['zip_sha256'],
        'writer_receipt': receipt, 'runtime_seconds': time.time() - t0,
        'surface_file': '.cache/derived/final_preplacement_surface.npy',
        'preview_dots_file': '.cache/derived/preview_dots.npy',
        'final_dots_file': '.cache/derived/final_dots.npy',
        'discarded_first_pass': ('Trained with ctx_dist_visible; 0.0 DTI; discarded before '
                                 'any conclusion. See docstring and holdout receipt.'),
    }
    (ROOT / 'evidence/campaign_20261027.json').write_text(
        json.dumps(campaign, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'winner': winner, 'filename': filename,
                      'sha256': receipt['sha256'], 'runtime': campaign['runtime_seconds']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
