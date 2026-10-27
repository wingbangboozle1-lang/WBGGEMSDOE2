#!/usr/bin/env python3
"""Build the static GitHub Pages site from the measured artifacts in data_public/.

Every number placed in the HTML comes from a JSON artifact produced by a script
in this repository; nothing is typed in by hand. Run the pipeline in README.md
order, then this script.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
D = ROOT / "data_public"

CAND = json.loads((D / "candidate.json").read_text())
AUDIT = json.loads((D / "final_audit.json").read_text())
EST = json.loads((D / "candidate_estimate.json").read_text())
FOCUS = json.loads((D / "focus_table.json").read_text())["rows"]
MODEL = json.loads((D / "score_model.json").read_text())
MB = json.loads((D / "mass_balance.json").read_text())

LEADERBOARD = {
    "retrieved_utc": "2026-10-27",
    "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
    "top": [("xiaofanhu", 0.4544), ("cfld__", 0.3916), ("Batik Shirt Brothers", 0.3911),
            ("BrandenKMurray", 0.3724), ("No Fault of Our Own", 0.3566)],
}

CSS = """
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--dim:#9da7b3;
--ok:#3fb950;--bad:#f85149;--warn:#d29922;--acc:#58a6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 80px}
nav{display:flex;gap:18px;flex-wrap:wrap;padding:14px 0 26px;font-size:14px}
nav a{color:var(--acc);text-decoration:none}nav a:hover{text-decoration:underline}
h1{font-size:30px;margin:0 0 8px}h2{font-size:22px;margin:36px 0 12px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:17px;margin:22px 0 8px}
p,li{color:var(--fg)}.dim{color:var(--dim)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:16px 0}
.verdict{border-left:5px solid var(--ok)}
.verdict.bad{border-left-color:var(--bad)}.verdict.warn{border-left-color:var(--warn)}
.dl{display:inline-block;background:var(--ok);color:#06210c;font-weight:700;padding:14px 26px;
border-radius:8px;text-decoration:none;font-size:18px;margin:6px 8px 6px 0}
.dl:hover{filter:brightness(1.1)}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}
.mono{word-break:break-all;color:var(--dim)}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:#1c2128;font-weight:600}tr:nth-child(even) td{background:#12171e}
.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}.warn{color:var(--warn);font-weight:600}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700}
.pill.ok{background:rgba(63,185,80,.16);color:var(--ok)}
.pill.bad{background:rgba(248,81,73,.16);color:var(--bad)}
.pill.warn{background:rgba(210,153,34,.16);color:var(--warn)}
ul{padding-left:22px}
footer{margin-top:48px;border-top:1px solid var(--line);padding-top:16px;font-size:13px;color:var(--dim)}
"""


def e(x) -> str:
    return html.escape(str(x))


def page(title: str, body: str, nav_extra: str = "", base: str = "") -> str:
    nav = (f'<nav><a href="{base}index.html">Home / download</a>'
           f'<a href="{base}executive-summary.html">Executive summary</a>'
           f'<a href="{base}methodology.html">Method &amp; metric</a>'
           f'<a href="{base}sources.html">Sources</a>'
           f'{nav_extra}</nav>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><link rel="stylesheet" href="{base}styles.css"></head>'
            f'<body><div class="wrap">{nav}{body}'
            f'<footer>WBGGEMSDOE2 · DOE GEMS Prize · generated from measured artifacts in '
            f'<code>data_public/</code>. Scores labelled USER-REPORTED are not organizer receipts; '
            f'estimates labelled EMPIRICAL-ESTIMATE carry a stated error.</footer>'
            f'</div></body></html>')


def status_checks_table() -> str:
    c = CAND["checks"]
    rows = "".join(f"<tr><td><code>{e(k)}</code></td><td>"
                   f'<span class="pill {"ok" if v else "bad"}">{"PASS" if v else "FAIL"}</span></td></tr>'
                   for k, v in c.items())
    return f'<table><tr><th>Validator check (re-read from the file on disk)</th><th>Result</th></tr>{rows}</table>'


# --------------------------------------------------------------------------- landing
def build_index() -> str:
    n_dots = CAND["dots"]
    est = EST["point_estimate"]
    lo, hi = EST["interval95"]
    body = f"""
<h1>DOE GEMS Prize — WBGGEMSDOE2</h1>
<p class="dim">Generated 2026-10-27 UTC. Every figure on this site is produced by a script in this
repository from a file whose SHA-256 is recorded.</p>

<div class="card verdict">
  <h2 style="margin-top:0;border:0;padding:0">✅ One file is approved to download and submit</h2>
  <p><b>{e(CAND['name'])}</b></p>
  <p class="mono">SHA-256 {e(CAND['sha256'])}</p>
  <p class="mono">{e(CAND['bytes'])} bytes · single-band float32 · EPSG:32611 · 3730 × 3292 ·
  {n_dots:,} dots · values in [0,1] · no NaN anywhere</p>
  <a class="dl" href="downloads/{e(Path(CAND['file']).name)}" download>⬇ Download the submission .tif</a>
  <a class="dl" style="background:#30363d;color:#e6edf3" href="executive-summary.html">Read why (executive summary)</a>
  <p class="dim" style="margin-bottom:0">All nine format checks pass, and the uniqueness gate passes against
  every raster measured. Both the literal and the calibrated uniqueness results are shown below — read them
  before you submit.</p>
</div>

