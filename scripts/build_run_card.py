#!/usr/bin/env python3
"""Validate the negative card and bind exact portable forensic outputs; no new run."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
card_path = ROOT / 'evidence/run_card.json'
card = json.loads(card_path.read_text())
audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
parallel = json.loads((ROOT / 'docs/data/portfolio.json').read_text())
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
corroboration = json.loads((ROOT / 'evidence/parallel_candidate_audit.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
lat = audit['lattice_capacity']
dense = audit['dense_probability_prior']
# Stop before changing published files if the card is inconsistent with either
# independently reopened audit or any null/non-promotion invariant.
if not (card['verdict'] == 'negative' and card['ok_to_submit'] is False
        and card['ok_to_download_new_tif'] is False and card['raster_sha256'] is None
        and card['submission_name'] is None and card['submission_note'] is None
        and card['holdout']['dti'] is None and card['holdout']['ci95'] is None
        and card['holdout_dti']['value'] is None and card['holdout_dti']['ci95'] is None
        and card['experiment_count'] == 0 and card['weekly_submission_slots_used'] == 0
        and card['uniqueness']['candidate_surface_correlation'] is None
        and card['uniqueness']['candidate_final_overlap'] is None
        and card['uniqueness']['minimum_overlap_bound'] == lat['minimum_overlap']
        and card['registry']['binary_lattice_minimum_overlap_at_budget'] == lat['minimum_overlap']
        and lat['minimum_overlap'] == parallel['literal_registry_witness']['minimum_possible_overlap_at_example_budget']
        and dense['full_footprint_positive'] is True
        and parallel['dense_probability_witness']['universal_overlap_blocker'] is True
        and card['registry']['dense_probability_prior_full_footprint'] is True
        and review['ok_to_submit'] is False
        and corroboration['ok_to_submit'] is False
        and corroboration['candidate_sha256'] == review['sha256']
        and corroboration['witnesses']['lattice']['overlap_fraction'] == review['literal_overlap_3px']['lattice']
        and corroboration['format']['dataset_mask_invalid_inside_footprint'] == review['format']['masked_inside']
        and review['literal_overlap_3px']['lattice'] > .7
        and review['format']['format_valid_against_reference'] is False
        and card['parallel_session']['rejected_candidate_sha256'] == review['sha256']
        and card['parallel_session']['lattice_overlap_3px'] == review['literal_overlap_3px']['lattice']
        and card['parallel_session']['continuous_prior_overlap_3px'] == review['literal_overlap_3px']['continuous_prior']
        and card['parallel_session']['masked_inside_footprint'] == review['format']['masked_inside']
        and card['parallel_session']['source_reported_holdout'] == review['source_reported_holdout']
        and card['parallel_session']['ok_to_submit'] is False
        and conduit['ok_to_submit'] is False and conduit['holdout_dti'] is None
        and conduit['preplacement_surface_correlation'] is None
        and conduit['witnesses']['13GEMSDOE']['source_threshold_ge_0_5']['fraction'] > .7
        and card['conduit_parallel_session']['rejected_candidate_sha256'] == conduit['sha256']
        and card['conduit_parallel_session']['lattice_overlap_3px_source_threshold'] == conduit['witnesses']['13GEMSDOE']['source_threshold_ge_0_5']['fraction']
        and card['conduit_parallel_session']['continuous_prior_overlap_3px'] == conduit['witnesses']['17GEMSDOE_dense_prior']['source_threshold_ge_0_5']['fraction']
        and card['conduit_parallel_session']['holdout_dti'] is None
        and card['conduit_parallel_session']['preplacement_surface_correlation'] is None
        and card['conduit_parallel_session']['ok_to_submit'] is False
        and len(card['note']) <= 140):
    raise ValueError('Run-card evidence changed; manual review required before publication')
import sys
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.release import CANONICAL_RUN_CARDS, digest, load_negative_release
release = load_negative_release(ROOT)
if (card['release_reconciliation']['owned_tif_paths'] != release['scope']['owned_tif_paths']
        or card['release_reconciliation']['distinct_raster_sha256'] != release['scope']['distinct_tif_sha256']):
    raise ValueError('Research inventory changed; review the canonical disposition')

# A separate local recheck must reproduce both prior measurements, not merely
# have a newer timestamp. These receipts only reject existing rasters; they do
# not measure an original surface, certify the whole registry or approve a slot.
registry_recheck_path = ROOT / 'evidence/registry_independent_review_20261027.json'
release_recheck_path = ROOT / 'evidence/release_independent_review_20261027.json'
registry_recheck = json.loads(registry_recheck_path.read_text())
release_recheck = json.loads(release_recheck_path.read_text())
without_time = lambda record: {k: v for k, v in record.items() if k != 'generated_utc'}
if without_time(registry_recheck) != without_time(audit) or without_time(release_recheck) != without_time(release):
    raise ValueError('Independent recheck changed a measurement; review before publishing')
card['independent_forensic_recheck'] = {
    'evidence_class': 'BYTE-LEVEL-FORENSIC-MEASUREMENT; not an experiment or submission approval',
    'registry_receipt': str(registry_recheck_path.relative_to(ROOT)),
    'registry_receipt_sha256': digest(registry_recheck_path),
    'registry_recorded_utc': registry_recheck['generated_utc'],
    'release_receipt': str(release_recheck_path.relative_to(ROOT)),
    'release_receipt_sha256': digest(release_recheck_path),
    'release_recorded_utc': release_recheck['generated_utc'],
    'measurements_match_prior_receipts_excluding_timestamps': True,
    'all_current_registry_rasters_checked': False,
    'new_experiments': 0,
    'weekly_slots_used': 0,
}
card['validator']['status'] = (
    f"No raster generated in this review. {len(release['artifacts'])} existing identities in "
    f"{release['scope']['owned_tif_paths']} paths and {len(release['zip_archives'])} ZIPs "
    "were independently reopened; format checks are not organizer acceptance."
)
card['release_reconciliation']['pinned_witnesses'] = release['scope']['registry_rasters_opened']
card['release_reconciliation']['zip_archives'] = len(release['zip_archives'])
# Derive exact existing-artifact diagnostics from the independently generated
# audit; never populate the null NEW-candidate or score fields.
card['existing_artifact_audit'] = {
    'evidence_class': release['evidence_class'],
    'source_path': 'evidence/release_audit.json',
    'source_sha256': digest(ROOT / 'evidence/release_audit.json'),
    'recorded_utc': release['generated_utc'],
    'scope': release['scope'],
    'reference': release['reference'],
    'artifacts': [{k:r[k] for k in ('path','aliases','sha256','positive_support_cells','validator',
                                   'strict_all_finite_validator','surface_rank_correlation',
                                   'final_rank_correlation','lattice_overlap_3px','maximum_overlap_3px',
                                   'duplicate_witnesses','leaderboard_score_estimate','ok_to_submit','verdict')}
                  for r in release['artifacts']],
    'zip_archives': release['zip_archives'],
}

text = json.dumps(card, indent=2, allow_nan=False) + '\n'
for rel in CANONICAL_RUN_CARDS:
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print('Mirrored canonical card:', out)
