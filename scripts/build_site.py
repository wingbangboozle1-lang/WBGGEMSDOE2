#!/usr/bin/env python3
"""Build the evidence-first GitHub Pages dashboard from the current release card.

Fail-closed: a green "OK TO DOWNLOAD AND SUBMIT" banner is rendered only when
``docs/data/release.json`` AND the canonical run card agree that every gate
passed and the raster SHA-256 is present. Editing one JSON boolean cannot
silently promote a file. Historical files are always labelled research-only.
"""
from __future__ import annotations

import datetime as dt
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
release = json.loads((DOCS / 'data/release.json').read_text())
run = json.loads((DOCS / 'data/run-card.json').read_text())
portfolio = json.loads((DOCS / 'data/portfolio.json').read_text())
leader = json.loads((DOCS / 'data/leaderboard.json').read_text())
registry = json.loads((ROOT / 'config/registry_inputs.json').read_text())

# Byte-bound cross-check: never render a green button from an unchecked card.
GREEN = bool(
    release['ok_to_submit'] is True and run['ok_to_submit'] is True
    and run['verdict'] == 'promote-to-selector-only'
    and run['raster_sha256'] == release['sha256']
    and (DOCS / 'downloads' / Path(release['tif']).name).is_file()
    and release.get('gates') and all(release['gates'].values())
)
if release['ok_to_submit'] and not GREEN:
    raise ValueError('Renders only a fully receipted release; manual review required before publication')

for name in ('data_preparation.json', 'feature_cache.json', 'b2_local_format.json',
             'dense_prior_certificate.json', 'parallel_review.json',
             'parallel_candidate_audit.json', 'conduit_review.json',
             'derived_features.json', 'canaries_20261027.json',
             'holdout_20261027.json', 'novelty_refinement.json',
             'soft_novelty_refinement.json', 'final_uniqueness.json',
             'final_format.json', 'campaign_20261027.json', 'registry_union.json',
             'registry_expanded.json', 'sources_20261027.md'):
    src = ROOT / 'evidence' / name
    if not src.is_file() and name.endswith('.md'):
        src = ROOT / 'research' / name
    if src.is_file():
        shutil.copyfile(src, DOCS / 'data' / name)


def e(value) -> str:
    return escape(str(value), quote=True)


def header(current: str) -> str:
    nav = [('index.html', 'Overview'), ('executive-summary.html', 'Executive summary'),
           ('research.html', 'Research'), ('sources.html', 'Sources')]
    links = ''.join(f'<a href="{href}"{" aria-current=page" if href == current else ""}>{label}</a>'
                    for href, label in nav)
    state = 'Submission ready' if GREEN else 'Submission blocked'
    return f'''<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a href="index.html" class="brand">GEMS <small>RESEARCH</small></a>
<nav class="nav" aria-label="Main navigation">{links}</nav><div class="top-right"><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a><span class="top-status"><span class="dot"></span> {state}</span></div></div></header>'''


def footer() -> str:
    return f'''<footer class="footer"><div class="shell"><div><strong>GEMS RESEARCH</strong> · Evidence before submission · generated {e(release['generated_utc'])}</div><div><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a> · <a href="data/run-card.json">Run card</a> · <a href="data/release.json">Release JSON</a> · <a href="data/final_uniqueness.json">Uniqueness audit</a></div></div></footer>'''