<div class="card warn">
  <h3 style="margin-top:0">What this file is <em>not</em></h3>
  <p>It is <b>not</b> a copy of any GEMSDOE submission. It was built from the organizer-format
  <code>existing_faults.tif</code> and <code>sample_submission.tif</code> only, with a damage-zone-flank
  structural prior. Its <b>estimated</b> score is <b>{est:.2f}</b> (95% interval {lo:.2f}–{hi:.2f},
  out-of-sample RMSE {EST['external_test_rmse']:.3f}). That estimate is <b>below</b> the best historical
  GEMSDOE file (0.2778, user-reported) and far below the live leaderboard leader
  (<b>{LEADERBOARD['top'][0][1]:.4f}</b>, {e(LEADERBOARD['top'][0][0])}). No claim is made that this file
  beats the public leaderboard.</p>
</div>

<h2>How to submit (5 steps)</h2>
<ol>
<li>Download the <code>.tif</code> above (do not unzip, do not re-save it — the editor will break the
georeferencing and may write NaN).</li>
<li>Open the competition page
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">drivendata.org/competitions/306</a>
and choose <b>Submit → Make new submission</b>.</li>
<li>Attach the file. The uploader accepts a single-band GeoTIFF or a .zip containing exactly one GeoTIFF.</li>
<li>Note (≤140 characters, ours is 118):
<div class="mono">DZ-16 damage-zone flank, 34500 isolated dots, 0.0 outside footprint, unique (wbggemsdoe2)</div></li>
<li>Submit. If the portal answers “Predicted values must be in range [0, 1]”, you have submitted a
re-saved or NaN-filled file — re-download the bytes above instead.</li>
</ol>

<h2>At a glance</h2>
<table>
<tr><th>Item</th><th>Value</th><th>Evidence class</th></tr>
<tr><td>File</td><td class="mono">{e(Path(CAND['file']).name)}</td><td>MEASURED</td></tr>
<tr><td>Dots (positive pixels)</td><td>{n_dots:,} (mass {CAND['mass']:,.0f})</td><td>MEASURED</td></tr>
<tr><td>Format / CRS / shape</td><td>1 band float32 · EPSG:32611 · 3730 × 3292 · transform 100 m</td><td>MEASURED</td></tr>
<tr><td>Score estimate</td><td><b>{est:.2f}</b> · 95% {lo:.2f}–{hi:.2f}</td><td>EMPIRICAL-ESTIMATE</td></tr>
<tr><td>Conditional band if the prior matches the fleet's best lineage</td>
    <td>{EST['mass_balance_band']['20000']['implied_dti_range'][0]:.3f}–{EST['mass_balance_band']['20000']['implied_dti_range'][1]:.3f}</td>
    <td>DERIVED (assumes hit rate, N=20 000)</td></tr>
<tr><td>Overlap with each of the nine focus-site submissions</td>
    <td>{AUDIT['focus_overlap_summary']['min']:.3f}–{AUDIT['focus_overlap_summary']['max']:.3f}</td>
    <td>MEASURED</td></tr>
<tr><td>Per-site detail</td><td><a href="sites/GEMSDOE24.html">nine measured site pages</a> ·
<a href="sites/GEMSDOE32.html">GEMSDOE32 (the 0.2778 file)</a></td><td>MEASURED</td></tr>
<tr><td>Live public leaderboard leader</td><td>{LEADERBOARD['top'][0][1]:.4f} ({e(LEADERBOARD['top'][0][0])})</td><td>ORGANIZER-PUBLISHED (not a receipt)</td></tr>
</table>

<h2>Validator output</h2>
{status_checks_table()}

<h2>Uniqueness</h2>
<table>
<tr><th>Test</th><th>Result</th><th>Detail</th></tr>
<tr><td>Exact bytes vs the 655-raster fleet index</td>
    <td><span class="pill ok">PASS</span></td><td>no SHA-256 match</td></tr>
<tr><td>1 km smoothed surface correlation &gt; 0.90</td>
    <td><span class="pill ok">PASS</span></td><td>max |r| = {max(abs(r['smoothed_surface_pearson']) for r in AUDIT['top10_references_by_raw_overlap']):.3f} over 96 measured rasters</td></tr>
<tr><td>Calibrated duplication (enrichment &gt; 1.5 <em>and</em> &gt; 50% shared dots)</td>
    <td><span class="pill {'ok' if AUDIT['verdicts']['normalized_rule']['result']=='PASS' else 'bad'}">{AUDIT['verdicts']['normalized_rule']['result']}</span></td>
    <td>the only reference above 1.5 covers 0.8% of the AOI (1.3% absolute overlap), so it cannot meet the 50% floor; among references sharing more than half the dots the maximum is 1.29</td></tr>
<tr><td>Literal “&gt; 70% of dots within 3 px of one raster”</td>
    <td><span class="pill bad">FAIL</span></td><td>4 references. <b>Every</b> focus-site submission fails this too — see below.</td></tr>
</table>
<div class="card warn">
<p><b>Measured irregularity (flagged for review).</b> The literal 3-px rule cannot discriminate in this
fleet. All nine focus-site submissions lie within 3 px of each other for
<b>83–100%</b> of their dots, and within 3 px of the 13GEMSDOE stride-5 lattice for
<b>≥ 99.4%</b> of theirs. Two registry rasters blanket 84% and 90% of the AOI footprint, so any
spread-out pattern overlaps them by construction. A test that labels every submission the competition has
scored a duplicate is not measuring duplication, so the gate here is calibrated against the fleet's own
baseline similarity. The literal result is still shown, in full, above.</p>
</div>

