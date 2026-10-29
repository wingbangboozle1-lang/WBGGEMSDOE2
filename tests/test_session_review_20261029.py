import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_is_negative_and_never_claims_a_missing_raster():
    card = json.loads((ROOT / "evidence/session_run_card_20261029.json").read_text())
    assert card["verdict"] == "negative"
    assert card["experiments_run"] == 0
    assert card["weekly_slots_used"] == 0
    assert card["holdout_dti"] is None
    assert card["holdout_ci_95"] is None
    assert card["withheld_positives"] is None
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["submission_note"] is None
    assert card["validator_output"]["raster_exists"] is False
    assert card["validator_output"]["status"].startswith("NOT RUN")


def test_review_page_is_explicitly_negative_and_has_no_downloadable_tif():
    page = (ROOT / "docs/session-review-20261029.html").read_text()
    assert "NEGATIVE — DO NOT SUBMIT" in page
    assert "No new TIFF was generated" in page
    assert 'button disabled aria-disabled="true"' in page
    assert not re.search(r'href=["\'][^"\']+\.tif(?:["\']|\?)', page, re.I)
    assert "Current review" in (ROOT / "docs/index.html").read_text()


def test_leaderboard_capture_is_dated_public_observation_not_project_receipt():
    snapshot = json.loads((ROOT / "docs/data/leaderboard.json").read_text())
    assert snapshot["status"] == "fresh"
    assert snapshot["top_public_dti"] == 0.4544
    assert snapshot["top_participant"] == "xiaofanhu"
    assert "PUBLIC-LEADERBOARD" in snapshot["evidence_class"]
    assert "not a receipt" in snapshot["note"].lower()


def test_shortlist_remains_proposal_only_and_lane_is_unassigned():
    research = json.loads((ROOT / "config/research_hypotheses.json").read_text())
    assert research["method_lane"]["status"] == "UNASSIGNED"
    assert 3 <= len(research["hypotheses"]) <= 5
    for hypothesis in research["hypotheses"]:
        for key in ("layers", "signature", "why_uncatalogued", "difference_from_reviewed_methods", "non_fault_mimic", "implementation_cost"):
            assert hypothesis.get(key)
