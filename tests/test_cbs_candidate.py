"""Byte-bound guards for the CBS/D19-DOTTED candidate and its run card."""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence/RUN_CARD_CBS.json").read_text())
TIF = ROOT / CARD["candidate"]["file"]

def test_candidate_bytes_match_run_card():
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == CARD["candidate"]["sha256"]

def test_candidate_portal_range_and_grid():
    with rasterio.open(TIF) as ds:
        a = ds.read(1)
        assert ds.count == 1 and ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611 and ds.shape == (3730, 3292)
        assert tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
    # Portal rule: every value finite and in [0,1], no NaN anywhere.
    assert np.isfinite(a).all() and a.min() >= 0.0 and a.max() <= 1.0
    assert int((a == 1).sum()) == CARD["candidate"]["dots"] == 38000
    assert set(np.unique(a)) <= {0.0, 1.0}

def test_zip_contains_exactly_the_tif():
    z = zipfile.ZipFile(TIF.with_suffix(".zip"))
    assert z.namelist() == [TIF.name]
    assert z.read(TIF.name) == TIF.read_bytes()

def test_run_card_gates_and_labels():
    assert CARD["result_cbs_hypothesis"] == "negative"
    h = CARD["holdout"]
    assert h["evidence_class"] == "HOLDOUT-DTI" and h["withheld_positive_pixels"] == 60988
    assert h["ctrl_19b_dotted"]["dti"] > h["repo_best_before_same_evaluator"]["holdout_dti"]
    assert h["leakage_canaries"]["max_two_sided_auc"] <= 0.90
    u = CARD["candidate"]["correlation_overlap_vs_registry"]
    assert u["max_3px_overlap_vs_9_focus_champions"] <= 0.70
    assert u["max_abs_surface_spearman_vs_discrete_peers"] <= 0.90
    assert len(CARD["candidate"]["note_le_140_chars"]) <= 140
    assert CARD["weekly_slots_used"] == 0
    # Merged main governs fail-closed: no promotion without an owner ruling
    # on the space-filling witnesses; the file is research-only meanwhile.
    assert CARD["verdict"] == "negative" and CARD["ok_to_submit"] is False
    assert "Literal any-registry" in CARD["blocking_gate"]

def test_cbs_pages_link_the_exact_file():
    for p in ("docs/cbs/index.html", "docs/cbs/executive-summary.html"):
        txt = (ROOT / p).read_text()
        assert TIF.name in txt and CARD["candidate"]["sha256"] in txt
        assert "USER-REPORTED" in txt  # historical scores never labelled as receipts
        assert "DO NOT SUBMIT" in txt
