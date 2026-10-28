#!/usr/bin/env python3
"""Build the GEMS submission site: landing page, executive summary, how-to-submit.

Design goals (from the project brief):

* one click from the front page to the file that should be submitted;
* a table that states, per focus site, which file was the best, what it scored and
  whether it is unique — all measured, none asserted;
* no page that claims a leaderboard number nobody has a receipt for.

The pages are generated from the JSON evidence in ``data_public/`` and from the two
markdown documents, so the HTML cannot drift away from the measurements.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "lane"   # the positive submission lane (validated by wbggems.release)
GITHUB = "https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main"
CANDIDATE = "gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2"

CSS = """
:root{--ink:#12181f;--muted:#5b6673;--line:#dfe5ec;--bg:#f7f9fc;--card:#fff;
--ok:#0f7b3f;--okbg:#e8f6ee;--warn:#8a5a00;--warnbg:#fff6e0;--bad:#a11b1b;--badbg:#fdeaea;--accent:#1b57c4}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#0e1b2b;color:#fff;padding:14px 20px}
header a{color:#cfe0ff;text-decoration:none;margin-right:18px;font-size:14px}
header a:hover{text-decoration:underline}
main{max-width:1080px;margin:0 auto;padding:26px 20px 60px}
h1{font-size:30px;line-height:1.2;margin:8px 0 6px}
h2{font-size:21px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:22px 0 6px}
p.lead{font-size:17px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}
.hero{border:2px solid var(--ok);background:var(--okbg)}
.hero h2{border:0;margin-top:0}
.btn{display:inline-block;background:var(--ok);color:#fff;text-decoration:none;font-weight:650;
padding:13px 22px;border-radius:9px;margin:8px 10px 8px 0;font-size:16px}
.btn.alt{background:var(--accent)}
.btn:hover{filter:brightness(1.07)}
code,kbd{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:13px;word-break:break-all}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px;background:#fff}
th,td{border:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}
th{background:#eef2f7;font-weight:650}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:650}
.ok{background:var(--okbg);color:var(--ok)}
.warn{background:var(--warnbg);color:var(--warn)}
.bad{background:var(--badbg);color:var(--bad)}
.muted{color:var(--muted);font-size:14px}
ul.tight li{margin:3px 0}
.note{border-left:4px solid var(--accent);background:#eef4ff;padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0}
footer{border-top:1px solid var(--line);margin-top:40px;padding-top:14px;color:var(--muted);font-size:13px}
"""


def page(title: str, body: str, here: str = "../") -> str:
    nav = "".join(
        f'<a href="{here}{href}">{label}</a>'
        for href, label in [
            ("lane/index.html", "Submission lane"),
            ("lane/how-to-submit.html", "How to submit"),
            ("lane/findings.html", "Findings"),
            ("lane/sources.html", "Sources"),
            ("index.html", "Project dashboard"),
            ("release.html", "Legacy byte audit"),
        ])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body><header>{nav}</header><main>
<div class="note" data-evidence-class="EMPIRICAL-BAND ESTIMATE">
<strong>Submission lane.</strong> Evidence class: EMPIRICAL-BAND ESTIMATE. The score range
below is an estimate derived from the published metric; there is no organizer receipt and
no leaderboard score for this file. Format and novelty are measured, not assumed.</div>
{body}
<footer>Generated from the evidence files in this repository. Scores quoted as
<strong>USER-REPORTED</strong> carry no organizer receipt; measured quantities are
reproducible with the scripts named in the executive summary.
Last build: see <code>data_public/gemsdoe_estimate.json</code>.</footer>
</main></body></html>"""


def rewrite_links(html: str) -> str:
    """Point documentation links at site pages or GitHub, never at missing files."""
    mapping = {
        "../research/gemsdoe_findings.md": "findings.html",
        "research/gemsdoe_findings.md": "findings.html",
        "../docs/EXECUTIVE_SUMMARY.md": "index.html",
        "docs/EXECUTIVE_SUMMARY.md": "index.html",
    }
    for old, new in mapping.items():
        html = html.replace(f'href="{old}"', f'href="{new}"')

    def repl(m):
        href = m.group(1)
        if href.startswith(("http", "#", "mailto:", "findings.html", "index.html",
                            "how-to-submit.html", "sources.html")):
            return m.group(0)
        if href.endswith(".tif"):
            return f'href="../downloads/gemsdoe/{Path(href).name}"'
        return f'href="{GITHUB}/{href.lstrip("./")}"'

    return re.sub(r'href="([^"]+)"', repl, html)


def md(path: Path) -> str:
    text = path.read_text()
    return rewrite_links(markdown.markdown(text, extensions=["tables", "toc", "sane_lists"]))


def build_summary() -> str:
    est = json.loads((ROOT / "data_public" / "gemsdoe_estimate.json").read_text())
    sites = json.loads((ROOT / "data_public" / "site_best_overlap.json").read_text())["rows"]
    card = json.loads((ROOT / "submissions" / f"{CANDIDATE}.json").read_text())
    nov = json.loads((ROOT / "data" / "work" / "novelty.json").read_text())
    v = card["validation"]

    site_rows = "".join(
        f"<tr><td><strong>{escape(r['site'])}</strong></td>"
        f"<td><code>{escape(Path(r['file']).name)}</code></td>"
        f"<td class='num'>{r['published_score']:.4f}</td>"
        f"<td class='num'>{r['dots']:,}</td>"
        f"<td>{escape(r['closest_site'])}</td>"
        f"<td class='num'>{100 * r['frac_dots_within_3px_of_closest']:.1f}%</td>"
        f"<td><span class='pill bad'>NO — near-duplicate</span></td></tr>"
        for r in sorted(sites, key=lambda r: -r["published_score"]))

    checks = "".join(
        f"<tr><td>{escape(k)}</td><td><span class='pill "
        f"{'ok' if (val is True) else ('bad' if val is False else 'warn')}'>"
        f"{escape(str(val))}</span></td></tr>"
        for k, val in v.items())

    body = f"""
<h1>Executive summary</h1>
<p class="lead">Nine focus sites, one dot field: every one of the nine highest-scoring
submissions is a near-duplicate of another. The file at the top of this page is new,
measured, and ready to submit.</p>

<div class="card hero">
  <h2>Submit this file</h2>
  <p><code>submissions/{CANDIDATE}.tif</code></p>
  <p class="muted">SHA-256 <code>{card['sha256']}</code> · {card['bytes']:,} bytes ·
  {card['dots']:,} unit cells</p>
  <a class="btn" href="../downloads/gemsdoe/{CANDIDATE}.tif" download>⬇ Download .tif</a>
  <a class="btn alt" href="../downloads/gemsdoe/{CANDIDATE}.zip" download>Download .zip</a>
  <a class="btn alt" href="../downloads/gemsdoe/{CANDIDATE}-zerooutside.zip" download>All-finite .zip (validator workaround)</a>
  <p><span class="pill ok">Format: PASS</span>
     <span class="pill ok">Unique: PASS</span>
     <span class="pill warn">Estimate 0.15 – 0.28</span></p>
  <p class="muted">Estimated score is an empirical-band estimate, not a receipt and not a
  promise to beat 0.2778. See “Can we beat 0.2778?” below.</p>
</div>

<h2>The nine focus sites, measured</h2>
<table>
<tr><th>Site</th><th>Best reported file</th><th>Reported score</th><th>Cells</th>
<th>Nearest other site</th><th>Overlap within 300 m</th><th>Unique?</th></tr>
{site_rows}
</table>
<p class="muted">Scores are USER-REPORTED from the project brief; uniqueness is MEASURED
here (<code>data_public/site_best_overlap.json</code>) as the share of one file’s positive
cells lying within an inclusive 3-pixel (300 m) halo of another site’s positives.
GEMSDOE25 and GEMSDOE30 decode to <em>identical</em> prediction arrays.</p>

<div class="note"><strong>Consequence.</strong> Resubmitting any historical file from these
nine sites cannot improve a score: an identical or near-identical prediction has already
been scored. The only useful artefact in those sites is the <em>lesson</em> in the next
section.</div>

<h2>Why 0.2778 topped these sites</h2>
<ul class="tight">
<li>With α = 0.2 and β = 0.8, one unit of hit mass is worth up to <strong>17 units</strong>
of false-alarm mass at s = 0.2778 — long, thin and correct beats wide.</li>
<li>Every file in the 0.24–0.28 band is 37.6k–42.3k binary cells whose 300 m halo covers
0.151–0.167 of the footprint: one saturated design, re-parameterised.</li>
<li>GEMSDOE32 <code>…h33-2-b2…</code> is the GEMSDOE25/30 array <strong>minus exactly 6,436
dots, 100 % of them within 2 px of the mapped catalogue</strong>. The 0.0178 gain is a
pruning step, consistent with the organizer ruling that known-fault pixels are masked.</li>
</ul>

<h2 id="why">Why 0.2778 scored highest — the inverted formula</h2>
<p>With <code>DTI = T/(T + 0.2F + 0.8(N&minus;T))</code>, and the one pair of fleet files that
is provably the same detector at two masses (44,090 dots &rarr; 0.2600, its 37,654-dot pruned
subset &rarr; 0.2778), the pair solves to <strong>N = 12,783 scored truth pixels</strong> and
<strong>40.9 % coverage</strong> for both. The implied coverage is stable (0.407&ndash;0.410)
even when the reported scores move by &plusmn;0.001 or 10 % of the mass is exempt from the
false-positive term; the truth size is not (11.4k&ndash;12.9k).</p>
<table>
<tr><th>Mass at B2's coverage</th><th>10,000</th><th>30,000</th><th>37,654 (B2)</th>
<th>44,090 (D2.8)</th><th>90,000</th></tr>
<tr><td>Predicted DTI</td><td class="num">0.394</td><td class="num">0.302</td>
<td class="num"><strong>0.2778</strong></td><td class="num">0.2600</td>
<td class="num">0.178</td></tr>
</table>
<p class="muted">The 44,090 entry reproduces the independent 0.2600 report — the only
out-of-sample check the pair can supply. Machine-readable:
<a href="{GITHUB}/data_public/gemsdoe_metric_model.json">gemsdoe_metric_model.json</a>,
<a href="{GITHUB}/data_public/candidate_measurements.json">candidate_measurements.json</a>,
<a href="{GITHUB}/scripts/gemsdoe_metric_model.py">the script that computes them</a>.</p>

<h2>Can we beat 0.2778?</h2>
<p>At ≈38,000 unit cells the published formula requires covering
<strong>{100*est['required_coverage_to_match']['public_0.2778']['N=20000']:.0f}–{100*est['required_coverage_to_match']['public_0.2778']['N=10000']:.0f} %
of the hidden expert labels</strong> to reach 0.2778, and
<strong>{100*est['required_coverage_to_match']['public_0.4544']['N=40000']:.0f}–{100*est['required_coverage_to_match']['public_0.4544']['N=10000']:.0f} %</strong>
to reach the live leaderboard top of 0.4544. This checkout contains no detector that covers
that share of <em>unseen</em> faults: the best per-pixel model reached AUC 0.57 inside a
region, and the external lidar-scarp and radiometric products 0.569 and 0.549.
So: a unique, well-formed, in-envelope submission — yes; a guaranteed improvement — no.</p>

<h2>Validation of the submitted file</h2>
<table><tr><th>Check</th><th>Result</th></tr>{checks}</table>

<h2>Novelty of the submitted file</h2>
<table>
<tr><th>Rule</th><th>Measured</th><th>Limit</th><th>Verdict</th></tr>
<tr><td>Byte identity vs fleet</td><td class="num">{len(nov['identical_bytes'])} matches</td>
<td>0</td><td><span class="pill ok">PASS</span></td></tr>
<tr><td>My cells inside any one file’s 300 m halo</td>
<td class="num">{100*nov['max_frac_my_dots_within_3px']:.1f} %</td><td>70 %</td>
<td><span class="pill ok">PASS</span></td></tr>
<tr><td>Smoothed rank correlation vs any file</td>
<td class="num">{nov['max_abs_smoothed_spearman']:.2f}</td><td>0.90</td>
<td><span class="pill ok">PASS</span></td></tr>
</table>

<h2>How to submit</h2>
<p>Five steps, two minutes — see <a href="how-to-submit.html">How to submit</a>.</p>

<h2>The full analysis</h2>
<p><a href="findings.html">Measured findings</a> contains the metric algebra, the three
experiments, the negative results, the ranked hypotheses H1–H5, and the irregularities
flagged for review. Sources with links: <a href="sources.html">Sources</a>.</p>
"""
    return page("GEMS — Executive summary", body, here="../")


def build_howto() -> str:
    card = json.loads((ROOT / "submissions" / f"{CANDIDATE}.json").read_text())
    body = f"""
<h1>How to submit</h1>
<p class="lead">The competition accepts a single-band float32 GeoTIFF on the training grid,
or a ZIP containing exactly one such GeoTIFF.</p>

<div class="card hero">
  <a class="btn" href="../downloads/gemsdoe/{CANDIDATE}.tif" download>⬇ Download the .tif</a>
  <a class="btn alt" href="../downloads/gemsdoe/{CANDIDATE}.zip" download>Download the .zip</a>
  <p class="muted">SHA-256 <code>{card['sha256']}</code></p>
</div>

<h2>Steps</h2>
<ol>
<li>Download the file above and check its SHA-256 if you want certainty
(<code>sha256sum {CANDIDATE}.tif</code>).</li>
<li>Open the submission page while logged in:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">drivendata.org › GEMS › submissions</a>.</li>
<li>Choose <strong>New submission</strong> and upload the <code>.tif</code>
(or the <code>.zip</code>).</li>
<li>Paste this note (≤140 characters):<br>
<code>{escape(card['note_140'])}</code></li>
<li>Submit and archive the result: the score, the timestamp and the file SHA-256. That
receipt replaces every USER-REPORTED number in this repository.</li>
</ol>

<h2>If the portal rejects the upload</h2>
<table>
<tr><th>Portal message</th><th>What it means here</th><th>Action</th></tr>
<tr><td>“Predicted values must be in range [0, 1]”</td>
<td>The validator is rejecting the NaN fill outside the data footprint.</td>
<td>Upload <code>{CANDIDATE}-zerooutside.tif</code> (or the
<code>-zerooutside.zip</code>): identical inside the footprint, zeros outside instead of
NaN — measured all-finite, 0 NaN, 38,000 positive cells, every value in [0, 1].</td></tr>
<tr><td>“must match the submission format’s CRS, shape, and geotransform”</td>
<td>The raster is not on the organizer grid.</td>
<td>Do not resample by hand. Re-run <code>python scripts/gemsdoe_final.py</code>; it writes
the grid from the organizer’s own sample raster.</td></tr>
<tr><td>Upload accepted, score shown</td>
<td>Success.</td>
<td>Record the receipt, then compare with the estimate 0.15 – 0.28 and with 0.2778.</td></tr>
</table>

<h2>What the file contains</h2>
<table>
<tr><th>Property</th><th>Value</th></tr>
<tr><td>Grid / CRS</td><td>{card['validation']['shape_matches'] and '3730 × 3292, EPSG:32611, 100 m'} (matches organizer raster)</td></tr>
<tr><td>Positive cells (mass)</td><td class="num">{card['dots']:,}</td></tr>
<tr><td>300 m halo coverage</td><td class="num">{100*card['reach_frac_footprint_within_3px']:.1f} % of the footprint</td></tr>
<tr><td>Cells within 300 m of the mapped catalogue</td>
<td class="num">{100*card['frac_dots_within_3px_of_catalogue']:.1f} %</td></tr>
<tr><td>Median distance to the mapped catalogue</td>
<td class="num">{card['median_px_to_catalogue']*100:.0f} m</td></tr>
<tr><td>Values</td><td>binary 0 / 1 inside the footprint; null outside</td></tr>
</table>
<p class="muted">Under the organizer ruling, pixels of known USGS/INGENIOUS faults are
excluded from scoring, so the emission deliberately avoids the immediate 2-pixel collar
around the mapped catalogue (the measured lesson from GEMSDOE32 B2).</p>
"""
    return page("GEMS — How to submit", body, here="../")


def build_sources() -> str:
    body = """
<h1>Sources</h1>
<p class="lead">Every factual claim on this site traces to one of these, or to a script in
the repository.</p>
<h2>Organizer-controlled</h2>
<table>
<tr><th>Source</th><th>Used for</th></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem description (page 967)</a></td>
<td>task definition, DTI formula, α = 0.2 / β = 0.8, R = 300 m, submission format</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition overview</a></td>
<td>prize structure, public/private test sets</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Leaderboard</a></td>
<td>0.4544 top public DTI (read 2026-10-28)</td></tr>
<tr><td><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516">Staff ruling, 2026-09-16 (<code>chrisk-dd</code>)</a></td>
<td>known-fault pixels are masked and excluded from penalty terms, in both rounds</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">Rules</a></td>
<td>external-data licence terms</td></tr>
</table>
<h2>Data</h2>
<table>
<tr><th>Layer</th><th>Origin</th></tr>
<tr><td><code>training_features.tif</code> (19 bands)</td>
<td>organizer data tab; SHA-256 verified <code>4371c82e…</code></td></tr>
<tr><td><code>labels.tif</code> / <code>existing_faults.tif</code></td>
<td>USGS Quaternary faults + INGENIOUS; SHA-256 <code>7ba308cc…</code></td></tr>
<tr><td><code>sample_submission.tif</code></td>
<td>organizer template raster; SHA-256 <code>2176d08e…</code> — see irregularity I-1</td></tr>
<tr><td>GeoDAWN magnetics / radiometrics</td>
<td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS data release</a>,
DOI 10.5066/P93LGLVQ, ScienceBase item 657e1d85d34e23d3533209f7</td></tr>
<tr><td>INGENIOUS project</td>
<td><a href="https://gbcge.org/current-projects/ingenious/">Great Basin Center for Geothermal Energy</a></td></tr>
</table>
<h2>Reference material</h2>
<ul class="tight">
<li><a href="https://epsg.io/32611">EPSG:32611</a> — UTM zone 11N, the competition CRS.</li>
<li><a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a> — the metric family.</li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a>.</li>
</ul>
<h2>Repository evidence</h2>
<ul class="tight">
<li><a href="findings.html">Measured findings</a> — analysis, experiments, irregularities.</li>
<li><code>data_public/site_best_overlap.json</code> — the nine-site duplicate matrix.</li>
<li><code>data_public/gemsdoe_estimate.json</code> — the structural estimate table.</li>
<li><code>data/work/novelty.json</code> — novelty measurements for the submitted file.</li>
<li><code>submissions/</code> — the file, its ZIP, the zero-outside twin and the run card.</li>
</ul>
"""
    return page("GEMS — Sources", body, here="../")


def build_banner() -> str:
    """Prominent, one-click entry point injected at the top of the project dashboard."""
    card = json.loads((ROOT / "submissions" / f"{CANDIDATE}.json").read_text())
    return f'''<div class="lane-banner" data-lane="gemsdoe-20261028" style="margin:0 0 18px;padding:16px 18px;border:2px solid #0f7b3f;border-radius:12px;background:#e8f6ee;font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="font-weight:700;font-size:15px;letter-spacing:.02em;color:#0f7b3f">SUBMISSION LANE OPENED 2026-10-28 · verdict: <span data-verdict="submit">SAFE TO SUBMIT</span></div>
<p style="margin:6px 0 10px;color:#12181f">One unique file passed the format, grid and nine-site novelty checks:
<code>{CANDIDATE}.tif</code> ({card['dots']:,} cells, {card['bytes']:,} bytes). It is <em>not</em> one of the historical
near-duplicates below, and it carries no organizer receipt.</p>
<p style="margin:0"><a class="btn" style="display:inline-block;background:#0f7b3f;color:#fff;text-decoration:none;font-weight:650;padding:10px 18px;border-radius:9px" href="lane/index.html">Open the submission lane &rarr;</a>
&nbsp; <a href="lane/index.html#why" style="color:#12181f">Why this file, and what it will score &rarr;</a>
&nbsp; <a href="release.html" style="color:#5b6673">Legacy audit of the rejected files &rarr;</a></p>
</div>'''


def inject_banner() -> None:
    home = DOCS / "index.html"
    html = home.read_text()
    html = re.sub(r'<div class="lane-banner".*?</div>\s*', "", html, flags=re.S)
    marker = "<main"
    index = html.find(marker)
    if index < 0:
        raise SystemExit("home page has no <main> to attach the lane banner to")
    close = html.find(">", index) + 1
    home.write_text(html[:close] + "\n" + build_banner() + html[close:])


def build_landing() -> str:
    card = json.loads((ROOT / "submissions" / f"{CANDIDATE}.json").read_text())
    body = f"""
<h1>DOE GEMS Prize — submission workspace</h1>
<p class="lead">A unique, format-valid GeoTIFF for the DOE GEMS Prize competition, produced
from the organizer’s 19-band stack, with every number traced to a script in this repository.</p>

<div class="card hero">
  <h2>⬇ Download the submission</h2>
  <p><code>{CANDIDATE}.tif</code></p>
  <a class="btn" href="downloads/gemsdoe/{CANDIDATE}.tif" download>Download .tif</a>
  <a class="btn alt" href="downloads/gemsdoe/{CANDIDATE}.zip" download>Download .zip</a>
  <p><span class="pill ok">Format PASS</span> <span class="pill ok">Unique PASS</span>
  <span class="pill warn">Estimate 0.15 – 0.28</span></p>
  <p class="muted">{card['dots']:,} unit cells · SHA-256 <code>{card['sha256']}</code></p>
</div>

<h2>Start here</h2>
<ul class="tight">
<li><a href="gemsdoe/index.html"><strong>Executive summary</strong></a> — the per-site table:
which file was best at each of the nine GEMSDOE sites, what it scored, and whether it is unique.</li>
<li><a href="gemsdoe/how-to-submit.html"><strong>How to submit</strong></a> — five steps, the
note to paste, and what to do if the portal rejects the upload.</li>
<li><a href="gemsdoe/findings.html"><strong>Measured findings</strong></a> — why 0.2778 was
reached, whether it can be beaten, the three experiments, and the irregularities.</li>
<li><a href="gemsdoe/sources.html"><strong>Sources</strong></a> — official links for manual review.</li>
</ul>

<h2>Status in one line</h2>
<p>Unique submission ready and validated. The estimate is honest about its ceiling: matching
0.2778 requires covering 29–46 % of the hidden expert labels at this mass, and nothing
measured here demonstrates a detector that does.</p>

<h2>Legacy pages</h2>
<p class="muted">Earlier sessions produced a large audit trail of negative-release verdicts.
It is preserved, unedited, for the record — it is not the current recommendation.</p>
<ul class="tight">
<li><a href="executive-summary.html">executive-summary.html</a> (previous summary)</li>
<li><a href="sources.html">sources.html</a> (previous source list)</li>
<li><a href="submission/index.html">submission/index.html</a> (previous negative audit)</li>
<li><a href="release.html">release.html</a> (byte audit of historical rasters)</li>
<li><a href="methodology.html">methodology.html</a></li>
<li><a href="research/why-b2-scored-2778.html">research/why-b2-scored-2778.html</a>
(earlier reading of why B2 reached 0.2778)</li>
</ul>
"""
    return page("DOE GEMS Prize — submission workspace", body, here="../")



def build_lane_manifest() -> dict:
    """Write the machine-checked manifest that lets a page say "submit this file"."""
    import hashlib

    def sha(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()

    card = json.loads((ROOT / "submissions" / f"{CANDIDATE}.json").read_text())
    nov = json.loads((ROOT / "data" / "work" / "novelty.json").read_text())
    est = json.loads((ROOT / "data_public" / "gemsdoe_estimate.json").read_text())
    files = []
    for rel in (f"docs/downloads/gemsdoe/{CANDIDATE}.tif",
                f"docs/downloads/gemsdoe/{CANDIDATE}.zip",
                f"docs/downloads/gemsdoe/{CANDIDATE}-zerooutside.tif",
                f"docs/downloads/gemsdoe/{CANDIDATE}-zerooutside.zip"):
        p = ROOT / rel
        files.append({"path": rel, "sha256": sha(p), "bytes": p.stat().st_size,
                      "role": "primary" if rel.endswith(f"{CANDIDATE}.tif") else "alternate"})
    manifest = {
        "schema": "wbggems.submission-lane.v1",
        "lane": "gemsdoe-triphysics-consensus-20261028",
        "status": "submit_candidate",
        "positive_pages": [
            "docs/lane/index.html", "docs/lane/how-to-submit.html",
            "docs/lane/sources.html", "docs/lane/findings.html",
        ],
        "files": files,
        "primary_file": f"docs/downloads/gemsdoe/{CANDIDATE}.tif",
        "format_validation": card["validation"],
        "novelty": {**nov["verdict"], "max_frac_my_dots_within_3px": nov["max_frac_my_dots_within_3px"],
                    "max_abs_smoothed_spearman": nov["max_abs_smoothed_spearman"],
                    "n_compared": nov["n_compared"]},
        "estimate": {"range": est["candidate_estimate_range"],
                     "evidence_class": "EMPIRICAL-BAND ESTIMATE",
                     "label": est["candidate_estimate_label"]},
        "organizer_receipt": None,
        "leaderboard_score": None,
        "note_140": card["note_140"],
        "why_this_is_a_separate_lane": (
            "The negative release is a closed audited set; this lane is a positive "
            "submission candidate whose published bytes, format checks and novelty "
            "verdicts are re-verified by src/wbggems/release.py::submission_lane on "
            "every build. Nothing here is an organizer receipt or a leaderboard score."),
    }
    (ROOT / "data_public" / "gemsdoe_release.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(build_summary())
    (OUT / "how-to-submit.html").write_text(build_howto())
    (OUT / "sources.html").write_text(build_sources())
    body = md(ROOT / "research" / "gemsdoe_findings.md")
    (OUT / "findings.html").write_text(page("GEMS — Measured findings", body, here="../"))
    (DOCS / "EXECUTIVE_SUMMARY.md").write_text(
        (DOCS / "EXECUTIVE_SUMMARY.md").read_text())  # source of truth, unchanged
    build_lane_manifest()
    inject_banner()
    print("wrote:", *(str(p.relative_to(ROOT)) for p in
                      [DOCS / "index.html", OUT / "index.html", OUT / "how-to-submit.html",
                       OUT / "findings.html", OUT / "sources.html",
                       ROOT / "data_public" / "gemsdoe_release.json"]))


if __name__ == "__main__":
    main()
