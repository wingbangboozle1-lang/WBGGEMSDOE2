#!/usr/bin/env python3
"""Build the static, evidence-first GitHub Pages site without a web framework."""
from __future__ import annotations
import datetime as dt
from html import escape
import json
from pathlib import Path
import shutil
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
portfolio = json.loads((DOCS / 'data/portfolio.json').read_text())
leader = json.loads((DOCS / 'data/leaderboard.json').read_text())
fresh = json.loads((DOCS / 'data/focus-freshness.json').read_text())
run = json.loads((DOCS / 'data/run-card.json').read_text())
# Fail closed: this renderer is specifically a negative-run dashboard. A future
# candidate cannot silently inherit a green button by editing a JSON boolean.
if run.get('verdict') != 'negative' or run.get('ok_to_submit') is not False or run.get('raster_sha256') is not None:
    raise ValueError('This dashboard renders only the audited negative run; review and implement a byte-bound release before changing status.')
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
if (review.get('ok_to_submit') is not False or review.get('sha256') != run.get('parallel_session', {}).get('rejected_candidate_sha256')
        or review.get('format', {}).get('masked_inside') != 5132809
        or round(review.get('literal_overlap_3px', {}).get('lattice', 0), 6) != 0.993838):
    raise ValueError('Parallel-file evidence changed; review the static narrative before publishing.')
if (conduit.get('ok_to_submit') is not False or conduit.get('sha256') != run.get('conduit_parallel_session', {}).get('rejected_candidate_sha256')
        or round(conduit.get('witnesses', {}).get('13GEMSDOE', {}).get('source_threshold_ge_0_5', {}).get('fraction', 0), 6) != 0.998726):
    raise ValueError('Conduit-file evidence changed; review the static narrative before publishing.')
for name in ('data_preparation.json', 'feature_cache.json', 'b2_local_format.json', 'dense_prior_certificate.json', 'parallel_review.json', 'parallel_candidate_audit.json', 'conduit_review.json', 'shared_registry_index_summary.json', 'parallel_range_diagnostics_20261027.json', 'public_leaderboard_observation_20261027.json'):
    source = ROOT / 'evidence' / name
    if source.is_file():
        shutil.copyfile(source, DOCS / 'data' / name)


def e(value) -> str:
    return escape(str(value), quote=True)


def icon(name: str) -> str:
    paths = {
        'shield': '<path d="M12 2.5 20 6v5.3c0 5-3.1 8.4-8 10.2-4.9-1.8-8-5.2-8-10.2V6l8-3.5Z"/><path d="M12 7.3v5.1m0 3.4h.01"/>',
        'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
        'chart': '<path d="M4 19V5m0 14h16M8 15l3-4 3 2 5-7"/>',
        'target': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".5"/>',
        'spark': '<path d="m12 3 1.6 5.3L19 10l-5.4 1.7L12 17l-1.6-5.3L5 10l5.4-1.7L12 3Zm6 12 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7L18 15Z"/>',
        'lock': '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v2"/>',
        'download': '<path d="M12 3v12m-4-4 4 4 4-4M5 18v2h14v-2"/>',
    }
    return f'<svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>'


def header(current: str) -> str:
    nav = [('index.html','Overview'),('executive-summary.html','Executive summary'),('research.html','Research'),('sources.html','Sources')]
    links = ''.join('<a href="{}"{}>{}</a>'.format(href, ' aria-current="page"' if href == current else '', label) for href, label in nav)
    return f'''<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a href="index.html" class="brand" aria-label="GEMS research home"><span class="brandmark"><svg aria-hidden="true" width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M3 17.2 8.3 6l4.2 8 2.7-5 5.8 8.2" stroke="white" stroke-width="1.8" stroke-linejoin="round"/><path d="M4 19h16" stroke="#a9d8bc" stroke-width="1.5"/></svg></span>GEMS <small>RESEARCH</small></a>
<nav class="nav" aria-label="Main navigation">{links}</nav><div class="top-right"><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a><span class="top-status"><span class="dot"></span> Submission blocked</span></div></div></header>'''