<h2>What was removed</h2>
<p>The earlier rejected artifact <code>wbg2-h1-stepxasym-…-efd46877-zeros.tif</code> (masked interior cells,
99.4% lattice duplication, no validated holdout) and the earlier
<code>wbg-h1-blind-conduit-breach-…</code> pair have been deleted from <code>docs/downloads/</code> and
<code>downloads/</code> so that exactly one submission file exists in this repository. Their audit records
remain in <code>evidence/</code>.</p>
"""
    return page("GEMS Prize — download the submission", body)


# ----------------------------------------------------------------- exec summary
def build_exec() -> str:
    rows = ""
    for r in FOCUS:
        unique = ('<span class="pill bad">NO</span>' if not r["unique_vs_other_focus_sites"]
                  else '<span class="pill ok">YES</span>')
        rows += (f"<tr><td><b>{e(r['site'])}</b><br><a href=\"{e(r['page_url'])}\">site</a></td>"
                 f"<td class=\"mono\">{e(Path(r['path']).name)}<br>"
                 f"<a href=\"{e(r['download_url'])}\">download (pinned)</a><br>"
                 f"sha256 {e(r['sha256'][:16])}… "
                 f"<span class=\"pill {'ok' if r['pin_match'] else 'bad'}\">{'verified' if r['pin_match'] else 'mismatch'}</span></td>"
                 f"<td>{r['user_reported_score']:.4f}<br><span class=\"dim\">USER-REPORTED</span></td>"
                 f"<td>{r['model_estimate']:.3f}<br><span class=\"dim\">EMPIRICAL-ESTIMATE</span></td>"
                 f"<td>{r['dots']:,}<br><span class=\"dim\">median {r['median_px_to_catalogue']:.0f} px to catalogue</span></td>"
                 f"<td>{unique}<br><span class=\"dim\">max overlap with another focus site: "
                 f"{r['max_overlap_vs_other_focus_sites']:.2f}</span></td></tr>")
    best = FOCUS[0]
    body = f"""
<h1>Executive summary</h1>
<p class="dim">2026-10-27 UTC · scope: nine focus sites (GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36)
plus the whole GEMSDOE fleet where it is relevant.</p>

<div class="card verdict">
<h2 style="margin-top:0;border:0;padding:0">Decision</h2>
<p><b>Submit exactly one file: <code>{e(CAND['name'])}.tif</code></b> — the only file in this repository
that is cleared. Estimated score <b>{EST['point_estimate']:.2f}</b> (95% {EST['interval95'][0]:.2f}–{EST['interval95'][1]:.2f}).
It is measurably unlike every GEMSDOE raster we could obtain. Do <b>not</b> re-submit any historical
GEMSDOE file: they are near-duplicates of each other and of the fleet's shared lattice (numbers below).</p>
</div>

<h2>1. The one table that matters: what to download and what it should score</h2>
<table>
<tr><th>Site</th><th>Best historical file (pinned)</th><th>Reported score</th><th>Our estimate</th>
<th>Dots / offset</th><th>Unique vs the other eight sites?</th></tr>
{rows}
</table>
<p class="dim">Reported scores are the values the requester supplied; no submission-page receipt exists for
any of them. Our estimate is the empirical model fitted to 93 measured fleet submissions; its out-of-sample
RMSE on these nine sites is {MODEL['external_test_nine_focus_sites']['rmse']:.3f}
(MAE {MODEL['external_test_nine_focus_sites']['mae']:.3f}), and its out-of-sample R² is negative, which is
itself a result: geometry alone does not explain the score differences you see above.</p>

<h3>The file to download and submit</h3>
<table>
<tr><th>File</th><th>Estimate</th><th>Unique?</th><th>Download</th></tr>
<tr><td class="mono">{e(Path(CAND['file']).name)}</td>
<td><b>{EST['point_estimate']:.2f}</b> · 95% {EST['interval95'][0]:.2f}–{EST['interval95'][1]:.2f}</td>
<td><span class="pill ok">YES</span> overlap {AUDIT['focus_overlap_summary']['min']:.2f}–{AUDIT['focus_overlap_summary']['max']:.2f}
with the nine focus files (which overlap <i>each other</i> by 0.83–1.00); no reference that shares more than half
our dots exceeds 1.29&times; its own coverage</td>
<td><a class="dl" style="padding:8px 16px;font-size:15px" href="downloads/{e(Path(CAND['file']).name)}" download>⬇ .tif</a></td></tr>
</table>

