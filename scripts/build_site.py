#!/usr/bin/env python3
"""Build the decision-driven, byte-bound GEMS executive site (docs/*.html).

Fail-closed: a green "OK TO DOWNLOAD AND SUBMIT" button is rendered ONLY when the
committed decision.json is byte-bound to the committed raster (sha256 equality),
backed by a machine-validation receipt with every gate true, and free of any
invented leaderboard score. A flipped JSON boolean or a changed raster cannot
produce a green page. Stdlib only (runs in the Pages workflow without pip data).
"""
from __future__ import annotations
import datetime as dt
import hashlib
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# ---------------------------------------------------------------- data loads
def jload(rel):
    return json.loads((ROOT / rel).read_text())

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

decision = jload("docs/data/decision.json")
validation = jload("docs/data/decision_validation.json")
portfolio = jload("docs/data/portfolio.json")
leader = jload("docs/data/leaderboard.json")
card = jload("docs/data/h1_run_card.json")
exps = jload("docs/data/h1_experiments.json")
uniq = jload("docs/data/h1_uniqueness.json")
canary = jload("docs/data/h1_canary.json")

NAME = decision["candidate"]["submission_name"]
TIF_REL = f"downloads/{NAME}.tif"
ZIP_REL = f"downloads/{NAME}.zip"
TIF = DOCS / TIF_REL
ZIP = DOCS / ZIP_REL
DECISION_LABEL = decision["decision_label"]  # "OK TO DOWNLOAD AND SUBMIT"

# ---------------------------------------------------------- FAIL-CLOSED guard
problems = []
if decision.get("verdict") != "promote" or decision.get("ok_to_submit") is not True or decision.get("ok_to_download_new_tif") is not True:
    problems.append("decision is not a promote")
if not all(decision.get("promotion_gates", {}).values()):
    problems.append("a promotion gate is false")
if decision.get("estimated_score", {}).get("leaderboard_dti") is not None:
    problems.append("an invented leaderboard score was found")
if len(decision.get("candidate", {}).get("note", "")) > 140 or len(NAME) > 140:
    problems.append("name/note exceeds 140 chars")
if not TIF.is_file():
    problems.append("raster file missing")
else:
    if sha256(TIF) != decision["candidate"]["raster_sha256"]:
        problems.append("raster sha256 != decision (byte binding broken)")
    if sha256(TIF) != card.get("raster_sha256"):
        problems.append("raster sha256 != run card")
if not ZIP.is_file() or sha256(ZIP) != decision["candidate"]["zip_sha256"]:
    problems.append("zip missing or sha mismatch")
if validation.get("verdict") != "OK TO DOWNLOAD AND SUBMIT" or validation.get("ok_to_submit") is not True:
    problems.append("machine-validation receipt is not a pass")
if validation.get("raster_sha256") != decision["candidate"]["raster_sha256"]:
    problems.append("validation receipt is bound to a different raster")
if validation.get("checks_passed") != validation.get("checks_total"):
    problems.append("not all machine checks passed")
if problems:
    raise ValueError("UNVERIFIED PROMOTION — refusing to render a green button: " + "; ".join(problems))

GATE_COUNT = validation["checks_passed"]
NOTE = decision["candidate"]["note"]
DOTS = decision["candidate"]["positive_dots"]
HOLDOUT = decision["estimated_score"]["holdout_proxy"]
HD = HOLDOUT["dti"]
HLO, HHI = HOLDOUT["ci95"]
GEN = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# nine focus sites, sorted by user-reported claim
SITES = sorted(portfolio["sites"], key=lambda r: float(r["user_reported_score"]), reverse=True)
CLAIMS = {r["site"]: r["user_reported_score"] for r in SITES}
BEST_CLAIM = float(SITES[0]["user_reported_score"])
BEST_SITE = SITES[0]["site"]


def e(value):
    return escape(str(value), quote=True)


def icon(name, size=19):
    paths = {
        "download": '<path d="M12 3v12m-4-4 4 4 4-4M5 18v2h14v-2"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
        "shield": '<path d="M12 2.5 20 6v5.3c0 5-3.1 8.4-8 10.2-4.9-1.8-8-5.2-8-10.2V6l8-3.5Z"/><path d="m9 12 2 2 4-4"/>',
        "chart": '<path d="M4 19V5m0 14h16M8 15l3-4 3 2 5-7"/>',
        "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".5"/>',
        "flask": '<path d="M9 3h6M10 3v6L5 18a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 18l-5-9V3M7.5 15h9"/>',
        "link": '<path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7-7l-1.2 1.1M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7 7l1.1-1.1"/>',
        "warn": '<path d="M12 3 2 20h20L12 3Zm0 6v5m0 3h.01"/>',
    }
    return (f'<svg aria-hidden="true" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>')


NAV = [("index.html", "Overview"), ("executive-summary.html", "Executive summary"),
       ("submit.html", "How to submit"), ("research.html", "Research"), ("sources.html", "Sources")]


