#!/usr/bin/env python3
"""Populate evidence/RUN_CARD_MSPTCD.json from verified WBG2-MSPTCD and registry audit receipts."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    msptcd = json.loads((ROOT / "evidence/wbg2_msptcd_results.json").read_text(encoding="utf-8"))
    cross = json.loads((ROOT / "evidence/wbg2_msptcd_cross_lane_audit.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "evidence/registry_audit.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "evidence/parallel_review.json").read_text(encoding="utf-8"))
    conduit = json.loads((ROOT / "evidence/conduit_review.json").read_text(encoding="utf-8"))

    lat = audit["lattice_capacity"]
    best_arm = msptcd["winning_experiment"]
    best_sc = msptcd["holdout_pooled"]["scores"][best_arm]
    ctrl_sc = msptcd["holdout_pooled"]["scores"]["ctrl_19b"]
    exp1_sc = msptcd["holdout_pooled"]["scores"]["exp1_msptcd_core"]
    exp2_sc = msptcd["holdout_pooled"]["scores"]["exp2_msptcd_strain_pu"]
    delta_ctrl = msptcd["paired_vs_ctrl_19b"][best_arm]
    delta_exp1 = msptcd["paired_vs_ctrl_19b"]["exp1_msptcd_core"]

    note = (
        "Negative/DO NOT SUBMIT: WBG2-MSPTCD HOLDOUT-DTI 0.0426 (+81.8% vs 19B), "
        "unique vs 9 focus, stopped by literal 13GEMSDOE/17GEMSDOE >70% gate."
    )
    assert len(note) <= 140

    card = {
        "schema": "wbggems.run-card.v2",
        "generated_utc": msptcd["generated_utc"],
        "updated_utc": cross["generated_utc"],
        "lane_id": "wbg2-msptcd",
        "hypothesis": (
            "WBG2-MSPTCD: Depth-invariant potential-field tilt horizontal gradients "
            "(Miller & Singh 1994), dip-shifted gravity-magnetic concordance across "
            "depth_to_base_surf steps, cross-strike cond_surf flank asymmetry, "
            "terrain-normalized radiometric tc edges, and multi-scale Hessian scarp "
            "ridges decoded via greedy 300 m triangular-kernel submodular allocation."
        ),
        "mechanism": (
            "Normal/transtensional faulting juxtaposes dense/magnetic footwall rock "
            "against basin fill while localizing clay/saline fluid alteration and "
            "degraded piedmont scarps along concealed fault projections."
        ),
        "non_fault_mimic": (
            "Unfaulted pluton/dike contacts, playal clay/evaporite pans, shoreline "
            "risers, and variable airborne survey clearance."
        ),
        "lane_status": (
            "Executed 3 preregistered zero-leakage experiments (EXP-1, EXP-2, EXP-3 vs "
            "CTRL-19B) on unmodified gems57-pooled-hide-v2; stopped at literal all-registry gate."
        ),
        "experiment_budget": {
            "experiments_run": msptcd["budget_compliance"]["experiments_run"],
            "maximum_experiments": 3,
            "runtime_seconds": round(msptcd["runtime_seconds"], 2),
            "maximum_hours": 2,
            "weekly_slots_used": 0,
            "scope": "wbg2-msptcd single method lane; preserves sibling DZ-16 and H3-PACK lanes intact",
        },
        "holdout": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": msptcd["holdout_pooled"]["evaluator_version"],
            "split_version": "label-blind-quadrants-v2 (buffer_px=80, 8.0 km buffer)",
            "withheld_positive_pixels": best_sc["withheld_positive_pixels"],
            "winning_arm": best_arm,
            "dti": best_sc["dti"],
            "ci95": best_sc["ci95"],
            "control_19b_dti": ctrl_sc["dti"],
            "control_19b_ci95": ctrl_sc["ci95"],
            "exp1_msptcd_core_dti": exp1_sc["dti"],
            "exp1_msptcd_core_ci95": exp1_sc["ci95"],
            "exp1_paired_delta_vs_ctrl": delta_exp1["delta"],
            "exp1_paired_delta_ci95": delta_exp1["ci95"],
            "exp2_msptcd_strain_pu_dti": exp2_sc["dti"],
            "exp2_msptcd_strain_pu_ci95": exp2_sc["ci95"],
            "paired_delta_vs_ctrl_19b": delta_ctrl["delta"],
            "paired_delta_ci95": delta_ctrl["ci95"],
            "detached_splay_dti": msptcd["detached_splay_diagnostic"][best_arm]["detached"]["pooled_dti"],
            "control_detached_splay_dti": msptcd["detached_splay_diagnostic"]["ctrl_19b"]["detached"]["pooled_dti"],
            "status": "completed on unmodified gems57.evaluate_holdout (1,000 paired 20 km spatial-cluster draws)",
        },
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "COMPLETED",
            "evaluator_version": msptcd["holdout_pooled"]["evaluator_version"],
            "withheld_positives": best_sc["withheld_positive_pixels"],
            "value": best_sc["dti"],
            "ci95": best_sc["ci95"],
            "control_19b_value": ctrl_sc["dti"],
            "paired_delta_vs_control": delta_ctrl["delta"],
            "paired_delta_ci95": delta_ctrl["ci95"],
        },
        "organizer_confirmed": {
            "evidence_class": "ORGANIZER-CONFIRMED",
            "value": None,
            "receipt": None,
            "status": "not submitted; weekly competition slots preserved",
        },
        "feature_canary": {
            "evidence_class": "LEAKAGE-CANARY-MEASUREMENT",
            "status": "passed",
            "features_tested": msptcd["canary_summary"]["features_tested"],
            "folds_tested": msptcd["canary_summary"]["folds_tested"],
            "total_checks": msptcd["canary_summary"]["features_tested"] * msptcd["canary_summary"]["folds_tested"],
            "threshold_two_sided_auc": 0.90,
            "max_two_sided_auc": msptcd["canary_summary"]["max_two_sided_auc"],
            "max_two_sided_feature": msptcd["canary_summary"]["max_two_sided_feature"],
            "details_file": msptcd["canary_summary"]["details_file"],
        },
        "uniqueness": {
            "registry_scope": "23 verified rasters (9 focus champions, 2 sibling WBGGEMSDOE2 lanes DZ-16 & H3-PACK, 13GEMSDOE lattice, 17GEMSDOE prior, 2 historic H31/H47 witnesses, 6 2026-10-26/27 sibling rasters, 2 local rejected parallel rasters)",
            "unique_vs_all_9_focus_sites": msptcd["registry_comparison"]["unique_vs_all_9_focus_sites"],
            "unique_vs_sibling_wbggemsdoe2_lanes": True,
            "sibling_lane_comparisons": cross["comparisons_against_sibling_lanes"],
            "candidate_max_focus_surface_correlation": msptcd["registry_comparison"]["max_focus_abs_surface_spearman"],
            "candidate_max_focus_final_overlap": msptcd["registry_comparison"]["max_focus_forward_overlap_3px"],
            "candidate_max_focus_site": msptcd["registry_comparison"]["max_focus_overlap_site"],
            "candidate_max_all_registry_surface_correlation": max(
                abs(r["surface_spearman_rho"]) for r in msptcd["registry_comparison"]["rows"]
            ),
            "candidate_max_all_registry_final_overlap": max(
                r["forward_overlap_3px"] for r in msptcd["registry_comparison"]["rows"]
            ),
            "status": "unique vs all 9 focus champions (<=68.06% 3px overlap) and both sibling lanes (27.36% vs DZ-16, 20.59% vs H3-PACK), but stopped by literal all-registry witnesses (>70%)",
            "witnesses_exceeding_limit": msptcd["registry_comparison"]["blanket_witnesses_triggered"],
            "witness": "13GEMSDOE stride-5 lattice",
            "standard_budget": lat["budget"],
            "minimum_overlap_bound": lat["minimum_overlap"],
            "limit": 0.7,
            "observed_other_site_H31_overlap": audit["items"]["GEMSDOE27_H31"]["fraction_within_3px_of_lattice"],
            "dense_prior_witness": "17GEMSDOE continuous probability prior",
            "dense_prior_full_footprint_positive": True,
        },
        "raster_sha256": None,
        "research_candidate": {
            "name": msptcd["artifact"]["stem"],
            "tif_path": msptcd["artifact"]["tif_path"],
            "zip_path": msptcd["artifact"]["zip_path"],
            "receipt_path": msptcd["artifact"]["receipt_path"],
            "tif_sha256": msptcd["artifact"]["tif_sha256"],
            "tif_bytes": msptcd["artifact"]["tif_bytes"],
            "zip_sha256": msptcd["artifact"]["zip_sha256"],
            "zip_bytes": msptcd["artifact"]["zip_bytes"],
            "emitted_dots": msptcd["artifact"]["dots"],
            "ok_to_download_for_research": True,
            "ok_to_submit_to_competition": False,
        },
        "validator": {
            "status": "passed local byte-level GeoTIFF & mask validation on research candidate",
            "no_nan_inside_footprint": msptcd["artifact"]["validator"]["no_nan_inside_footprint"],
            "values_in_0_1": msptcd["artifact"]["validator"]["inside_values_in_0_1"],
            "crs_shape_transform_match": msptcd["artifact"]["inspect_tif"]["grid_match_reference"],
            "masked_inside_footprint": msptcd["artifact"]["validator"]["masked_inside_footprint"],
            "dtype": msptcd["artifact"]["validator"]["dtype"],
            "crs": msptcd["artifact"]["validator"]["crs"],
            "shape": msptcd["artifact"]["inspect_tif"]["shape"],
        },
        "submission_name": None,
        "submission_note": None,
        "proposed_research_name": msptcd["artifact"]["stem"],
        "note": note,
        "ok_to_submit": False,
        "ok_to_download_new_tif": False,
        "ok_to_download_research_tif": True,
        "verdict": "negative",
        "experiment_count": msptcd["budget_compliance"]["experiments_run"],
        "weekly_submission_slots_used": 0,
        "parallel_session": {
            "evidence": "evidence/parallel_review.json",
            "rejected_candidate_sha256": review["sha256"],
            "user_reported_public_dti": 0.0725,
            "ok_to_submit": False,
        },
        "conduit_parallel_session": {
            "evidence": "evidence/conduit_review.json",
            "rejected_candidate_sha256": conduit["sha256"],
            "ok_to_submit": False,
        },
    }

    for dst in (ROOT / "evidence/RUN_CARD_MSPTCD.json", ROOT / "docs/data/RUN_CARD_MSPTCD.json"):
        dst.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for extra in ("wbg2_msptcd_results.json", "wbg2_msptcd_canaries.json", "wbg2_msptcd_cross_lane_audit.json"):
        shutil.copyfile(ROOT / "evidence" / extra, ROOT / "docs/data" / extra)
        shutil.copyfile(ROOT / "evidence" / extra, ROOT / "site/data" / extra)
    print("Wrote evidence/RUN_CARD_MSPTCD.json and mirrored WBG2-MSPTCD receipts into docs/data/ and site/data/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
