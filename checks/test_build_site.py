import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _stage(tmp_path):
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts/build_site.py", tmp_path / "scripts/build_site.py")
    shutil.copytree(ROOT / "docs/data", tmp_path / "docs/data")
    (tmp_path / "docs/downloads").mkdir(parents=True)
    dec = json.loads((tmp_path / "docs/data/decision.json").read_text())
    name = dec["candidate"]["submission_name"]
    for ext in (".tif", ".zip"):
        shutil.copy(ROOT / "docs/downloads" / (name + ext), tmp_path / "docs/downloads" / (name + ext))
    return dec, name


def test_builder_is_byte_bound_and_renders_verified_promotion(tmp_path):
    """A green button needs a byte-bound, machine-validated decision, not a flipped boolean."""
    dec, name = _stage(tmp_path)
    result = subprocess.run([sys.executable, str(tmp_path / "scripts/build_site.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "docs/index.html").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT" in html
    assert (name + ".tif") in html


def test_builder_refuses_unreviewed_promotion(tmp_path):
    """Editing a JSON boolean / breaking the byte binding cannot create a green page."""
    dec, name = _stage(tmp_path)
    # (1) break the raster<->decision byte binding
    path = tmp_path / "docs/data/decision.json"
    dec["candidate"]["raster_sha256"] = "0" * 64
    path.write_text(json.dumps(dec))
    result = subprocess.run([sys.executable, str(tmp_path / "scripts/build_site.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "UNVERIFIED PROMOTION" in result.stderr
    # (2) a false promotion gate also blocks, even with intact bytes
    dec["candidate"]["raster_sha256"] = json.loads((ROOT / "evidence/decision.json").read_text())["candidate"]["raster_sha256"]
    dec["promotion_gates"]["leakage_canary_pass"] = False
    path.write_text(json.dumps(dec))
    result = subprocess.run([sys.executable, str(tmp_path / "scripts/build_site.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "UNVERIFIED PROMOTION" in result.stderr
    # (3) an invented leaderboard score also blocks
    dec["promotion_gates"]["leakage_canary_pass"] = True
    dec["estimated_score"]["leaderboard_dti"] = 0.99
    path.write_text(json.dumps(dec))
    result = subprocess.run([sys.executable, str(tmp_path / "scripts/build_site.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "UNVERIFIED PROMOTION" in result.stderr


def test_scheduled_and_legacy_pages_share_url_layout():
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "cp -R docs/. _site/docs/" in workflow and "cp -R site/. _site/site/" in workflow and "path: _site" in workflow
    assert 'href="../site/sites/GEMSDOE32.html"' in (ROOT / "docs/index.html").read_text()
    assert "url=./docs/" in (ROOT / "index.html").read_text()
    assert 'href="sources.html"' in (ROOT / "docs/index.html").read_text()
    assert "Official source inventory" in (ROOT / "docs/sources.html").read_text()