def header(current):
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(h, ' aria-current="page"' if h == current else "", lab)
        for h, lab in NAV
    )
    return f'''<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a href="index.html" class="brand" aria-label="GEMS research home"><span class="brandmark">{icon("chart", 20)}</span>GEMS <small>RESEARCH</small></a>
<nav class="nav" aria-label="Main navigation">{links}</nav>
<div class="top-right"><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a>
<span class="top-status ok"><span class="dot"></span> OK TO SUBMIT</span></div></div></header>
<div class="decision-strip"><div class="shell"><span class="ds-badge">{icon("check",15)} {e(DECISION_LABEL)}</span>
<span class="ds-copy">Machine-validated {GATE_COUNT}/{validation["checks_total"]} checks · raster sha256 {e(decision["candidate"]["raster_sha256"][:12])}…</span>
<a class="ds-download" href="{e(TIF_REL)}">{icon("download",15)} Download TIF</a></div></div>'''


def footer():
    return f'''<footer class="footer"><div class="shell"><div><strong>GEMS RESEARCH</strong> · Evidence before submission · generated {e(GEN)}</div>
<div><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a> &nbsp;·&nbsp;
<a href="data/decision.json">Decision JSON</a> &nbsp;·&nbsp; <a href="data/h1_run_card.json">Run card</a> &nbsp;·&nbsp;
<a href="data/decision_validation.json">Validation receipt</a></div></div></footer>'''


def page(title, current, body, description):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="description" content="{e(description)}"><meta name="theme-color" content="#0b5d4d">'
            f'<title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script></head>'
            f'<body>{header(current)}<main id="main" class="shell main">{body}</main>{footer()}</body></html>')


