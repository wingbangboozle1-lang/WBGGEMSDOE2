#!/usr/bin/env python3
"""Build the focus-site research pages from the current fail-closed decision.

This publisher deliberately offers no TIFF/ZIP download. A local format pass or
historical holdout/novelty record is not selector authorization. Any future
positive release requires the separate selector policy and a reviewed publisher
change; stale candidate reports cannot turn the page green.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from html import escape
import re
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "lane"

CSS = """
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#15202b;background:#f5f7fa;line-height:1.55}
*{box-sizing:border-box}body{margin:0}header{background:#12263a;color:#fff;padding:14px max(20px,calc((100% - 1040px)/2))}
header a{color:#e6efff;margin-right:18px}main{max-width:1040px;margin:auto;padding:28px 20px 60px}
.banner{background:#fff0f0;border:2px solid #a61b1b;border-radius:12px;padding:20px;margin:16px 0}
.banner h1{margin:0 0 8px;color:#8b1515}.card{background:white;border:1px solid #d9e0e7;border-radius:10px;padding:18px;margin:16px 0}
button{font:inherit;padding:10px 14px;background:#d9dee5;color:#333;border:0;border-radius:7px}table{border-collapse:collapse;width:100%}
th,td{padding:9px;border:1px solid #d9e0e7;text-align:left;vertical-align:top}th{background:#edf1f5}
code{overflow-wrap:anywhere}.muted{color:#536272}.tag{font-weight:700;color:#971717}
"""


def page(title: str, content: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>{escape(title)}</title><style>{CSS}</style></head><body>
<header><a href="../index.html">Project dashboard</a><a href="../executive-summary.html">Nine-site executive summary</a><a href="../release.html">Byte audit</a><a href="../research.html">Hypotheses</a></header>
<main>{content}<footer class="muted">Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} UTC · negative release status is not an organizer receipt.</footer></main></body></html>'''


def decision_banner() -> str:
    return '''<section class="banner" role="alert"><h1>NO FILE APPROVED — DO NOT SUBMIT</h1>
<p>This project currently has no eligible submission GeoTIFF. There is no one-click submission download. The nine historical GEMSDOE files are research references, not eligible submissions.</p>
<p><strong>Score estimate for a new submission: unavailable.</strong> Historical scores in the table are user-reported claims; they are not new-score estimates or organizer receipts.</p><button disabled aria-disabled="true">No submission file available</button>
<p><a href="../executive-summary.html">Open the nine-site executive summary and historical file table →</a></p></section>'''


def build_summary() -> str:
    content = decision_banner() + '''<section class="card"><h2>Executive summary</h2>
<p>The requested comparison table is published on the <a href="../executive-summary.html">nine-site executive summary page</a>. It lists the exact historical file links, user-reported scores, measured pinned-file overlap, unavailable new-score estimates, and the DO NOT SUBMIT decision for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33 and 36.</p>
<p>The highest claim in that list is GEMSDOE32 B2 at 0.2778 (USER-REPORTED). Byte-level lineage is consistent with its being a pruned member of the GEMSDOE25/30 raster family, but this does not prove why the organizer score changed. The hidden labels and a receipt bound to the exact submitted bytes are not available here, so no causal score decomposition or new-score estimate is asserted.</p></section>
<section class="card"><h2>Why no candidate is offered</h2><p>The current checkout is blocked: method lane is unassigned; authenticated competition rasters, derived feature cache and pinned shared evaluator are absent; the current registry is incomplete; the literal duplicate gate has decisive witnesses; the continuous-prior interpretation is unresolved; and a separate selector decision has not occurred.</p><p>The latest diagnostic and session card are linked from the <a href="../readiness.html">readiness page</a>. Existing rasters are research artifacts only.</p></section>'''
    return page("GEMS focus sites — negative release decision", content)


def build_howto() -> str:
    content = decision_banner() + '''<section class="card"><h2>Why a submission is blocked</h2>
<ul><li>No explicitly assigned method lane in the current research ledger.</li>
<li>Current checkout is missing authenticated competition rasters, the derived cache and pinned shared evaluator required for holdout/canary validation.</li>
<li>The registry audit is incomplete and the literal three-pixel duplicate gate has decisive witnesses; dense-prior interpretation is unresolved and no exemption is authorized.</li>
<li>No separate selector approval or organizer receipt exists. A format check alone is not enough.</li></ul></section>
<section class="card"><h2>Submission workflow once a future file passes every gate</h2>
<ol><li>Download the candidate only from an explicitly selector-authorized release page.</li>
<li>Check the exact filename and SHA-256 in its run card.</li>
<li>Log into DrivenData and open the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">submission page</a>.</li>
<li>Choose New submission, upload a single-band GeoTIFF or a ZIP containing one GeoTIFF, and paste the release note (at most 140 characters).</li>
<li>After portal acceptance, archive the receipt and label the score ORGANIZER-CONFIRMED. A local validator cannot certify portal acceptance.</li></ol>
<p>Do not upload any of the historical files linked by the nine-site table under the current negative decision.</p></section>
<section class="card"><h2>Range error</h2><p>DrivenData requires predicted values in [0,1]. A future writer should validate every pixel the portal reads, including masked/outside-footprint cells, against the official sample format. This repository has not identified the exact previously uploaded bytes, so the earlier user error cannot be attributed with certainty to a specific TIFF. Do not assume a zero-outside twin is accepted until the portal confirms it.</p></section>
<section class="card"><h2>Official references</h2><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem description and submission format</a></li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">Competition rules</a></li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a></li></ul></section>'''
    return page("GEMS — submission steps (blocked)", content)


def build_findings() -> str:
    content = decision_banner() + '''<section class="card"><h2>Verified byte-level result and limits</h2>
<p>The hash-pinned focus-site audit reports that the nine historical files are one highly overlapping family rather than nine independent prediction strategies. In particular, GEMSDOE25 and GEMSDOE30 decode to identical in-footprint arrays, and GEMSDOE32 B2 is a pruned subset. This confirms raster lineage only; it does not establish the causal reason for the reported score.</p>
<p>Historical scores in the brief, including 0.2778 for B2, remain USER-REPORTED. A fresh leaderboard score estimate is unavailable; no new HOLDOUT-DTI was run in this review. No candidate experiment or submission slot was used.</p>
<h2>Read the detailed evidence</h2><ul><li><a href="../research/why-b2-scored-2778.html">B2 metric and lineage analysis</a></li><li><a href="../research/session-review-20261028-verification.html">Independent byte-level review and nine-site table</a></li><li><a href="../research/candidate_hypotheses_20261027.html">Ranked untested hypotheses and mimics</a></li><li><a href="../readiness.html">Current checkout readiness / blockers</a></li><li><a href="../data/run-card.json">Current negative run card</a></li></ul></section>'''
    return page("GEMS focus-site findings — research only", content)


def build_sources() -> str:
    content = decision_banner() + '''<section class="card"><h2>Official competition sources</h2><ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition overview</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem description, metric and format</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">DrivenData about page</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">DrivenData data tab (login required)</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public leaderboard</a> — must be refreshed at decision time; no live score is asserted here.</li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference-solution repository</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN official data release</a></li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE Geothermal Data Repository submission 1391</a></li>
<li><a href="https://epsg.io/32611">EPSG:32611 registry entry</a></li></ul>
<p>Source links are provided for review; this build did not fetch or re-verify external pages. Historical repository measurements are documented in <a href="../research/session-review-20261028-verification.html">the verification review</a> and <a href="../data/run-card.json">the negative run card</a>.</p></section>'''
    return page("GEMS — sources and verification limits", content)


def main() -> None:
    run = json.loads((ROOT / "evidence/session_run_card_20261028.json").read_text())
    readiness = json.loads((ROOT / "evidence/checkout_readiness.json").read_text())
    if run.get("verdict") != "negative" or run.get("submission", {}).get("ok_to_download_and_submit") is not False:
        raise SystemExit("STOP: current run card is not a negative release; review the publisher before changing it.")
    if readiness.get("ok_to_submit") is not False:
        raise SystemExit("STOP: checkout readiness is not blocked; review the publisher before changing it.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(build_summary(), encoding="utf-8")
    (OUT / "how-to-submit.html").write_text(build_howto(), encoding="utf-8")
    (OUT / "findings.html").write_text(build_findings(), encoding="utf-8")
    (OUT / "sources.html").write_text(build_sources(), encoding="utf-8")
    manifest = {
        "schema": "wbggems.submission-lane.v2",
        "status": "blocked_do_not_submit",
        "primary_file": None,
        "estimated_leaderboard_score": None,
        "organizer_receipt": None,
        "ok_to_download_and_submit": False,
        "decision_evidence": "evidence/session_run_card_20261028.json",
        "checkout_readiness": "evidence/checkout_readiness.json",
        "reason": "No assigned lane; required cached shared evaluator/data absent; registry incomplete; separate selector not run.",
        "focus_sites": ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"],
        "last_build_utc": datetime.now(timezone.utc).isoformat(),
    }
    (ROOT / "data_public/gemsdoe_release.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote negative-only focus-site pages; no submission TIFF or ZIP offered")


if __name__ == "__main__":
    main()
