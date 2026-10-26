#!/usr/bin/env python3
"""Validate and mirror the single canonical negative run card, not a new run."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
card_path = ROOT / 'evidence/run_card.json'
card = json.loads(card_path.read_text())
audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
parallel = json.loads((ROOT / 'docs/data/portfolio.json').read_text())
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
corroboration = json.loads((ROOT / 'evidence/parallel_candidate_audit.json').read_text())
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
        and len(card['note']) <= 140):
    raise ValueError('Run-card evidence changed; manual review required before publication')
text = json.dumps(card, indent=2, allow_nan=False) + '\n'
for rel in ('docs/data/run-card.json', 'docs/data/run_card.json', 'site/data/run_card.json'):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print('Mirrored canonical card:', out)