def footer() -> str:
    return '''<footer class="footer"><div class="shell"><div><strong>GEMS RESEARCH</strong> · Evidence before submission</div><div><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a> &nbsp;·&nbsp; <a href="data/run-card.json">Run card</a> &nbsp;·&nbsp; <a href="data/portfolio.json">Audit data</a></div></div></footer>'''


def page(title: str, current: str, body: str, description: str, *, base: str = '') -> str:
    base_tag = f'<base href="{e(base)}">' if base else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">{base_tag}<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{e(description)}"><meta name="theme-color" content="#0b5d4d"><title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script></head><body>{header(current)}<main id="main" class="shell main">{body}</main>{footer()}</body></html>'''


def intro(label, title, subtitle):
    stamp = e(portfolio['generated_utc'].replace('T',' ').split('.')[0] + ' UTC')
    return f'''<div class="intro"><div><p class="eyebrow">{e(label)}</p><h1>{title}</h1><p>{e(subtitle)}</p></div><div class="intro-meta">Audit recorded<br><strong>{stamp}</strong></div></div>'''


def decision():
    return f'''<section class="banner" aria-labelledby="decision-heading"><div class="banner-icon">{icon('shield')}</div><div class="banner-copy"><p class="banner-label">Current recommendation · negative</p><h2 id="decision-heading">No file is approved for submission.</h2><p>This review lane generated no TIFF. Two parallel research files failed the literal registry gate; one also masks most footprint cells. Neither is approved for upload.</p></div><div class="actions"><button class="button" disabled>{icon('download')} No submission file</button><a class="text-link" href="executive-summary.html">See the checklist →</a></div></section>'''


def freshness():
    captured = leader.get('captured_utc') or ''
    status = leader.get('status') or 'stale'
    return f'<span class="freshness" data-captured="{e(captured)}" data-status="{e(status)}">Snapshot · {e(captured or "no capture time")}</span>'


def stats():
    score = leader.get('top_public_dti')
    display = f'{float(score):.4f}' if isinstance(score,(float,int)) and not isinstance(score,bool) and 0 <= score <= 1 else 'Unavailable'
    return f'''<section class="stats" aria-label="Key evidence"><article class="stat"><div class="stat-top">Official public leader <span class="stat-icon">{icon('chart')}</span></div><div class="stat-value">{display}</div><div class="stat-sub">{freshness()} · <a href="{e(leader['source_url'])}">source ↗</a></div></article>
<article class="stat"><div class="stat-top">Best of nine · reported <span class="stat-icon">{icon('target')}</span></div><div class="stat-value">0.2778</div><div class="stat-sub">GEMSDOE32 · user-reported, not a receipt</div></article>
<article class="stat"><div class="stat-top">New-file estimate <span class="stat-icon">{icon('spark')}</span></div><div class="stat-value small">Unavailable</div><div class="stat-sub">No calibrated leaderboard forecast</div></article>
<article class="stat"><div class="stat-top">Novelty gate <span class="stat-icon">{icon('lock')}</span></div><div class="stat-value small">Blocked</div><div class="stat-sub">Literal registered-prior rule · see proof</div></article></section>'''


def compare_section():
    score = leader.get('top_public_dti')
    if not isinstance(score,(float,int)) or isinstance(score,bool) or not 0 < score <= 1:
        score = None
    leader_txt = f'{score:.4f}' if score is not None else 'Unavailable'
    denominator = max(score or 0, .2778)
    bar_a = 100 * score / denominator if score is not None else 0
    bar_b = min(100,.2778/denominator*100)
    return f'''<div class="grid"><article class="card"><div class="card-body"><div class="section-header"><div><h2>What the best result tells us</h2><p>Historical context, not a prediction.</p></div><span class="tag">Evidence review</span></div><div class="compare"><div class="compare-text"><h3>0.2778 <span style="font-size:12px;color:#97a69b;letter-spacing:0">user-reported</span></h3><p>The GEMSDOE32 B2 reference is the strongest result supplied across the nine sites. Its sparse dots may reduce redundant false-positive cost, but the hidden labels and upload receipt are unavailable.</p><div class="meter"><div class="meter-label"><span>Official public leader · snapshot</span><strong>{leader_txt}</strong></div><div class="track"><span class="fill" style="width:{bar_a:.2f}%"></span></div></div><div class="meter"><div class="meter-label"><span>GEMSDOE32 B2 · user-reported</span><strong>0.2778</strong></div><div class="track"><span class="fill muted" style="width:{bar_b:.2f}%"></span></div></div></div><div class="contour" aria-hidden="true"><svg viewBox="0 0 150 150" fill="none"><g stroke="#8ebfa1" stroke-width="1" opacity=".7"><path d="M-10 105C20 104 19 56 53 59c31 3 25 45 58 42 17-1 30-21 50-14"/><path d="M-12 114c38-1 36-56 66-51 28 5 23 45 58 43 21-2 33-24 50-15"/><path d="M-12 123c44-1 40-61 68-56 26 5 22 45 57 44 25-1 35-26 50-16"/><path d="M-15 132c50-1 44-66 72-61 24 5 21 45 56 45 29 0 37-28 52-17"/><path d="M-15 140c56-1 48-71 74-65 23 5 21 44 55 46 32 1 39-30 53-18"/><path d="M-12 96c24 0 28-47 64-42 33 4 28 45 58 42 14-1 27-20 49-13"/></g><circle cx="77" cy="76" r="21" fill="#fff" stroke="#c5ddca"/><path d="m68 79 6-10 5 8 3-5 5 7" stroke="#3c8b67" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="88" cy="65" r="3" fill="#d0a55a"/></svg></div></div></div><div class="note-strip">The exact B2 array is D2.8 with all pixels within 2 catalogue pixels removed. <a href="research/why-b2-scored-2778.html">Read the forensic analysis →</a></div></article>
