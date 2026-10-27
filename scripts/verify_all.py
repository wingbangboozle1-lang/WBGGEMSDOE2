#!/usr/bin/env python3
"""Three independent review passes over the whole GEMS deliverable.

Pass 1 — BYTE INTEGRITY: raster/ZIP/JSON byte-binding, format, [0,1], grid.
Pass 2 — SCIENTIFIC INTEGRITY: leakage canary, holdout, uniqueness, no invented score.
Pass 3 — PUBLICATION INTEGRITY: both dashboards, links, decision copy, no stale "blocked" text.

Writes evidence/review_passes.json (and mirrors to docs/data, site/data). Exit 0
only if all three passes are green. This is the "do multiple passes" gate: no
single check can green-light the submission.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


def jload(rel):
    return json.loads((ROOT / rel).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        v = dict(attrs)
        if "id" in v:
            self.ids.add(v["id"])
        for k in ("href", "src"):
            if k in v:
                self.refs.append(v[k])


def pass1_bytes():
    out = {"pass": 1, "name": "BYTE INTEGRITY", "checks": []}

    def c(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": str(detail)[:160]})

    dec = jload("evidence/decision.json")
    card = jload("evidence/h1_run_card.json")
    fmt = jload("evidence/h1_format.json")
    name = dec["candidate"]["submission_name"]
    tif = ROOT / dec["candidate"]["file"]
    zipf = ROOT / dec["candidate"]["zip"]
    h = sha(tif)
    c("raster_sha_matches_decision", h == dec["candidate"]["raster_sha256"])
    c("raster_sha_matches_run_card", h == card["raster_sha256"])
    c("raster_sha_matches_format_receipt", h == fmt["sha256"])
    c("zip_sha_matches", sha(zipf) == dec["candidate"]["zip_sha256"])
    with zipfile.ZipFile(zipf) as z:
        names = z.namelist()
        c("zip_single_tiff", names == [f"{name}.tif"], names)
        c("zip_tiff_bytes_equal", hashlib.sha256(z.read(names[0])).hexdigest() == h)
    c("docs_copy_identical", (ROOT / dec["candidate"]["docs_file"]).read_bytes() == tif.read_bytes())
    c("docs_zip_identical", (ROOT / dec["candidate"]["docs_zip"]).read_bytes() == zipf.read_bytes())
    import numpy as np
    import rasterio
    with rasterio.open(tif) as ds:
        a = ds.read(1)
        c("single_band_float32", ds.count == 1 and ds.dtypes[0] == "float32")
        c("crs_epsg_32611", str(ds.crs) == "EPSG:32611", str(ds.crs))
        c("shape_3730x3292", ds.shape == (3730, 3292), str(ds.shape))
        c("transform_exact", tuple(ds.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0))
        c("no_nan_inf", bool(np.isfinite(a).all()))
        c("all_values_in_0_1", bool(((a >= 0) & (a <= 1)).all()), f"[{a.min()},{a.max()}]")
        c("no_masked_interior", int((ds.read_masks(1) == 0).sum()) == 0)
        c("nodata_unset", ds.nodata is None)
    c("format_receipt_all_pass", fmt["shared_writer_receipt"]["validator"]["all_checks_passed"])
    c("independent_inspector_pass", fmt["independent_inspect_tif"]["format_valid_against_reference"])
    out["passed"] = all(x["pass"] for x in out["checks"])
    return out


def pass2_science():
    out = {"pass": 2, "name": "SCIENTIFIC INTEGRITY", "checks": []}

    def c(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": str(detail)[:160]})

    dec = jload("evidence/decision.json")
    card = jload("evidence/h1_run_card.json")
    exp = jload("evidence/h1_experiments.json")
    can = jload("evidence/h1_canary.json")
    uni = jload("evidence/h1_uniqueness.json")
    c("verdict_promote", dec["verdict"] == "promote" and card["verdict"] == "promote")
    c("all_promotion_gates", all(card["promotion_gates"].values()))
    c("leakage_canary_all_real_pass", can["all_real_features_pass"])
    c("leakage_demo_correctly_flagged", can["features"]["halo_from_FULL_catalogue_LEAK_DEMO"]["pass"] is False)
    c("surface_corr_le_0_90", uni["max_all_registry_abs_spearman"] <= 0.90, uni["max_all_registry_abs_spearman"])
    c("dot_overlap_le_0_70", uni["max_real_submission_overlap_3px"] <= 0.70, uni["max_real_submission_overlap_3px"])
    c("holdout_evaluator_labeled", exp["evaluator_version"].startswith("gems57"))
    c("holdout_withheld_positives", exp["withheld_positives_total"] > 0, exp["withheld_positives_total"])
    c("holdout_ci_present", len(card["holdout"]["ci95"]) == 2)
    c("beats_champion_mechanism", exp["paired_differences_vs_promoted"]["control_B2_mechanism"]["ci95"][0] > 0)
    c("holdout_not_a_leaderboard_score", card["holdout"]["not_a_leaderboard_score"] is True)
    c("no_invented_leaderboard_score", dec["estimated_score"]["leaderboard_dti"] is None)
    c("irregularities_flagged", len(dec["flagged_irregularities"]) >= 3)
    c("no_weekly_slot_spent", dec["weekly_submission_slots_used"] == 0)
    c("name_note_le_140", len(dec["candidate"]["note"]) <= 140 and len(dec["candidate"]["submission_name"]) <= 140)
    c("archived_negative_lane_synced", jload("evidence/run_card.json")["verdict"] == "negative")
    out["passed"] = all(x["pass"] for x in out["checks"])
    return out


def pass3_publication():
    out = {"pass": 3, "name": "PUBLICATION INTEGRITY", "checks": []}

    def c(name, cond, detail=""):
        out["checks"].append({"check": name, "pass": bool(cond), "detail": str(detail)[:160]})

    # decision mirrors identical
    d = (ROOT / "evidence/decision.json").read_bytes()
    c("decision_mirrors_identical", all((ROOT / r).read_bytes() == d
      for r in ("docs/data/decision.json", "site/data/decision.json")))
    # both dashboards carry the promote decision; no stale "blocked" copy on main landing pages
    for rel in ("docs/index.html", "docs/executive-summary.html", "docs/submit.html",
                "docs/research.html", "docs/sources.html"):
        t = (ROOT / rel).read_text()
        c(f"promote_copy::{rel}", "OK TO DOWNLOAD AND SUBMIT" in t)
    for rel in ("docs/index.html", "site/index.html", "site/executive.html"):
        t = (ROOT / rel).read_text()
        c(f"no_stale_blocked::{rel}", "No file is approved for submission." not in t
          and "NO FILE CLEARED" not in t and "Submission download unavailable" not in t)
    c("fieldnotes_promote", "OK TO SUBMIT" in (ROOT / "site/index.html").read_text())
    c("fieldnotes_guide_actionable", "Download .tif" in (ROOT / "site/executive.html").read_text()
      or "Download the submission" in (ROOT / "site/executive.html").read_text())
    # download button present and resolves
    idx = (ROOT / "docs/index.html").read_text()
    tif_link = f"downloads/{jload('evidence/decision.json')['candidate']['submission_name']}.tif"
    c("download_button_present", tif_link in idx)
    c("download_target_exists", (ROOT / "docs" / tif_link).is_file())
    # executive summary tables
    ex = (ROOT / "docs/executive-summary.html").read_text()
    c("exec_table_has_score_and_unique", "HOLDOUT-DTI" in ex and "Unique" in ex and "Download" in ex)
    # per-site pages: 9, each with the best-submission banner + table
    site_pages = list((ROOT / "site/sites").glob("GEMSDOE*.html"))
    c("nine_site_pages", len(site_pages) == 9, len(site_pages))
    c("all_sites_have_exec_banner", all("Best submission to submit today" in p.read_text() for p in site_pages))
    c("all_sites_have_table", all("Estimated score" in p.read_text() for p in site_pages))
    # all local links resolve across every HTML page
    broken = []
    pages = list((ROOT / "docs").rglob("*.html")) + list((ROOT / "site").rglob("*.html")) + [ROOT / "index.html"]
    for page in pages:
        p = Links()
        p.feed(page.read_text())
        for link in p.refs:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith("mailto:"):
                continue
            path = (page.parent / unquote(parts.path)).resolve() if parts.path else page
            if path.is_dir():
                path /= "index.html"
            if not path.exists():
                broken.append(f"{page.name}:{link}")
    c("all_local_links_resolve", not broken, "; ".join(broken[:4]))
    # README carries current decision and preserves original prompt
    readme = (ROOT / "README.md").read_text()
    c("readme_current_decision", "CURRENT DECISION: **OK TO DOWNLOAD AND SUBMIT**" in readme)
    c("readme_preserved_prompt", "## Original project prompt" in readme and "MUST GENERATE A UNIQUE TIF" in readme)
    # verify script + tests
    r = subprocess.run([sys.executable, "scripts/wbg_verify_decision.py", "--quiet"],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    c("verifier_script_pass", r.returncode == 0, (r.stdout + r.stderr)[:120])
    t = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True,
                       cwd=str(ROOT), timeout=300)
    m = re.search(r"(\d+) passed", t.stdout)
    c("pytest_all_green", t.returncode == 0 and m is not None, m.group(0) if m else t.stdout[-120:])
    out["passed"] = all(x["pass"] for x in out["checks"])
    return out


def main():
    passes = [pass1_bytes(), pass2_science(), pass3_publication()]
    overall = all(p["passed"] for p in passes)
    report = {
        "schema": "wbggems.review_passes.v1",
        "evidence_class": "MULTI-PASS-VERIFICATION",
        "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "decision": "OK TO DOWNLOAD AND SUBMIT" if overall else "DO NOT SUBMIT",
        "all_passes_green": overall,
        "passes": passes,
        "note": ("Three independent passes: byte integrity, scientific integrity, publication integrity. "
                 "A single pass cannot green-light the submission. Leaderboard score remains UNKNOWN."),
    }
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    (ROOT / "evidence/review_passes.json").write_text(text)
    for rel in ("docs/data/review_passes.json", "site/data/review_passes.json"):
        (ROOT / rel).write_text(text)
    for p in passes:
        print(f"Pass {p['pass']} {p['name']}: {'GREEN' if p['passed'] else 'RED'} "
              f"({sum(x['pass'] for x in p['checks'])}/{len(p['checks'])} checks)")
        for x in p["checks"]:
            if not x["pass"]:
                print(f"   FAIL {x['check']}: {x['detail']}")
    print("OVERALL:", report["decision"])
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