# ------------------------------------------------------------------ OVERVIEW
def home():
    hero = f'''<section class="hero-good" aria-labelledby="hero-title">
<div class="hg-icon">{icon("check",26)}</div>
<div class="hg-copy"><p class="eyebrow">Current decision · machine validated</p>
<h1 id="hero-title">{e(DECISION_LABEL)}</h1>
<p>A genuinely new, unique GeoTIFF is ready. It is <strong>not a copy of any previous submission</strong>
— final-dot overlap is at most {uniq["max_real_submission_overlap_3px"]:.0%} against the nine focus sites and recent H31/H47 files,
and surface rank-correlation is at most {uniq["max_all_registry_abs_spearman"]:.2f} against every registered raster.
All {GATE_COUNT} automated gates below passed.</p>
<div class="hg-actions"><a class="button big" href="{e(TIF_REL)}">{icon("download",20)} Download the submission TIF</a>
<a class="button secondary big" href="{e(ZIP_REL)}">{icon("download",18)} Download .zip</a>
<a class="text-link" href="submit.html">How to submit →</a></div></div></section>'''

    honest = f'''<section class="card honest"><div class="honest-head">{icon("warn",18)}<h2>What this decision does — and does not — mean</h2></div>
<p><strong>It means:</strong> the file is a valid single-band float32 GeoTIFF, EPSG:32611, 100 m, with the exact
competition shape and transform; every value is in <code>[0, 1]</code>; there is no NaN/Inf anywhere; nothing is
predicted outside the footprint or on mapped faults. It is a distinct, leakage-audited prediction cleared for you
to download and try. <strong>This directly fixes the “Predicted values must be in range [0, 1]” error.</strong></p>
<p><strong>It does not mean:</strong> a leaderboard score. The public/private scoring truth (expert-labelled NEW
faults) is not published and there is no organizer receipt for this file, so <em>no leaderboard score can be
estimated</em>. The local <strong>HOLDOUT-DTI {HD:.4f} (95% CI {HLO:.4f}–{HHI:.4f})</strong> is a research proxy on an
owner-mirrored catalogue, not a leaderboard number. Data are a hash-verified public owner mirror, not an
authenticated DrivenData download. The weekly slot (max 3) is a separate selector decision; this lane spent
<strong>0 slots</strong>. Read the <a href="executive-summary.html">executive summary</a> and
<a href="sources.html">irregularities</a> before uploading.</p></section>'''

    leader_score = leader.get("top_public_dti")
    leader_txt = f"{float(leader_score):.4f}" if isinstance(leader_score, (int, float)) else "unavailable"
    stats = f'''<section class="stats" aria-label="Key evidence">
<article class="stat"><div class="stat-top">Decision <span class="stat-icon">{icon("check")}</span></div>
<div class="stat-value small ok-text">OK TO SUBMIT</div><div class="stat-sub">byte-bound · {GATE_COUNT}/{validation["checks_total"]} checks</div></article>
<article class="stat"><div class="stat-top">HOLDOUT-DTI proxy <span class="stat-icon">{icon("chart")}</span></div>
<div class="stat-value">{HD:.4f}</div><div class="stat-sub">95% CI {HLO:.4f}–{HHI:.4f} · {HOLDOUT["withheld_positive_pixels"]:,} withheld</div></article>
<article class="stat"><div class="stat-top">Uniqueness vs 9 sites <span class="stat-icon">{icon("target")}</span></div>
<div class="stat-value">{uniq["max_real_submission_overlap_3px"]:.0%}</div><div class="stat-sub">max 3px dot overlap · limit 70%</div></article>
<article class="stat"><div class="stat-top">Leaderboard score <span class="stat-icon">{icon("warn")}</span></div>
<div class="stat-value small">Unknown</div><div class="stat-sub">public leader {e(leader_txt)} (snapshot) · not our file</div></article>
</section>'''

    # priority table
    rows = []
    rows.append(f'''<tr class="champion"><td data-label="File / site"><span class="site-name">★ NEW · H1 cross-physics (this repo)</span>
<a class="file-link" href="{e(TIF_REL)}" title="{e(NAME)}.tif">{e(NAME)}.tif ↓ download</a></td>
<td data-label="Estimated score"><span class="score ok-text">HOLDOUT-DTI {HD:.4f}</span>
<span class="small-meta">CI {HLO:.4f}–{HHI:.4f} · proxy, NOT a leaderboard score</span></td>
<td data-label="Unique?"><span class="status-yes">Yes</span><span class="small-meta">≤{uniq["max_real_submission_overlap_3px"]:.0%} overlap · |ρ|≤{uniq["max_all_registry_abs_spearman"]:.2f}</span></td>
<td data-label="Action"><a class="button tiny" href="{e(TIF_REL)}">{icon("download",14)} Download &amp; submit</a></td></tr>''')
    for r in SITES:
        site = r["site"]
        claim = r["user_reported_score"]
        ov = r["max_3px_overlap_vs_other_focus"]
        wit = r["max_overlap_witness_site"]
        dl = r["download_url"]
        rows.append(f'''<tr><td data-label="File / site"><a class="site-name" href="../site/sites/{e(site)}.html">{e(site)} ↗</a>
<a class="file-link" href="{e(dl)}" title="historical research only">historical best · {e(claim)} (claim)</a></td>
<td data-label="Estimated score"><span class="score">{e(claim)}</span><span class="small-meta">USER-REPORTED claim · not a receipt</span></td>
<td data-label="Unique?"><span class="status-no">No</span><span class="small-meta">{ov*100:.0f}% within 3px of {e(wit)}</span></td>
<td data-label="Action"><span class="status-muted">Research only</span><span class="small-meta">do not re-submit</span></td></tr>''')
    table = f'''<section class="card table-card" id="priority-sites"><div class="table-heading"><div>
<h2>Which submission is best to submit?</h2>
<p>One new, unique candidate plus the highest <em>user-reported</em> historical result from each of the nine focus sites.
Historical scores are unverified claims, not organizer-confirmed receipts; no leaderboard forecast is available for any file.
Uniqueness is measured against the registered raster set.</p></div>
<div class="table-tools"><span class="tag green">1 new candidate</span><a class="text-link" href="data/portfolio.json">Audit JSON ↗</a></div></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">File / site</th><th scope="col">Estimated score (labelled)</th>
<th scope="col">Unique submission?</th><th scope="col">Action</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<div class="table-footer"><div>“Estimated score” for the new file is a labelled HOLDOUT-DTI proxy; its leaderboard score is unknown until an organizer receipt exists.</div>
<div><a href="executive-summary.html">Full executive summary →</a></div></div></section>'''

    why = f'''<section class="card guide-card"><div class="section-header"><div><h2>Why did the {BEST_SITE} “{BEST_CLAIM:.4f}” result win, and can we beat it?</h2>
<p>A PhD-level, byte-verified reading — not a score projection.</p></div><span class="tag">Evidence review</span></div>
<p>We reopened the exact historical bytes. The {BEST_SITE} B2 raster is <strong>bit-for-bit</strong> the earlier
D2.8 dotted line (GEMSDOE25 = GEMSDOE30, {portfolio["champion_lineage"]["d28_pixels"]:,} dots) with every dot within
2 px of the mapped-fault catalogue removed — {portfolio["champion_lineage"]["d28_pixels_removed"]:,} dots pruned,
leaving {portfolio["champion_lineage"]["b2_pixels"]:,}. GEMSDOE36 then re-added 1,200 dots and its claim fell slightly
(0.2750). This is measured lineage, not proof the bytes were submitted or caused the score.</p>
<p><strong>Mechanism (DTI, α=0.2, β=0.8, 300 m triangular kernel):</strong> the metric rewards probability mass placed
within 300 m of a true (hidden) fault pixel, while false negatives are penalised 4× false positives. A sparse, evenly
spaced dotted line along structural ridges keeps kernel coverage of many possible true traces while limiting redundant
false-positive mass. Pruning the 2 px halo around <em>mapped</em> faults removes dots that the organizer masks from
scoring anyway, so they cannot earn credit — raising the ratio without losing coverage. Sparse → less FP mass;
catalogue-pruned → no wasted dots on known traces. That is a plausible explanation for the ordering 0.2778 &gt; 0.2750 &gt; 0.2600.</p>
<p><strong>Can we beat it?</strong> Not provably from here. {BEST_CLAIM:.4f}, 0.3195 and 0.4413 are user-reported
observations of different leaderboards/prize rounds, not receipts tied to these bytes, and the private truth is
hidden — so any “estimated winning score” would be a hallucination. What we <em>can</em> do is submit a genuinely
different, independently-motivated prediction (H1) so it is not merely re-testing the same d2.8 ridge family; the
organizer’s returned score — and only that — tells us whether it is better. On our own leakage-free holdout the new
candidate scores <strong>{HD:.4f}</strong> vs the champion mechanism’s
<strong>{exps["scores"]["control_B2_mechanism"]["dti"]:.4f}</strong> on the same folds. Read the
<a href="research.html">full analysis and ranked hypotheses →</a></p></section>'''

    return page("Overview", "index.html", hero + honest + stats + table + why,
                "GEMS DOE Prize: a machine-validated, unique submission TIF ready to download and submit.")


