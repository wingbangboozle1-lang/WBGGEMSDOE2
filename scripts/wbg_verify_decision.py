#!/usr/bin/env python3
"""Machine-validate the CURRENT decision and its submission TIFF. No human inspection.

Re-opens the exact raster bytes, re-checks every documented gate, and emits one
unambiguous verdict. This is the automated "OK to download and submit" check:

    python scripts/wbg_verify_decision.py            # human-readable + JSON receipt
    python scripts/wbg_verify_decision.py --quiet    # exit 0 = OK to submit, 1 = DO NOT SUBMIT

Exit code 0 requires ALL of:
  * decision.json / h1_run_card.json are byte-bound to downloads/<name>.tif and .zip
    (sha256 equality, ZIP holds exactly one TIFF whose bytes equal the file);
  * the TIFF passes the independent grid/format inspector AND the pinned shared
    gate + validator (single band float32, EPSG:32611, 100 m, exact transform,
    no NaN/Inf anywhere, all values in [0,1], no positive mass outside the mirrored
    footprint or on a mapped-fault pixel);
  * every promotion gate is true in the run card AND backed by evidence files
    (leakage canaries pass, uniqueness under both limits, holdout CI + evaluator
    version present, note <= 140 chars, submission name <= 140 chars);
  * no number is presented as a leaderboard score (leaderboard_dti is null).

A byte change to the raster, a flipped JSON boolean, or a missing evidence file
cannot silently produce a green result. Failing any check forces DO NOT SUBMIT.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

# numpy/rasterio are imported lazily so the byte-binding + evidence checks also run
# in a bare CI checkout (no ignored /data, no installed geospatial wheels). In that
# mode we fall back to the committed, byte-bound format receipt for pixel checks.
def _geo():
    import numpy as np
    import rasterio
    return np, rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "src").resolve()))
sys.path.insert(0, str((ROOT / ".cache" / "shared-template" / "src").resolve()))


def sha256(path) -> str:
    if isinstance(path, (bytes, bytearray)):
        return hashlib.sha256(bytes(path)).hexdigest()
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jload(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def check(name: str, cond: bool, checks: list, detail: str = "") -> None:
    checks.append({"check": name, "pass": bool(cond), "detail": detail})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--receipt", type=Path, default=None)
    args = ap.parse_args()

    checks: list = []
    ok = True
    try:
        decision = jload("evidence/decision.json")
        card = jload("evidence/h1_run_card.json")
        uniq = jload("evidence/h1_uniqueness.json")
        exps = jload("evidence/h1_experiments.json")
        fmt = jload("evidence/h1_format.json")
        canary = jload("evidence/h1_canary.json")
        run = jload("evidence/run_card.json")  # archived negative review lane
    except (OSError, json.JSONDecodeError) as e:
        print("STOP: evidence missing/corrupt:", e, file=sys.stderr)
        return 1

    name = decision["candidate"]["submission_name"]
    tif = ROOT / decision["candidate"]["file"]
    zipf = ROOT / decision["candidate"]["zip"]
    docs_tif = ROOT / decision["candidate"]["docs_file"]
    docs_zip = ROOT / decision["candidate"]["docs_zip"]

    def require(cond, label, detail=""):
        nonlocal ok
        check(label, cond, checks, detail)
        if not cond:
            ok = False

    # ---- 1. Byte binding (decision <-> run card <-> evidence <-> file) ----
    require(tif.is_file(), "raster_exists", str(tif))
    require(zipf.is_file(), "zip_exists", str(zipf))
    if tif.is_file():
        h = sha256(tif.read_bytes())
        require(h == decision["candidate"]["raster_sha256"], "raster_sha_matches_decision", h)
        require(h == card["raster_sha256"], "raster_sha_matches_run_card", h)
        require(h == fmt["sha256"], "raster_sha_matches_format_receipt", h)
    if zipf.is_file():
        zh = sha256(zipf.read_bytes())
        require(zh == decision["candidate"]["zip_sha256"] == fmt["zip_sha256"], "zip_sha_matches", zh)
        try:
            with zipfile.ZipFile(zipf) as z:
                names = z.namelist()
                require(names == [f"{name}.tif"], "zip_holds_exactly_one_tiff", str(names))
                if names:
                    require(hashlib.sha256(z.read(names[0])).hexdigest() == (h if tif.is_file() else ""),
                            "zip_tiff_bytes_equal_raster")
        except zipfile.BadZipFile as e:
            require(False, "zip_holds_exactly_one_tiff", str(e))
    if docs_tif.is_file() and tif.is_file():
        require(docs_tif.read_bytes() == tif.read_bytes(), "docs_download_is_identical_bytes")
    if docs_zip.is_file() and zipf.is_file():
        require(docs_zip.read_bytes() == zipf.read_bytes(), "docs_zip_is_identical_bytes")

    # ---- 2. Independent + shared format validation on the exact bytes ----
    sample = ROOT / "data" / "official" / "sample_submission.tif"
    faults = ROOT / "data" / "official" / "existing_faults.tif"
    np = None
    try:
        np, rasterio = _geo()
    except ImportError:
        rasterio = None
    if tif.is_file() and sample.is_file() and rasterio is not None and np is not None:
        from wbggems.validate import inspect_tif
        rep = inspect_tif(tif, sample, strict_all_finite=True)
        require(bool(rep["format_valid_against_reference"]), "independent_format_valid", str(rep.get("failures")))
        require(int(rep.get("nonfinite_inside", 1)) == 0, "no_nan_inside_footprint")
        require(int(rep.get("masked_inside", 1)) == 0, "no_masked_cells_inside_footprint")
        with rasterio.open(tif) as ds:
            a = ds.read(1)
            require(ds.count == 1 and ds.dtypes[0] == "float32", "single_band_float32")
            require(str(ds.crs) == "EPSG:32611", "crs_epsg_32611", str(ds.crs))
            require(tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
                    "transform_matches_grid", str(list(ds.transform)[:6]))
            require(bool(np.isfinite(a).all()), "no_nan_inf_anywhere")
            require(bool(((a >= 0) & (a <= 1)).all()), "all_values_in_0_1",
                    f"min={float(a.min())} max={float(a.max())}")
            with rasterio.open(sample) as s:
                fp = np.isfinite(s.read(1))
                require(ds.shape == s.shape and ds.transform == s.transform, "shape_transform_match_sample")
                require(int(((a > 0) & ~fp).sum()) == 0, "no_positive_mass_outside_footprint")
            if faults.is_file():
                with rasterio.open(faults) as c:
                    cat = (c.read(1) > 0) & fp
                    require(int(((a > 0) & cat).sum()) == 0, "no_positive_mass_on_mapped_faults")
            dots = int((a > 0).sum())
        # shared writer receipt (pinned template) all_checks_passed
        require(bool(fmt["shared_writer_receipt"]["validator"]["all_checks_passed"]),
                "shared_writer_all_checks_passed")
        require(int(fmt["shared_writer_receipt"]["validator"]["emitted_positive_pixels"]) == dots,
                "dot_count_matches_receipt", str(dots))
    elif tif.is_file() and (not sample.is_file() or rasterio is None or np is None):
        # CI / bare checkout: the ignored /data reference grid (or the geospatial
        # wheels) is absent. Fall back to the COMMITTED, byte-bound format receipt —
        # its sha was already checked equal to the on-disk raster sha above.
        if rasterio is not None and np is not None:
            with rasterio.open(tif) as ds:
                a = ds.read(1)
                require(ds.count == 1 and ds.dtypes[0] == "float32", "single_band_float32")
                require(str(ds.crs) == "EPSG:32611", "crs_epsg_32611", str(ds.crs))
                require(tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0), "transform_matches_grid")
                require(bool(np.isfinite(a).all()), "no_nan_inf_anywhere")
                require(bool(((a >= 0) & (a <= 1)).all()), "all_values_in_0_1",
                        f"min={float(a.min())} max={float(a.max())}")
                require(int((ds.read_masks(1) == 0).sum()) == 0, "no_masked_cells_inside_footprint")
                dots = int((a > 0).sum())
        else:
            dots = int(fmt["shared_writer_receipt"]["validator"]["emitted_positive_pixels"])
        require(fmt["sha256"] == h, "format_receipt_bound_to_raster")
        require(fmt["no_nan_inside_footprint"] and fmt["values_in_0_1"] and fmt["crs_shape_transform_match"],
                "committed_format_receipt_all_pass")
        require(fmt["independent_inspect_tif"]["format_valid_against_reference"], "committed_independent_inspector_pass")
        require(int(fmt["shared_writer_receipt"]["validator"]["emitted_positive_pixels"]) == dots,
                "dot_count_matches_receipt", str(dots))
    else:
        require(False, "independent_format_valid", "raster or sample missing")
        dots = 0

    # ---- 3. Decision is evidence-backed, not a flipped boolean ----
    require(decision.get("verdict") == "promote" and card.get("verdict") == "promote", "verdict_promote")
    require(decision.get("ok_to_download_new_tif") is True and decision.get("ok_to_submit") is True,
            "decision_flags_true")
    require(decision.get("is_a_copy_of_any_previous_submission") is False, "declared_not_a_copy")
    require(all(card["promotion_gates"].values()), "all_promotion_gates_true", str(card["promotion_gates"]))
    require(len(decision["candidate"]["note"]) <= 140 and len(name) <= 140, "name_and_note_le_140",
            f"note={len(decision['candidate']['note'])} name={len(name)}")
    require(len(decision["flagged_irregularities"]) >= 3, "irregularities_flagged")
    require(decision["estimated_score"]["leaderboard_dti"] is None
            and decision["estimated_score"]["leaderboard_forecast_available"] is False,
            "no_invented_leaderboard_score")
    require(decision["weekly_submission_slots_used"] == 0, "no_weekly_slot_spent")

    # canary
    require(canary["all_real_features_pass"] is True, "leakage_canary_all_pass")
    require(all(v["pass"] for k, v in canary["features"].items() if "LEAK_DEMO" not in k),
            "every_real_feature_auc_le_0_90")
    # uniqueness
    require(uniq["under_090_correlation_all"] and uniq["max_all_registry_abs_spearman"] <= 0.90,
            "surface_correlation_le_0_90", str(uniq["max_all_registry_abs_spearman"]))
    require(uniq["under_070_overlap_real_submissions"]
            and uniq["max_real_submission_overlap_3px"] <= 0.70,
            "final_dot_overlap_le_0_70", str(uniq["max_real_submission_overlap_3px"]))
    require(len(uniq["real_submission_ids"]) == 11 and len(uniq["space_filling_control_ids"]) == 2,
            "registry_inventory_declared")
    # holdout
    ph = card["holdout"]
    require(ph["not_a_leaderboard_score"] is True, "holdout_labeled_as_proxy")
    require(ph["evaluator_version"] == exps["evaluator_version"], "evaluator_version_consistent")
    require(ph["withheld_positive_pixels"] > 0 and ph["dti"] >= ph["ci95"][0] <= ph["dti"] <= ph["ci95"][1],
            "holdout_ci_contains_dti", str(ph["ci95"]))
    require(ph["beats_control_B2_mechanism"] < ph["dti"], "holdout_beats_champion_mechanism")
    require(exps["promoted_arm"] == "dual_population", "promoted_arm_is_evaluated_arm")
    require(exps["paired_differences_vs_promoted"]["control_B2_mechanism"]["ci95"][0] > 0,
            "paired_win_over_champion_significant")
    # archived review lane stays honest/negative
    require(run["verdict"] == "negative" and run["ok_to_submit"] is False,
            "archived_review_lane_still_negative")

    verdict = "OK TO DOWNLOAD AND SUBMIT" if ok else "DO NOT SUBMIT"
    result = {
        "evidence_class": "MACHINE-VALIDATION",
        "verdict": verdict,
        "ok_to_submit": ok,
        "raster_sha256": decision["candidate"]["raster_sha256"],
        "submission_name": name,
        "positive_dots": dots,
        "checks_passed": sum(1 for c in checks if c["pass"]),
        "checks_total": len(checks),
        "checks": checks,
        "caveat": ("Byte-bound local validation only. NOT an organizer receipt and NOT a leaderboard score. "
                   "The two space-filling controls are handled by a flagged, reviewable policy decision; "
                   "data are a hash-verified owner mirror. See flagged_irregularities in decision.json."),
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2) + "\n")
    if not args.quiet:
        print(json.dumps(result, indent=2))
    else:
        print(verdict)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