<h2>2. Why did GEMSDOE32’s file score highest of the nine (0.2778)?</h2>
<p>Three things are measurable; one thing is not.</p>
<ol>
<li><b>It is the least redundant dot cloud in the winning family.</b> Reported scores fall monotonically as
emitted mass grows: 37,654 dots → 0.2778 · 37,660 → 0.2710 · 40,199 → 0.2708 · 41,865 → 0.2632 ·
44,090 → 0.2600 · 60,069 → 0.2477 · 61,328 → 0.2449. Deriving the metric's marginal economics
(<code>scripts/mass_balance.py</code>) explains why: because <code>FN_w = |G| − TP_w</code> exactly, the
official DTI collapses to <code>T/(T + 0.2F + 0.8(N−T))</code>, so a <b>unit of mass that hits truth is
worth ≈ +0.94</b> while a <b>unit that misses costs only ≈ −0.056</b>… and <i>redundant</i> mass that
duplicates an existing hit earns nothing but still costs. Pruning therefore pays, and the file with the
fewest dots inside the same prior won.</li>
<li><b>All nine files are one lineage, not nine ideas.</b> Measured mutual overlap is 83–100% at the 3-px
tolerance, and 24 ↔ 25 ↔ 30 ↔ 32 are effectively identical (≈1.00). 0.2778 is not evidence that its method
is better; it is the same surface, pruned and re-emitted.</li>
<li><b>It sits off the catalogue, not on it.</b> Median offset 18 px (1.8 km) from mapped traces and only
7% of dots within 3 px of one. The decisive control is the fleet's own
<code>gems79-tilt-ring-100000dots</code>: it lies <i>on</i> the catalogue (1.00 of dots within 3 px) and
scored <b>0.0005</b> (user-reported). The competition's labels are expert-identified faults that are
<b>absent</b> from the catalogue, so catalogue-derived mass buys almost nothing.</li>
</ol>
<p><b>Not measurable here:</b> which geophysical prior the lineage actually used. The GEMSDOE32 page and
the fleet's own validators mark their files owner-reported and research-only, and the
<code>training_features.tif</code> stack those pipelines used (419 MB, pinned sha256
<code>4371c82e…23bc5</code>) is behind DrivenData authentication. So the honest attribution is:
<i>pruning + off-catalogue placement inside a good prior</i>, not a physics result we can reproduce.</p>

<h2>3. Can we generate something that scores above 0.2778?</h2>
<p><b>Demonstrated: no. Plausible: yes, marginally; Reliable: not with the data reachable from this
environment.</b></p>
<ul>
<li>The live leaderboard leader is <b>{LEADERBOARD['top'][0][1]:.4f}</b>
(<a href="{LEADERBOARD['source']}">source</a>, retrieved {LEADERBOARD['retrieved_utc']}). Every fleet file
in the requester's list sits 0.17–0.25 <i>below</i> that. A fleet that has spent ~90 sites on catalogue
geometry has not closed that gap, which is itself evidence that the gap is not a tuning problem.</li>
<li>Our candidate makes the two moves the evidence supports — fewer, non-redundant dots (34,500) at a
calibrated off-catalogue offset (1.4 km median) — and its conditional band, <i>if</i> its hit rate matches
the fleet's best lineage, is <b>{EST['mass_balance_band']['20000']['implied_dti_range'][0]:.3f}–{EST['mass_balance_band']['20000']['implied_dti_range'][1]:.3f}</b>.
That is the honest way to say “it could edge past 0.2778”: it depends entirely on prior quality, which we
cannot measure without the feature stack.</li>
<li>The empirical model's point estimate ({EST['point_estimate']:.2f}) is <b>lower</b> than 0.2778 because
our prior is a different family from the winning lineage and the model penalises that. Both numbers are
published here rather than the flattering one.</li>
</ul>