# --------------------------------------------------------- EXECUTIVE SUMMARY
def guide():
    intro = f'''<div class="intro"><div><p class="eyebrow">Executive summary</p><h1>One file. Clear decision. <span>Exactly how to submit.</span></h1>
<p>The current decision is <strong>{e(DECISION_LABEL)}</strong> — {GATE_COUNT}/{validation["checks_total"]} automated checks passed.</p></div>
<div class="intro-meta">Decision recorded<br><strong>{e(GEN)}</strong></div></div>'''

    dl = f'''<section class="card dl-card"><div class="dl-left"><span class="tag green">CLEARED FOR DOWNLOAD</span>
<h2 id="download">Download the unique submission</h2>
<p>Single-band float32 GeoTIFF · EPSG:32611 · 100 m · 3730×3292 · all values in [0,1] · no NaN/Inf ·
{DOTS:,} positive dots · sha256 <code>{e(decision["candidate"]["raster_sha256"])}</code>.</p>
<div class="hg-actions"><a class="button big" href="{e(TIF_REL)}">{icon("download",20)} Download .tif</a>
<a class="button secondary big" href="{e(ZIP_REL)}">{icon("download",18)} Download .zip (one TIFF)</a></div></div>
<div class="dl-right"><span class="dl-check">{icon("check",16)} {GATE_COUNT}/{validation["checks_total"]} gates</span>
<a href="data/decision_validation.json">Validation receipt ↗</a><a href="data/h1_run_card.json">Run card ↗</a>
<a href="data/h1_format.json">Format receipt ↗</a></div></section>'''

    # one executive summary per focus site
    site_lines = []
    for r in SITES:
        site_lines.append(
            f'<li><a href="../site/sites/{e(r["site"])}.html">{e(r["site"])}</a> — historical best '
            f'<strong>{e(r["user_reported_score"])}</strong> (USER-REPORTED, not a receipt). '
            f'Not unique: {r["max_3px_overlap_vs_other_focus"]*100:.0f}% of its dots sit within 3px of '
            f'{e(r["max_overlap_witness_site"])}. <em>Do not re-submit.</em></li>')
    per_site = f'''<section class="card guide-card"><h2>Per-site executive summaries (nine focus sites)</h2>
<p>Every historical “best” belongs to one near-identical d2.8 ridge family; they are research references, not
downloadable new submissions. The best file to submit today is the single new H1 candidate above.</p>
<ul class="source-list per-site">{"".join(site_lines)}</ul></section>'''

    table = f'''<section class="card table-card"><div class="table-heading"><div><h2>Decision table</h2>
<p>File to download · estimated score (honestly labelled) · whether it is unique.</p></div></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>File to download</th><th>Estimated score</th>
<th>Unique vs other GEMSDOE sites?</th><th>Why / decision</th></tr></thead><tbody>
<tr class="champion"><td data-label="File"><a href="{e(TIF_REL)}">{e(NAME)}.tif ↓</a></td>
<td data-label="Estimated score"><span class="score ok-text">HOLDOUT-DTI {HD:.4f}</span>
<span class="small-meta">CI {HLO:.4f}–{HHI:.4f} · {HOLDOUT["withheld_positive_pixels"]:,} withheld · NOT a leaderboard score</span></td>
<td data-label="Unique?"><span class="status-yes">Yes</span><span class="small-meta">≤{uniq["max_real_submission_overlap_3px"]:.0%} dot overlap, |ρ|≤{uniq["max_all_registry_abs_spearman"]:.2f} vs registry</span></td>
<td data-label="Why">Novel cross-physics lineament + buffered continuation; distinct from the d2.8 family; passes every automated gate. <strong>Best to submit.</strong></td></tr>
<tr><td data-label="File">9 historical site bests (research only)</td>
<td data-label="Estimated score"><span class="score">{min(CLAIMS.values())}–{max(CLAIMS.values())}</span>
<span class="small-meta">USER-REPORTED claims · unverified</span></td>
<td data-label="Unique?"><span class="status-no">No</span><span class="small-meta">&gt;70% mutual overlap</span></td>
<td data-label="Why">Duplicates of one family; re-submitting wastes a weekly slot.</td></tr>
</tbody></table></div></section>'''

    steps = f'''<section class="card guide-card"><h2 id="steps">Exactly how to submit (step by step)</h2>
<ol class="steps">
<li><strong>Download the exact file.</strong> Use the green button above. Save <code>{e(NAME)}.tif</code>
(or the .zip, which contains only that one GeoTIFF). Verify its SHA-256 equals
<code>{e(decision["candidate"]["raster_sha256"])}</code>.</li>
<li><strong>Do not clip or rescale it.</strong> Values are already finite and in <code>[0,1]</code> everywhere (zeros
outside the footprint, <code>nodata</code> unset). This is what avoids the “Predicted values must be in range [0, 1]”
portal error — a cause of earlier failures was NaN or out-of-range sentinel values leaking into the raster.</li>
<li><strong>Confirm the local format.</strong> The <a href="data/h1_format.json">format receipt</a> and
<a href="data/decision_validation.json">validation receipt</a> confirm one float32 band, EPSG:32611, 100 m,
matching shape/transform, no NaN in the footprint. A local pass is not organizer acceptance.</li>
<li><strong>Open DrivenData.</strong> Sign in, enroll, choose <em>Submit → Make new submission</em>, and select the
single .tif (or the one-TIFF .zip). Do not upload multiple rasters.</li>
<li><strong>Enter a unique name and short note.</strong> Suggested name (≤140 chars):<br>
<code class="copy">{e(NAME)}</code><br>Suggested note ({len(NOTE)} chars):<br><code class="copy">{e(NOTE)}</code></li>
<li><strong>Respect the weekly cap.</strong> Official rules allow up to three automated-scoring submissions per week;
check the remaining allowance on the submission page. This lane spent <strong>0</strong> slots — the actual upload is your
separate selector decision.</li>
<li><strong>Keep the receipt.</strong> Record the exact filename, hash, note, timestamp and organizer result. Only that
organizer number is a real score — the HOLDOUT-DTI here is a proxy, not a leaderboard score.</li>
<li><strong>Disclose AI use.</strong> Generative-AI assistance was used to develop this method; the prize narrative
must disclose its extent per the official rules.</li>
</ol>
<div class="callout">Portal acceptance, the leaderboard score, and organizer data authenticity are <strong>not</strong>
proven by any local check. The competition grid is a hash-verified owner mirror whose sample bytes are not
organizer-authenticated; see <a href="sources.html">irregularities</a>.</div>
<p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Official submission format ↗</a>
&nbsp;·&nbsp; <a class="text-link" href="submit.html">Dedicated how-to-submit page ↗</a>
&nbsp;·&nbsp; <a class="text-link" href="NEXT_STEPS.md">Limitations &amp; next steps ↗</a></p></section>'''

    return page("Executive summary", "executive-summary.html", intro + dl + table + steps + per_site,
                "Executive summary: which GEMS file to download, its labelled estimated score, uniqueness, and exactly how to submit.")


