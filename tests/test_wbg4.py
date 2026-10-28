"""Tests for the WBG4 lane: metric consistency, fold invariants, writer rules."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wbg2.metric import dti_binary as dti_binary_ref  # noqa: E402
from wbg3.metric import dti_binary, dti_bruteforce, dti_probabilistic  # noqa: E402

import wbg4.emit as EM  # noqa: E402
import wbg4.lane as L  # noqa: E402

HAS_DATA = (ROOT / "data" / "labels.tif").exists()


def toy(seed=7, n=60, m=70):
    rng = np.random.default_rng(seed)
    truth = np.zeros((n, m), bool)
    truth[10:50, 20] = True
    truth[10, 20:45] = True
    pred = np.zeros((n, m), bool)
    pred[10:40, 22] = True
    pred[12, 20:40] = True
    active = np.ones((n, m), bool)
    active[:, :3] = False
    return pred, truth, active


def test_binary_dti_matches_independent_bruteforce():
    pred, truth, active = toy()
    a = dti_binary(pred.astype(float), truth, active)
    b = dti_bruteforce(pred.astype(float), truth, active)
    assert a["dti"] == pytest.approx(b["dti"], rel=1e-9, abs=1e-12)
    assert a["tp"] == pytest.approx(b["tp"], rel=1e-9, abs=1e-9)


def test_binary_dti_matches_second_independent_implementation():
    pred, truth, active = toy()
    a = dti_binary(pred.astype(float), truth, active)
    b = dti_binary_ref(pred, truth, active)
    assert a["dti"] == pytest.approx(b["dti"], rel=1e-9, abs=1e-12)


def test_probabilistic_dti_equals_binary_for_zero_one_input():
    pred, truth, active = toy()
    a = dti_binary(pred.astype(float), truth, active)
    b = dti_probabilistic(pred.astype(float), truth, active)
    assert a["dti"] == pytest.approx(b["dti"], rel=1e-9, abs=1e-12)


def test_kernel_values_are_the_documented_ones():
    from wbg3.metric import kernel
    assert kernel(0) == pytest.approx(1.0)
    assert kernel(1) == pytest.approx(2 / 3)
    assert kernel(2) == pytest.approx(1 / 3)
    assert kernel(3) == pytest.approx(0.0)
    assert kernel(4) == pytest.approx(0.0)


def test_false_negative_identity():
    pred, truth, active = toy()
    a = dti_binary(pred.astype(float), truth, active)
    assert a["fn"] == pytest.approx(a["n_truth"] - a["tp"], abs=1e-9)


@pytest.mark.skipif(not HAS_DATA, reason="competition labels not present in this checkout")
def test_fold_masks_are_disjoint_and_complete():
    fp = L.load_footprint()
    lab = L.load_labels()
    comp, n = L.fault_components(lab, fp)
    ids = L.fold_ids(comp, fp)
    assert n == len(ids)
    total_hidden = 0
    for f in range(4):
        hidden, hbuf, vis_feat, vis_exact = L.fold_masks(comp, ids, f, buffer_px=3)
        assert not (hidden & vis_exact).any(), "withheld faults must not be visible"
        assert vis_exact.any() and hidden.any()
        assert hbuf.all() or (hidden <= hbuf).all()
        assert (vis_feat <= vis_exact).all()
        total_hidden += int(hidden.sum())
    assert total_hidden == int((comp > 0).sum()), "folds must partition the catalogue"


@pytest.mark.skipif(not HAS_DATA, reason="competition labels not present in this checkout")
def test_fold_partition_covers_all_components():
    fp = L.load_footprint()
    lab = L.load_labels()
    comp, n = L.fault_components(lab, fp)
    ids = L.fold_ids(comp, fp)
    seen = set()
    for f in range(4):
        hidden, _, _, _ = L.fold_masks(comp, ids, f)
        seen |= set(np.unique(comp[hidden]).tolist())
    assert seen == set(range(1, n + 1))


def test_writer_rejects_bad_values(tmp_path):
    good = np.zeros((EM.HEIGHT, EM.WIDTH), np.float32)
    out = tmp_path / "x.tif"
    EM.write_submission(good, out)
    assert out.exists()

    bad = good.copy()
    bad[10, 10] = 1.5
    with pytest.raises(ValueError):
        EM.write_submission(bad, tmp_path / "y.tif")

    nan = good.copy()
    nan[5, 5] = np.nan
    with pytest.raises(ValueError):
        EM.write_submission(nan, tmp_path / "z.tif")

    wrong = np.zeros((10, 10), np.float32)
    with pytest.raises(ValueError):
        EM.write_submission(wrong, tmp_path / "w.tif")


def test_writer_roundtrip_validates(tmp_path):
    vals = np.zeros((EM.HEIGHT, EM.WIDTH), np.float32)
    vals[100:200, 100:130] = 1.0
    out = EM.write_submission(vals, tmp_path / "rt.tif")
    fp = np.ones((EM.HEIGHT, EM.WIDTH), bool)
    res = EM.validate(out, fp)
    assert res["ok"], res["checks"]
    assert res["positive_inside_footprint"] == 3000
    assert res["unique_values"] == [0.0, 1.0]


@pytest.mark.skipif(not HAS_DATA, reason="competition labels not present in this checkout")
def test_config_pins_match_local_bytes():
    pins = L.verify_pins()
    assert pins["all_match"], {k: v for k, v in pins.items() if not v.get("matches_config", True)}


@pytest.mark.skipif(not HAS_DATA, reason="competition labels not present in this checkout")
def test_official_grid_shape_and_footprint():
    fp = L.load_footprint()
    lab = L.load_labels()
    assert fp.shape == (L.HEIGHT, L.WIDTH)
    assert int(fp.sum()) == 5_167_373
    assert int(lab.sum()) == 60_988
    assert not (lab & ~fp).any()
