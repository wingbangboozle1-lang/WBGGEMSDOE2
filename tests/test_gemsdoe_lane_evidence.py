"""The focus-site publisher is fail-closed: old release artifacts are not approvals."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def test_historical_release_records_are_not_selector_authorization():
    sys.path.insert(0, str(ROOT / "src"))
    from wbggems.release import approved_candidates, registered_release_assets

    assets = registered_release_assets(ROOT)
    assert assets, "historical hash-bound records should remain auditable"
    assert approved_candidates(ROOT) == {}, "no selector receipt exists in this checkout"
    register = read_json("config/release_register.json")
    assert register["candidates"]
    assert all(c.get("selector_authorized") is False and c.get("selector_receipt") is None
               for c in register["candidates"])
    # Two-tier policy: historical entries stay research-only, and the single
    # research-grade entry must be hash-bound to an all-pass run card.
    decisions = {c["decision"] for c in register["candidates"]}
    assert decisions <= {"RESEARCH_ONLY_DO_NOT_SUBMIT", "OK_TO_DOWNLOAD_AND_SUBMIT_RESEARCH_GRADE"}
    ready = [c for c in register["candidates"] if c["decision"] == "OK_TO_DOWNLOAD_AND_SUBMIT_RESEARCH_GRADE"]
    assert len(ready) <= 1, "one research-grade file at a time"
    for c in ready:
        assert c["selector_authorized"] is False and c["selector_receipt"] is None
        card = read_json(c["run_card"])
        assert card["verdict"] == "OK_TO_DOWNLOAD_AND_SUBMIT"
        assert card["raster"]["sha256"] == c["sha256"]
        assert card["validator"]["all_passed"] is True
        assert card["uniqueness"]["max_frac_my_dots_within_3px"] <= 0.70


def test_nine_focus_site_measurements_are_scoped_and_no_estimate_is_claimed():
    overlap = read_json("data_public/site_best_overlap.json")
    rows = overlap["rows"]
    required = {f"GEMSDOE{s}" for s in ("24", "25", "27", "28", "30", "31", "32", "33", "36")}
    assert {r["site"] for r in rows} == required
    for row in rows:
        frac = row["frac_dots_within_3px_of_closest"]
        assert 0.90 < frac <= 1.0
    summary = (ROOT / "docs/executive-summary.md").read_text()
    assert "0.2778 USER-REPORTED" in summary
    assert "New-score estimates are unavailable" in summary
    assert "DO NOT SUBMIT" in summary


def test_focus_site_pages_show_negative_status_without_download_controls():
    for name in ("index.html", "how-to-submit.html", "findings.html", "sources.html"):
        text = (ROOT / "docs/lane" / name).read_text().lower()
        assert "no file approved" in text
        assert "do not submit" in text
        assert "download .tif" not in text
        assert "submit this file" not in text


def test_lane_manifest_is_negative_and_has_no_candidate_path():
    manifest = read_json("data_public/gemsdoe_release.json")
    assert manifest["status"] == "blocked_do_not_submit"
    assert manifest["primary_file"] is None
    assert manifest["estimated_leaderboard_score"] is None
    assert manifest["organizer_receipt"] is None
    assert manifest["ok_to_download_and_submit"] is False


def test_existing_lane_tiff_hashes_still_match_register_but_are_research_only():
    register = read_json("config/release_register.json")
    for rec in register["candidates"]:
        path = ROOT / rec["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec["sha256"]
        assert rec["selector_authorized"] is False
