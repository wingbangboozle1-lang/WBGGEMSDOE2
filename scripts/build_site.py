#!/usr/bin/env python3
"""Build the static, evidence-first GitHub Pages site without a web framework."""
from __future__ import annotations
import datetime as dt
from html import escape
import json
from pathlib import Path
import shutil
import sys
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
portfolio = json.loads((DOCS / 'data/portfolio.json').read_text())
leader = json.loads((DOCS / 'data/leaderboard.json').read_text())
fresh = json.loads((DOCS / 'data/focus-freshness.json').read_text())
run = json.loads((DOCS / 'data/run-card.json').read_text())
hypothesis_data = json.loads((ROOT / 'config/research_hypotheses.json').read_text())
# Fail closed: this renderer is specifically a negative-run dashboard. A future
# candidate cannot silently inherit a green button by editing a JSON boolean.
if run.get('verdict') != 'negative' or run.get('ok_to_submit') is not False or run.get('raster_sha256') is not None:
    raise ValueError('This dashboard renders only the audited negative run; review and implement a byte-bound release before changing status.')
if (hypothesis_data.get('method_lane', {}).get('status') != 'UNASSIGNED'
        or not 3 <= len(hypothesis_data.get('hypotheses', [])) <= 5):
    raise ValueError('Research hypotheses or lane status changed; update the reviewed narrative before publishing.')
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
if (review.get('ok_to_submit') is not False or review.get('sha256') != run.get('parallel_session', {}).get('rejected_candidate_sha256')
        or review.get('format', {}).get('masked_inside') != 5132809
        or round(review.get('literal_overlap_3px', {}).get('lattice', 0), 6) != 0.993838):
    raise ValueError('Parallel-file evidence changed; review the static narrative before publishing.')
if (conduit.get('ok_to_submit') is not False or conduit.get('sha256') != run.get('conduit_parallel_session', {}).get('rejected_candidate_sha256')
        or round(conduit.get('witnesses', {}).get('13GEMSDOE', {}).get('source_threshold_ge_0_5', {}).get('fraction', 0), 6) != 0.998726):
    raise ValueError('Conduit-file evidence changed; review the static narrative before publishing.')
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.release import load_negative_release
from build_release import dphs_evidence
release_audit = load_negative_release(ROOT)
_, dphs_row, dphs_holdout = dphs_evidence(ROOT, release_audit)

for name in ('data_preparation.json', 'feature_cache.json', 'b2_local_format.json', 'dense_prior_certificate.json', 'parallel_review.json', 'parallel_candidate_audit.json', 'conduit_review.json', 'shared_registry_index_summary.json', 'parallel_range_diagnostics_20261027.json', 'public_leaderboard_observation_20261027.json', 'feature_semantics_review.json', 'organizer_reference_review.json', 'public_leaderboard_recheck_20261027.json', 'request_claim_conflicts.json'):
    source = ROOT / 'evidence' / name
    if source.is_file():
        shutil.copyfile(source, DOCS / 'data' / name)