<article class="card"><div class="card-body"><div class="section-header"><div><h2>Submission pipeline</h2><p>Each gate needs evidence; a format pass is not approval.</p></div><span class="tag red">Not ready</span></div><ul class="gate-list"><li><span class="gate-icon">✓</span><div><div class="gate-title">Data restored</div><div class="gate-desc">Hash-pinned owner mirror, not an authenticated official copy</div></div><span class="gate-state">Checked</span></li><li><span class="gate-icon">✓</span><div><div class="gate-title">Historical priority-site audit</div><div class="gate-desc">Nine pinned files plus two registry witnesses</div></div><span class="gate-state">Checked</span></li><li><span class="gate-icon block">!</span><div><div class="gate-title">Literal novelty preflight</div><div class="gate-desc">Registered positive support prevents clearance</div></div><span class="gate-state block">Stop</span></li><li><span class="gate-icon wait">–</span><div><div class="gate-title">Canary, holdout and candidate TIFF</div><div class="gate-desc">Not run after the preflight stop</div></div><span class="gate-state">Not run</span></li></ul></div></article></div>'''


def focus_table():
    rows = sorted(portfolio['sites'], key=lambda r:float(r['user_reported_score']), reverse=True)
    trs = []
    for row in rows:
        filename = row['path'].rsplit('/',1)[-1]
        exact = row.get('decoded_exact_matches_in_focus') or []
        explanation = ('Exact decoded match: ' + ', '.join(exact)) if exact else (f"{row['max_3px_overlap_vs_other_focus']*100:.1f}% near {row['max_overlap_witness_site']}")
        trs.append(f'''<tr{(' class="champion"' if row['site']=='GEMSDOE32' else '')}><td data-label="Site / file"><a class="site-name" href="../site/sites/{e(row['site'])}.html">{e(row['site'])} ↗</a><a class="file-link" href="{e(row['download_url'])}" title="{e(filename)} — historical research only">{e(filename)} ↗</a></td><td data-label="Reported DTI"><span class="score">{e(row['user_reported_score'])}</span><span class="small-meta">USER-REPORTED</span></td><td data-label="Estimate"><span class="status-muted">Unavailable</span><span class="small-meta">no valid forecast</span></td><td data-label="Unique vs peers?"><span class="status-no">No</span><span class="small-meta">{e(explanation)}</span></td><td data-label="Action"><span class="status-no">Do not submit</span><span class="small-meta">historical reference</span></td></tr>''')
    changed = int(fresh.get('changed_count', 0))
    unknown = int(fresh.get('unknown_count', 0))
    checked = fresh.get('checked_utc', '')
    freshness_copy = f'{changed} of 9 site HEADs changed since the pinned audit; {unknown} checks unknown. Newer rasters have not been audited.'
    return f'''<section class="card table-card" id="priority-sites"><div class="table-heading"><div><h2>Nine priority sites</h2><p>The highest historical result supplied for each site. Scores are user-reported, not organizer-confirmed; files are for research only. Uniqueness is measured against other listed priority files.</p><p class="fresh-warning">{e(freshness_copy)} <a href="data/focus-freshness.json">HEAD check ↗</a> · <span class="freshness" data-captured="{e(checked)}" data-status="{('stale' if unknown else 'snapshot')}">Checked {e(checked)}</span></p></div><div class="table-tools"><span class="tag">9 sites</span><a class="text-link" href="data/portfolio.json">Audit JSON ↗</a></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Site / historical file</th><th scope="col">Reported DTI</th><th scope="col">Estimated score</th><th scope="col">Unique vs peers?</th><th scope="col">Action</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div><div class="table-footer"><div>Historical files may have NaN outside the footprint; none is a new submission.</div><div><a href="data/user-reported-ledger.csv">Download the broader user-reported ledger ↓</a></div></div></section>'''


def home():
    body = intro('Executive overview','Clarity before a <span>submission.</span>','A research dashboard for the DOE GEMS Prize, built around evidence and clear decisions.') + decision() + stats() + compare_section() + focus_table()
    body += '''<section class="brief-grid" aria-label="Research resources"><article class="card brief"><div class="brief-number">01</div><h3>Understand the stop</h3><p>A registered lattice gives a provable lower bound on overlap. A continuous prior blocks all nonempty support under the shared literal implementation.</p><a href="executive-summary.html#novelty">Explore the proof →</a></article><article class="card brief"><div class="brief-number">02</div><h3>Research the next lane</h3><p>Five ranked geological proposals, their layers, possible mimics and a blocked-validation protocol.</p><a href="research.html">View research →</a></article><article class="card brief"><div class="brief-number">03</div><h3>Check the evidence</h3><p>Competition requirements, source provenance and the difference between a format check and an organizer receipt.</p><a href="sources.html">Browse sources →</a></article></section><section class="dark-card"><p class="eyebrow">Next move</p><h2>Protect the slot. Resolve the rule.</h2><p>The current instructions require a literal all-registry stop, not a density exemption. No candidate or score will be invented to make the dashboard green. <a href="data/run-card.json">Read the negative run card →</a> · <a href="executive-summary/">See both rejected parallel files →</a> · <a href="../site/">Open nine individual evidence briefs →</a></p></section>'''
    return page('Overview','index.html',body,'Evidence-first DOE GEMS Prize research and submission status.')


def guide():
    w = portfolio['literal_registry_witness']
    d = portfolio['dense_probability_witness']
    body = intro('Executive summary','From research to <span>submission.</span>','A practical checklist for the moment a candidate actually clears every gate.') + decision()
    body += f'''<div class="guide-layout"><article class="card guide-card"><div class="section-header"><div><h2>How to submit, when approved</h2><p>No file is currently eligible. These steps do not authorize the historical references.</p></div><span class="tag red">Currently locked</span></div><ol><li><strong>Check the decision first.</strong> A new candidate must pass the surface and final-dot registry checks, every leakage canary, a comparable blocked holdout, and byte-bound format validation. Promotion to a weekly slot is a separate selector step.</li><li><strong>Download the exact approved file.</strong> Use the future candidate's single-band GeoTIFF or a ZIP containing only that GeoTIFF. Verify its SHA-256 against its receipt. There is no approved file to download today.</li><li><strong>Confirm the local format receipt.</strong> The official page requires EPSG:32611, 100 m, matching shape and transform, one float32 layer and values in [0,1]. The pinned shared gate has a known finite-NoData-in-footprint gap; our supplemental check blocks it but the upstream tool still needs a fix. Our conservative all-finite check is not proof that zero-outside meets the official null/NaN wording or that the portal will accept it.</li><li><strong>Open DrivenData.</strong> Sign in, enroll, choose <em>Submit → Make new submission</em>, select the approved file and enter the byte-bound short note (at most 140 characters for this project). Check the actual remaining weekly allowance on the submission page.</li><li><strong>Keep the receipt.</strong> Record the exact filename, hash, note, timestamp and organizer result. A local HOLDOUT-DTI or an unvalidated projection is never a live score.</li></ol><div class="callout">A previous upload returned “Predicted values must be in range [0, 1]”. Its actual cause is unknown without the rejected bytes. The read-back validator reports NaN, infinity, below-zero, above-one and masked-cell counts separately inside and outside the reference footprint. It never clips or silently repairs a raster.</div><p>With an authenticated official template: <code>python scripts/validate_tif.py candidate.tif --reference authenticated_sample.tif --strict-all-finite</code>. A format pass is not a uniqueness, holdout or slot approval.</p><p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Read the official format ↗</a></p></article>
