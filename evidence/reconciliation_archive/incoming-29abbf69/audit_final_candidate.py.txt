#!/usr/bin/env python3
"""Independent byte-level audit of the 2026-10-27 TIFF.

Reports BOTH readings of the parallel-run duplicate rule:
* literal -- every finite positive pixel of every registry raster is a "dot";
* like-for-like -- dot-overlap is applied only to geological dot fields, while
  rank correlation is applied to every raster (see docs/PROJECT_CHARTER.md).

Also checks the pre-placement surfaces, preview dots and final dots against every
resolved public raster, runs the shared + supplemental format validator, and
writes an exploratory (explicitly NOT-A-SCORE) historical calibration bracket.
No leaderboard value is invented and no submission slot is selected.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from validate_submission import run as format_run  # noqa: E402

SAMPLE = ROOT / 'data/official/sample_submission.tif'
UNIQUE_JSON = ROOT / 'evidence/final_uniqueness.json'
FORMAT_JSON = ROOT / 'evidence/final_format.json'
RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
JACCARD_LIMIT = 0.50
SUBSAMPLE = 250_000


def disk3() -> np.ndarray:
    y, x = np.mgrid[-3:4, -3:4]
    return (x * x + y * y) <= 9


def overlap(my_dots: np.ndarray, their_dots: np.ndarray, struct: np.ndarray) -> float:
    if my_dots.shape != their_dots.shape or not my_dots.any() or not their_dots.any():
        return 0.0
    halo = ndi.binary_dilation(their_dots, structure=struct)
    return float(halo[my_dots].mean())


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


def main() -> int:
    campaign = json.loads((ROOT / 'evidence/campaign_20261027.json').read_text())
    union_receipt = json.loads((ROOT / 'evidence/registry_union.json').read_text())
    holdout = json.loads((ROOT / 'evidence/holdout_20261027.json').read_text())
    tif = ROOT / campaign['file']
    with rasterio.open(SAMPLE) as src:
        fp = np.isfinite(src.read(1))
        expected = (src.shape, src.crs, src.transform)
    with rasterio.open(tif) as src:
        final_values = src.read(1)
        tif_meta = dict(shape=list(src.shape), crs=str(src.crs),
                        transform=list(src.transform)[:6], dtype=src.dtypes[0],
                        count=src.count, nodata=src.nodata)
    final_dots = np.isfinite(final_values) & (final_values > 0) & fp
    preview = np.load(ROOT / campaign['preview_dots_file']).astype(bool) & fp
    surface = np.load(ROOT / campaign['surface_file']).astype(np.float32)
    crowd = np.load(ROOT / 'data/registry_crowd.npy').astype(np.float32)
    lam = float(campaign['winner']['lam'])
    weighted = (surface * (1.0 - lam * np.minimum(crowd / 100.0, 1.0))).astype(np.float32)
    weighted[~fp] = 0

    rng = np.random.default_rng(20261027)
    fp_idx = np.flatnonzero(fp.ravel())
    pick = rng.choice(fp_idx, min(SUBSAMPLE, fp_idx.size), replace=False)
    sy, sx = np.unravel_index(pick, fp.shape)
    s0 = surface[sy, sx].astype(np.float64)
    s1 = weighted[sy, sx].astype(np.float64)

    cls = {r.get('local'): r for r in union_receipt['rows'] if r.get('local')}
    struct = disk3()
    rows = []
    for entry in union_receipt['rows']:
        base = dict(site=entry.get('site'), submission=entry.get('submission_name'),
                    sha256=entry.get('sha256'), local=entry.get('local'),
                    url=entry.get('url'), representation=entry.get('class', 'unavailable'))
        if 'sha256' not in entry or entry.get('class') in ('invalid', 'unavailable', None):
            base['error'] = entry.get('error', 'not fetched or invalid')
            rows.append(base)
            continue
        path = ROOT / entry['local']
        try:
            with rasterio.open(path) as src:
                if (src.shape, src.crs, src.transform) != expected or src.count != 1:
                    raise ValueError('grid mismatch or multi-band')
                a = src.read(1)
            dots = np.isfinite(a) & (a > 0) & fp
            v = a[sy, sx].astype(np.float64)
            rho0 = float(spearmanr(s0, v).statistic)
            rho1 = float(spearmanr(s1, v).statistic)
            if not np.isfinite(rho0):
                rho0 = 0.0
            if not np.isfinite(rho1):
                rho1 = 0.0
            base.update(
                their_dots=int(dots.sum()),
                final_overlap=overlap(final_dots, dots, struct),
                preview_overlap=overlap(preview, dots, struct),
                jaccard_final=jaccard(final_dots, dots),
                surface_spearman=rho0, weighted_surface_spearman=rho1,
                surface_spearman_abs=max(abs(rho0), abs(rho1)),
                duplicate_by_rho=bool(max(abs(rho0), abs(rho1)) > RHO_LIMIT),
                duplicate_by_overlap=bool(overlap(final_dots, dots, struct) > OVERLAP_LIMIT),
                decoded_identical=bool(np.array_equal(final_dots & fp, dots)),
                byte_identical=entry.get('sha256') == campaign['tif_sha256'],
            )
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            base['error'] = str(exc)[:200]
        rows.append(base)

    checked = [r for r in rows if 'error' not in r]
    dot_rows = [r for r in checked if r['representation'] == 'dot_field']
    focus_ids = {'GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28',
                 'GEMSDOE30', 'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36'}

    def worst(subset, key):
        if not subset:
            return None, None
        r = max(subset, key=lambda x: x[key])
        return r[key], r['submission']

    lit_ov, lit_ov_name = worst(checked, 'final_overlap')
    lit_rho, lit_rho_name = worst(checked, 'surface_spearman_abs')
    like_ov, like_ov_name = worst(dot_rows, 'final_overlap')
    focus_rows = [r for r in checked if r['site'] in focus_ids]
    focus_ov, focus_ov_name = worst(focus_rows, 'final_overlap')
    focus_jac, focus_jac_name = worst(focus_rows, 'jaccard_final')
    focus_by_site = {}
    for r in focus_rows:
        cur = focus_by_site.setdefault(r['site'], dict(overlap=0.0, jaccard=0.0, files=0))
        cur['overlap'] = max(cur['overlap'], r['final_overlap'])
        cur['jaccard'] = max(cur['jaccard'], r['jaccard_final'])
        cur['files'] += 1
    nine_sites_covered = focus_ids.issubset(focus_by_site)
    literal_firings = [r['submission'] for r in checked if r['duplicate_by_overlap']]
    like_firings = [r['submission'] for r in dot_rows if r['duplicate_by_overlap']]
    rho_firings = [r['submission'] for r in checked if r['duplicate_by_rho']]
    available = [e for e in union_receipt['rows']
                 if e.get('class') in ('dot_field', 'continuous_surface', 'space_filling_control')]
    complete = (len(checked) == len(available)
                and not any(r.get('error') for r in rows if r.get('local') in
                            {e.get('local') for e in available}))

    # Exploratory calibration bracket: historical holdout DTI vs USER-REPORTED
    # public claims. Explicitly NOT a score and never written as one.
    ledger = json.loads((ROOT / 'config/registry_inputs.json').read_text())
    claims = {e['id']: e['user_reported_claim'] for e in ledger['inputs'][:9]}
    hist = {e['arm'].replace('H_', ''): e['dti'] for e in holdout['estimates']
            if e['arm'].startswith('H_')}
    ours = float(holdout['pooled_summary']['scores'][holdout['winner']['arm']]['dti'])
    pairs = [(hid, hist[hid], claims[hid]) for hid in claims
             if hid in hist and claims[hid] is not None and hist[hid] is not None]
    neighbours = [c for _hid, d, c in pairs if abs(d - ours) <= 0.03]
    bracket = dict(
        evidence_class='EXPLORATORY-PROJECTION-NOT-A-SCORE',
        method=('Historical focus rasters evaluated on the SAME folds; user-reported '
               'claims (NOT organizer receipts) within +/-0.03 holdout DTI of this '
               'candidate define a bracket. No calibrated leaderboard forecast exists.'),
        historical_pairs=[dict(site=h, holdout_dti=d, user_reported_claim=c) for h, d, c in pairs],
        candidate_holdout_dti=ours,
        bracket=[min(neighbours), max(neighbours)] if neighbours else None,
        usable_as_score=False,
        note='A projection is never a score. Public/private truth and receipts are unavailable.',
    )

    format_receipt = format_run(tif, SAMPLE)
    FORMAT_JSON.write_text(json.dumps(format_receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    result = {
        'schema': 'wbggems.final-uniqueness.v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'evidence_class': 'REGISTRY-MEASUREMENT',
        'file': campaign['file'], 'tif_sha256': campaign['tif_sha256'],
        'tif_meta': tif_meta, 'my_dots': int(final_dots.sum()),
        'preview_dots': int(preview.sum()),
        'footprint_cells': int(fp.sum()),
        'rho_limit': RHO_LIMIT, 'overlap_limit': OVERLAP_LIMIT,
        'jaccard_limit': JACCARD_LIMIT,
        'registry_scope': union_receipt['scope'],
        'registry_rasters_expected': len(available), 'registry_rasters_checked': len(checked),
        'registry_unavailable_or_invalid': len(rows) - len(available),
        'complete_accessible_scan': bool(complete),
        'representation_counts': union_receipt['counts'],
        'literal_reading': dict(
            worst_spearman=lit_rho, worst_spearman_submission=lit_rho_name,
            worst_forward_overlap=lit_ov, worst_overlap_submission=lit_ov_name,
            overlap_firings=len(literal_firings), rho_firings=len(rho_firings),
            duplicate=bool(literal_firings or rho_firings),
            note=('Literal reading fires on space-filling controls / continuous prior for ANY '
                  'nonempty candidate; reported, not silently exempted.')),
        'like_for_like_reading': dict(
            dot_field_rasters=len(dot_rows),
            worst_forward_overlap=like_ov, worst_overlap_submission=like_ov_name,
            overlap_firings=len(like_firings), rho_firings=len(rho_firings),
            duplicate=bool(like_firings or rho_firings),
            nine_focus_worst_overlap=focus_ov, nine_focus_worst_site=focus_ov_name,
            nine_focus_worst_jaccard=focus_jac, nine_focus_worst_jaccard_site=focus_jac_name,
            nine_focus_sites_checked=len(focus_by_site),
            per_focus_site_worst=focus_by_site,
            unique_vs_nine_focus=bool(nine_sites_covered
                                      and all(v['overlap'] <= OVERLAP_LIMIT
                                              and v['jaccard'] <= JACCARD_LIMIT
                                              for v in focus_by_site.values())
                                      and not any(r['decoded_identical'] for r in focus_rows)),
            note=('Inherited thresholds applied to geological dot fields; rank correlation '
                  'applied to every raster including continuous surfaces and controls.')),
        'format': dict(ok=bool(format_receipt['ok']),
                       shared_format_ok=bool(format_receipt['shared_format_ok']),
                       supplemental_mask_and_format_ok=bool(format_receipt['supplemental_mask_and_format_ok']),
                       masked_inside_footprint=format_receipt['masked_inside_footprint'],
                       no_nan_inside_footprint=format_receipt['no_nan_inside_footprint'],
                       inside_values_in_0_1=format_receipt['inside_values_in_0_1'],
                       reference_provenance=format_receipt['reference_provenance'],
                       organizer_acceptance=format_receipt['organizer_acceptance']),
        'exploratory_projection_not_score': bracket,
        'rows': rows,
    }
    UNIQUE_JSON.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('my_dots', 'registry_rasters_checked',
          'complete_accessible_scan', 'literal_reading', 'like_for_like_reading', 'format')}, indent=2))
    return 0 if format_receipt['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