# --------------------------------------------------------------- SUBMIT PAGE
def submit():
    body = f'''<div class="intro"><div><p class="eyebrow">How to submit</p><h1>Download, verify, <span>upload.</span></h1>
<p>A short, exact guide. Current decision: <strong>{e(DECISION_LABEL)}</strong>.</p></div></div>
<section class="hero-good slim"><div class="hg-icon">{icon("download",24)}</div><div class="hg-copy">
<h2 id="download">1 — Get the file</h2>
<p><code>{e(NAME)}.tif</code> — {DOTS:,} dots, float32, all values in [0,1], no NaN.</p>
<div class="hg-actions"><a class="button big" href="{e(TIF_REL)}">{icon("download",20)} Download .tif</a>
<a class="button secondary big" href="{e(ZIP_REL)}">Download .zip</a></div></div></section>
<section class="card guide-card"><h2>2 — Verify (no human inspection needed)</h2>
<p>Run <code>python scripts/wbg_verify_decision.py</code> in a checkout with dependencies installed; it re-opens the
raster bytes and re-checks all {validation["checks_total"]} gates, exiting 0 only on <em>OK TO DOWNLOAD AND SUBMIT</em>.
Or compare the committed receipts: <a href="data/decision_validation.json">validation</a>,
<a href="data/h1_format.json">format</a>, <a href="data/h1_run_card.json">run card</a>.</p>
<p class="audit-line">sha256: {e(decision["candidate"]["raster_sha256"])}<br>zip sha256: {e(decision["candidate"]["zip_sha256"])}</p></section>
<section class="card guide-card"><h2>3 — Upload on DrivenData</h2>
<p>Submit → Make new submission → select the single .tif or the one-TIFF .zip. Enter a unique name and the short note below.</p>
<p><strong>Name:</strong> <code class="copy">{e(NAME)}</code><br><strong>Note ({len(NOTE)} chars):</strong> <code class="copy">{e(NOTE)}</code></p></section>
<section class="card guide-card"><h2>4 — Rules and honesty</h2>
<p>Up to three submissions per week (check the live cap); the score you get back is the only real score. Dispose of the
AI-use disclosure in the prize narrative. Values must stay in [0,1] — do not rescale or clip the file. Data provenance,
the space-filling-control policy decision and leaderboard-score uncertainty are documented on the
<a href="sources.html">sources &amp; irregularities</a> page.</p>
<p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Official format ↗</a>
&nbsp;·&nbsp; <a class="text-link" href="executive-summary.html">Full executive summary ↗</a></p></section>'''
    return page("How to submit", "submit.html", body, "Step-by-step: download, machine-verify, and submit the unique GEMS TIF.")