<aside class="card guide-card" id="novelty"><div class="section-header"><div><h2>Why the gate is blocked</h2><p>Two independently reopened prior files.</p></div></div><p><strong>Binary lattice witness.</strong> {w['within_3px_pixels']:,} of {w['footprint_pixels']:,} footprint cells are within three pixels of a registered lattice dot. Only {w['outside_3px_pixels']:,} are outside. For {w['example_budget_distinct_dots']:,} distinct in-footprint dots, the minimum possible overlap is <strong>{w['minimum_possible_overlap_at_example_budget']*100:.2f}%</strong>, above the 70% limit.</p><p><strong>Continuous-prior witness.</strong> The shared literal implementation counts any finite positive prior pixel as support. A registered continuous prior is positive across the entire footprint. Under that implementation every nonempty candidate overlaps it completely; whether a continuous field should count as “dots” is unresolved, not silently exempted.</p><p><a href="{e(w['source'])}">Lattice source ↗</a> · <a href="{e(d['source'])}">Continuous prior ↗</a> · <a href="data/portfolio.json">Measured proof ↗</a></p><div class="callout">The binary-lattice budget bound does not prove every smaller raster fails. The continuous-prior result depends on the explicitly stated shared support definition.</div></aside></div>'''
    body += '<div style="height:20px"></div>' + focus_table()
    body += '''<section class="card guide-card"><h2>What remains unknown</h2><p>Private fault labels, a submission-page receipt linking each historical score to its exact bytes, organizer acceptance of the local export policy, the current weekly quota and a defensible cross-family leaderboard forecast are unavailable. The cached competition inputs are a hash-pinned owner mirror, not an independently authenticated download.</p><p><a href="data/run-card.json">Download the run card ↗</a> · <a href="data/b2_local_format.json">Historical B2 format receipt ↗</a> · <a href="sources.html">Official sources and irregularities ↗</a></p></section>'''
    return page('Executive summary','executive-summary.html',body,'Decision, nine-site scorecard, novelty proof, and submission instructions.')


def research():
    body = intro('Scientific research','Better questions. <span>Better evidence.</span>','Five ranked desk proposals; none is an executed or approved lane. H1 is provisional, and two concepts require external data not yet obtained.') + decision()
    cards = [
        ('01 · MEDIUM COST · H1 PROVISIONAL LANE','Depth-shifted gravity–magnetic discontinuity (H1)','Signed directional gradients at 300/600/1200 m: test whether a magnetic edge displaced along the gravity-edge normal by a bounded depth/dip proxy indicates a concealed fault. Uses iso_grav_anom, rtp, depth_to_base_surf (conductive base, not basement), det_elev.','Unfaulted lithologic contacts, dikes and flight-line striping.'),
        ('02 · MEDIUM COST','Conductive-flank asymmetry','Compare conductivity on opposite sides of a depth/gravity step, normalized by local background and depth — lateral flank asymmetry, not conductivity alone.','Clay-rich sediments, saline groundwater, non-faulted contacts.'),
        ('03 · LOW–MEDIUM COST','Slope asymmetry along buried edges','Opposite-side slope/curvature profiles perpendicular to a persistent gravity/magnetic edge, requiring consistent sign over ≥1 km strike.','Drainage incisions, alluvial fans, shorelines, roads and landslides.'),
        ('04 · HIGH COST · NOT YET VIABLE','Catchment-normalized drainage deflection','Repeated cross-channel deflections normalized by catchment size/lithology from an absolute-elevation DEM (requires USGS 3DEP tiles — not yet verified obtainable).','Lithologic erosion, paleochannels, roads/terraces.'),
        ('05 · HIGH COST · NOT YET VIABLE','Flight-line repeatability veto','Re-grid GeoDAWN flight vs. tie-line magnetics independently; retain only edges reproducible across acquisition directions (CC0, but lines not yet verified obtainable).','Real contacts/dikes; uneven survey geometry.'),
    ]
    body += '<div class="research-list">' + ''.join(f'''<article class="card research-item"><span class="num">{e(n)}</span><h2>{e(t)}</h2><p>{e(p)}</p><p><strong>Non-fault mimic:</strong> {e(m)}</p><span class="tag">Proposed · not tested</span></article>''' for n,t,p,m in cards) + '</div><div style="height:20px"></div>'
    body += '''<section class="card guide-card"><div class="section-header"><div><h2>Research guardrails</h2><p>These are hypotheses, not geological discoveries or leaderboard forecasts.</p></div><a class="text-link" href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses.md">Full preregistration notes →</a></div><p>Once the literal novelty policy and method lane are resolved, derive catalogue features from visible faults only, hide buffered whole fault components, and run each feature-alone leakage canary. Compare pooled HOLDOUT-DTI against a matched incumbent and report the evaluator, withheld count and spatial-block 95% CI. Do not use a holdout statistic as an organizer score.</p><ul class="source-list"><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN data release ↗</a> — magnetic and radiometric survey design and limitations.</li><li><a href="https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa">USGS structural-discontinuity study ↗</a> — stress/strain and hydrothermal settings.</li><li><a href="https://gdr.openei.org/submissions/1391">GDR INGENIOUS compilation ↗</a> — geothermal observations, data sources and license.</li><li><a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP ↗</a> — free elevation data; source bytes have not been independently fetched here.</li></ul></section>'''
    return page('Research','research.html',body,'Ranked geothermal fault-mapping hypotheses, mimics, sources and safeguards.')