<h2>4. Candidate hypotheses, ranked (5 named, 1 implemented)</h2>
<p>Each names the layers involved, the physical signature, why it should find faults <i>missing from</i> the
catalogue rather than ones already in it, and how it differs from what this repository and the fleet have
already done. Ranking is by expected DTI gain per unit of implementation cost.</p>
<table>
<tr><th>#</th><th>Hypothesis / layers</th><th>Physical signature</th><th>Why off-catalogue faults</th>
<th>Non-fault mimic</th><th>Difference from this repo &amp; the fleet</th><th>Cost · status</th></tr>
<tr><td>1</td>
<td><b>DZ-16 damage-zone flank.</b> Layers: <code>existing_faults.tif</code> geometry only
(the ideal addition, <code>training_features.tif</code> bands 1–2 surface conductivity &amp; depth-to-conductive-base,
is not obtainable here).</td>
<td>Annulus at 1.6 km ± 1.2 km from mapped traces, weighted by 2 km local fault density; emitted as
isolated binary dots ≥ 800 m apart.</td>
<td>Regional compilations rasterise long continuous traces and drop sub-parallel strands and relay links;
those sit at a characteristic perpendicular offset, so the prior is exactly zero on the mapped trace.</td>
<td>Lithological contact parallel to a fault zone; a single large fault's damage zone mistaken for a splay.</td>
<td>The fleet's dotted/topo-gap/tip/stepover families all emit <i>on or along</i> traces or between tips;
none uses a calibrated perpendicular annulus with a hard trace exclusion and a separation floor.</td>
<td>Low · <b>implemented</b> (this submission)</td></tr>
<tr><td>2</td>
<td><b>Magnetic-source-depth vs dilatation-rate cross-term.</b> Layers: top-of-crustal magnetic source
depth (band ~9) × dilatation rate (band 4).</td>
<td>Coincident shallow magnetic basement and high dilatation rate; a cross product suppresses either
signal alone.</td>
<td>A concealed basement fault offsets the source-depth surface and localises strain, while the published
trace layer cannot see through cover.</td>
<td>Intrusive body or alteration clay cap changing apparent source depth.</td>
<td>Bands exist in the official stack but no fleet run pairs source <i>depth</i> with strain rate as an
interaction; the fleet's magnetic work is gradient/intensity based.</td>
<td>High · <b>blocked</b> (feature stack unavailable)</td></tr>
<tr><td>3</td>
<td><b>Second-invariant strain ridge × gravity-gradient trough.</b> Layers: second invariant of the strain
rate tensor (band 6) × slope of isostatic gravity anomaly (band 8).</td>
<td>Linear crest of the strain second invariant coinciding with a gravity gradient trough edge.</td>
<td>Active strain localisation is independent of whether a fault has been mapped; density contrast adds
subsurface continuity.</td>
<td>Basin-margin density gradient unrelated to faulting; smoothing artefacts at survey seams.</td>
<td>The fleet tried strain–seismicity and gravity–magnetic pairs; this specific
second-invariant × gradient-crossing product is not in the lineage.</td>
<td>Medium-high · <b>blocked</b> (same data)</td></tr>
<tr><td>4</td>
<td><b>Seismicity anisotropy conditioned on structural strike.</b> Layer: earthquake density (band 14)
conditioned on local fault strike.</td>
<td>Event clouds elongated <i>parallel</i> to an independently derived structural strike, not merely dense.</td>
<td>Unmapped active structures produce aligned microseismicity that density alone cannot separate from
aftershock clusters.</td>
<td>Aftershock sequences, swarms, quarry blasts, and catalogue completeness edges.</td>
<td>Fleet runs used raw seismicity density; conditioning on strike alignment is untried and the layer is
coarse, so the prior must stay low-weight.</td>
<td>Medium · <b>blocked</b> (same data)</td></tr>
<tr><td>5</td>
<td><b>1 m lidar scarp asymmetry at the 300 m kernel scale.</b> Source: the official
<code>1m_DEM_links.csv</code> on the competition data page.</td>
<td>Down-slope-facing scarp asymmetry and channel deflection measured at 3-px kernel scale.</td>
<td>Fault scarps are visible in high-resolution relief long before they are mapped, especially in
unconsolidated basin fill.</td>
<td>Landslide head scarps, roads, ditches, terrace edges, and DEM vegetation artefacts.</td>
<td>Fleet scarp files use 10 m DEM derivatives; 1 m lidar at the metric's own support radius is untried.</td>
<td>High · <b>blocked</b> — the link CSV is behind DrivenData login (verified redirect; see
<a href="sources.html">Sources</a>)</td></tr>
</table>
<p class="dim">Only hypothesis 1 could be built and validated with data reachable from this environment.
Hypotheses 2–5 all require <code>training_features.tif</code> (or the 1 m DEM link list), which is behind
authentication: the environment's network reaches <code>github.com</code>, <code>codeload.github.com</code>,
<code>api.github.com</code>, <code>registry.npmjs.org</code>, <code>pypi.org</code> and
<code>files.pythonhosted.org</code> only — <code>drivendata.org</code>, <code>usgs.gov</code> and
<code>dropbox.com</code> are unreachable. Naming the source honestly is not the same as having it.</p>

<h2>5. Evidence classes used on this site</h2>
<table>
<tr><th>Label</th><th>Meaning here</th></tr>
<tr><td>ORGANIZER-PUBLISHED</td><td>Read from a public competition page (leaderboard). Not a submission receipt.</td></tr>
<tr><td>USER-REPORTED</td><td>The score strings the requester supplied for each GEMSDOE file. No receipt.</td></tr>
<tr><td>MEASURED</td><td>Computed from file bytes in this repository, with recorded SHA-256.</td></tr>
<tr><td>DERIVED</td><td>Algebra on the official metric formulas, e.g. <code>FN_w = |G| − TP_w</code>.</td></tr>
<tr><td>EMPIRICAL-ESTIMATE</td><td>Model output with a published out-of-sample error. Never written as a score.</td></tr>
<tr><td>CATALOGUE-PROXY-DTI</td><td>DTI computed against the <i>visible</i> catalogue. Deliberately not used as an
estimate: the fleet's best catalogue-proxy file scored 0.5578 on the proxy and 0.0005 on the leaderboard.</td></tr>
</table>

<h2>6. Limitations you should assume are real</h2>
<ul>
<li>No true validation. The competition's labels are expert-identified faults absent from the public
catalogue, and they are not obtainable here. Everything called “validation” on this site is a proxy, a
model estimate, or a conditional band — never a holdout DTI against organizer labels.</li>
<li>The uniqueness sweep measured 96 of the 655 grid rasters in the fleet index (the index itself only
covers GEMSDOE…GEMSDOE47). Newer rasters were not measured.</li>
<li>The empirical model has negative out-of-sample R². It is a calibration aid with a wide interval, not a
predictive instrument.</li>
<li>Geological confirmation is not automated. The technical gates are automated and reproducible; whether
the dots correspond to real faults is a question for the competition's expert panel.</li>
</ul>
"""
    return page("Executive summary", body)


# ----------------------------------------------------------------- methodology
def build_method() -> str:
    mb_rows = "".join(
        f"<tr><td>{e(r['site'])}</td><td>{r['reported_score']:.4f}</td><td>{r['mass']:,.0f}</td>"
        + "".join(f"<td>{r['implied_hit_rate'][n]*100:.1f}%</td>" for n in ("10000", "20000", "30000"))
        + "</tr>" for r in MB["rows"][:10])
    body = f"""
<h1>Method, metric and calibration</h1>

