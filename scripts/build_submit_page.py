#!/usr/bin/env python3
"""Build a fail-closed submission guide from the reviewed portfolio and run card.

This page never exposes a TIFF download button. A format-valid file is not enough:
all-registry novelty, holdout, provenance, and separate selector gates must pass.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PORTFOLIO = json.loads((DOCS / "data/portfolio.json").read_text(encoding="utf-8"))
RUN_CARD = json.loads((DOCS / "data/run-card.json").read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_page(*, nested: bool) -> str:
    base = "../" if nested else ""
    if RUN_CARD.get("verdict") != "negative" or RUN_CARD.get("ok_to_submit") is not False:
        raise ValueError("Submission guide only renders a negative run card; review a future byte-bound release explicitly.")
    rows = []
    for site in sorted(PORTFOLIO["sites"], key=lambda x: x["site"]):
        overlap = site["max_3px_overlap_vs_other_focus"]
        witness = site["max_overlap_witness_site"]
        score = site["user_reported_score"]
        rows.append(
            "<tr>"
            f"<td><a href=\"{base}sites/{esc(site['site'])}.html\">{esc(site['site'])}</a></td>"
            f"<td><code>{esc(Path(site['path']).name)}</code></td>"
            f"<td>{esc(score)} <small>USER-REPORTED; no authenticated receipt</small></td>"
            "<td>Not defensible</td>"
            f"<td>FAIL: {overlap:.1%} of this raster's dots are within 3 px of {esc(witness)}</td>"
            "<td><strong>DO NOT SUBMIT</strong></td></tr>"
        )
    nav = f"<a href=\"{base}index.html\">Project home</a> · <a href=\"{base}executive-summary.html\">Executive summary</a> · <a href=\"{base}sources.html\">Sources</a>"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Submission guide — GEMS research</title>
<style>
:root{{--ink:#18212b;--muted:#5b6672;--line:#d8dee6;--red:#a21c18;--pale:#fff0ef;--blue:#174ea6}}
*{{box-sizing:border-box}} body{{margin:0;background:#f5f7fa;color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:26px 20px 70px}} nav{{padding:14px 20px;background:#fff;border-bottom:1px solid var(--line)}}
h1{{font-size:2rem;margin:.4em 0}} h2{{margin-top:1.8em}} a{{color:var(--blue)}}
.alert{{padding:18px 20px;background:var(--pale);border:3px solid var(--red);border-radius:12px;color:var(--red)}}
.alert strong{{font-size:1.35rem}} .card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:18px 0}}
.table-wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}} th,td{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}} th{{background:#edf1f5}} code{{overflow-wrap:anywhere}}
small{{display:block;color:var(--muted)}} .no-file{{font-weight:800;color:var(--red)}} footer{{color:var(--muted);margin-top:35px}}
</style></head><body><nav>{nav}</nav><main>
<h1>DOE GEMS Prize — executive summary &amp; submission instructions</h1>
<div class="alert"><strong>NO TIFF IS CLEARED — DO NOT DOWNLOAD A HISTORICAL/RESEARCH TIFF FOR SUBMISSION.</strong>
<p>The current run card is negative. Existing GeoTIFFs are historical or research artifacts. A local format pass, a high owner-reported score, or uniqueness among only the nine named sites does not authorize submission.</p></div>
<div class="card"><h2 style="margin-top:0">Decision and evidence</h2>
<p><b>New submission file:</b> None. <b>Leaderboard score estimate:</b> not defensible; no validated candidate and no organizer receipt. <b>Competition slots used:</b> {RUN_CARD.get('weekly_submission_slots_used', 0)}.</p>
<p>The earlier WBG2-MSPTCD campaign's <b>HOLDOUT-DTI</b> is 0.042554 (95% CI 0.032059–0.054765), evaluator <code>gems57-pooled-hide-v2</code>, 60,988 withheld positives. This is a local hide-and-recover result, not an organizer score. Its candidate failed the literal registry gate outside the nine-site focus set. The prescribed three-experiment budget for that lane is spent.</p>
<p>The requester/site-owner historical GEMSDOE32 B2 figure 0.2778 is <b>USER-REPORTED</b>, not independently tied to an organizer submission receipt. The strongest such reported figure among the nine is not proof of a reproducible new submission.</p>
<p><a href="{base}data/run-card.json">Current negative run card</a> · <a href="{base}data/portfolio.json">Measured nine-site portfolio</a> · <a href="{base}data/RUN_CARD_MSPTCD.json">Prior MSPTCD run card</a></p></div>
<h2>Nine-site executive table</h2>
<p>Scores below are historical reported values. Uniqueness is measured within the pinned nine-site set only; that limited comparison cannot prove novelty against the full registry. Estimates are intentionally unavailable.</p>
<div class="table-wrap"><table><thead><tr><th>Site</th><th>Historical file</th><th>Reported value / evidence</th><th>New candidate estimate</th><th>Unique within these nine?</th><th>Action</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="card"><h2 style="margin-top:0">How to submit — only after a separate approval exists</h2>
<ol><li>Check the current run card and the exact candidate release record. Continue only when it explicitly says <b>OK TO DOWNLOAD AND SUBMIT</b>, names the file and SHA-256, and records a passing validator, holdout and complete-registry checks.</li>
<li>Do not treat a score estimate, projection, local format pass, or this historical table as approval. A holdout must beat a matched incumbent under the pinned evaluator and include the evaluator version, withheld positives and 95% CI.</li>
<li>Download the exact approved GeoTIFF (or a ZIP containing exactly one GeoTIFF) and verify its SHA-256. Current project specifications require matching CRS, shape and geotransform, one band, and predictions in [0,1]. The validator must check NaNs and masks against the footprint, not silently clip or repair.</li>
<li>On the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition page</a>, open <b>Submit → Make new submission</b>, choose the exact approved file, and paste the short release note (≤140 characters). Check the live weekly allowance and current rules; the project does not automate upload or choose a slot.</li>
<li>Save the submission-page receipt. Only that receipt can support the label <b>ORGANIZER-CONFIRMED</b>. A public leaderboard entry alone is not a receipt for a particular file.</li></ol>
<p><b>Current form-ready filename:</b> None. <b>Current note:</b> None. Do not submit.</p>
<p>Official checks: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem and submission format</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">rules</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">public leaderboard</a>.</p></div>
<footer>WBGGEMSDOE2 · evidence-first research · generated from reviewed portfolio and negative run-card artifacts.</footer>
</main></body></html>'''


def main() -> None:
    targets = [DOCS / "submit/index.html", DOCS / "submission/index.html", DOCS / "submission/executive-summary.html"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        # `nested=True` changes relative links from docs/submission/ to docs/.
        target.write_text(build_page(nested=target.parent.name in {"submission", "submit"}), encoding="utf-8")
        print(f"built {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