shutil.copyfile(ROOT / 'config/research_hypotheses.json', DOCS / 'data/research_hypotheses.json')


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
    nav = [('index.html','Overview'),('release.html','Download status'),('executive-summary.html','Executive summary'),('research.html','Research'),('sources.html','Sources')]
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
    stamp = e(dt.datetime.fromisoformat(release_audit['generated_utc'].replace('Z', '+00:00')).astimezone(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    return f'''<div class="intro"><div><p class="eyebrow">{e(label)}</p><h1>{title}</h1><p>{e(subtitle)}</p></div><div class="intro-meta">Release-byte audit<br><strong>{stamp}</strong></div></div>'''


H3_SUB = json.loads((ROOT / 'evidence/h3_submission.json').read_text())

def h3_banner(suffix: str = '') -> str:
    """Historical approvals are revoked, not alternatives for a user to pick."""
    return f'''<section class="card guide-card" aria-labelledby="historical-heading{suffix}"><h2 id="historical-heading{suffix}">DZ-16 and H3-PACK: former approvals revoked</h2><p>Their own literal registry tests failed. A density-normalized gate or nine-site-only comparison cannot override this prompt's all-registry stop. No defensible leaderboard estimate is available.</p><p><a href="release.html#research-downloads">Existing research TIFFs, exact hashes and independent byte checks →</a> · <a href="submission/index.html">Reconciled historical lane →</a></p></section>'''


MSPTCD_CARD = json.loads((DOCS / 'data/RUN_CARD_MSPTCD.json').read_text())


def msptcd_banner(suffix: str = '') -> str:
    """Historical campaign results do not validate corrected local features."""
    h = MSPTCD_CARD['holdout']
    return f'''<section class="card guide-card" aria-labelledby="msptcd-heading{suffix}"><h2 id="msptcd-heading{suffix}">Historical MSPTCD: source-reported HOLDOUT-DTI, not a release</h2><p><strong>HOLDOUT-DTI {h['dti']:.6f}</strong>, 95% CI [{h['ci95'][0]:.6f}, {h['ci95'][1]:.6f}], {h['withheld_positive_pixels']:,} withheld positives, evaluator <code>{e(h['evaluator_version'])}</code>; not independently reproduced in this review. The v1 orientation feature treated perpendicular edges as coherent; corrected v2 has no measured holdout result. A passed AUC canary does not prove absence of leakage.</p><p><a href="msptcd/index.html">Corrected historical report →</a> · <a href="release.html">Current download decision →</a></p></section>'''


def dphs_banner(suffix: str = '') -> str:
    """Historic source result plus independently measured rejection, not a forecast."""
    h = dphs_holdout
    return f'''<section class="card guide-card" aria-labelledby="dphs-heading{suffix}"><h2 id="dphs-heading{suffix}">Historical DPHS: research only — DO NOT SUBMIT</h2><p><strong>SOURCE-REPORTED HOLDOUT-DTI {h['dti']:.6f}</strong>, 95% CI [{h['ci95'][0]:.6f}, {h['ci95'][1]:.6f}], {h['withheld_positive_pixels']:,} withheld positives, evaluator <code>{e(h['evaluator_version'])}</code>; the campaign and its canaries were not independently replayed. A passed canary does not prove no leakage. On independent readback, {dphs_row['lattice_overlap_3px']*100:.3f}% of this file's positive footprint pixels lie within three pixels of the registered binary lattice, exceeding the literal 70% stop. The old 467-raster audit and regression are not current uniqueness clearance or a leaderboard forecast.</p><p><a href="dphs/index.html">Open the DPHS research record &amp; nine-site table →</a> · <a href="dphs/how-to-submit.html">Future submission checklist →</a> · <a href="dphs/executive-summary.html">B2 evidence and uncertainty →</a></p></section>'''


DISTAL_CARD_PATH = DOCS / 'data/run-card-distal-oof.json'
DISTAL_CARD = json.loads(DISTAL_CARD_PATH.read_text()) if DISTAL_CARD_PATH.is_file() else None


def distal_banner(suffix: str = '') -> str:
    """WBG2-DISTAL lane: holdout-best 100% OOF map, promoted to selector only (no slot spent)."""
    if DISTAL_CARD is None:
        return ''
    det = DISTAL_CARD['evidence_details']
    est = det['empirical_estimate']
    scope = det['uniqueness_audit_scope']
    return f'''<section class="card guide-card" aria-labelledby="distal-oof-heading{suffix}"><h2 id="distal-oof-heading{suffix}">WBG2-DISTAL 100% spatial-OOF: {DISTAL_CARD['holdout_dti']:.4f} HOLDOUT-DTI — selector decision required, DO NOT SUBMIT automatically</h2><p><strong>HOLDOUT-DTI {DISTAL_CARD['holdout_dti']:.6f}</strong>, 95% CI [{DISTAL_CARD['ci95'][0]:.6f}, {DISTAL_CARD['ci95'][1]:.6f}], 60,988 withheld positives, evaluator <code>gems57-pooled-hide-v2</code> (61/61 canaries &le; 0.6180; strict whole-array [0,1]/zero-NaN PASS). New repo holdout best; unique vs all 9 focus champions (max {max(det['focus_primary_overlap'].values()):.3f}) and all {scope['sparse_peer_rasters']} sparse peer-budget fleet rasters (max {scope['sparse_peer_max_overlap']:.3f}); fails only the literal dense/blanket rule that also rejects GEMSDOE32 B2 itself. EMPIRICAL-ESTIMATE {est['point']:.4f} (95% PI [{est['pi95'][0]:.4f}, {est['pi95'][1]:.4f}]), not a score; 0 slots used.</p><p><a href="distal/index.html">Open DISTAL selector decision table →</a> · <a href="distal/executive-summary.html">Executive summary →</a> · <a href="distal/how-to-submit.html">Selector submission steps →</a></p></section>'''


def decision(suffix: str = ''):
    return f'''<section class="banner" data-release-status="blocked" aria-labelledby="decision-heading{suffix}"><div class="banner-icon">{icon('shield')}</div><div class="banner-copy"><p class="banner-label">Authoritative all-lane decision · NEGATIVE</p><h2 id="decision-heading{suffix}">No file is approved for submission. DO NOT SUBMIT.</h2><p>Every audited TIFF fails the literal all-registry duplicate gate under finite-positive support. No method lane or weekly slot is authorized. Former DZ-16 and H3-PACK approvals are revoked.</p></div><div class="actions"><button class="button" disabled>{icon('download')} No submission file</button><a class="text-link" href="release.html">Research downloads &amp; byte audit →</a><a class="text-link" href="readiness.html">Checkout readiness &amp; blockers →</a></div></section>'''


def concurrent_banner(suffix: str = '') -> str:
    item = run['concurrent_distal_candidate']
    return f'''<section class="card guide-card" aria-labelledby="distal-heading{suffix}"><h2 id="distal-heading{suffix}">Concurrent distal research file — DO NOT SUBMIT</h2><p>A separate session added a 6,000-dot raster. The independent recheck measured <strong>{item['lattice_overlap_3px']*100:.3f}%</strong> overlap with the binary lattice (below 70%) but <strong>{item['continuous_prior_overlap_3px']*100:.1f}%</strong> with the continuous prior under literal finite-positive support. The prior's interpretation remains unresolved, not exempted.</p><p>No pre-placement surface, canaries or matched holdout were replayed; a local format pass is not organizer acceptance. <a href="candidate.html">Read the scoped artifact audit →</a></p></section>'''


def leaderboard_stale():
    captured = leader.get('captured_utc')
    if leader.get('status') != 'fresh' or not captured:
        return True
    try:
        stamp = dt.datetime.fromisoformat(captured.replace('Z', '+00:00'))
        age = (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds()
        return age > 24 * 60 * 60 or age < -300
    except (TypeError, ValueError):
        return True


def freshness():
    captured = leader.get('captured_utc') or ''
    status = 'stale' if leaderboard_stale() else 'fresh'
    label = 'STALE public-leaderboard snapshot' if status == 'stale' else 'Public-leaderboard snapshot'
    return f'<span class="freshness" data-captured="{e(captured)}" data-status="{status}">{label} · {e(captured or "time unavailable")}</span>'


def score_evidence_notice():
    value = leader.get('top_public_dti')
    observed = leader.get('captured_utc') or 'timestamp unavailable'
    snapshot = (f'{float(value):.4f}' if isinstance(value, (int, float)) and not isinstance(value, bool)
                and 0 <= value <= 1 else 'unavailable')
    stale = leaderboard_stale()
    status = 'stale' if stale else 'fresh at the recorded capture time'
    return f'''<div class="callout" role="status"><strong>Score-source conflict.</strong> The prompt's 0.3195 and 0.4413 “current high” figures are USER-SUPPLIED and conflict. The saved {status.upper()} ORGANIZER-PUBLISHED PUBLIC-LEADERBOARD SNAPSHOT is {snapshot}, observed {e(observed)}; it is not an ORGANIZER-CONFIRMED receipt for any TIFF and is not HOLDOUT-DTI. The dated public observation can change; check the official source for the latest value.</div>'''


def stats():
    score = leader.get('top_public_dti')
    display = f'{float(score):.4f}' if isinstance(score,(float,int)) and not isinstance(score,bool) and 0 <= score <= 1 else 'Unavailable'
    return f'''<section class="stats" aria-label="Key evidence"><article class="stat"><div class="stat-top">Last public-leaderboard snapshot <span class="stat-icon">{icon('chart')}</span></div><div class="stat-value">{display}</div><div class="stat-sub">{freshness()} · <a href="{e(leader['source_url'])}">source ↗</a> · not a per-file receipt</div></article>
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
    return f'''<div class="grid"><article class="card"><div class="card-body"><div class="section-header"><div><h2>What the best result tells us</h2><p>Historical context, not a prediction.</p></div><span class="tag">Evidence review</span></div><div class="compare"><div class="compare-text"><h3>0.2778 <span style="font-size:12px;color:#97a69b;letter-spacing:0">user-reported</span></h3><p>The GEMSDOE32 B2 reference is the strongest result supplied across the nine sites. Its sparse dots may reduce redundant false-positive cost, but the hidden labels and upload receipt are unavailable.</p><div class="meter"><div class="meter-label"><span>{'Stale' if leaderboard_stale() else 'Recorded'} public-leaderboard snapshot</span><strong>{leader_txt}</strong></div><div class="track"><span class="fill" style="width:{bar_a:.2f}%"></span></div></div><div class="meter"><div class="meter-label"><span>GEMSDOE32 B2 · user-reported</span><strong>0.2778</strong></div><div class="track"><span class="fill muted" style="width:{bar_b:.2f}%"></span></div></div></div><div class="contour" aria-hidden="true"><svg viewBox="0 0 150 150" fill="none"><g stroke="#8ebfa1" stroke-width="1" opacity=".7"><path d="M-10 105C20 104 19 56 53 59c31 3 25 45 58 42 17-1 30-21 50-14"/><path d="M-12 114c38-1 36-56 66-51 28 5 23 45 58 43 21-2 33-24 50-15"/><path d="M-12 123c44-1 40-61 68-56 26 5 22 45 57 44 25-1 35-26 50-16"/><path d="M-15 132c50-1 44-66 72-61 24 5 21 45 56 45 29 0 37-28 52-17"/><path d="M-15 140c56-1 48-71 74-65 23 5 21 44 55 46 32 1 39-30 53-18"/><path d="M-12 96c24 0 28-47 64-42 33 4 28 45 58 42 14-1 27-20 49-13"/></g><circle cx="77" cy="76" r="21" fill="#fff" stroke="#c5ddca"/><path d="m68 79 6-10 5 8 3-5 5 7" stroke="#3c8b67" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="88" cy="65" r="3" fill="#d0a55a"/></svg></div></div></div><div class="note-strip">The exact B2 array is D2.8 with all pixels within 2 catalogue pixels removed. <a href="research/why-b2-scored-2778.html">Read the forensic analysis →</a></div></article>
<article class="card"><div class="card-body"><div class="section-header"><div><h2>Submission pipeline</h2><p>Each gate needs evidence; a format pass is not approval.</p></div><span class="tag red">Not ready</span></div><ul class="gate-list"><li><span class="gate-icon">✓</span><div><div class="gate-title">Data restored</div><div class="gate-desc">Hash-pinned owner mirror, not an authenticated official copy</div></div><span class="gate-state">Checked</span></li><li><span class="gate-icon">✓</span><div><div class="gate-title">Historical priority-site audit</div><div class="gate-desc">Nine focus files; 13 pinned rejection witnesses</div></div><span class="gate-state">Checked</span></li><li><span class="gate-icon block">!</span><div><div class="gate-title">Literal novelty preflight</div><div class="gate-desc">Registered positive support prevents clearance</div></div><span class="gate-state block">Stop</span></li><li><span class="gate-icon wait">–</span><div><div class="gate-title">Canary, holdout and candidate TIFF</div><div class="gate-desc">Not run after the preflight stop</div></div><span class="gate-state">Not run</span></li></ul></div></article></div>'''


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
    body = intro('Executive overview','Clarity before a <span>submission.</span>','A research dashboard for the DOE GEMS Prize, built around evidence and clear decisions.') + decision() + distal_banner() + concurrent_banner() + dphs_banner() + h3_banner() + msptcd_banner() + stats() + score_evidence_notice() + compare_section() + focus_table()
    body += '''<section class="brief-grid" aria-label="Research resources"><article class="card brief"><div class="brief-number">01</div><h3>Understand the stop</h3><p>A registered lattice gives a provable lower bound on overlap. A continuous prior blocks all nonempty support under the shared literal implementation.</p><a href="executive-summary.html#novelty">Explore the proof →</a></article><article class="card brief"><div class="brief-number">02</div><h3>Review the research shortlist</h3><p>Four ranked, untested proposals. No single method lane has been assigned; no experiment or submission slot is authorized.</p><a href="research.html">View proposals →</a></article><article class="card brief"><div class="brief-number">03</div><h3>Check the evidence</h3><p>Competition requirements, source provenance and the difference between a format check and an organizer receipt.</p><a href="sources.html">Browse sources →</a></article></section><section class="dark-card"><p class="eyebrow">Next move</p><h2>Protect the slot. Resolve the rule.</h2><p>The current instructions require a literal all-registry stop, not a density exemption. No candidate or score will be invented to make the dashboard green. <a href="data/run-card.json">Read the negative run card →</a> · <a href="release.html#research-downloads">See all rejected research files →</a> · <a href="../site/">Open nine individual evidence briefs →</a></p></section>'''
    body += '''<section class="card" id="download"><div class="card-body"><div class="section-header"><div><h2>Research downloads — DO NOT SUBMIT</h2><p>No existing TIFF or ZIP is approved. Do not use the former H3/DZ-16 download recommendation.</p></div><span class="tag red">All blocked</span></div><p>Review the exact saved TIFF hashes, ZIP members, format/mask counts and literal rejection witnesses. These are historical research artifacts, not a new submission.</p><p><a class="text-link" href="release.html#research-downloads">Open research-only files and byte audit →</a> · <a class="text-link" href="data/run-card.json">Download the current negative run card →</a></p></div></section>'''

    return page('Overview','index.html',body,'Evidence-first DOE GEMS Prize research and submission status.')


def guide():
    w = portfolio['literal_registry_witness']
    d = portfolio['dense_probability_witness']
    body = intro('Executive summary','From research to <span>submission.</span>','A practical checklist for the moment a candidate actually clears every gate.') + decision('-guide') + concurrent_banner('-guide') + dphs_banner('-guide') + h3_banner('-guide') + msptcd_banner('-guide') + score_evidence_notice()
    body += f'''<div class="guide-layout"><article class="card guide-card"><div class="section-header"><div><h2>How to submit, when approved</h2><p>No file is currently eligible. These steps do not authorize the historical references.</p></div><span class="tag red">Currently locked</span></div><ol><li><strong>Check the decision first.</strong> A new candidate must pass the surface and final-dot registry checks, every leakage canary, a comparable blocked holdout, and byte-bound format validation. Promotion to a weekly slot is a separate selector step.</li><li><strong>Download the exact approved file.</strong> Use the future candidate's single-band GeoTIFF or a ZIP containing only that GeoTIFF. Verify its SHA-256 against its receipt. There is no approved file to download today.</li><li><strong>Confirm the local format receipt.</strong> The official page requires EPSG:32611, 100 m, matching shape and transform, one float32 layer and values in [0,1]. The pinned shared gate has a known finite-NoData-in-footprint gap; our supplemental check blocks it but the upstream tool still needs a fix. Our conservative all-finite check is not proof that zero-outside meets the official null/NaN wording or that the portal will accept it.</li><li><strong>Open DrivenData.</strong> Sign in, enroll, open this competition’s submission form (the authenticated menu labels were not inspected), and select the approved file and enter the byte-bound short note (at most 140 characters for this project). Check the actual remaining weekly allowance on the submission page.</li><li><strong>Keep the receipt.</strong> Record the exact filename, hash, note, timestamp and organizer result. A local HOLDOUT-DTI or an unvalidated projection is never a live score.</li></ol><div class="callout">A previous upload returned “Predicted values must be in range [0, 1]”. Its actual cause is unknown without the rejected bytes. The read-back validator reports NaN, infinity, below-zero, above-one and masked-cell counts separately inside and outside the reference footprint. It never clips or silently repairs a raster.</div><p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Read the official format ↗</a></p></article>
<aside class="card guide-card" id="novelty"><div class="section-header"><div><h2>Why the gate is blocked</h2><p>Two independently reopened prior files.</p></div></div><p><strong>Binary lattice witness.</strong> {w['within_3px_pixels']:,} of {w['footprint_pixels']:,} footprint cells are within three pixels of a registered lattice dot. Only {w['outside_3px_pixels']:,} are outside. For {w['example_budget_distinct_dots']:,} distinct in-footprint dots, the minimum possible overlap is <strong>{w['minimum_possible_overlap_at_example_budget']*100:.2f}%</strong>, above the 70% limit.</p><p><strong>Continuous-prior witness.</strong> The shared literal implementation counts any finite positive prior pixel as support. A registered continuous prior is positive across the entire footprint. Under that implementation every nonempty candidate overlaps it completely; whether a continuous field should count as “dots” is unresolved, not silently exempted.</p><p><a href="{e(w['source'])}">Lattice source ↗</a> · <a href="{e(d['source'])}">Continuous prior ↗</a> · <a href="data/portfolio.json">Measured proof ↗</a></p><div class="callout">The binary-lattice budget bound does not prove every smaller raster fails. The continuous-prior result depends on the explicitly stated shared support definition.</div></aside></div>'''
    body += '<div style="height:20px"></div>' + focus_table()
    body += '''<section class="card guide-card"><h2>What remains unknown</h2><p>Private fault labels, a submission-page receipt linking each historical score to its exact bytes, organizer acceptance of the local export policy, the current weekly quota and a defensible cross-family leaderboard forecast are unavailable. The cached competition inputs are a hash-pinned owner mirror, not an independently authenticated download.</p><p><a href="data/run-card.json">Download the run card ↗</a> · <a href="data/b2_local_format.json">Historical B2 format receipt ↗</a> · <a href="sources.html">Official sources and irregularities ↗</a></p></section>'''
    return page('Executive summary','executive-summary.html',body,'Decision, nine-site scorecard, novelty proof, and submission instructions.')


def research():
    lane = hypothesis_data['method_lane']
    body = intro('Scientific research','Better questions. <span>Better evidence.</span>','Four qualitative proposals for future testing. None is implemented, validated, or assigned as the method lane.') + decision()
    body += f'''<section class="card guide-card"><div class="section-header"><div><h2>Method lane: {e(lane['status'])}</h2><p>Ranked ideas are not an authorization to choose or run one.</p></div><span class="tag red">No experiment cleared</span></div><p>{e(lane['reason'])}</p><p>{e(hypothesis_data['ranking_basis'])}</p><p>{e(hypothesis_data['novelty_scope'])}</p></section><div style="height:20px"></div>'''
    cards = []
    for h in sorted(hypothesis_data['hypotheses'], key=lambda row: row['potential_rank']):
        layers = '; '.join(h['layers'])
        external = h.get('external_data')
        external_html = ''
        if external:
            external_html = f'<p><strong>External source/access:</strong> <a href="{e(external["url"])}">{e(external["source"])} ↗</a>. {e(external["access_check"])}</p>'
        sources = ''.join(f'<li><a href="{e(url)}">Source for review ↗</a></li>' for url in h.get('sources', []))
        cards.append(f'''<article class="card research-item"><span class="num">{e(h['id'])} · QUALITATIVE PRIOR RANK {h['potential_rank']} · {e(h['implementation_cost']).upper()} COST</span><h2>{e(h['title'])}</h2><p><strong>Expected spatially blocked HOLDOUT-DTI potential:</strong> {e(h['potential_label'])}; not a leaderboard score estimate.</p><p><strong>Layers:</strong> {e(layers)}</p><p><strong>Physical signature:</strong> {e(h['signature'])}</p><p><strong>Why it could target a catalogue-missing fault:</strong> {e(h['why_uncatalogued'])}</p><p><strong>Difference from reviewed work:</strong> {e(h['difference_from_reviewed_methods'])}</p><p><strong>Named non-fault mimic:</strong> {e(h['non_fault_mimic'])}</p><p><strong>Data/access status:</strong> {e(h['data_status'])}</p>{external_html}<ul class="source-list">{sources}</ul><span class="tag">Proposal only · not tested</span></article>''')
    body += '<div class="research-list">' + ''.join(cards) + '</div><div style="height:20px"></div>'
    body += '''<section class="card guide-card"><div class="section-header"><div><h2>Research guardrails</h2><p>These are proposals, not geological discoveries or leaderboard forecasts.</p></div><a class="text-link" href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses.md">Full research notes →</a> · <a class="text-link" href="data/research_hypotheses.json" download>Structured JSON ↓</a></div><p>No holdout can be run until the lane, registry interpretation, authenticated data and shared cache are available. For any future authorized experiment, derive catalogue features from visible faults only, withhold whole fault segments plus a buffer, mask visible faults pixel-exactly, and run each feature-alone leakage canary. Use the pinned shared evaluator and compare pooled HOLDOUT-DTI against a matched incumbent on the same folds; report evaluator version, withheld-positive count and spatial-block 95% CI. A holdout statistic is not an organizer score.</p><ul class="source-list"><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem and layer inventory ↗</a> — fault traces are the target, not geothermal vents.</li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release ↗</a> — source metadata; line-level data were not obtained here.</li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS release ↗</a> — source/access notes in the register.</li><li><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP products ↗</a> — exact tile coverage remains unverified.</li></ul></section>'''
    return page('Research','research.html',body,'Ranked geothermal fault-mapping hypotheses, mimics, sources and safeguards.')

def sources():
    body = intro('Evidence & sources','Trace each <span>claim.</span>','Official requirements, scientific references, and the limits of our own measurements.') + decision('-sources') + h3_banner('-sources')
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
    body += '''<section class="card guide-card"><h2>GEMSDOE32 B2: what was measured</h2><p>We reopened and hash-checked the historical B2 and D2.8 arrays. B2's 37,654 positive cells equal D2.8's 44,090 cells after removing 6,436 within two pixels of the mirrored catalogue. That is reproducible lineage, not proof that those exact bytes were uploaded.</p><p>Sparse predictions could reduce false-positive mass while preserving coverage under the official 300 m kernel. The unverified 0.2778 claim, unavailable private truth and lack of a per-file receipt do not establish causation or predict a new score.</p><p><a href="data/portfolio.json">Measured portfolio and lineage ↗</a> · <a href="data/b2_local_format.json">Historical local format receipt ↗</a> · <a href="research/why-b2-scored-2778.html">Why the 0.2778 claim is plausible, not proven ↗</a> · <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">Owner's historical page ↗</a></p></section>'''
    body += '''<section class="card guide-card"><h2>Provenance and access</h2><p>The sample grid, labels and 19-band feature stack were restored from owner mirrors at pinned hashes, not an authenticated organizer download. The data page requires login; official GDR and USGS binary access was not verified in this sandbox. Large data and cached template code are excluded from Git.</p><ul class="source-list"><li><a href="data/data_preparation.json">Data restoration receipt ↗</a> — pinned file hashes and local paths.</li><li><a href="data/feature_cache.json">Feature cache inventory ↗</a> — band descriptions and limitations.</li><li><a href="data/dense_prior_certificate.json">Continuous-prior certificate ↗</a> — literal overlap preflight evidence.</li><li><a href="data/focus-freshness.json">Priority-site HEAD check ↗</a> — update detection only, not a new raster audit.</li><li><a href="data/shared_registry_index_summary.json">Shared index scope ↗</a> — historical metadata only; not a complete or current raster audit.</li><li><a href="data/parallel_range_diagnostics_20261027.json">Rejected TIFF range and mask diagnostic ↗</a> — saved bytes, not organizer acceptance.</li><li><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/docs/research/evidence-and-sources.md">Full evidence notes on GitHub ↗</a> — equations, irregularities and additional sources.</li></ul></section>'''
    return page('Sources','sources.html',body,'Official competition and scientific sources with measured evidence and provenance.')


for name, content in [('index.html',home()),('executive-summary.html',guide()),('research.html',research()),('sources.html',sources())]:
    (DOCS / name).write_text(content,encoding='utf-8')
    print(f'built {DOCS / name}')

# Render the byte-audited B2 explanation at the existing nested URL.
b2_source = DOCS / 'research/why-b2-scored-2778.md'
if b2_source.is_file():
    b2_body = markdown.markdown(b2_source.read_text(encoding='utf-8'), extensions=['sane_lists'])
    b2_page = page('Why B2 may have scored well', 'research.html',
                   f'<article class="card guide-card research-prose">{b2_body}</article>',
                   'An evidence-labeled B2 lineage and metric analysis.', base='../')
    (DOCS / 'research/why-b2-scored-2778.html').write_text(b2_page.replace('href="#main"', 'href="research/why-b2-scored-2778.html#main"'), encoding='utf-8')
    print('built', DOCS / 'research/why-b2-scored-2778.html')

# Preserve both URLs from the concurrent session, but render the qualified
# source instead of its unverified score projection and causal claims.
distal_source = ROOT / 'research/candidate_hypotheses_20261027.md'
if distal_source.is_file():
    distal_body = markdown.markdown(distal_source.read_text(encoding='utf-8'), extensions=['sane_lists'])
    for old, new in (('../evidence/release_independent_review_20261027.json', 'data/release_audit.json'),
                     ('hypotheses.md', 'research.html'),
                     ('../docs/research/why-b2-scored-2778.md', 'research/why-b2-scored-2778.html')):
        distal_body = distal_body.replace(f'href="{old}"', f'href="{new}"')
    for target, base, skip in ((DOCS / 'research/candidate_hypotheses_20261027.html', '../', 'research/candidate_hypotheses_20261027.html#main'),
                               (ROOT / 'site/research/candidate_hypotheses_20261027.html', '../../docs/', '../site/research/candidate_hypotheses_20261027.html#main')):
        content = page('Concurrent distal hypothesis', 'research.html',
                       f'<article class="card guide-card research-prose">{distal_body}</article>',
                       'A qualified, unassigned distal piedmont research proposal.', base=base)
        target.write_text(content.replace('href="#main"', f'href="{skip}"'), encoding='utf-8')
        print('built', target)