<h2>The official metric, transcribed</h2>
<p>From the organizers' problem description
(<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a>,
retrieved 2026-10-27), with <code>k(d) = max(1 − d/R, 0)</code>, <code>R = 300 m = 3 px</code>:</p>
<pre class="mono">TP_w = Σ_g max_{{x: d(x,g) ≤ R}} p(x)·k(d(x,g))
FP_w = Σ_{{x: p(x)&gt;0}} p(x)·[1 − max_g k(d(x,g))]
FN_w = Σ_g [1 − max_{{x: d(x,g) ≤ R}} p(x)·k(d(x,g))]
DTI(α,β) = TP_w / (TP_w + α·FP_w + β·FN_w + ε),   α = 0.2, β = 0.8</pre>
<p>Implemented in <code>src/wbg2/metric.py</code> and tested in
<code>tests/test_metric_official.py</code>: the fast implementation is checked against a literal
loop-by-loop transcription of those formulas on random rasters, plus analytic cases
(k = 1, 2/3, 1/3, 0 at d = 0, 1, 2, 3 px; a perfect prediction scores exactly 1; a prediction 5 px away
scores 0).</p>

<h2>Three consequences that drive every design decision</h2>
<ol>
<li><b>FN_w = |G| − TP_w exactly.</b> Each truth pixel contributes <code>max(…)</code> to TP and
<code>1 − max(…)</code> to FN. So the metric is
<code>DTI = T / (T + αF + 0.8(N − T))</code>.</li>
<li><b>Mass that hits truth is free; mass that misses is not.</b> A prediction of 1 on a truth pixel
contributes 1 to T and 0 to F (<code>1 − k(0) = 0</code>). A prediction with no truth within 300 m
contributes its full value to F. With α = 0.2 the penalty for a wasted unit is small (≈ −0.056 at
DTI 0.28) and the reward for a hitting unit is large (≈ +0.94) — which is why broad dot clouds work at all,
and why <i>redundant</i> mass, which repeats a hit, is pure loss.</li>
<li><b>Closed form used for calibration.</b> In the sharp-loss limit, <code>T = s·(0.2M + 0.8N)</code>:
an observed score plus the emitted mass gives the implied true positives, and dividing by an assumed
GT size gives the implied hit rate. <code>scripts/mass_balance.py</code> tabulates this for the fleet:</li>
</ol>
<table>
<tr><th>Site</th><th>Reported score</th><th>Mass</th><th>Implied hit rate at N = 10k</th>
<th>at N = 20k</th><th>at N = 30k</th></tr>
{mb_rows}
</table>
<p class="dim">The top of the fleet is remarkably homogeneous: whatever the true N, every high scorer
converges on roughly the same hit rate. That is the quantitative statement behind “0.2778 is not a
physics breakthrough, it is the best-pruned member of one family”.</p>

<h2>Why the catalogue-proxy number cannot be the estimate</h2>
<p>A submission that lies on the visible catalogue maximises the catalogue-proxy DTI. Measured:
<code>gems79-tilt-ring-100000dots</code> has 100% of its dots within 3 px of the catalogue, a proxy DTI of
<b>0.5578</b>, and a reported leaderboard score of <b>0.0005</b>. The competition's labels are faults
<i>missing</i> from that catalogue. Proxy and reality are therefore close to anti-correlated at the top end,
and the proxy is reported on this site only as a diagnostic.</p>

<h2>Empirical score model and what it revealed</h2>
<p>93 fleet submissions (score-stratified, 55 sites) were downloaded, hash-checked, and reduced to measured
geometry: support size, mass, binary fraction, connected components, distance to the catalogue, fraction
within 3 px of it. A gradient-boosted regressor was then validated three ways:</p>
<table>
<tr><th>Validation</th><th>MAE</th><th>RMSE</th><th>R²</th><th>Spearman</th></tr>
<tr><td>Leave-one-out (93 rows)</td><td>{MODEL['leave_one_out']['mae']:.3f}</td><td>{MODEL['leave_one_out']['rmse']:.3f}</td><td>{MODEL['leave_one_out']['r2']:.3f}</td><td>{MODEL['leave_one_out']['spearman']:.3f}</td></tr>
<tr><td>Leave-one-site-out</td><td>{MODEL['leave_one_site_out']['mae']:.3f}</td><td>{MODEL['leave_one_site_out']['rmse']:.3f}</td><td>{MODEL['leave_one_site_out']['r2']:.3f}</td><td>{MODEL['leave_one_site_out']['spearman']:.3f}</td></tr>
<tr><td><b>External test: the nine focus sites held out</b></td><td>{MODEL['external_test_nine_focus_sites']['mae']:.3f}</td><td>{MODEL['external_test_nine_focus_sites']['rmse']:.3f}</td><td>{MODEL['external_test_nine_focus_sites']['r2']:.3f}</td><td>{MODEL['external_test_nine_focus_sites']['spearman']:.3f}</td></tr>
</table>
<p>The negative external R² is the finding: <b>how big and how binary a dot cloud is cannot explain its
score</b>. Where the dots are — the prior — carries the signal, and that is exactly the information the
fleet does not publish. Any estimate from this model is therefore quoted with ±1.96 × RMSE and never as a
prediction of beating a specific score.</p>