# --------------------------------------------------------------- RESEARCH
def research():
    intro = '''<div class="intro"><div><p class="eyebrow">Research</p><h1>Why 0.2778 won — and <span>what we actually tested.</span></h1>
<p>PhD-level, byte-verified analysis. Every number is labelled HOLDOUT-DTI or USER-REPORTED; none is a leaderboard score.</p></div></div>'''

    arms = exps["scores"]
    arm_rows = "".join(
        f'<tr><td>{e(k)}</td><td><span class="score">{v["dti"]:.4f}</span></td>'
        f'<td>{v["ci95"][0]:.4f}–{v["ci95"][1]:.4f}</td><td>{v["withheld_positive_pixels"]:,}</td></tr>'
        for k, v in arms.items())
    hold = f'''<section class="card guide-card"><h2 id="holdout">Spatially-blocked hide-and-recover holdout</h2>
<p>Evaluator <code>{e(exps["evaluator_version"])}</code>, α={exps["alpha"]}, β={exps["beta"]},
{exps["triangular_radius_m"]:.0f} m triangular kernel, {exps["folds"]} buffered whole-component folds,
{exps["withheld_positives_total"]:,} withheld positives. Catalogue-derived features use <strong>visible faults
only</strong>; visible fault pixels are masked pixel-exactly. A paired block bootstrap gives the 95% CI.</p>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Withheld +</th></tr></thead>
<tbody>{arm_rows}</tbody></table></div>
<p>The promoted <code>dual_population</code> arm ({arms["dual_population"]["dti"]:.4f}) beats the user-reported
champion mechanism B2 ({arms["control_B2_mechanism"]["dti"]:.4f}) on the same folds — paired Δ
{exps["paired_differences_vs_promoted"]["control_B2_mechanism"]["delta"]:.4f}, 95% CI
{exps["paired_differences_vs_promoted"]["control_B2_mechanism"]["ci95"][0]:.4f}–{exps["paired_differences_vs_promoted"]["control_B2_mechanism"]["ci95"][1]:.4f}.
Superiority over the diagnostic continuation control is <em>not</em> statistically proven (CI straddles zero); the
promotion rests on being a genuinely distinct, uniquely novel method that is no worse on this proxy while carrying
off-catalogue coverage for the real (new-fault) target.</p>
<p><strong>Honest limitation:</strong> hide-and-recover withholds <em>catalogue</em> segments, so it structurally favours
near-fault continuation; the leaderboard instead rewards expert-labelled NEW faults. That is exactly why the promoted
arm emits both near-catalogue continuation dots and off-catalogue cross-physics lineament dots.</p></section>'''

    can_rows = "".join(
        f'<tr><td>{e(k)}</td><td>{v["auc_two_sided"]:.4f}</td>'
        f'<td>{"<span class=status-yes>pass</span>" if v["pass"] else "<span class=status-no>FLAG / LEAK DEMO</span>"}</td></tr>'
        for k, v in canary["features"].items())
    leak = f'''<section class="card guide-card"><h2 id="canary">Leakage canary</h2>
<p>Each input feature is tested alone on the holdout; a two-sided AUC above 0.90 is treated as leakage until proven
otherwise. Every real feature passes. The full-catalogue halo is a deliberate leakage <em>demonstration</em> (AUC
{canary["features"]["halo_from_FULL_catalogue_LEAK_DEMO"]["auc_two_sided"]:.4f}) and is never used by any arm.</p>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Feature</th><th>Two-sided AUC</th><th>Canary</th></tr></thead>
<tbody>{can_rows}</tbody></table></div></section>'''

    why = '''<section class="card guide-card"><h2 id="b2">A byte-verified reading of the 0.2778 result</h2>
<p>The nine focus-site “best” files are one near-identical family: GEMSDOE25 and GEMSDOE30 have identical decoded
footprint predictions (44,090 dots); GEMSDOE32 B2 equals that D2.8 raster with all dots within 2 px of the mapped
catalogue removed (6,436 pruned → 37,654); GEMSDOE36 adds 1,200 dots back and removes none. Their claims
(0.2449–0.2778) are USER-REPORTED, not organizer-confirmed receipts.</p>
<p><strong>Why sparse + pruned can win under DTI (α=0.2, β=0.8, 300 m kernel):</strong> false negatives are weighted
4× false positives, so a sparse dotted line along structural ridges keeps partial kernel credit near many possible
true traces while keeping the FP term small. Dots on or beside mapped faults earn no credit because the organizer
masks known-fault pixels; pruning that halo removes wasted mass. Sparse emission also avoids redundant, overlapping
dots that add FP without adding coverage. This explains the ordering 0.2778 (B2) &gt; 0.2750 (B2 + points) &gt;
0.2600 (unpruned D2.8) as a plausible mechanism — not a proven cause, since the private truth and per-dot receipts
are unavailable.</p>
<p><strong>Can we beat it?</strong> Only an organizer result can answer that. The three leaderboard figures in the
brief (0.4413 public lead, 0.3195, 0.2778) are inconsistent, time-varying, user-reported observations of different
rounds — not receipts bound to these bytes. No calibrated leaderboard forecast exists, so we deliberately submit a
genuinely different prediction (H1) rather than another member of the same family.</p></section>'''

    # ranked hypotheses
    hyps = [
        ("H1 — Multiscale cross-physics lineament coherence (PROMOTED)",
         "tc, iso_grav_anom, tmi, det_elev, cond_surf, geod_2ndinv (+ depth_to_base_surf prior)",
         "Through-going linear discontinuities whose Gaussian-derivative orientation is coherent across scales (σ=1,2,4 px) AND coincident across independent physics; combined by geometric mean so a single-sensor artifact cannot dominate.",
         "Buried / blind faults can lack a surface scarp yet still juxtapose density, magnetisation, conductivity and strain — a coincident multi-physics edge survives where a single DEM/topo ridge does not. The depth prior up-weights basin fill where faults are missing from surface mapping.",
         "Aeromagnetic flight-line leveling artifacts; intrusive/dike or lithologic contacts. Mitigated by cross-physics agreement; a deeply buried contact can still be indistinguishable from a blind fault.",
         "New to this repo (uses the restored 19-band stack, not the d2.8 dotted-ridge family). Verified: |ρ|≤0.22, dot overlap ≤0.29 vs registry.",
         "Validated: HOLDOUT-DTI ~0.0966 (CI 0.0877–0.1051) vs B2 mechanism 0.0039 on the same folds.",
         "Low — all layers already provided; no external download needed."),
        ("H2 — Conductivity / depth-to-conductive-base contact edges",
         "cond_surf, depth_to_base_surf (band 17, 15) + iso_grav_anom_vg",
         "Narrow conductive corridors with a coincident gravity-gradient contrast marking fluid pathways along unmapped faults.",
         "Geothermal upflow alters rock along faults with no surface rupture; a conductivity break can reveal the fault.",
         "Clay-rich playa sediments, saline groundwater, cultural conductors — also conductive.",
         "Not implemented here; complements H1 by adding an independent subsurface response.",
         "Expected small, unmeasured HOLDOUT-DTI gain; high mimic risk. No score projection.",
         "Low–medium — bands provided; needs careful metadata/unit check (mirrored band-15 label disagrees with official)."),
        ("H3 — Geodetic strain-transition junctions",
         "geod_shearrate, geod_dilaterate, geod_2ndinv (bands 7, 8, 4)",
         "Spatially persistent strain-gradient boundaries or orientation changes marking active structural zones without a mapped trace.",
         "Active/long-lived faults lacking surface rupture localise present-day strain.",
         "Broad tectonic deformation, GPS interpolation artifacts, volcanic/anthropogenic transients.",
         "Not implemented here; H1 uses the 2nd invariant but not the full tensor morphology.",
         "Expected small, unmeasured gain; strain fields may be too coarse for individual traces.",
         "Low — bands provided."),
        ("H4 — Radiometric Th/K-low alteration corridor",
         "tc (radiometric total counts) + det_elev_slope; scarp-strike continuation beyond catalogue tips",
         "Hydrothermal clay alteration (Th/K-low) following a fault past its mapped tip, cross-checked against slope asymmetry.",
         "Blind geothermal upflow can alter rock along a fault with no surface rupture.",
         "Playa clay flats / erosional escarpments (also Th/K-low).",
         "Related to a blocked historical parallel H1; must be replayed with fold-local features and canaries first.",
         "Unknown — its prior holdout used a private evaluator and failed the registry gate; needs re-validation.",
         "Medium — verify official tc metadata vs mirror disagreement before use."),
        ("H5 — 1 m DEM drainage / scarp deflection at lineament intersections",
         "1m_DEM_links.csv (official free tiles) + det_elev derivatives",
         "Repeated channel deflection, aligned saddles and abrupt valley asymmetry reflecting fault control.",
         "Unmapped geomorphic expression where the fault is too subtle for the 100 m DEM.",
         "Lithologic contrasts, drainage capture, roads/ditches, landslides.",
         "DEM-scarp/topo-gap approaches are common across the historical fleet; novelty uncertain.",
         "Unknown — lowest priority; high geomorphic confounding.",
         "High — needs the free official 1m DEM links (USGS 3DEP / provided CSV); check license & coverage first."),
    ]
    hyp_cards = []
    for i, (title, layers, sig, whycatch, mimic, diff, dti, cost) in enumerate(hyps, 1):
        cls = " promoted" if i == 1 else ""
        hyp_cards.append(f'''<article class="card hyp{cls}"><div class="hyp-head"><span class="hyp-rank">RANK {i}</span>
{"<span class='tag green'>VALIDATED TOP CANDIDATE</span>" if i==1 else ""}</div>
<h3>{e(title)}</h3>
<p><strong>Layers:</strong> {e(layers)}</p>
<p><strong>Physical signature:</strong> {e(sig)}</p>
<p><strong>Why it catches a catalogue-missing fault:</strong> {e(whycatch)}</p>
<p><strong>Non-fault mimic:</strong> {e(mimic)}</p>
<p><strong>Difference from this repo / fleet:</strong> {e(diff)}</p>
<p><strong>Expected DTI improvement:</strong> {e(dti)}</p>
<p><strong>Implementation cost / data:</strong> {e(cost)}</p></article>''')
    hypotheses = f'''<section id="hypotheses"><h2>Five ranked geological hypotheses</h2>
<p class="section-lede">Ranked by expected HOLDOUT-DTI gain ÷ implementation cost. Only rank 1 was implemented and
validated on the spatially-blocked holdout before any submission-slot consideration; ranks 2–5 are unmeasured priors,
not scores. Free official data sources are named where an idea would need new input.</p>
<div class="hyp-grid">{"".join(hyp_cards)}</div></section>'''

    mech = f'''<section class="card guide-card"><h2 id="mechanism">Promoted mechanism &amp; named non-fault mimic</h2>
<p>{e(card["mechanism"])}</p>
<p><strong>Named non-fault mimic:</strong> {e(card["named_non_fault_mimic"])}</p>
<p><strong>Uniqueness:</strong> max surface |ρ| {uniq["max_all_registry_abs_spearman"]:.2f} (limit 0.90);
max final-dot 3px overlap vs real submissions {uniq["max_real_submission_overlap_3px"]:.0%} (limit 70%).
See the <a href="data/h1_uniqueness.json">uniqueness receipt</a> and
<a href="data/h1_run_card.json">run card</a>.</p></section>'''

    return page("Research", "research.html", intro + why + hold + leak + hypotheses + mech,
                "PhD-level analysis of the 0.2778 result, ranked geological hypotheses, leakage canary and holdout DTI.")


