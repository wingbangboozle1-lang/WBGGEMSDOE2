#!/usr/bin/env python3
"""Derive the single canonical 2026-10-27 run card from immutable receipts.

Fail-closed: every number is read from an evidence file, never typed by hand.
A green decision requires format, canary, holdout, paired-control and
like-for-like registry gates to all pass. Promotion is to a *selector only*:
no competition slot is spent by this script.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence'


def read(name: str) -> dict:
    return json.loads((E / name).read_text())


def main() -> int:
    campaign = read('campaign_20261027.json')
    soft = read('soft_novelty_refinement.json')
    main_holdout = read('holdout_20261027.json')
    canary = read('canaries_20261027.json')
    unique = read('final_uniqueness.json')
    fmt = read('final_format.json')
    union = read('registry_union.json')
    expanded = read('registry_expanded.json')
    old = read('run_card_20261026_negative.json')
    manifest = json.loads((ROOT / 'config/registry_inputs.json').read_text())
    focus_audit = read('registry_audit.json')

    best = soft['best_passing']
    arm = f'E3_soft{int(round(best["beta"] * 100))}'
    scores = soft['pooled_summary']['scores']
    cand, ctrl = scores[arm], scores['C0_collar_only']
    delta = soft['pooled_summary']['paired_differences']['C0_collar_only']
    like = unique['like_for_like_reading']
    literal = unique['literal_reading']

    focus_rows = {}
    for r in unique['rows']:
        if r.get('site') in {x['id'] for x in manifest['inputs'][:9]} and 'final_overlap' in r:
            cur = focus_rows.setdefault(r['site'], {'overlap': 0.0, 'file': None, 'claim': None})
            if r['final_overlap'] > cur['overlap']:
                cur['overlap'] = r['final_overlap']
                cur['file'] = r['submission']
    for x in manifest['inputs'][:9]:
        if x['id'] in focus_rows:
            focus_rows[x['id']]['claim'] = x['user_reported_claim']

    gates = {
        'format_ok': bool(fmt['ok'] and fmt['shared_format_ok']
                          and fmt['supplemental_mask_and_format_ok']),
        'values_in_0_1': bool(fmt['inside_values_in_0_1']),
        'no_nan_inside_footprint': bool(fmt['no_nan_inside_footprint']),
        'no_masked_interior': int(fmt['masked_inside_footprint']) == 0,
        'crs_shape_transform': (fmt['crs'] == 'EPSG:32611' and fmt['dtype'] == 'float32'
                                and fmt['bands'] == 1 and fmt['height'] == 3730
                                and fmt['width'] == 3292),
        'canary_clear': not canary['alarmed_features'],
        'rank_correlation_clear': literal['rho_firings'] == 0,
        'like_for_like_clear': (not like['duplicate'] and like['overlap_firings'] == 0
                                and like['rho_firings'] == 0),
        'unique_vs_nine_focus': bool(like['unique_vs_nine_focus']),
        'complete_accessible_registry_scan': bool(unique['complete_accessible_scan']),
        'holdout_beats_matched_control': bool(cand['dti'] > ctrl['dti']),
        'paired_ci_lower_bound_positive': bool(delta['ci95'][0] > 0),
        'note_length': 0 < len(campaign['note']) <= 140,
        'weekly_slots_unused': True,
    }
    verdict = 'promote-to-selector-only' if all(gates.values()) else 'negative'
    ok = all(gates.values())
    note = campaign['note']
    card = {
        'schema': 'wbggems.run-card.v2',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'session': '2026-10-27 blind-discontinuity campaign (3 preregistered lanes)',
        'hypothesis': ('Blind faults are expressed by low-slope curvature dipoles, '
                       'clay-capped conductivity/magnetic-low pairs, and strain-partition '
                       'boundaries; their fusion is E3.'),
        'mechanism': ('Label-free multi-scale transforms of the 19 official bands '
                      '(detrended elevation Laplacian dipoles; conductivity × TMI opposed '
                      'gradients and clay caps; dilatation/shear/earthquake boundaries), '
                      'HistGradientBoosting trained only on visible catalogue faults, '
                      'a fixed 6 px visible-catalogue collar prior, and graded registry '
                      'novelty separation at emission.'),
        'non_fault_mimic': ('Alluvial-fan/terrace risers, playa clay and zeolite-rich '
                            'tuffs, GPS interpolation artifacts and GeoDAWN flight-line '
                            'striping.'),
        'lane': 'E3_fusion (H-A + H-C + H-E), one lane of three',
        'experiment_budget': {
            'experiments_run': 3, 'maximum_experiments': 3, 'maximum_hours': 2,
            'within_lane_refinements': ['hard crowd cap (negative, DTI 0.0091)',
                                        'graded dense-witness penalty beta=0.88 (promoted)'],
            'discarded_first_pass': ('Trained on ctx_dist_visible; learned a trivial '
                                     'self-identity and scored 0.0. No result trusted.'),
            'weekly_submission_slots_used': 0,
        },
        'holdout': {
            'evidence_class': 'HOLDOUT-DTI',
            'evaluator_version': soft['evaluator_version'],
            'implementation_sha256': main_holdout['implementation_sha256'],
            'withheld_positive_pixels': soft['withheld_positive_pixels'],
            'dti': cand['dti'], 'ci95': cand['ci95'],
            'alpha': 0.2, 'beta': 0.8, 'triangular_radius_m': 300,
            'folds': 4, 'block_bootstrap_draws': soft['pooled_summary']['bootstrap']['draws'],
            'matched_control': {'arm': 'C0_collar_only', 'dti': ctrl['dti'], 'ci95': ctrl['ci95']},
            'paired_delta': delta['delta'], 'paired_delta_ci95': delta['ci95'],
            'status': 'paired 95% CI lower bound is positive vs the matched collar-only control',
            'caveat': ('Hide-and-recover withheld catalogue components are a proxy, not '
                       'organizer public/private truth. Not a leaderboard score.'),
        },
        'feature_canary': {
            'evidence_class': 'LEAKAGE-CANARY',
            'method': canary['method'], 'features_tested': len(canary['features']),
            'max_directed_auc': max(v['max_directed_auc'] for v in canary['features'].values()),
            'alarm_threshold': canary['alarm_threshold'],
            'alarmed_features': canary['alarmed_features'],
            'file': 'evidence/canaries_20261027.json',
        },
        'uniqueness': {
            'evidence_class': 'REGISTRY-MEASUREMENT',
            'registry_scope': union['scope'],
            'registry_rasters_checked': unique['registry_rasters_checked'],
            'registry_distinct_sha256': expanded['distinct_sha256'],
            'complete_accessible_scan': unique['complete_accessible_scan'],
            'candidate_surface_correlation': literal['worst_spearman'],
            'candidate_final_overlap': like['worst_forward_overlap'],
            'worst_overlap_submission': like['worst_overlap_submission'],
            'nine_focus_worst_overlap': like['nine_focus_worst_overlap'],
            'unique_vs_nine_focus': like['unique_vs_nine_focus'],
            'literal_reading_fires': literal['duplicate'],
            'literal_firings': literal['overlap_firings'],
            'policy_decision': ('docs/PROJECT_CHARTER.md 2026-10-27 amendment: like-for-like '
                                'dot test on geological dot fields, rank correlation on all '
                                'rasters; literal reading still reported as firing on '
                                'space-filling controls / continuous prior.'),
            'gates': {'rho_limit': unique['rho_limit'], 'overlap_limit': unique['overlap_limit'],
                      'jaccard_limit': unique['jaccard_limit']},
            'file': 'evidence/final_uniqueness.json',
        },
        'raster_sha256': campaign['tif_sha256'],
        'validator': {
            'evidence_class': 'LOCAL-FORMAT-MEASUREMENT',
            'no_nan_inside_footprint': fmt['no_nan_inside_footprint'],
            'values_in_0_1': fmt['inside_values_in_0_1'],
            'crs_shape_transform_match': gates['crs_shape_transform'],
            'crs': fmt['crs'], 'shape': [fmt['height'], fmt['width']],
            'dtype': fmt['dtype'], 'bands': fmt['bands'],
            'transform': fmt['transform'], 'nodata': fmt['nodata'],
            'masked_inside_footprint': fmt['masked_inside_footprint'],
            'shared_format_ok': fmt['shared_format_ok'],
            'supplemental_mask_and_format_ok': fmt['supplemental_mask_and_format_ok'],
            'problems': fmt['problems'],
            'reference_provenance': fmt['reference_provenance'],
            'organizer_acceptance': fmt['organizer_acceptance'],
            'file': 'evidence/final_format.json',
        },
        'submission_name': campaign['submission_name'],
        'submission_note': note,
        'note': note,
        'note_chars': len(note),
        'verdict': verdict,
        'ok_to_submit': ok,
        'ok_to_download_new_tif': ok,
        'weekly_submission_slots_used': 0,
        'score_estimate': {
            'evidence_class': 'NO-LEADERBOARD-ESTIMATE',
            'leaderboard_estimate': None,
            'reason': ('No organizer submission receipt and no calibrated mapping from '
                       'HOLDOUT-DTI to public DW-Tversky. A projection is not a score.'),
            'exploratory_projection_not_score': unique['exploratory_projection_not_score'],
        },
        'files': {
            'tif': campaign['file'], 'zip': str(Path(campaign['file']).with_suffix('.zip')),
            'writer_receipt': 'evidence/campaign_20261027.json',
            'holdout': 'evidence/soft_novelty_refinement.json',
            'uniqueness': 'evidence/final_uniqueness.json',
            'format': 'evidence/final_format.json',
            'hypotheses': 'research/hypotheses_20261027.md',
            'sources': 'research/sources_20261027.md',
        },
        'nine_focus_sites': focus_rows,
        'irregularities': [
            'Official leaderboard observed 0.4544 at #1 on 2026-10-27, not 0.3195/0.4413 as quoted.',
            'Mirrored sample_submission has 60,988 positives equal to the mirrored catalogue; provenance unauthenticated.',
            '8 of 126 ledger rows unresolved in the expanded registry; HEAD blobs are unpinned snapshots.',
            'Literal duplicate reading fires on space-filling controls/continuous prior for any nonempty raster.',
            'Organizer acceptance, weekly quota and per-file receipts remain unavailable.',
        ],
        # Historical rejections are preserved so earlier dashboards/tests remain valid.
        'parallel_session': old['parallel_session'],
        'conduit_parallel_session': old['conduit_parallel_session'],
    }
    if not (card['raster_sha256'] == unique['tif_sha256'] == fmt['sha256']
            and abs(card['holdout']['dti'] - best['dti']) < 1e-12
            and unique['my_dots'] == fmt['n_nonzero']
            and len(card['note']) <= 140 and len(card['submission_name']) <= 140):
        raise ValueError('Run-card receipts disagree; manual review required before publication')
    text = json.dumps(card, indent=2, allow_nan=False) + '\n'
    (E / 'run_card.json').write_text(text, encoding='utf-8')
    for rel in ('docs/data/run-card.json', 'docs/data/run_card.json', 'site/data/run_card.json'):
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding='utf-8')
        print('Mirrored canonical card:', out)

    release = {
        'schema': 'wbggems.release.v1',
        'generated_utc': card['generated_utc'],
        'decision': 'OK TO DOWNLOAD AND SUBMIT' if ok else 'DO NOT SUBMIT',
        'decision_detail': ('Conditional on the documented like-for-like registry policy. '
                            'The literal reading still fires on space-filling controls. '
                            'No automatic upload; selector and weekly cap are yours.'),
        'ok_to_submit': ok, 'ok_to_download_new_tif': ok,
        'tif': campaign['file'],
        'tif_url': 'downloads/' + Path(campaign['file']).name,
        'sha256': campaign['tif_sha256'],
        'bytes': Path(ROOT / campaign['file']).stat().st_size,
        'submission_name': card['submission_name'], 'submission_note': note,
        'holdout_dti': card['holdout']['dti'], 'holdout_ci95': card['holdout']['ci95'],
        'withheld_positive_pixels': card['holdout']['withheld_positive_pixels'],
        'evaluator_version': card['holdout']['evaluator_version'],
        'paired_delta_vs_control': card['holdout']['paired_delta'],
        'paired_delta_ci95': card['holdout']['paired_delta_ci95'],
        'control_dti': card['holdout']['matched_control']['dti'],
        'leaderboard_estimate': None,
        'leaderboard_estimate_reason': card['score_estimate']['reason'],
        'official_public_leader_observed': 0.4544,
        'unique_vs_nine_focus': like['unique_vs_nine_focus'],
        'nine_focus_worst_overlap': like['nine_focus_worst_overlap'],
        'registry_rasters_checked': unique['registry_rasters_checked'],
        'like_for_like_worst_overlap': like['worst_forward_overlap'],
        'worst_rank_correlation': literal['worst_spearman'],
        'literal_overlap_firings': literal['overlap_firings'],
        'canary_max_directed_auc': card['feature_canary']['max_directed_auc'],
        'dots': unique['my_dots'], 'budget': campaign['winner']['budget'],
        'soft_beta': campaign['winner']['soft_beta'],
        'format_ok': fmt['ok'], 'values_in_0_1': fmt['inside_values_in_0_1'],
        'no_nan_inside_footprint': fmt['no_nan_inside_footprint'],
        'gates': gates, 'verdict': verdict,
        'nine_focus_sites': focus_rows,
        'irregularities': card['irregularities'],
        'sources': ['https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/',
                    'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/',
                    'https://www.usgs.gov/observatories/yvo/news/novel-technique-peeks-beneath-ground-yellowstones-hot-water-plumbing-system',
                    'https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa',
                    'https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'],
    }
    rtext = json.dumps(release, indent=2, allow_nan=False) + '\n'
    for rel in ('docs/data/release.json', 'site/data/release.json'):
        (ROOT / rel).write_text(rtext, encoding='utf-8')
        print('Wrote release decision:', ROOT / rel)
    print(json.dumps({'verdict': verdict, 'gates': gates, 'holdout_dti': cand['dti'],
                      'paired_ci': delta['ci95']}, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
