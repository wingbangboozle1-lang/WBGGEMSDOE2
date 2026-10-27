#!/usr/bin/env python3
"""Validate and mirror the single canonical negative run card across both dashboards."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
card_path = ROOT / "evidence/run_card.json"
card = json.loads(card_path.read_text())
audit = json.loads((ROOT / "evidence/registry_audit.json").read_text())
parallel = json.loads((ROOT / "docs/data/portfolio.json").read_text())
review = json.loads((ROOT / "evidence/parallel_review.json").read_text())
corroboration = json.loads((ROOT / "evidence/parallel_candidate_audit.json").read_text())
conduit = json.loads((ROOT / "evidence/conduit_review.json").read_text())
msptcd = json.loads((ROOT / "evidence/wbg2_msptcd_results.json").read_text())

lat = audit["lattice_capacity"]
dense = audit["dense_probability_prior"]
best_arm = msptcd["winning_experiment"]
best_sc = msptcd["holdout_pooled"]["scores"][best_arm]

if not (
    card["verdict"] == "negative"
    and card["ok_to_submit"] is False
    and card["ok_to_download_new_tif"] is False
    and card["raster_sha256"] is None
    and card["submission_name"] is None
    and card["submission_note"] is None
    and card["experiment_count"] == msptcd["budget_compliance"]["experiments_run"] == 3
    and card["weekly_submission_slots_used"] == 0
    and card["holdout"]["evaluator_version"] == "gems57-pooled-hide-v2"
    and card["holdout"]["withheld_positive_pixels"] == 60988
    and card["holdout"]["dti"] == best_sc["dti"]
    and card["holdout"]["ci95"] == best_sc["ci95"]
    and card["holdout_dti"]["value"] == best_sc["dti"]
    and card["holdout_dti"]["ci95"] == best_sc["ci95"]
    and card["feature_canary"]["status"] == "passed"
    and card["feature_canary"]["max_two_sided_auc"] == msptcd["canary_summary"]["max_two_sided_auc"]
    and card["feature_canary"]["max_two_sided_auc"] <= 0.90
    and card["research_candidate"]["tif_sha256"] == msptcd["artifact"]["tif_sha256"]
    and card["research_candidate"]["ok_to_submit_to_competition"] is False
    and card["validator"]["no_nan_inside_footprint"] is True
    and card["validator"]["values_in_0_1"] is True
    and card["validator"]["masked_inside_footprint"] == 0
    and card["uniqueness"]["unique_vs_all_9_focus_sites"] is True
    and card["uniqueness"]["minimum_overlap_bound"] == lat["minimum_overlap"]
    and card["registry"]["binary_lattice_minimum_overlap_at_budget"] == lat["minimum_overlap"]
    and lat["minimum_overlap"] == parallel["literal_registry_witness"]["minimum_possible_overlap_at_example_budget"]
    and dense["full_footprint_positive"] is True
    and parallel["dense_probability_witness"]["universal_overlap_blocker"] is True
    and card["registry"]["dense_probability_prior_full_footprint"] is True
    and review["ok_to_submit"] is False
    and corroboration["ok_to_submit"] is False
    and corroboration["candidate_sha256"] == review["sha256"]
    and corroboration["witnesses"]["lattice"]["overlap_fraction"] == review["literal_overlap_3px"]["lattice"]
    and corroboration["format"]["dataset_mask_invalid_inside_footprint"] == review["format"]["masked_inside"]
    and review["literal_overlap_3px"]["lattice"] > 0.7
    and review["format"]["format_valid_against_reference"] is False
    and card["parallel_session"]["rejected_candidate_sha256"] == review["sha256"]
    and card["parallel_session"]["lattice_overlap_3px"] == review["literal_overlap_3px"]["lattice"]
    and card["parallel_session"]["continuous_prior_overlap_3px"] == review["literal_overlap_3px"]["continuous_prior"]
    and card["parallel_session"]["masked_inside_footprint"] == review["format"]["masked_inside"]
    and card["parallel_session"]["source_reported_holdout"] == review["source_reported_holdout"]
    and card["parallel_session"]["ok_to_submit"] is False
    and conduit["ok_to_submit"] is False
    and conduit["holdout_dti"] is None
    and conduit["preplacement_surface_correlation"] is None
    and conduit["witnesses"]["13GEMSDOE"]["source_threshold_ge_0_5"]["fraction"] > 0.7
    and card["conduit_parallel_session"]["rejected_candidate_sha256"] == conduit["sha256"]
    and card["conduit_parallel_session"]["lattice_overlap_3px_source_threshold"] == conduit["witnesses"]["13GEMSDOE"]["source_threshold_ge_0_5"]["fraction"]
    and card["conduit_parallel_session"]["continuous_prior_overlap_3px"] == conduit["witnesses"]["17GEMSDOE_dense_prior"]["source_threshold_ge_0_5"]["fraction"]
    and card["conduit_parallel_session"]["holdout_dti"] is None
    and card["conduit_parallel_session"]["preplacement_surface_correlation"] is None
    and card["conduit_parallel_session"]["ok_to_submit"] is False
    and len(card["note"]) <= 140
):
    raise ValueError("Run-card evidence changed; manual review required before publication")

text = json.dumps(card, indent=2, allow_nan=False) + "\n"
for rel in ("docs/data/run-card.json", "docs/data/run_card.json", "site/data/run_card.json"):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print("Mirrored canonical card:", out)