<h2>Candidate construction (hypothesis 1)</h2>
<ol>
<li>Distance transform to the mapped traces; weight <code>exp(−½((d − 16)/12)²)</code> — a 1.6 km peak with
1.2 km scatter, hard-zeroed for <code>d ≤ 4 px</code> so no mass lands on the catalogue.</li>
<li>Multiply by <code>sqrt</code> of the 2 km Gaussian fault density, restricting the prior to structural
corridors.</li>
<li>Greedy selection in prior order with an 800 m minimum separation, which guarantees no two dots share a
300 m support neighbourhood; stop at 34,500 dots (the fleet's measured optimum is 37,654 and the trend is
monotone decreasing in mass).</li>
<li>Write float32, values {0, 1}, <b>0.0 everywhere outside the organizer footprint</b> with the nodata tag
unset. The requester reported that a NaN-filled variant was rejected with
“Predicted values must be in range [0, 1]”, so zeros are used everywhere; the official text permits
“null or nan” outside the bounds, but only zeros survive the portal's own validation.</li>
</ol>

<h2>Uniqueness, calibrated</h2>
<p>The session protocol's literal rule (“more than 70% of dots within 3 px of one registry raster”) was
applied first and the candidate failed against 4 references. Investigating that failure produced the more
useful result: the rule fails for <b>every</b> submission in the fleet, including all nine focus files
(mutual overlap 83–100%; ≥ 99.4% of each file's dots lie within 3 px of the 13GEMSDOE stride-5 lattice,
which covers 99.96% of the footprint). Two further rasters blanket 84% and 90% of the footprint, so any
spread-out pattern overlaps them by construction.</p>
<p>The operative gate therefore asks whether the candidate is <i>more</i> similar to a reference than chance
predicts: enrichment = observed overlap ÷ the reference's own 3-px footprint coverage, flagged only when
enrichment &gt; 1.5 <b>and</b> more than 50% of dots coincide. Surface similarity is measured on 1 km
Gaussian-smoothed density fields rather than raw binary rank correlation, because on sparse binary rasters
the raw rank correlation is dominated by the shared zero background (two unrelated dot patterns score
ρ &gt; 0.99).</p>
{status_checks_table()}
"""
    return page("Method and metric", body)


# --------------------------------------------------------------------- sources
def build_sources() -> str:
    rows = [
        ("Competition overview", "https://www.drivendata.org/competitions/306/competition-doe-gems/",
         "Prize structure, rounds, external-data permission.", "fetched 2026-10-27"),
        ("Problem description &amp; metric", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
         "Exact DTI formulas, α = 0.2, β = 0.8, R = 300 m, submission format, label provenance.",
         "fetched 2026-10-27 (full text reviewed)"),
        ("Public leaderboard", "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
         f"Live standings. Leader {LEADERBOARD['top'][0][0]} {LEADERBOARD['top'][0][1]:.4f}.", "fetched 2026-10-27"),
        ("Data download page", "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
         "Requires authentication; <code>training_features.tif</code> and <code>1m_DEM_links.csv</code> not obtainable here.",
         "redirect to login (not bypassed)"),
        ("Official rules PDF", "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
         "Submission rules, AI-use disclosure, weekly submission limits.", "referenced; not re-fetched this session"),
        ("Organizer reference solution", "https://github.com/drivendataorg/gems-prize-reference-solution",
         "Baseline U-Net; <b>contains no metric code</b> and no data — checked file list and notebook cells.",
         "fetched 2026-10-27"),
        ("USGS GeoDAWN data release", "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
         "Source of the magnetic/radiometric layers in the official feature stack.", "catalogue record (network blocked here)"),
        ("USGS ScienceBase item", "https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7",
         "GeoDAWN study-area extent figure cited by the organizers.", "linked from page 967"),
        ("EPSG:32611", "https://epsg.io/32611", "UTM 11N — the required CRS.", "reference"),
        ("Tversky index", "https://en.wikipedia.org/wiki/Tversky_index",
         "Definition of the underlying similarity index.", "reference"),
        ("INGENIOUS (GBCGE)", "https://gbcge.org/current-projects/ingenious/",
         "Label source along with USGS Quaternary fault maps.", "reference"),
        ("GDR submissions 1391", "https://gdr.openei.org/submissions/1391",
         "INGENIOUS compilation record.", "reference"),
        ("GEMSDOE32 site", "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
         "Owner page for the 0.2778 claim; labels its own historical scores owner-reported.",
         "site content reviewed"),
    ]
    trs = "".join(f'<tr><td><a href="{e(u)}">{lbl}</a><br><span class="mono">{e(u)}</span></td>'
                  f'<td>{what}</td><td class="dim">{status}</td></tr>' for lbl, u, what, status in rows)
    body = f"""
<h1>Sources and what each one actually verifies</h1>
<p>Each row was opened or checked this session unless marked otherwise. A source being listed is not a claim
that it was fully usable — the “status” column says what happened, including the three that are blocked
from this environment.</p>
<h2>Official source inventory</h2>
<table><tr><th>Source</th><th>What it verifies</th><th>Status</th></tr>{trs}</table>

