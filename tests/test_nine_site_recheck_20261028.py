"""Regression checks for the 2026-10-28 nine-site executive summary.

These guard the facts the summary depends on: file hashes, the validator
outcome for the two triphysics variants, and the README verdict. The validator
checks need the owner-mirror grid template in data/official (run
`python scripts/prepare_data.py --fetch`); they skip cleanly otherwise.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

ZERO = "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2-zerooutside.tif"
NAN = "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif"
ZERO_SHA = "c8f41c0490f84a26d86073df12fea351464a12e8934a55ca538da5af9253813c"
NAN_SHA = "b14766fedf4953b79a8315adb3c82b6c8a8a3eab4b9132e61e902b261dc4f2fe"
D2 = "docs/downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif"
D2_SHA = "0ebf5e2d717361af83f507bb2f64ba7bc9d7266de73907e4c4769574d0a56b10"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_download_copy_matches_submission_bytes():
    assert _sha(ROOT / ZERO) == ZERO_SHA
    assert _sha(ROOT / "docs/downloads/gemsdoe" / Path(ZERO).name) == ZERO_SHA
    assert _sha(ROOT / NAN) == NAN_SHA


def test_download_pick_distal2_bytes_and_uniqueness():
    assert _sha(ROOT / D2) == D2_SHA
    report = json.loads((ROOT / "evidence/nine_site_recheck_20261028.json").read_text())
    rows = {c["file"]: c for c in report["candidates"]}
    d2 = next(v for k, v in rows.items() if k.endswith("062373ad-zeros.tif"))
    assert d2["validator_ok"] is True
    assert d2["passes_vs_nine_sites"] is True
    run_card = json.loads((ROOT / "evidence/run_card_nine_site_20261028.json").read_text())
    assert run_card["download_for_record_only"]["sha256"] == D2_SHA


def test_recheck_evidence_records_current_hashes():
    report = json.loads((ROOT / "evidence/nine_site_recheck_20261028.json").read_text())
    by_file = {c["file"]: c for c in report["candidates"]}
    assert by_file[ZERO]["sha256"] == ZERO_SHA
    assert by_file[ZERO]["validator_ok"] is True
    assert by_file[NAN]["sha256"] == NAN_SHA
    assert by_file[NAN]["validator_ok"] is False
    for site, meta in report["sites"].items():
        assert len(meta["sha256"]) == 64, site
    assert report["site_pairwise_min_off_diagonal"] > 0.85


def test_nine_site_uniqueness_claims_pass_for_zero_variant():
    report = json.loads((ROOT / "evidence/nine_site_recheck_20261028.json").read_text())
    zero = next(c for c in report["candidates"] if c["file"] == ZERO)
    assert zero["max_frac_my_dots_within_3px"] <= 0.70
    assert abs(zero["max_abs_smoothed_spearman"]) <= 0.90
    assert zero["passes_vs_nine_sites"] is True


@pytest.mark.parametrize("rel,expect_ok", [(ZERO, True), (NAN, False)])
def test_validator_outcome_matches_summary(rel, expect_ok):
    sample = ROOT / "data/official/sample_submission.tif"
    if not sample.is_file():
        pytest.skip("grid template not fetched (run scripts/prepare_data.py --fetch)")
    from validate_submission import run
    report = run(ROOT / rel, sample)
    assert bool(report["ok"]) is expect_ok


def test_readme_start_here_is_do_not_submit_and_points_to_nine_site_evidence():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    head = text[: text.index("## Original project prompt")]
    assert "DO NOT SUBMIT" in head
    assert "EXECUTIVE_SUMMARY_NINE_SITES_20261028.md" in head
    assert "no new submission file to download" in head.lower()
    assert "cleared to submit" not in head.lower()
    assert "session_run_card_20261029.json" in head