def sources():
    body = intro('Evidence & sources','Trace each <span>claim.</span>','Official requirements, scientific references, and the limits of our own measurements.') + decision()
    rows = [
      ('Target', 'Predict previously unmapped faults indicative of geothermal resources; a fault prediction is not proof of a geothermal vent.', 'DrivenData problem description', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/'),
      ('Format', 'Single float32 band, EPSG:32611, 100 m grid, matching bounds and values in [0,1]; the public text describes null/NaN outside bounds.', 'Official submission format', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format'),
      ('Metric', 'Distance-weighted Tversky uses a 300 m triangular kernel with alpha 0.2 and beta 0.8.', 'Official metric and equations', 'https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric'),
      ('Fault masking', 'Staff say known USGS/INGENIOUS fault pixels are excluded in both rounds; no two-pixel buffer is confirmed.', 'Organizer staff clarification', 'https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516'),
      ('Rules', 'External data must have an appropriate use-and-sharing license; verify current eligibility, deadlines and slot limits before submission.', 'Official overview and rules', 'https://www.drivendata.org/competitions/306/competition-doe-gems/'),
      ('Timing caution', 'The overview lists 3 December 2026, 23:59 UTC; the rules separately mention 5 p.m. ET for final content or the submission form. Whether those govern different deliverables is unverified.', 'Official rules PDF, Appendix A.1', 'https://docs.nlr.gov/docs/fy26osti/96647.pdf'),
      ('Leaderboard', 'The public leaderboard is time-varying and is not a receipt identifying a particular historical file.', 'Official public leaderboard', 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'),
      ('Reference model', 'The organizer reference solution supports CPU and GPU; the unavailable GPU is not by itself proof that all experiments are impossible.', 'Organizer reference solution', 'https://github.com/drivendataorg/gems-prize-reference-solution'),
      ('Geophysics', 'GeoDAWN documents magnetic and radiometric surveys, acquisition geometry and limitations; the release is CC0.', 'USGS GeoDAWN release', 'https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and'),
      ('Geothermal data', 'The INGENIOUS compilation lists geothermal observations and source licenses; binary access and coverage were not verified in this sandbox.', 'GDR INGENIOUS release', 'https://gdr.openei.org/submissions/1391'),
    ]
    trs = ''.join(f'<tr><td data-label="Topic"><strong>{e(topic)}</strong></td><td data-label="Claim"><span>{e(claim)}</span></td><td data-label="Source"><a href="{e(url)}">{e(label)} ↗</a></td></tr>' for topic,claim,label,url in rows)
    body += f'''<section class="card table-card"><div class="table-heading"><div><h2>Official source inventory</h2><p>Follow each source for the full wording; a local observation never substitutes for organizer acceptance.</p></div><span class="tag">Sources</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Topic</th><th scope="col">What the source supports</th><th scope="col">Verify</th></tr></thead><tbody>{trs}</tbody></table></div></section>'''
    body += '''<section class="card guide-card"><h2>GEMSDOE32 B2: what was measured</h2><p>We reopened and hash-checked the historical B2 and D2.8 arrays. B2's 37,654 positive cells equal D2.8's 44,090 cells after removing 6,436 within two pixels of the mirrored catalogue. That is reproducible lineage, not proof that those exact bytes were uploaded.</p><p>Sparse predictions could reduce false-positive mass while preserving coverage under the official 300 m kernel. The unverified 0.2778 claim, unavailable private truth and lack of a per-file receipt do not establish causation or predict a new score.</p><p><a href="data/portfolio.json">Measured portfolio and lineage ↗</a> · <a href="data/b2_local_format.json">Historical local format receipt ↗</a> · <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">Owner's historical page ↗</a></p></section>'''
    body += '''<section class="card guide-card"><h2>Provenance and access</h2><p>The sample grid, labels and 19-band feature stack were restored from owner mirrors at pinned hashes, not an authenticated organizer download. The data page requires login; official GDR and USGS binary access was not verified in this sandbox. Large data and cached template code are excluded from Git.</p><ul class="source-list"><li><a href="data/data_preparation.json">Data restoration receipt ↗</a> — pinned file hashes and local paths.</li><li><a href="data/feature_cache.json">Feature cache inventory ↗</a> — band descriptions and limitations.</li><li><a href="data/dense_prior_certificate.json">Continuous-prior certificate ↗</a> — literal overlap preflight evidence.</li><li><a href="data/focus-freshness.json">Priority-site HEAD check ↗</a> — update detection only, not a new raster audit.</li><li><a href="data/shared_registry_index_summary.json">Shared index scope ↗</a> — historical metadata only; not a complete or current raster audit.</li><li><a href="data/parallel_range_diagnostics_20261027.json">Rejected TIFF range and mask diagnostic ↗</a> — exact saved bytes, not organizer acceptance.</li><li><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/docs/research/evidence-and-sources.md">Full evidence notes on GitHub ↗</a> — equations, irregularities and additional sources.</li></ul></section>'''
    return page('Sources','sources.html',body,'Official competition and scientific sources with measured evidence and provenance.')


for name, content in [('index.html',home()),('executive-summary.html',guide()),('research.html',research()),('sources.html',sources())]:
    (DOCS / name).write_text(content,encoding='utf-8')
    print(f'built {DOCS / name}')

# Render the other session's B2 analysis from its reviewed Markdown source.
# The base preserves existing /docs/ navigation from this nested URL.
b2_source = DOCS / 'research/why-b2-scored-2778.md'
if b2_source.is_file():
    b2_body = markdown.markdown(b2_source.read_text(encoding='utf-8'), extensions=['sane_lists'])
    b2_page = page('Why B2 may have scored well', 'research.html',
                   f'<article class="card guide-card research-prose">{b2_body}</article>',
                   'An evidence-labeled B2 lineage and metric analysis.', base='../')
    (DOCS / 'research/why-b2-scored-2778.html').write_text(b2_page, encoding='utf-8')
    print('built', DOCS / 'research/why-b2-scored-2778.html')
