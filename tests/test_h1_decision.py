"""Lock in the byte-bound, machine-validated H1 decision. No human inspection needed.

These tests guarantee that the "OK TO DOWNLOAD AND SUBMIT" decision cannot be
silently produced by a flipped boolean, a swapped raster, or an invented score.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text())


@pytest.fixture(scope="module")
def decision():
    return load("evidence/decision.json")


@pytest.fixture(scope="module")
def card():
    return load("evidence/h1_run_card.json")


def test_decision_is_the_current_promote_and_byte_bound(decision, card):
    assert decision["decision_label"] == "OK TO DOWNLOAD AND SUBMIT"
    assert decision["verdict"] == "promote"
    assert decision["ok_to_download_new_tif"] is True and decision["ok_to_submit"] is True
    assert decision["is_a_copy_of_any_previous_submission"] is False
    tif = ROOT / decision["candidate"]["file"]
    h = hashlib.sha256(tif.read_bytes()).hexdigest()
    assert h == decision["candidate"]["raster_sha256"] == card["raster_sha256"]
    assert decision["candidate"]["file"].endswith(".tif")
    # byte-identical copies published for the Pages site
    docs = ROOT / decision["candidate"]["docs_file"]
    assert docs.read_bytes() == tif.read_bytes()
    zipf = ROOT / decision["candidate"]["zip"]
    with zipfile.ZipFile(zipf) as z:
        assert z.namelist() == [Path(decision["candidate"]["file"]).name]
        assert hashlib.sha256(z.read(z.namelist()[0])).hexdigest() == h
    assert hashlib.sha256(zipf.read_bytes()).hexdigest() == decision["candidate"]["zip_sha256"]


def test_decision_mirrors_are_identical():
    d = (ROOT / "evidence/decision.json").read_bytes()
    for rel in ("docs/data/decision.json", "site/data/decision.json"):
        assert (ROOT / rel).read_bytes() == d
    c = (ROOT / "evidence/h1_run_card.json").read_bytes()
    for rel in ("docs/data/h1_run_card.json", "site/data/h1_run_card.json"):
        assert (ROOT / rel).read_bytes() == c


def test_raster_format_fixes_the_0_1_error(decision):
    tif = ROOT / decision["candidate"]["file"]
    with rasterio.open(tif) as ds:
        assert ds.count == 1 and ds.dtypes[0] == "float32"
        assert str(ds.crs) == "EPSG:32611"
        assert ds.shape == (3730, 3292)
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None  # no NoData=0 mask inside the footprint
        a = ds.read(1)
        assert np.isfinite(a).all()                 # no NaN/Inf anywhere
        assert bool(((a >= 0) & (a <= 1)).all())   # all values in [0,1]
        assert (ds.read_masks(1) == 0).sum() == 0  # no masked-in-footprint cells
        with rasterio.open(ROOT / "data/official/sample_submission.tif") as s:
            fp = np.isfinite(s.read(1))
            assert int(((a > 0) & ~fp).sum()) == 0
            with rasterio.open(ROOT / "data/official/existing_faults.tif") as c:
                cat = (c.read(1) > 0) & fp
                assert int(((a > 0) & cat).sum()) == 0
        dots = int((a > 0).sum())
    assert dots > 1000


def test_all_promotion_gates_true_and_backed_by_evidence(decision, card):
    assert all(card["promotion_gates"].values()), card["promotion_gates"]
    assert all(decision["promotion_gates"].values())
    uni = load("evidence/h1_uniqueness.json")
    can = load("evidence/h1_canary.json")
    exp = load("evidence/h1_experiments.json")
    fmt = load("evidence/h1_format.json")
    assert can["all_real_features_pass"] is True
    assert all(v["pass"] for k, v in can["features"].items() if "LEAK_DEMO" not in k)
    assert can["features"]["halo_from_FULL_catalogue_LEAK_DEMO"]["pass"] is False  # leakage is caught
    assert uni["under_090_correlation_all"] and uni["max_all_registry_abs_spearman"] <= 0.90
    assert uni["under_070_overlap_real_submissions"] and uni["max_real_submission_overlap_3px"] <= 0.70
    assert exp["promoted_arm"] == "dual_population"
    assert exp["paired_differences_vs_promoted"]["control_B2_mechanism"]["ci95"][0] > 0
    assert fmt["no_nan_inside_footprint"] and fmt["values_in_0_1"] and fmt["crs_shape_transform_match"]
    assert fmt["shared_writer_receipt"]["validator"]["all_checks_passed"]


def test_no_invented_leaderboard_score_and_caveats_present(decision, card):
    est = decision["estimated_score"]
    assert est["leaderboard_dti"] is None and est["leaderboard_forecast_available"] is False
    hp = est["holdout_proxy"]
    assert hp["evidence_class"] == "HOLDOUT-DTI" and hp["evaluator_version"]
    assert hp["withheld_positive_pixels"] > 0 and len(hp["ci95"]) == 2
    assert hp["ci95"][0] <= hp["dti"] <= hp["ci95"][1]
    assert card["holdout"]["not_a_leaderboard_score"] is True
    assert decision["weekly_submission_slots_used"] == 0
    assert len(decision["flagged_irregularities"]) >= 3
    assert len(decision["candidate"]["note"]) <= 140 and len(decision["candidate"]["submission_name"]) <= 140
    assert len(card["note"]) == card["note_chars"] <= 140


def test_archived_negative_review_lane_stays_synced():
    src = (ROOT / "evidence/run_card.json").read_bytes()
    assert json.loads(src)["verdict"] == "negative"
    for rel in ("docs/data/run-card.json", "docs/data/run_card.json", "site/data/run_card.json"):
        assert (ROOT / rel).read_bytes() == src


def test_verifier_script_returns_ok(tmp_path):
    r = subprocess.run([sys.executable, "scripts/wbg_verify_decision.py", "--quiet"],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    assert r.returncode == 0 and "OK TO DOWNLOAD AND SUBMIT" in (r.stdout + r.stderr)


def test_verifier_detects_a_tampered_raster(decision, tmp_path):
    """A copied, byte-changed raster must force DO NOT SUBMIT."""
    import shutil
    stage = tmp_path / "repo"
    stage.mkdir()
    for d in ("scripts", "src", "evidence", "docs/data", "docs/downloads", "data/official", "downloads"):
        (stage / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "scripts/wbg_verify_decision.py", stage / "scripts/wbg_verify_decision.py")
    for f in (ROOT / "evidence").glob("*.json"):
        shutil.copy(f, stage / "evidence" / f.name)
    for f in (ROOT / "data/official").glob("*"):
        shutil.copy(f, stage / "data/official" / f.name)
    shutil.copytree(ROOT / "src" / "wbggems", stage / "src" / "wbggems")
    name = decision["candidate"]["submission_name"]
    # write a valid-grid but byte-different raster
    with rasterio.open(ROOT / decision["candidate"]["file"]) as ds:
        a = ds.read(1).copy()
        profile = ds.profile
    ys, xs = np.nonzero(a > 0)
    a[ys[0], xs[0]] = 0.5  # change one value -> different sha
    for base in (stage / "downloads", stage / "docs/downloads"):
        with rasterio.open(base / (name + ".tif"), "w", **profile) as dst:
            dst.write(a, 1)
    shutil.copy(ROOT / decision["candidate"]["zip"], stage / "downloads" / (name + ".zip"))
    # run verifier in the staged repo
    r = subprocess.run([sys.executable, "scripts/wbg_verify_decision.py", "--quiet"],
                       capture_output=True, text=True, cwd=str(stage), timeout=120)
    assert r.returncode != 0 and "DO NOT SUBMIT" in (r.stdout + r.stderr)
