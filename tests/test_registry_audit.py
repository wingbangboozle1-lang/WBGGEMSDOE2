from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_registry as audit


def test_exact_strict_bound_and_first_failure():
    # Seven of ten forced overlaps is exactly the ceiling and does not fail.
    b = audit.overlap_bound(10, 7, 10)
    assert b["minimum_overlap_fraction"] == 0.7
    assert b["guaranteed_duplicate"] is False
    assert audit.overlap_bound(10, 8, 10)["guaranteed_duplicate"] is True
    assert audit.overlap_bound(5_167_373, 5_160_724, 37_654)["first_dot_count_forced_over_threshold"] == 22_164
    assert audit.overlap_bound(100, 100, 1)["guaranteed_duplicate"] is True
    assert audit.overlap_bound(100, 0, 100)["first_dot_count_forced_over_threshold"] is None
    assert audit.overlap_bound(10, 7, 10, Fraction(0))["guaranteed_duplicate"] is True


@pytest.mark.parametrize("args", [(0, 0, 0), (10, 11, 1), (10, -1, 1), (10, 1, 11), (10, 1, True), (10., 1, 1)])
def test_invalid_bound_inputs_fail_closed(args):
    with pytest.raises(ValueError):
        audit.overlap_bound(*args)


def test_coverage_is_euclidean_and_inclusive_at_radius():
    dots = np.zeros((9, 9), dtype=bool)
    dots[4, 4] = True
    c = audit.coverage(dots, 3)
    assert c.sum() == 29
    assert c[4, 7] and c[6, 6]
    assert not c[7, 7]
    with pytest.raises(ValueError):
        audit.coverage(dots.astype(float))


def test_coverage_agrees_with_exact_euclidean_distance_transform():
    from scipy.ndimage import distance_transform_edt
    rng = np.random.default_rng(11)
    for shape in ((1, 1), (5, 7), (17, 15)):
        mask = rng.random(shape) < 0.15
        mask[0, 0] = True
        for radius in (0, 1, 2, 3):
            assert np.array_equal(audit.coverage(mask, radius), distance_transform_edt(~mask) <= radius)


def test_pinned_github_only_and_no_cache_traversal(tmp_path):
    source = "https://github.com/o/r/blob/" + "a" * 40 + "/dir/file.tif"
    assert audit.api_url(source) == "https://api.github.com/repos/o/r/contents/dir/file.tif?ref=" + "a" * 40
    for bad in ["http://github.com/o/r/blob/" + "a" * 40 + "/x", "https://evil.example/x", source + "?raw=1", source.replace("a" * 40, "main"), source.replace("dir/file", "../file")]:
        with pytest.raises(ValueError):
            audit.api_url(bad)
    with pytest.raises(ValueError):
        audit.cache_path(tmp_path, "../escape")


def _write(path, array, dtype, transform):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1], count=1,
                       dtype=dtype, crs="EPSG:32611", transform=transform) as dst:
        dst.write(array.astype(dtype), 1)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_manifest(tmp_path, monkeypatch):
    shape = (6, 6)
    transform = Affine(100, 0, 243350, 0, -100, 4508550)
    monkeypatch.setattr(audit, "GRID", {"shape": shape, "crs": "EPSG:32611", "transform": tuple(transform)[:6]})
    fp = np.ones(shape, dtype=bool)
    fp[0, 0] = False
    template = np.zeros(shape, dtype=np.float32)
    template[0, 0] = np.nan
    template[1, 1] = 1
    labels = np.zeros(shape, dtype=np.int8)
    labels[1, 1] = 1
    lattice = np.zeros(shape, dtype=np.float32)
    lattice[0, 0] = np.nan
    lattice[2, 2] = 1
    core = {}
    for name, arr, dtype in (("template", template, "float32"), ("catalogue", labels, "int8"), ("lattice", lattice, "float32")):
        path = tmp_path / f"{name}.tif"
        _write(path, arr, dtype, transform)
        core[name] = {"local": path.name, "sha256": _hash(path)}
    content_sha = hashlib.sha256(np.asarray(lattice[fp], dtype="<f4").tobytes()).hexdigest()
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"unique_rasters": [{"id": "witness", "sha256": core["lattice"]["sha256"], "footprint_sha256": content_sha}]}))
    core["registry"] = {"local": reg.name, "sha256": _hash(reg)}
    dots = {
        "GEMSDOE30": [(1, 1), (1, 2), (2, 2)],
        "GEMSDOE31": [(1, 2), (2, 2)],
        "GEMSDOE32": [(2, 2)],
        "GEMSDOE36": [(2, 2), (3, 3)],
    }
    rows = []
    for site, coords in dots.items():
        arr = np.zeros(shape, dtype=np.float32)
        arr[0, 0] = np.nan
        for y, x in coords:
            arr[y, x] = 1
        path = tmp_path / f"{site}.tif"
        _write(path, arr, "float32", transform)
        rows.append({"site": site, "local": path.name, "sha256": _hash(path),
                     "footprint_sha256": hashlib.sha256(np.asarray(arr[fp], dtype="<f4").tobytes()).hexdigest()})
    return {"core": core, "focus_sites": rows}


def test_analyze_reopens_inputs_and_proves_lineage(tmp_path, monkeypatch):
    manifest = synthetic_manifest(tmp_path, monkeypatch)
    result = audit.analyze(manifest, tmp_path, budget=2)
    assert result["grid"]["sample_positives_equal_catalogue"] is True
    assert result["lineage"]["b2_dots_not_in_r1"] == 0
    assert result["lineage"]["r1_dots_not_in_d28"] == 0
    assert result["lineage"]["geothermal_additions_to_b2"] == 1
    assert all(r["literal_peer_duplicate"] for r in result["historical_focus"])
    assert not list(tmp_path.glob("*candidate*"))


def test_hash_mismatch_is_not_silently_accepted(tmp_path, monkeypatch):
    manifest = synthetic_manifest(tmp_path, monkeypatch)
    (tmp_path / "GEMSDOE32.tif").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="hash-mismatched"):
        audit.analyze(manifest, tmp_path, budget=2)


def test_registry_witness_mismatch_is_not_accepted(tmp_path, monkeypatch):
    manifest = synthetic_manifest(tmp_path, monkeypatch)
    p = tmp_path / "registry.json"
    p.write_text(json.dumps({"unique_rasters": []}))
    manifest["core"]["registry"]["sha256"] = _hash(p)
    with pytest.raises(ValueError, match="witness"):
        audit.analyze(manifest, tmp_path, budget=2)
