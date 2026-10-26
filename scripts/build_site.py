#!/usr/bin/env python3
"""Build a static, evidence-bound GitHub Pages site without network dependencies."""
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def focus_rows(manifest: dict, audit: dict) -> str:
    measured = {row["site"]: row for row in audit["historical_focus"]}
    sources = manifest["focus_sites"]
    if len(measured) != len(sources) or set(measured) != {item["site"] for item in sources}:
        raise ValueError("Site list does not match measured evidence")
    result = []
    # Sorting is only by explicitly unverified user-supplied claims, never estimates.
    for item in sorted(sources, key=lambda x: float(x["user_reported_claim"]), reverse=True):
        row = measured[item["site"]]
        if row["file_sha256"] != item["sha256"] or not row["literal_peer_duplicate"]:
            raise ValueError("Evidence changed or lacks the required duplicate finding; rebuild/review the site")
        url = item["url"] + "?raw=true"
        result.append(
            f'<tr><td><strong>{esc(item["site"])}</strong><small><a href="{esc(item["site_url"])}">Open site ↗</a></small></td>'
            f'<td><a href="{esc(url)}">{esc(item["filename"])} ↗</a><small>Historical mirror · research only</small></td>'
            f'<td><strong>{esc(item["user_reported_claim"])}</strong><small>USER-REPORTED · unverified</small></td>'
            '<td>Unavailable<small>No calibrated estimate</small></td>'
            f'<td><span class="bad">NO</span><small>{row["max_peer_overlap"] * 100:.1f}% vs {esc(row["max_peer_site"])}</small></td>'
            '<td><span class="pill">DO NOT SUBMIT</span></td></tr>'
        )
    return "\n".join(result)


def build(out: Path) -> None:
    manifest = json.loads((ROOT / "data/focus-inputs.json").read_text())
    audit = json.loads((ROOT / "docs/data/focus-audit.json").read_text())
    run = json.loads((ROOT / "docs/data/run-card.json").read_text())
    preflight = audit["preflight"]
    bound = preflight["bound"]
    ledger = run["registry"]
    lineage = audit["lineage"]
    sites = {item["site"]: item for item in manifest["focus_sites"]}
    rows = {row["site"]: row for row in audit["historical_focus"]}
    # The prose in this frozen report cites these exact observations. Refuse a
    # deploy rather than silently render stale values after evidence changes.
    consistent = (
        run.get("verdict") == "negative" and run.get("ok_to_submit") is False
        and run.get("raster_sha256") is None and bound["guaranteed_duplicate"]
        and bound["candidate_distinct_dots"] == ledger["planned_distinct_dots"] == 37_654
        and bound["uncovered_pixels"] == ledger["uncovered_footprint_pixels"] == 6_649
        and math.isclose(bound["minimum_overlap_fraction"], ledger["minimum_possible_overlap_fraction"], abs_tol=1e-12)
        and round(bound["minimum_overlap_fraction"] * 100, 2) == 82.34
        and preflight["lattice_file_sha256"] == ledger["witness_sha256"]
        and lineage["d28_dots_removed_to_r1"] == lineage["d28_removed_within_1px_catalogue"] == 3_891
        and lineage["r1_dots_removed_to_b2"] == lineage["r1_removed_within_2px_catalogue"] == 2_545
        and lineage["b2_dots_not_in_r1"] == lineage["r1_dots_not_in_d28"] == lineage["b2_not_in_geothermal"] == 0
        and lineage["geothermal_additions_to_b2"] == 1_200
        and rows["GEMSDOE30"]["positive_pixels"] == 44_090
        and rows["GEMSDOE31"]["positive_pixels"] == 40_199
        and rows["GEMSDOE32"]["positive_pixels"] == 37_654
        and sites["GEMSDOE32"]["user_reported_claim"] == "0.2778"
        and max(float(item["user_reported_claim"]) for item in sites.values()) == 0.2778
    )
    if not consistent:
        raise ValueError("Frozen page does not match the run card, source manifest or audited measurements")
    out.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "executive-summary.html"):
        source = (ROOT / "site" / name).read_text()
        source = source.replace("{{FOCUS_ROWS}}", focus_rows(manifest, audit))
        if "{{" in source or "}}" in source:
            raise ValueError(f"Unresolved template placeholder in {name}")
        (out / name).write_text(source)
    for sub, files in {
        "assets": ["style.css", "site.js"],
        "docs/data": ["focus-audit.json", "run-card.json", "leaderboard.json", "template-diagnostic.json"],
        "data": ["focus-inputs.json"],
        "research": ["preregistration.md", "decision-brief.md"],
    }.items():
        (out / sub).mkdir(parents=True, exist_ok=True)
        for filename in files:
            shutil.copyfile(ROOT / sub / filename, out / sub / filename)
    (out / ".nojekyll").write_text("")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".site")
    args = parser.parse_args()
    build(args.output)
    print(f"Built static site: {args.output}")


if __name__ == "__main__":
    main()