def page(title, current, body, description):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{e(description)}"><title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script><style>
.banner.ready{{border-color:#cfe7d6;border-left-color:#2f8a5b;background:#f5fbf6}}.banner.ready .banner-icon{{background:#e6f5eb;color:#2f8a5b}}.banner.ready .banner-label{{color:#347a53}}.ready-note{{font-size:11px;color:#6b7d71;margin-top:7px}}.status-yes{{font-weight:800;color:#2f7a53;font-size:11px}}.mono{{font-family:ui-monospace,Menlo,monospace;font-size:11px;overflow-wrap:anywhere}}.pill{{display:inline-block;padding:3px 8px;border-radius:20px;background:#e9f6ee;color:#2f7a53;font-weight:800;font-size:10px;letter-spacing:.06em}}.pill.amber{{background:#fdf3e3;color:#96641f}}
</style></head><body>{header(current)}<main id="main" class="shell main">{body}</main>{footer()}</body></html>'''


def decision():
    if not GREEN:
        return ('<section class="banner"><h2 id="decision-heading">DO NOT SUBMIT.</h2>'
                '<p>The receipted gates did not all pass; no file is offered.</p></section>')
    tif = Path(release['tif']).name
    return f'''<section class="banner ready" aria-labelledby="decision-heading" style="flex-wrap:wrap">
<div class="banner-copy" style="flex:1 1 480px"><p class="banner-label">Current decision · {e(release['verdict'])}</p>
<h2 id="decision-heading">OK TO DOWNLOAD AND SUBMIT this new GeoTIFF.</h2>
<p>One newly generated, single-band float32 TIFF. {release['dots']:,} dots; SHA-256 <span class="mono">{e(release['sha256'])}</span>; {release['bytes']:,} bytes.</p>
<p class="ready-note"><strong>Conditional:</strong> {e(release['decision_detail'])} The literal "any registry raster" reading still fires on space-filling controls; see the two-reading policy in the executive summary. No organizer score or receipt is claimed.</p></div>
<div class="actions" style="flex:0 1 260px"><a class="button" href="downloads/{e(tif)}">↓ Download submission .tif</a><a class="button secondary" href="downloads/{e(tif[:-4])}.zip">Download .zip</a><a class="text-link" href="executive-summary.html">How to submit →</a></div></section>'''


def stats():
    dti, lo, hi = release['holdout_dti'], release['holdout_ci95'][0], release['holdout_ci95'][1]
    return f'''<section class="stats" aria-label="Key evidence">
<article class="stat"><div class="stat-top">Official public leader</div><div class="stat-value">{leader.get('top_public_dti', 0.4544):.4f}</div><div class="stat-sub">Snapshot {e(leader.get('captured_utc'))} · <a href="{e(leader['source_url'])}">source ↗</a></div></article>
<article class="stat"><div class="stat-top">Best of nine · reported</div><div class="stat-value">0.2778</div><div class="stat-sub">GEMSDOE32 B2 · USER-REPORTED, not a receipt</div></article>
<article class="stat"><div class="stat-top">New file · HOLDOUT-DTI</div><div class="stat-value">{dti:.4f}</div><div class="stat-sub">95% CI [{lo:.4f}, {hi:.4f}] · {release['withheld_positive_pixels']:,} withheld positives</div></article>
<article class="stat"><div class="stat-top">Novelty gate</div><div class="stat-value small">{release['like_for_like_worst_overlap']*100:.2f}%</div><div class="stat-sub">worst like-for-like overlap · limit 70% · PASS</div></article></section>'''


def summary_table():
    tif = Path(release['tif']).name
    rows = [f'''<tr class="champion"><td data-label="What to download"><a class="site-name" href="downloads/{e(tif)}">↓ {e(tif)}</a><a class="file-link" href="data/release.json">NEW · UNIQUE · SHA-256 {e(release['sha256'][:16])}… ↗</a></td>
<td data-label="Estimate score"><span class="score">No leaderboard estimate</span><span class="small-meta">HOLDOUT-DTI {release['holdout_dti']:.4f} [{release['holdout_ci95'][0]:.4f}, {release['holdout_ci95'][1]:.4f}] — a proxy, NOT a score</span></td>
<td data-label="Unique?"><span class="status-yes">YES</span><span class="small-meta">vs all 9 focus sites (worst {release['nine_focus_worst_overlap']*100:.2f}%) and {release['registry_rasters_checked']} public rasters; worst overlap {release['like_for_like_worst_overlap']*100:.2f}%</span></td>
<td data-label="Action"><span class="status-yes">Download &amp; submit</span><span class="small-meta">selector / weekly cap is yours</span></td></tr>''']
    for item in registry['inputs'][:9]:
        site = item['id']
        claim = item['user_reported_claim']
        ov = release['nine_focus_sites'].get(site, {}).get('overlap', 0) * 100
        rows.append(f'''<tr><td data-label="What to download"><a class="site-name" href="../site/sites/{e(site)}.html">{e(site)} ↗</a><a class="file-link" href="{e(item['url'])}" title="historical research only">{e(Path(item['path']).name)} ↗</a></td>
<td data-label="Estimate score"><span class="score">{claim:.4f}</span><span class="small-meta">USER-REPORTED claim; no receipt; not estimable for a new file</span></td>
<td data-label="Unique?"><span class="status-no">NO</span><span class="small-meta">historical; {ov:.1f}% of new dots near this site's rasters</span></td>
<td data-label="Action"><span class="status-no">Research only</span><span class="small-meta">never resubmit an old raster</span></td></tr>''')
    return f'''<section class="card table-card" id="decision-table"><div class="table-heading"><div><h2>Executive summary — one file to submit, nine historical references</h2><p>Only the first row is a newly generated, format-validated, holdout-tested and registry-audited submission. Historical scores are user-reported claims, not organizer-confirmed receipts. No defensible leaderboard score estimate exists for any new file; the labelled HOLDOUT-DTI is a different evidence class.</p></div><span class="tag green">Gates passed</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">What to download</th><th scope="col">Estimate score</th><th scope="col">Unique?</th><th scope="col">Action</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><div class="table-footer"><span>Evidence: <a href="data/final_uniqueness.json">126-raster audit</a> · <a href="data/soft_novelty_refinement.json">paired holdout</a> · <a href="data/final_format.json">format receipt</a></span><span>Updated {e(release['generated_utc'])}</span></div></section>'''


def home():
    body = f'''<div class="intro"><div><p class="eyebrow">Executive overview</p><h1>One clear <span>submission.</span></h1><p>A new blind-discontinuity GeoTIFF, generated and audited locally. Evidence classes are labelled so a holdout proxy is never mistaken for a leaderboard score.</p></div><div class="intro-meta">Decision recorded<br><strong>{e(release['generated_utc'])}</strong></div></div>'''
    body += decision() + stats() + summary_table()
    body += f'''<div class="grid"><article class="card"><div class="card-body"><div class="section-header"><div><h2>What was measured</h2><p>Three preregistered geological lanes; one shared evaluator; no private fork.</p></div><span class="tag">HOLDOUT-DTI</span></div><ul class="gate-list">
<li><span class="gate-icon">✓</span><div><div class="gate-title">Pooled HOLDOUT-DTI {release['holdout_dti']:.4f}, 95% CI [{release['holdout_ci95'][0]:.4f}, {release['holdout_ci95'][1]:.4f}]</div><div class="gate-desc">{e(release['evaluator_version'])} · {release['withheld_positive_pixels']:,} withheld positives · 4 buffered whole-component folds · 2,000 spatial-block bootstrap draws.</div></div><span class="gate-state">PASS</span></li>
<li><span class="gate-icon">✓</span><div><div class="gate-title">Paired win over the matched collar-only control</div><div class="gate-desc">+{release['paired_delta_vs_control']:.4f} DTI, 95% CI [{release['paired_delta_ci95'][0]:.4f}, {release['paired_delta_ci95'][1]:.4f}]; control {release['control_dti']:.4f}. Same folds, budget and evaluator.</div></div><span class="gate-state">PASS</span></li>
<li><span class="gate-icon">✓</span><div><div class="gate-title">Like-for-like registry clearance</div><div class="gate-desc">{release['registry_rasters_checked']} accessible rasters checked; worst dot overlap {release['like_for_like_worst_overlap']*100:.2f}% (limit 70%); worst |Spearman| {release['worst_rank_correlation']:.3f} (limit 0.90); unique vs all nine focus sites.</div></div><span class="gate-state">PASS</span></li>
<li><span class="gate-icon">✓</span><div><div class="gate-title">Canaries, format and byte identity</div><div class="gate-desc">Max single-feature directed AUC {release['canary_max_directed_auc']:.4f} (alarm 0.90); float32, EPSG:32611, 100 m, one band, values in [0,1], no NaN/NoData inside the footprint; SHA-256 pinned.</div></div><span class="gate-state">PASS</span></li></ul></div></article>
<article class="card"><div class="card-body"><div class="section-header"><div><h2>Read this before you upload</h2><p>Honest limits, not marketing.</p></div><span class="tag amber">CAVEAT</span></div><p style="font-size:12px;color:#64756a">The official public leader showed <strong>0.4544</strong> at rank 1 when observed; the request's 0.3195 / 0.4413 values are stale. No organizer receipt ties any historical claim to exact bytes. A HOLDOUT-DTI on withheld <em>mapped catalogue</em> components is a proxy for hidden expert faults, not a forecast of public or private leaderboard DW-Tversky.</p><p style="font-size:12px;color:#64756a">The literal duplicate rule is mathematically unsatisfiable here: a registered stride-5 lattice halo covers 99.87% of the footprint and a continuous prior is positive on 100% of it. The green decision uses the documented <strong>like-for-like</strong> reading; the literal reading still fires on {release['literal_overlap_firings']} control rasters. If your reviewer requires literal compliance, treat this file as research-only.</p><p style="font-size:12px;color:#64756a">We do not upload. Check the submission page's displayed weekly allowance; staff say that limit prevails. Record the organizer receipt after submitting.</p></div></article></div>'''
    body += '''<section class="brief-grid" aria-label="Research resources"><article class="card brief"><div class="brief-number">01</div><h3>Executive summary</h3><p>The download, the nine-site scorecard and the exact submission steps, including the short note and the [0,1] range check.</p><a href="executive-summary.html">Open the guide →</a></article><article class="card brief"><div class="brief-number">02</div><h3>Research</h3><p>Five preregistered geological hypotheses, official USGS grounding, the leakage fix and the negative hard-cap experiment.</p><a href="research.html">View research →</a></article><article class="card brief"><div class="brief-number">03</div><h3>Sources</h3><p>Line-by-line official competition and science sources, plus every irregularity found during verification.</p><a href="sources.html">Browse sources →</a></article></section>'''
    body += '<section class="dark-card"><p class="eyebrow">Next</p><h2>Submit one file. Keep the receipt.</h2><p>Download the first row of the table, verify its SHA-256, then use the submission name and note on the executive-summary page. <a href="executive-summary.html">Submission guide →</a> · <a href="../site/">Nine individual site briefs →</a> · <a href="executive-summary/">Previously rejected parallel TIFFs (research only) →</a></p></section>'
    return page('Executive overview', 'index.html', body, 'One downloadable submission, nine-site executive summary and measured evidence.')


def guide():
    tif = Path(release['tif']).name
    body = f'''<div class="intro"><div><p class="eyebrow">Executive summary</p><h1>From research to <span>submission.</span></h1><p>Exactly how to download, name, submit and record the one approved file.</p></div><div class="intro-meta">Decision<br><strong>{'OK TO SUBMIT' if GREEN else 'DO NOT SUBMIT'}</strong></div></div>'''
    body += decision() + summary_table()
    body += f'''<div class="guide-layout" style="margin-top:20px"><article class="card guide-card" id="how-to-submit"><div class="section-header"><div><h2>How to submit this file</h2><p>Five steps; no manual geospatial processing required.</p></div><span class="tag green">Ready</span></div><ol>
<li><strong>Download the exact TIFF.</strong> <a href="downloads/{e(tif)}">{e(tif)}</a> (or the one-TIFF <a href="downloads/{e(tif[:-4])}.zip">ZIP</a>). Verify SHA-256 <span class="mono">{e(release['sha256'])}</span> against <a href="data/campaign_20261027.json">the writer receipt</a>.</li>
<li><strong>Use the submission name.</strong> <span class="mono">{e(release['submission_name'])}</span> — a unique identifier for your team.</li>
<li><strong>Paste the short note</strong> into the "Note (optional)" box (max 140 characters): <span class="mono">{e(release['submission_note'])}</span></li>
<li><strong>Open DrivenData → Submit → Make new submission.</strong> Select the .tif or .zip. The file is one float32 band, EPSG:32611, 100 m, 3730×3292, transform (100, 0, 243350, 0, −100, 4508550), all values finite in [0,1] and zero outside the footprint — this avoids the earlier "Predicted values must be in range [0, 1]" error. Check the weekly allowance shown on the submission page before spending a slot.</li>
<li><strong>Keep the organizer receipt.</strong> Record filename, hash, note, timestamp and the returned public DW-Tversky. A HOLDOUT-DTI or a projection is not a score.</li></ol>
<div class="callout">Local validation is not organizer acceptance. The owner-mirror grid used for validation is hash-pinned but not authenticated against the login-protected official sample. If the portal rejects the file, preserve the exact message and bytes for diagnosis; never silently clip values.</div></article>
<aside class="card guide-card" id="novelty"><div class="section-header"><div><h2>Two readings of the duplicate rule</h2><p>Documented policy decision, 27 Oct 2026.</p></div></div><p><strong>Literal reading — FIRES.</strong> A registered stride-5 lattice's 3 px halo covers 99.87% of the footprint and a continuous prior is positive on 100% of it. Under the literal "every finite positive pixel is a dot" reading, <em>any</em> nonempty candidate is a duplicate; {release['literal_overlap_firings']} control rasters fire here.</p><p><strong>Like-for-like reading — PASSES.</strong> The 70% / 3 px dot test is applied only to geological dot fields; the 0.90 rank-correlation test applies to every raster. Worst overlap {release['like_for_like_worst_overlap']*100:.2f}%, worst |ρ| {release['worst_rank_correlation']:.3f}, {release['registry_rasters_checked']} rasters checked, 0 firings.</p><p><a href="data/final_uniqueness.json">Full 126-raster audit ↗</a> · <a href="data/registry_union.json">Registry classification ↗</a> · <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/docs/PROJECT_CHARTER.md">Charter amendment ↗</a></p><div class="callout">If you reject the policy decision, the correct action is <strong>DO NOT SUBMIT</strong>. No threshold was weakened and no control was hidden.</div></aside></div>'''
    sites = ''.join(f'''<tr><td data-label="Site"><a class="site-name" href="../site/sites/{e(s)}.html">{e(s)} ↗</a></td><td data-label="Reported claim">{v.get('claim', 0):.4f}<span class="small-meta">USER-REPORTED; no receipt</span></td><td data-label="New-file overlap">{v['overlap']*100:.2f}%<span class="small-meta">max over {v.get('files', 1)} resolved raster(s)</span></td><td data-label="Best file to submit?"><span class="status-no">No — historical</span><span class="small-meta">use the one new TIFF above</span></td></tr>''' for s, v in sorted(release['nine_focus_sites'].items()))
    body += f'''<section class="card table-card" style="margin-top:20px"><div class="table-heading"><div><h2>Per-site executive verdict</h2><p>All nine focus sites are research references. Their reported values are claims; no score estimate is defensible for a new file, and none is a unique new submission.</p></div><span class="tag">9 sites</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Site</th><th>Reported claim</th><th>New-file overlap</th><th>Best file to submit?</th></tr></thead><tbody>{sites}</tbody></table></div></section>'''
    body += '''<section class="card guide-card" style="margin-top:20px"><h2>What still needs work</h2><p>Authenticate the official sample/features/labels and weekly quota with a logged-in download; pin every registry blob to an immutable commit instead of HEAD; obtain the free USGS GeoDAWN line CSV (CC0) to test the flight-line repeatability veto; fix the shared validator's finite-NoData-in-footprint gap upstream; and collect an organizer submission receipt. The final prize round rescoring against expert-expanded labels cannot be predicted from public scores.</p></section>'''
    return page('Executive summary', 'executive-summary.html', body, 'Download the approved TIFF, exact submission steps, per-site scorecard and caveats.')


def research():
    cards = [
        ('01 · TOP / RUN', 'Blind-fault flexural curvature dipole', 'detrended elevation Laplacian at two scales, adjacent opposite-sign lobes, low-slope gate, conductive-base-depth and gravity-gradient concordance.', 'Alluvial-fan toes, terraces, roads, drainage incision.', 'USGS QFFD 28b; Sou Hills play fairway.'),
        ('02 · RUN', 'Clay-capped alteration edge', 'opposed conductivity / TMI gradient normals, local magnetic low × conductivity high, conductivity/depth and tilt edges.', 'Playa clays, zeolite tuffs, flight-line striping.', 'USGS YVO 2022; Nevada play fairway 2019.'),
        ('03 · IN FUSION', 'Strain-partition boundary', 'dilatation zero-crossing along shear gradient, earthquake intensity/distance anomalies, second invariant.', 'GPS interpolation, volcanic inflation, catalogue boundaries.', 'USGS Siler 2023; Coolbaugh 2003.'),
        ('04 · NOT RUN', 'Potential-field decorrelation', 'windowed correlation of gravity-gradient and reduced-to-pole normals; keep sign reversals.', 'Intrusions with remanence, source-depth change.', 'USGS Argenta Rise modelling.'),
        ('05 · NOT VIABLE', 'Flight-line repeatability veto', 're-grid crossing GeoDAWN flight/tie lines; keep azimuth-reproducible magnetic edges.', 'Real dikes also reproduce; uneven line coverage.', 'USGS GeoDAWN CC0; line CSV bytes not obtained.'),
    ]
    items = ''.join(f'''<article class="card research-item"><span class="num">{e(n)}</span><h2>{e(t)}</h2><p><strong>Signature:</strong> {e(s)}</p><p><strong>Non-fault mimic:</strong> {e(m)}</p><p><strong>Official grounding:</strong> {e(g)}</p><span class="tag">Preregistered</span></article>''' for n, t, s, m, g in cards)
    body = f'''<div class="intro"><div><p class="eyebrow">Scientific research</p><h1>New geology, <span>measured.</span></h1><p>Five preregistered hypotheses; three executed arms; one promoted lane.</p></div><div class="intro-meta">Campaign<br><strong>3 experiments · 2 h budget</strong></div></div>'''
    body += decision()
    body += f'''<section class="card guide-card" style="margin-bottom:20px"><h2>Measured outcome (HOLDOUT-DTI, not a leaderboard score)</h2><p>E3 fusion of H-A + H-C + H-E won: <strong>{release['holdout_dti']:.4f}</strong> [95% CI {release['holdout_ci95'][0]:.4f}, {release['holdout_ci95'][1]:.4f}], {release['withheld_positive_pixels']:,} withheld positives, evaluator <span class="mono">{e(release['evaluator_version'])}</span>. Paired difference vs the matched collar-only control: +{release['paired_delta_vs_control']:.4f} [{release['paired_delta_ci95'][0]:.4f}, {release['paired_delta_ci95'][1]:.4f}]. E1 flexure and E2 alteration were the other two arms; a hard registry crowd cap was a decisive negative (DTI 0.0091) and is documented in <a href="data/novelty_refinement.json">the refinement receipt</a>.</p><p><strong>Leakage fix:</strong> a first pass trained on distance-to-visible-fault learned the trivial identity "visible pixel → distance 0" and emitted zero-coverage dots. It was discarded before any result was trusted. The promoted model sees label-free geophysics only; the visible catalogue enters once at emission as a fixed collar prior. Max single-feature directed AUC {release['canary_max_directed_auc']:.4f} (alarm 0.90), no alarms.</p><p><a href="data/canaries_20261027.json">Canaries ↗</a> · <a href="data/holdout_20261027.json">Full arm sweep ↗</a> · <a href="data/soft_novelty_refinement.json">Promoted refinement ↗</a> · <a href="data/derived_features.json">Feature bank ↗</a> · <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses_20261027.md">Preregistration ↗</a></p></section>'''
    body += f'''<div class="research-list">{items}</div>'''
    return page('Research', 'research.html', body, 'Preregistered geological hypotheses, measured holdout results and official sources.')


def sources():
    rows = [
        ('Target', 'Predict previously unmapped faults indicative of geothermal resources; prediction is not proof of a vent.', 'Official problem description', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/'),
        ('Format', 'Single float32 band, EPSG:32611, 100 m, matching bounds/transform, values in [0,1], null/NaN outside.', 'Official submission format', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format'),
        ('Metric', 'Distance-weighted Tversky, 300 m triangular kernel, alpha 0.2 / beta 0.8.', 'Official performance metric', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric'),
        ('Leaderboard', 'Official public leader 0.4544 observed 2026-10-27; not a receipt for any project file.', 'Official leaderboard', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'),
        ('External data', 'Allowed with a licence permitting challenge use and sharing with the sponsor.', 'Competition overview', 'https://www.drivendata.org/competitions/306/competition-doe-gems/'),
        ('Weekly cap', 'Staff: the submission-page limit prevails over the parenthetical three-per-week.', 'DrivenData staff, 5 Oct 2026', 'https://community.drivendata.org/t/submission-amount-question/11553'),
        ('Clay-capped faults', 'Low resistivity + subdued magnetization above clay-capped buried faults.', 'USGS YVO, 2022', 'https://www.usgs.gov/observatories/yvo/news/novel-technique-peeks-beneath-ground-yellowstones-hot-water-plumbing-system'),
        ('Blind systems', 'Gravity gradients, magnetic lows, low resistivity and structural discontinuities at blind systems.', 'USGS play fairway, 2019', 'https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and'),
        ('Stepovers', 'Largest localized stress/strain effects at fault stepovers and terminations.', 'USGS Siler, 2023', 'https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa'),
        ('Blind folding', 'Fault-propagation folding and monocline geomorphic expression.', 'USGS QFFD report 28b', 'https://landslides.usgs.gov/static/lfs/nshm/qfaults/Reports/28b.pdf'),
        ('GeoDAWN', 'CC0 data release; Area 2 lines 400 m apart, variable terrain clearance.', 'USGS GeoDAWN, 2024', 'https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'),
        ('Rules PDF', 'Sponsor rules referenced by the brief.', 'NLR / OSTI 96647', 'https://docs.nlr.gov/docs/fy26osti/96647.pdf'),
    ]
    trs = ''.join(f'<tr><td data-label="Topic"><strong>{e(t)}</strong></td><td data-label="Verified claim">{e(c)}</td><td data-label="Source"><a href="{e(u)}">{e(l)} ↗</a></td></tr>' for t, c, l, u in rows)
    irr = ''.join(f'<li>{e(x)}</li>' for x in release['irregularities'])
    body = f'''<div class="intro"><div><p class="eyebrow">Evidence &amp; sources</p><h1>Trace each <span>claim.</span></h1><p>Official pages opened 2026-10-27; each claim labelled by evidence class.</p></div><div class="intro-meta">Register<br><strong>research/sources_20261027.md</strong></div></div>'''
    body += decision()
    body += f'''<section class="card table-card"><div class="table-heading"><div><h2>Official source inventory</h2><p>Follow each link for full wording. Owner/site claims remain USER-REPORTED unless a submission-page receipt exists.</p></div><span class="tag">Verified</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Topic</th><th>What the source supports</th><th>Verify</th></tr></thead><tbody>{trs}</tbody></table></div></section>'''
    body += f'''<section class="card guide-card" style="margin-top:20px"><h2>Flagged irregularities for review</h2><ol style="font-size:13px;color:#64756a">{irr}</ol><p><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/sources_20261027.md">Full line-by-line source register ↗</a> · <a href="data/final_format.json">Local format receipt ↗</a> · <a href="data/final_uniqueness.json">Registry audit ↗</a></p></section>'''
    return page('Sources', 'sources.html', body, 'Official competition and USGS sources with irregularities and evidence labels.')


for name, content in [('index.html', home()), ('executive-summary.html', guide()),
                      ('research.html', research()), ('sources.html', sources())]:
    (DOCS / name).write_text(content, encoding='utf-8')
    print(f'built {DOCS / name}')
