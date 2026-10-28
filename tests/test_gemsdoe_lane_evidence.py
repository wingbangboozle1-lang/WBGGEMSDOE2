"""Pin the submission lane: bytes, geometry, novelty verdicts and the score model.

These tests exist so that the number published on the site cannot drift away from the
bytes in ``submissions/`` or from the arithmetic in ``data_public/gemsdoe_metric_model.json``.
They never touch the competition data, so they run in any checkout.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "data_public"
NAME = "gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2"


def read(name: str) -> dict:
    return json.loads((PUB / name).read_text())


def test_lane_primary_file_is_byte_and_grid_identical_to_its_receipt():
    m = read("candidate_measurements.json")
    tif = ROOT / "submissions" / f"{NAME}.tif"
    assert tif.stat().st_size == m["bytes"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == m["sha256"]
    with rasterio.open(tif) as d:
        a = d.read(1)
        assert (d.height, d.width, d.count) == (3730, 3292, 1)
        assert d.dtypes == ("float32",)
        assert str(d.crs) == "EPSG:32611"
        assert (d.transform.a, d.transform.c, d.transform.f) == (100.0, 243350.0, 4508550.0)
    assert int(np.nansum(a > 0)) == m["cells"] == 38000
    finite = np.isfinite(a)
    assert float(np.nanmin(a[finite])) >= 0.0 and float(np.nanmax(a[finite])) <= 1.0
    assert np.isnan(a).sum() > 0


def test_candidate_is_registered_with_pinned_bytes():
    """The release register is the only gate that may offer a real submission."""
    sys.path.insert(0, str(ROOT / "src"))
    from wbggems.release import approved_candidates

    approved = approved_candidates(ROOT)
    primary = read("gemsdoe_release.json")["primary_file"]
    assert primary in approved, f"{primary} is not registered"
    assert approved[primary]["sha256"] == read("candidate_measurements.json")["sha256"]
    for rel in (f"docs/downloads/gemsdoe/{NAME}.tif",
                f"docs/downloads/gemsdoe/{NAME}-zerooutside.tif"):
        assert rel in approved and approved[rel]["lane"] == "GEMSDOE", rel


def test_novelty_verdicts_are_true_and_are_the_ones_quoted_on_the_site():
    verdict = read("gemsdoe_release.json")["novelty"]
    assert verdict["unique_bytes"] is True
    assert verdict["passes_halo_rule"] is True
    assert verdict["passes_rank_rule"] is True
    assert verdict["max_frac_my_dots_within_3px"] <= 0.70
    assert abs(verdict["max_abs_smoothed_spearman"]) <= 0.90
    page = (ROOT / "docs" / "lane" / "index.html").read_text()
    assert "PASS" in page and "70 %" in page


def test_metric_model_reproduces_the_two_reported_scores():
    m = read("gemsdoe_metric_model.json")
    n = m["n_truth_pixels_solved"]
    t = m["implied_T_at_B2"]
    for score, mass in ((0.2778, 37_654), (0.2600, 44_090)):
        got = t / (t + 0.2 * mass + 0.8 * (n - t))
        assert abs(got - score) < 2e-4, (score, got)
    assert 10_000 < n < 16_000
    assert 0.35 < m["implied_coverage_at_B2"] < 0.45
    # the exchange rate at the plateau, as published in the findings and summary
    assert abs(m["exchange_rate_at_02778"]["one_unit_of_TP_justifies_FP_units"] - 17.0) < 0.05


def test_candidate_score_curve_matches_the_published_estimate_band():
    m = read("candidate_measurements.json")["structural_score_curve"]
    curve = m["by_coverage"]
    assert 0.09 < curve["0.150"] < 0.12
    assert 0.26 < curve["0.409"] < 0.29
    summary = (ROOT / "research" / "gemsdoe_executive_summary.md").read_text()
    assert "212,133" in summary and "12,783" in summary
    assert "0.15 – 0.28" in summary


def test_nine_site_table_is_measured_and_admits_no_unique_site():
    rows = read("site_best_overlap.json")["rows"]
    assert len(rows) == 9
    assert {r["site"] for r in rows} == {f"GEMSDOE{s}" for s in
                                         ("24", "25", "27", "28", "30", "31", "32", "33", "36")}
    for r in rows:
        assert 0.0 <= r["frac_dots_within_3px_of_closest"] <= 1.0
        assert r["frac_dots_within_3px_of_closest"] > 0.90, r["site"]


@pytest.mark.parametrize("page", ["index.html", "how-to-submit.html", "findings.html", "sources.html"])
def test_lane_pages_labelled_as_estimate(page):
    text = (ROOT / "docs" / "lane" / page).read_text().lower()
    assert "empirical-band estimate" in text
    assert "no organizer receipt" in text
    assert "0.15 – 0.28" in text or "0.20 – 0.30" not in text
