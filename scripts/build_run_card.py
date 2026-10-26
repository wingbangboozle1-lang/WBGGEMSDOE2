#!/usr/bin/env python3
"""Build one machine-readable negative run card from the checked-in evidence."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
portfolio = json.loads((ROOT / "docs/data/portfolio.json").read_text())
lat = portfolio["literal_registry_witness"]
dense = portfolio["dense_probability_witness"]
card = {
    "schema_version": 1,
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "hypothesis": "This review proposed multiscale gravity-magnetic gradient alignment residualized against detrended elevation; no lane was supplied and this review ran no model.",
    "mechanism": "Buried faulted contacts might produce coincident persistent gravity and magnetic edges even where surface expression is weak.",
    "named_non_fault_process": "Lithologic contacts or igneous dikes can produce aligned potential-field gradients; terrain-related survey artifacts can mimic structure.",
    "experiment_count": 0,
    "weekly_submission_slots_used": 0,
    "scope": "This review only; a separate parallel run generated and evaluated a candidate, independently audited below.",
    "holdout_dti": {"evidence_class": "HOLDOUT-DTI", "status": "NOT RUN", "evaluator_version": "gems57-pooled-hide-v2", "withheld_positives": None, "value": None, "ci95": None, "reason": "No assigned method and strict novelty preflight obstructed"},
    "single_feature_leakage_canaries": {"status": "NOT RUN", "reason": "No candidate or feature matrix evaluated"},
    "registry": {"evidence_class": "REGISTRY-MEASUREMENT", "surface_rank_correlation": None, "final_dot_overlap": None,
                 "scope": portfolio["audited_scope"], "all_current_registry_rasters_checked": False,
                 "binary_lattice_example_budget": lat["example_budget_distinct_dots"],
                 "binary_lattice_minimum_overlap_at_budget": lat["minimum_possible_overlap_at_example_budget"],
                 "dense_probability_prior_full_footprint": dense["universal_overlap_blocker"],
                 "interpretation": "Shared literal finite-positive definition makes the continuous prior a universal blocker; binary lattice bound holds at the stated budget only."},
    "raster_sha256": None,
    "validator_output": {"status": "NOT RUN FOR A CANDIDATE", "no_nan_inside_footprint": None, "range_0_1": None, "crs_shape_transform_match": None,
                         "historical_b2_format_receipt": "b2_local_format.json"},
    "submission_name": None,
    "submission_note": None,
    "ok_to_download_new_tif": False,
    "ok_to_submit": False,
    "verdict": "negative",
    "reason": "No candidate produced in this review; the separately generated parallel candidate fails the strict registry STOP. No assigned single method was supplied. Do not spend a slot.",
}
parallel_path = ROOT / "evidence/parallel_candidate_audit.json"
if parallel_path.is_file():
    parallel = json.loads(parallel_path.read_text())
    card["parallel_candidate"] = {
        "status": "DUPLICATE / STOP; research only",
        "raster_sha256": parallel["candidate_sha256"],
        "binary_lattice_overlap": parallel["witnesses"]["lattice"]["overlap_fraction"],
        "continuous_prior_overlap_literal": parallel["witnesses"]["dense_probability"]["overlap_fraction"],
        "preplacement_surface_checked": parallel["preplacement_surface_checked"],
        "evidence": "parallel_candidate_audit.json",
        "ok_to_submit": False,
    }
out = ROOT / "docs/data/run-card.json"
out.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
print(out)