# ---------------------------------------------------------------- SOURCES
def sources():
    intro = '''<div class="intro"><div><p class="eyebrow">Sources &amp; irregularities</p><h1>Official source inventory <span>&amp; flagged irregularities.</span></h1>
<p>Links for manual review; every competition fact verified against the official problem page where reachable.</p></div></div>'''
    official = '''<section class="card guide-card"><h2>Official, verified sources</h2>
<ul class="source-list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem &amp; metric page</a> — target is geological faults; test sets are expert-identified NEW faults omitted from the USGS/INGENIOUS catalogue; α=0.2, β=0.8, 300 m triangular kernel. <em>(fetched this session)</em></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Submission format</a> — single-band float32, EPSG:32611, 100 m, matching bounds, values in [0,1], outside null/NaN. <em>(fetched this session)</em></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features">Provided features</a> — conductivity, detrended elevation, strain, gravity, magnetics, earthquake density, 1m_DEM_links.csv.</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2">DrivenData staff clarification (thread 11516)</a> — known USGS/INGENIOUS fault pixels are excluded from scoring; no multi-pixel buffer stated.</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF (§§3.2–3.5)</a> — up to three automated submissions/week; one final selection; generative-AI use must be disclosed.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official public leaderboard</a> — team-level public ranking; a snapshot observation, not a per-file receipt.</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release</a> — airborne magnetic/radiometric surveys (CC0).</li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS 1391</a> — regional compilation incl. faults, temperature, geodetics (CC BY 4.0).</li>
<li><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP</a> — free 1 m DEM products without use restrictions.</li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a> — public reproducibility baseline.</li>
<li><a href="https://gbcge.org/current-projects/ingenious/">GBCGE INGENIOUS project</a> — project context for the fault/temperature/geodetic compilation.</li>
</ul></section>'''
    irreg = f'''<section class="card guide-card"><h2 id="irregularities">Flagged irregularities (for review)</h2>
<ul class="source-list irr">{"".join(f"<li>{e(x)}</li>" for x in decision["flagged_irregularities"])}</ul>
<div class="callout"><strong>The literal duplicate-rule contradiction.</strong> A registered stride-5 lattice covers
5,160,724 of 5,167,373 footprint cells within 3 px, and a registered continuous prior is positive everywhere. Under a
strictly literal “any registry raster dot” test, <em>every</em> non-empty candidate would be a duplicate — including
the user-reported 0.2778 champion (0.9992 lattice overlap). We therefore made an explicit, reviewable
<strong>policy decision</strong>: continuous probability fields and space-filling lattice controls are compared by the
rule’s surface rank-correlation branch (|ρ|≤{uniq["max_all_registry_abs_spearman"]:.2f}, pass), while the 3 px dot
branch is applied to discrete dot-emission submissions (≤{uniq["max_real_submission_overlap_3px"]:.0%}, pass). This is
surfaced, not silently exempted — see <a href="data/h1_uniqueness.json">the uniqueness receipt</a>.</div>
<p>Other standing caveats: the competition grid/labels are a hash-verified public owner mirror, not an authenticated
DrivenData download; the mirrored “sample” has 60,988 positives whereas the official example predicts total absence;
band 15 is labelled “depth to basement” in the mirror but “depth to conductive base” officially (used only as a mild
monotonic weight); the official data page requires login and no weekly-quota receipt was available. Large data and the
shared template cache are excluded from Git.</p>
<p><a href="data/h1_canary.json">Canary receipt ↗</a> · <a href="data/h1_experiments.json">Holdout experiments ↗</a> ·
<a href="data/parallel_review.json">Rejected parallel TIFF review ↗</a> ·
<a href="NEXT_STEPS.md">Limitations &amp; next steps ↗</a> ·
<a href="DECISION.md">Current decision (markdown) ↗</a> ·
<a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/findings.md">Full findings on GitHub ↗</a></p></section>'''
    return page("Sources", "sources.html", intro + official + irreg,
                "Official verified sources and flagged irregularities for the GEMS submission decision.")


# ------------------------------------------------------------ copy receipts
for name in ("decision.json", "decision_validation.json", "h1_run_card.json", "h1_experiments.json",
             "h1_canary.json", "h1_uniqueness.json", "h1_holdout.json", "h1_format.json", "review_passes.json"):
    src = ROOT / "evidence" / name
    if not src.is_file():
        src = ROOT / "docs" / "data" / name
    dst = DOCS / "data" / name
    if src.is_file() and src.resolve() != dst.resolve():
        shutil.copyfile(src, dst)

for name, content in [("index.html", home()), ("executive-summary.html", guide()),
                      ("submit.html", submit()), ("research.html", research()), ("sources.html", sources())]:
    (DOCS / name).write_text(content, encoding="utf-8")
    print(f"built {DOCS / name}")
print(f"DECISION: {DECISION_LABEL} (byte-bound to {decision['candidate']['raster_sha256'][:16]}…, {GATE_COUNT} gates)")
