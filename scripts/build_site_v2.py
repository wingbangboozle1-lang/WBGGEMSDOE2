#!/usr/bin/env python3
"""Build the legacy /docs/submission/ pages as a research-only archive.

The old generator consumed a stale DZ-16 positive run card and emitted an upload
button. This replacement intentionally does not read those candidate cards or
link to any GeoTIFF/ZIP. It only renders the canonical current disposition and
owner-reported nine-site research table.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from submission_status import load_submission_status

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "submission"
PORTFOLIO = DOCS / "data" / "portfolio.json"

CSS = """
:root{color-scheme:light;--ink:#17221d;--muted:#53625b;--line:#d5ded8;--red:#a22121;--pale:#fff2f0;--green:#164c3b;--blue:#0a527a}
*{box-sizing:border-box}body{margin:0;background:#f3f6f4;color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1100px;margin:auto;padding:26px 20px 64px}nav{display:flex;gap:16px;flex-wrap:wrap;padding:10px 0 24px}
a{color:var(--blue)}h1{font-size:clamp(2rem,5vw,3rem);line-height:1.1}h2{margin-top:1.7em}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;margin:16px 0}
.alert{border:2px solid var(--red);background:var(--pale)}.muted{color:var(--muted)}table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#eaf0ec}.bad{color:var(--red);font-weight:800}code{overflow-wrap:anywhere}footer{margin-top:32px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
"""


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str, *, nested: bool = False) -> str:
    prefix = "../" if nested else ""
    nav = f"""<nav><a href="{prefix}index.html">Archive status</a><a href="{prefix}executive-summary.html">Nine-site review</a><a href="{prefix}methodology.html">Protocol</a><a href="{prefix}sources.html">Official sources</a><a href="{prefix}parallel-lanes.html">Historical lanes</a><a href="{prefix}../index.html">Current dashboard</a></nav>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>{e(title)} · Research archive</title><link rel="stylesheet" href="{prefix}styles.css"></head><body><div class="wrap">{nav}{body}<footer>Research-only archive. No page in this section authorizes a competition upload. Current project status is governed by the canonical run card and separate selector release.</footer></div></body></html>"""


def status_card(reason: str, *, nested: bool = False) -> str:
    prefix = "../../" if nested else "../"
    return f"""<section class="card alert" role="alert"><p class="bad">CURRENT DECISION: DO NOT SUBMIT</p><h2>No candidate is cleared for download or upload.</h2><p>The canonical run card has no approved candidate bytes or complete release evidence; the current registry is not cleared and no separate weekly-slot selector record exists. Historical DZ-16/H3-PACK lane cards and local format or holdout results do not override the current negative disposition.</p><details><summary>Machine-check reasons</summary><p>{e(reason)}</p></details><p><a href="{prefix}data/run-card.json">Canonical run card</a> · <a href="{prefix}downloads/README.txt">Research-only artifact notice</a></p></section>"""


def portfolio_rows(rows: list[dict]) -> str:
    rendered = []
    for row in sorted(rows, key=lambda r: r["site"]):
        overlap = row.get("max_3px_overlap_vs_other_focus")
        overlap_text = f"{overlap * 100:.2f}%" if isinstance(overlap, (int, float)) else "Not measured"
        path = Path(row["path"]).name
        rendered.append(
            f"<tr><td><a href=\"sites/{e(row['site'])}.html\">{e(row['site'])}</a></td>"
            f"<td>{e(row.get('user_reported_score', 'Unavailable'))}<br><small>USER-REPORTED; no receipt</small></td>"
            f"<td><code>{e(path)}</code><br><small>historical mirror only</small></td>"
            f"<td>{e(overlap_text)}<br><small>vs another focus raster only</small></td>"
            f"<td class=\"bad\">Research only · DO NOT SUBMIT</td></tr>"
        )
    return "".join(rendered)


def main() -> None:
    status = load_submission_status(ROOT)
    if status["approved"]:
        raise SystemExit("A positive selector release exists; re-review the legacy archive renderer before publishing.")
    card = status.get("card") or {}
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    rows = portfolio["sites"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "styles.css").write_text(CSS, encoding="utf-8")

    summary_table = f"""<div class=\"card\"><h2>Nine priority-site references</h2><p>Scores below are historical USER-REPORTED claims, not organizer receipts. The overlap comparison is against other focus-site rasters only; it cannot prove uniqueness against the complete registry.</p><div style=\"overflow-x:auto\"><table><thead><tr><th>Site</th><th>Score and evidence</th><th>Historical file name (not linked)</th><th>Max 3-px peer overlap</th><th>Current decision</th></tr></thead><tbody>{portfolio_rows(rows)}</tbody></table></div></div>"""
    index_body = f"""<main><p class=\"muted\">Legacy URL preserved for provenance; this is not a submission page.</p><h1>Research archive, not a download page</h1>{status_card(status['reason'])}<section class=\"card\"><h2>Historical lane records</h2><p>The earlier DZ-16 card recorded a calibrated-gate promotion, but its holdout was not run and its literal uniqueness result failed. The H3 card also used a lane-level promote label despite registered novelty witnesses. Neither is current project authorization. WBG2-MSPTCD reports a local HOLDOUT-DTI result with evaluator, withheld-positive count and CI, but stopped on the literal registry gate.</p><p>No historical TIFF or ZIP is offered here. The raw artifacts are kept in the repository for reproducibility and audit; access to bytes does not mean permission to submit them.</p></section>{summary_table}</main>"""
    (OUT / "index.html").write_text(page("Research-only archive", index_body), encoding="utf-8")

    executive_body = f"""<main><p class=\"muted\">Evidence table · every historical score claim is labelled by provenance.</p><h1>Nine-site score and uniqueness review</h1>{status_card(status['reason'])}{summary_table}<section class=\"card\"><h2>Interpretation</h2><p>Highest owner-reported score among the nine is GEMSDOE32 at 0.2778. Its exact upload receipt is unavailable, and overlap is not a cross-registry novelty pass. No site file is recommended for submission.</p><p><a href=\"https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/\">Official public leaderboard</a> · <a href=\"../research/why-b2-scored-2778.html\">B2 lineage analysis</a></p></section></main>"""
    (OUT / "executive-summary.html").write_text(page("Nine-site evidence review", executive_body), encoding="utf-8")

    methodology_body = f"""<main><p class=\"muted\">Competition protocol and release boundaries</p><h1>Methodology and validation gates</h1>{status_card(status['reason'])}<section class=\"card\"><h2>Required before an experiment</h2><ul><li>One explicitly assigned method lane; no self-selection from a ranked hypothesis list.</li><li>Reuse the pinned shared feature cache, evaluator and writer; no private fork.</li><li>Withhold whole fault segments with a buffer; derive catalogue features from visible faults only; mask visible faults pixel-exactly.</li><li>Run pooled DTI with α=0.2, β=0.8, 300 m triangular kernel; report evaluator version, withheld-positive count and spatial-block 95% CI.</li><li>Run each feature-alone leakage canary; AUC &gt;0.90 is leakage until resolved.</li><li>Compare pre-placement surface correlation and final-dot 3-px overlap against the complete current registry.</li><li>Stop at three experiments or two hours. A research promotion is not a slot selection.</li></ul><p>HOLDOUT-DTI is local validation, not a leaderboard score. ORGANIZER-CONFIRMED requires a submission-page receipt that identifies the exact file.</p></section></main>"""
    (OUT / "methodology.html").write_text(page("Validation protocol", methodology_body), encoding="utf-8")

    sources_body = f"""<main><p class=\"muted\">Official links and source boundaries</p><h1>Sources and evidence limits</h1>{status_card(status['reason'])}<section class=\"card\"><ul><li><a href=\"https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/\">DrivenData problem description and format</a></li><li><a href=\"https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/\">DrivenData public leaderboard</a> — time-varying public observation, not a submission receipt.</li><li><a href=\"https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and\">USGS GeoDAWN</a> — source metadata; exact line-level coverage/access must be verified before use.</li><li><a href=\"https://gdr.openei.org/submissions/1391\">DOE GDR INGENIOUS release</a> — licenses/access notes are maintained in the project evidence inventory.</li></ul><p>See <a href=\"../research/evidence-and-sources.md\">the full evidence notes</a>. Claims copied from owner pages remain USER-REPORTED unless an exact organizer receipt is present.</p></section></main>"""
    (OUT / "sources.html").write_text(page("Official sources", sources_body), encoding="utf-8")

    lanes_body = f"""<main><p class=\"muted\">Provenance, not competing submission advice</p><h1>Historical lane records reconciled</h1>{status_card(status['reason'])}<section class=\"card\"><h2>Current project-level rule</h2><p>One canonical card and one separate selector release govern the current decision. A historical lane card can document an experiment, but cannot supersede the canonical project disposition or authorize the weekly slot.</p><table><tr><th>Record</th><th>Historical result</th><th>Current interpretation</th></tr><tr><td>DZ-16</td><td>Older calibrated-gate lane promotion; holdout NOT RUN; literal uniqueness FAIL.</td><td>Retained research artifact; not cleared.</td></tr><tr><td>H3-PACK</td><td>Older lane-level promotion with high overlap against registered witnesses.</td><td>Retained research artifact; not cleared.</td></tr><tr><td>WBG2-MSPTCD</td><td>HOLDOUT-DTI 0.042554, `gems57-pooled-hide-v2`, 60,988 withheld positives, 95% CI [0.032059, 0.054765].</td><td>Literal all-registry stop; research-only.</td></tr></table></section></main>"""
    (OUT / "parallel-lanes.html").write_text(page("Historical lane reconciliation", lanes_body), encoding="utf-8")

    sites = OUT / "sites"
    sites.mkdir(exist_ok=True)
    for row in rows:
        overlap = row.get("max_3px_overlap_vs_other_focus")
        overlap_text = f"{overlap * 100:.2f}%" if isinstance(overlap, (int, float)) else "Not measured"
        body = f"""<main><p class=\"muted\">Owner-mirror evidence; not a live submission recommendation</p><h1>{e(row['site'])}</h1>{status_card(status['reason'], nested=True)}<section class=\"card\"><p>Historical file: <code>{e(Path(row['path']).name)}</code> (not linked)</p><p>Reported score: <strong>{e(row.get('user_reported_score', 'Unavailable'))}</strong> · <strong>USER-REPORTED</strong>; no authenticated receipt.</p><p>Measured maximum 3-px overlap with another focus raster: <strong>{e(overlap_text)}</strong>. This is not a complete-registry uniqueness result.</p><p>Raster SHA-256: <code>{e(row.get('sha256', 'not recorded'))}</code></p><p>Repository: <a href=\"https://github.com/{e(row['repository'])}/tree/{e(row['ref'])}\">pinned owner repository reference</a> · <a href=\"{e(row['page_url'])}\">historical owner page</a>.</p><p class=\"bad\">Research only · DO NOT SUBMIT</p></section></main>"""
        (sites / f"{row['site']}.html").write_text(page(f"{row['site']} evidence review", body, nested=True), encoding="utf-8")

    print("wrote fail-closed docs/submission research archive pages")


if __name__ == "__main__":
    main()