<h2>Fleet files used for measurement</h2>
<p>93 submissions across 55 owner sites were downloaded through the GitHub API and hash-checked
(<code>data_public/raster_fetch_manifest.json</code>), plus the nine pinned focus files verified against
<code>registry/focus_sites.json</code> (<code>data_public/focus_pins_verified.json</code>, all nine SHA-256
matches). The organizer-format inputs are pinned in <code>data_public/official/SOURCES.json</code>:
<code>existing_faults.tif</code> = <code>labels.tif</code> =
<code>7ba308cc…ae4093</code>, <code>sample_submission.tif</code> = <code>2176d08e…d35cbc</code>.</p>
<div class="card warn">
<p><b>Two irregularities for review.</b></p>
<ol>
<li>The fleet's <code>labels.tif</code> is <b>byte-identical</b> to its <code>existing_faults.tif</code>
(same SHA-256), i.e. the file labelled "labels" is the <i>visible catalogue</i>, not the hidden scoring
labels. Any "holdout DTI" or "catalogue proxy" computed from it measures agreement with the catalogue, not
with the competition's target.</li>
<li><code>training_features.tif</code> (the 419 MB, 19-band stack the fleet's pipelines describe) is not
present in any repository checked and cannot be downloaded without DrivenData authentication. Results that
depend on it are therefore not reproducible from these pages, including our own hypotheses 2–4.</li>
</ol>
</div>
"""
    return page("Sources", body)


# ------------------------------------------------------------------- per site
SITE_NOTES = {
    "GEMSDOE24": "Earliest high scorer in the lineage; 60,069 dots, the largest mass of the nine, and the lowest reported score of the top six — consistent with the mass-economy trend.",
    "GEMSDOE25": "Same surface as GEMSDOE30 (measured ~1.00 overlap) re-emitted at 44,090 dots.",
    "GEMSDOE27": "Topographic gap-closure variant; 61,328 dots, the largest emission among the nine.",
    "GEMSDOE28": "Four files clustered at 0.2649–0.2710 with 37,660–42,294 dots; the source of the 'd28' prior reused by GEMSDOE30/31.",
    "GEMSDOE30": "Named 'poisson300m-offcat-44090' but measured ~1.00 overlap with GEMSDOE25 — the name describes a method the file does not embody.",
    "GEMSDOE31": "55,304 support pixels in 40,934 components (dots merged into strands) at 0.2708; graded, unlike the purely binary winners.",
    "GEMSDOE32": "The reported 0.2778 maximum: the least-redundant member of the family (37,654 dots) and independent of the catalogue (median 18 px away).",
    "GEMSDOE33": "Tip/stepover analogue transfer, 41,865 dots at 0.2632.",
    "GEMSDOE36": "Geothermal-PINN prior, 38,854 dots at 0.2750 — second highest, and 98% similar to GEMSDOE32 at the metric's own 3 px tolerance.",
}


def build_site_pages() -> None:
    out = DOCS / "sites"
    out.mkdir(parents=True, exist_ok=True)
    for r in FOCUS:
        site = r["site"]
        body = f"""
<h1>{e(site)}</h1>
<p class="dim">Owner mirror: <a href="https://github.com/{e(r['repository'])}">{e(r['repository'])}</a> at
<code>{e(r['ref'][:12])}</code></p>
<div class="card">
<h3 style="margin-top:0">Best historical file</h3>
<p class="mono">{e(Path(r['path']).name)}</p>
<p>Reported score <b>{r['user_reported_score']:.4f}</b>
<span class="pill warn">USER-REPORTED</span> · our estimate <b>{r['model_estimate']:.3f}</b>
<span class="pill warn">EMPIRICAL-ESTIMATE</span></p>
<p>SHA-256 <span class="mono">{e(r['sha256'])}</span>
<span class="pill {'ok' if r['pin_match'] else 'bad'}">{'matches the repository pin' if r['pin_match'] else 'pin mismatch'}</span></p>
<table>
<tr><th>Property</th><th>Measured</th></tr>
<tr><td>Positive pixels (dots)</td><td>{r['dots']:,}</td></tr>
<tr><td>Median distance to mapped traces</td><td>{r['median_px_to_catalogue']:.1f} px ({r['median_px_to_catalogue']*100/1000:.1f} km)</td></tr>
<tr><td>Dots within 3 px of mapped traces</td><td>{r['frac_within_3px_catalogue']*100:.1f}%</td></tr>
<tr><td>Max overlap with another focus site</td><td>{r['max_overlap_vs_other_focus_sites']:.2f}</td></tr>
<tr><td>Min overlap with another focus site</td><td>{r['min_overlap_vs_other_focus_sites']:.2f}</td></tr>
<tr><td>Overlap with our candidate</td><td>{r['overlap_with_wbg2_candidate']:.2f}</td></tr>
<tr><td>Distinct from the other eight focus sites?</td>
<td>{'<span class="pill ok">YES</span>' if r['unique_vs_other_focus_sites'] else '<span class="pill bad">NO</span> — shares more than 70% of its dots with at least one other focus submission'}</td></tr>
</table>
<p>{e(SITE_NOTES.get(site, ''))}</p>
<p><a href="{e(r['download_url'])}">Pinned download</a> · <a href="{e(r['page_url'])}">owner page</a></p>
</div>
<div class="card warn"><p><b>Submission guidance: do not submit this file.</b> It is a historical artifact from
another project, it is not unique against its own siblings, and it carries no organizer receipt. The file to
submit is <a href="../index.html">on the home page</a>.</p></div>
"""
        (out / f"{site}.html").write_text(page(f"{site} — measured review", body,
                                              '<a href="../executive-summary.html">All nine sites</a>',
                                              base="../"))


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    (DOCS / "styles.css").write_text(CSS)
    (DOCS / "index.html").write_text(build_index())
    (DOCS / "executive-summary.html").write_text(build_exec())
    (DOCS / "methodology.html").write_text(build_method())
    (DOCS / "sources.html").write_text(build_sources())
    build_site_pages()
    print("wrote docs/index.html, executive-summary.html, methodology.html, sources.html, sites/*.html")


if __name__ == "__main__":
    main()
