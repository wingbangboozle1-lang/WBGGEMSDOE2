#!/usr/bin/env python3
"""Build the static, evidence-first GitHub Pages site without a web framework."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
portfolio = json.loads((DOCS / "data/portfolio.json").read_text())
leader = json.loads((DOCS / "data/leaderboard.json").read_text())
fresh = json.loads((DOCS / "data/focus-freshness.json").read_text())
run = json.loads((DOCS / "data/run-card.json").read_text())

# Fail closed: this renderer is specifically a negative-run dashboard. A future
# candidate cannot silently inherit a green button by editing a JSON boolean.
if (
    run.get("verdict") != "negative"
    or run.get("ok_to_submit") is not False
    or run.get("raster_sha256") is not None
):
    raise ValueError(
        "This dashboard renders only the audited negative run; review and implement a byte-bound release before changing status."
    )

msptcd = json.loads((DOCS / "data/wbg2_msptcd_results.json").read_text())
review_path = ROOT / "evidence/parallel_review.json"
if not review_path.is_file():
    review_path = DOCS / "data/parallel_review.json"
conduit_path = ROOT / "evidence/conduit_review.json"
if not conduit_path.is_file():
    conduit_path = DOCS / "data/conduit_review.json"
review = json.loads(review_path.read_text())
conduit = json.loads(conduit_path.read_text())

if (
    review.get("ok_to_submit") is not False
    or review.get("sha256") != run.get("parallel_session", {}).get("rejected_candidate_sha256")
    or review.get("format", {}).get("masked_inside") != 5132809
    or round(review.get("literal_overlap_3px", {}).get("lattice", 0), 6) != 0.993838
):
    raise ValueError("Parallel-file evidence changed; review the static narrative before publishing.")
if (
    conduit.get("ok_to_submit") is not False
    or conduit.get("sha256") != run.get("conduit_parallel_session", {}).get("rejected_candidate_sha256")
    or round(
        conduit.get("witnesses", {}).get("13GEMSDOE", {}).get("source_threshold_ge_0_5", {}).get("fraction", 0),
        6,
    )
    != 0.998726
):
    raise ValueError("Conduit-file evidence changed; review the static narrative before publishing.")

for name in (
    "data_preparation.json",
    "feature_cache.json",
    "b2_local_format.json",
    "dense_prior_certificate.json",
    "parallel_review.json",
    "parallel_candidate_audit.json",
    "conduit_review.json",
    "wbg2_msptcd_results.json",
    "wbg2_msptcd_canaries.json",
):
    source = ROOT / "evidence" / name
    if source.is_file():
        shutil.copyfile(source, DOCS / "data" / name)


def e(value) -> str:
    return escape(str(value), quote=True)


def icon(name: str) -> str:
    paths = {
        "shield": '<path d="M12 2.5 20 6v5.3c0 5-3.1 8.4-8 10.2-4.9-1.8-8-5.2-8-10.2V6l8-3.5Z"/><path d="M12 7.3v5.1m0 3.4h.01"/>',
        "arrow": '<path d="M5 12h14m-5-5 5 5-5 5"/>',
        "chart": '<path d="M4 19V5m0 14h16M8 15l3-4 3 2 5-7"/>',
        "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".5"/>',
        "spark": '<path d="m12 3 1.6 5.3L19 10l-5.4 1.7L12 17l-1.6-5.3L5 10l5.4-1.7L12 3Zm6 12 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7L18 15Z"/>',
        "lock": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v2"/>',
        "download": '<path d="M12 3v12m-4-4 4 4 4-4M5 18v2h14v-2"/>',
    }
    return f'<svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>'


def header(current: str) -> str:
    nav = [
        ("index.html", "Overview"),
        ("executive-summary.html", "Executive summary"),
        ("research.html", "Research"),
        ("sources.html", "Sources"),
    ]
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(href, ' aria-current="page"' if href == current else "", label)
        for href, label in nav
    )
    return f'''<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a href="index.html" class="brand" aria-label="GEMS research home"><span class="brandmark"><svg aria-hidden="true" width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M3 17.2 8.3 6l4.2 8 2.7-5 5.8 8.2" stroke="white" stroke-width="1.8" stroke-linejoin="round"/><path d="M4 19h16" stroke="#a9d8bc" stroke-width="1.5"/></svg></span>GEMS <small>RESEARCH</small></a>
<nav class="nav" aria-label="Main navigation">{links}</nav><div class="top-right"><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a><span class="top-status"><span class="dot"></span> Submission blocked</span></div></div></header>'''


def footer() -> str:
    return '''<footer class="footer"><div class="shell"><div><strong>GEMS RESEARCH</strong> · Evidence before submission · Maximize P(Win) &amp; Own the Outcome</div><div><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a> &nbsp;·&nbsp; <a href="data/run-card.json">Run card</a> &nbsp;·&nbsp; <a href="data/wbg2_msptcd_results.json">MSPTCD results</a> &nbsp;·&nbsp; <a href="data/portfolio.json">Audit data</a></div></div></footer>'''


def page(title: str, current: str, body: str, description: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{e(description)}"><meta name="theme-color" content="#0b5d4d"><title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script></head><body>{header(current)}<main id="main" class="shell main">{body}</main>{footer()}</body></html>'''


def intro(label, title, subtitle):
    stamp = e(msptcd["generated_utc"].replace("T", " ").split(".")[0] + " UTC")
    return f'''<div class="intro"><div><p class="eyebrow">{e(label)}</p><h1>{title}</h1><p>{e(subtitle)}</p></div><div class="intro-meta">Campaign &amp; audit recorded<br><strong>{stamp}</strong></div></div>'''


def decision():
    art = msptcd["artifact"]
    best_sc = msptcd["holdout_pooled"]["scores"][msptcd["winning_experiment"]]
    tif_rel = "downloads/" + Path(art["tif_path"]).name
    zip_rel = "downloads/" + Path(art["zip_path"]).name
    return f'''<section class="banner" aria-labelledby="decision-heading"><div class="banner-icon">{icon('shield')}</div><div class="banner-copy"><p class="banner-label">Current recommendation · negative (0 weekly slots used)</p><h2 id="decision-heading">No file is approved for submission.</h2><p>Our new 3-experiment <strong>WBG2-MSPTCD</strong> research candidate (<code>{e(art['stem'])}.tif</code>, <code>{art['dots']:,}</code> dots) passed all 124 leakage canaries (max AUC <code>0.6131</code>), improved zero-leakage pooled <strong>HOLDOUT-DTI</strong> by <strong>+81.8%</strong> over the 19-band control (<code>{best_sc['dti']:.4f}</code> vs <code>0.0234</code>, 95% CI <code>[{best_sc['ci95'][0]:.4f}, {best_sc['ci95'][1]:.4f}]</code>), and is genuinely unique against all 9 priority focus champions (<code>64.45%–68.06% ≤ 70%</code>). However, under the literal all-registry 3-px rule it hits <code>100.00%</code> on the <code>13GEMSDOE</code> lattice and <code>17GEMSDOE</code> continuous prior (and <code>78.34%</code> on <code>GEMSDOE27_H31</code>)—so it is published strictly for <strong>research download only (DO NOT SUBMIT)</strong>.</p><p class="small-meta" style="margin-top:6px">Research-only files (DO NOT SUBMIT to DrivenData): <a href="{e(tif_rel)}">GeoTIFF ({art['tif_bytes']:,} B) ↓</a> · <a href="{e(zip_rel)}">Single-TIFF ZIP ({art['zip_bytes']:,} B) ↓</a> · SHA-256: <code>{e(art['tif_sha256'][:16])}…</code></p></div><div class="actions"><button class="button" disabled>{icon('download')} No submission file</button><a class="text-link" href="executive-summary.html">Executive summary &amp; table →</a></div></section>'''


def freshness():
    captured = leader.get("captured_utc") or ""
    status = leader.get("status") or "stale"
    return f'<span class="freshness" data-captured="{e(captured)}" data-status="{e(status)}">Snapshot · {e(captured or "no capture time")}</span>'


def stats():
    score = leader.get("top_public_dti")
    display = (
        f"{float(score):.4f}"
        if isinstance(score, (float, int)) and not isinstance(score, bool) and 0 <= score <= 1
        else "Unavailable"
    )
    best_sc = msptcd["holdout_pooled"]["scores"][msptcd["winning_experiment"]]
    return f'''<section class="stats" aria-label="Key evidence"><article class="stat"><div class="stat-top">Official public leader <span class="stat-icon">{icon('chart')}</span></div><div class="stat-value">{display}</div><div class="stat-sub">{freshness()} · <a href="{e(leader['source_url'])}">xiaofanhu (#1) ↗</a></div></article>
<article class="stat"><div class="stat-top">Best of nine · reported <span class="stat-icon">{icon('target')}</span></div><div class="stat-value">0.2778</div><div class="stat-sub">GEMSDOE32 B2 · user-reported, not a receipt</div></article>
<article class="stat"><div class="stat-top">WBG2-MSPTCD · HOLDOUT-DTI <span class="stat-icon">{icon('spark')}</span></div><div class="stat-value">{best_sc['dti']:.4f}</div><div class="stat-sub">95% CI [{best_sc['ci95'][0]:.4f}, {best_sc['ci95'][1]:.4f}] · +81.8% vs 19B ({best_sc['withheld_positive_pixels']:,} px)</div></article>
<article class="stat"><div class="stat-top">Competition upload gate <span class="stat-icon">{icon('lock')}</span></div><div class="stat-value small">DO NOT SUBMIT</div><div class="stat-sub">Unique vs 9 focus · stopped by 13GEMSDOE/17GEMSDOE</div></article></section>'''


def compare_section():
    score = leader.get("top_public_dti")
    if not isinstance(score, (float, int)) or isinstance(score, bool) or not 0 < score <= 1:
        score = None
    leader_txt = f"{score:.4f}" if score is not None else "Unavailable"
    denominator = max(score or 0, 0.2778)
    bar_a = 100 * score / denominator if score is not None else 0
    bar_b = min(100, 0.2778 / denominator * 100)
    return f'''<div class="grid"><article class="card"><div class="card-body"><div class="section-header"><div><h2>Why GEMSDOE32 B2 topped the nine sites</h2><p>Exact byte-level forensic lineage across 144 user-reported fleet runs.</p></div><span class="tag">Forensic proof</span></div><div class="compare"><div class="compare-text"><h3>0.2778 <span style="font-size:12px;color:#97a69b;letter-spacing:0">USER-REPORTED</span></h3><p><code>GEMSDOE32</code> (<code>h33-h33-2-b2</code>, <code>37,654</code> dots) equals <code>GEMSDOE25/30</code> (<code>44,090</code> Poisson-spaced 300 m dots) after pruning all <code>6,436</code> dots within <code>≤2 px</code> (<code>200 m</code>) of <code>existing_faults.tif</code>. Under DW-Tversky (<code>α=0.2, β=0.8</code>), removing redundant near-catalogue false positives cuts denominator drag while preserving 300 m kernel coverage on off-catalogue extensions. <code>GEMSDOE36</code> appended <code>1,200</code> dots (<code>0.2750</code>), while live leader <code>xiaofanhu</code> reached <strong>{leader_txt}</strong> (+0.1766 headroom).</p><div class="meter"><div class="meter-label"><span>Official public leader · snapshot</span><strong>{leader_txt}</strong></div><div class="track"><span class="fill" style="width:{bar_a:.2f}%"></span></div></div><div class="meter"><div class="meter-label"><span>GEMSDOE32 B2 · user-reported</span><strong>0.2778</strong></div><div class="track"><span class="fill muted" style="width:{bar_b:.2f}%"></span></div></div></div><div class="contour" aria-hidden="true"><svg viewBox="0 0 150 150" fill="none"><g stroke="#8ebfa1" stroke-width="1" opacity=".7"><path d="M-10 105C20 104 19 56 53 59c31 3 25 45 58 42 17-1 30-21 50-14"/><path d="M-12 114c38-1 36-56 66-51 28 5 23 45 58 43 21-2 33-24 50-15"/><path d="M-12 123c44-1 40-61 68-56 26 5 22 45 57 44 25-1 35-26 50-16"/><path d="M-15 132c50-1 44-66 72-61 24 5 21 45 56 45 29 0 37-28 52-17"/><path d="M-15 140c56-1 48-71 74-65 23 5 21 44 55 46 32 1 39-30 53-18"/><path d="M-12 96c24 0 28-47 64-42 33 4 28 45 58 42 14-1 27-20 49-13"/></g><circle cx="77" cy="76" r="21" fill="#fff" stroke="#c5ddca"/><path d="m68 79 6-10 5 8 3-5 5 7" stroke="#3c8b67" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="88" cy="65" r="3" fill="#d0a55a"/></svg></div></div></div><div class="note-strip">Band 6 (<code>tc</code>) empirically verified as positive radiometric counts (<code>q01=7.64, med=18.49, q99=29.02</code>), NOT magnetic tilt angle. <a href="sources.html">Read the forensic analysis →</a></div></article>
<article class="card"><div class="card-body"><div class="section-header"><div><h2>Automated gate checklist</h2><p>Zero-human-intervention validation across every protocol gate.</p></div><span class="tag red">Stop · Negative</span></div><ul class="gate-list"><li><span class="gate-icon">✓</span><div><div class="gate-title">124 leakage canaries passed (31 features × 4 folds)</div><div class="gate-desc">Max two-sided AUC = 0.6131 ≤ 0.90 across 8 km buffered quadrants</div></div><span class="gate-state">Pass</span></li><li><span class="gate-icon">✓</span><div><div class="gate-title">Unmodified gems57-pooled-hide-v2 holdout (3 exps)</div><div class="gate-desc">EXP-3 HOLDOUT-DTI 0.0426 vs 0.0234 control (Δ +0.0191, p &lt; 0.001)</div></div><span class="gate-state">Pass</span></li><li><span class="gate-icon">✓</span><div><div class="gate-title">Byte-level GeoTIFF &amp; [0, 1] mask validator</div><div class="gate-desc">float32, EPSG:32611, 3730×3292, [0, 1], 0 NaN, 0 interior NoData</div></div><span class="gate-state">Pass</span></li><li><span class="gate-icon block">!</span><div><div class="gate-title">All-registry 3-px novelty gate (21 rasters)</div><div class="gate-desc">Unique vs all 9 focus (≤68.1%); stopped by 13GEMSDOE/17GEMSDOE/H31</div></div><span class="gate-state block">Stop</span></li></ul></div></article></div>'''


def experiment_table() -> str:
    sc = msptcd["holdout_pooled"]["scores"]
    pv = msptcd["paired_vs_ctrl_19b"]
    det = msptcd["detached_splay_diagnostic"]
    arms = [
        ("CTRL-19B (Baseline)", "ctrl_19b", "19 raw GeoDAWN bands + Bayes-calibrated marginal bar", None),
        ("EXP-1 (MSPTCD-Core)", "exp1_msptcd_core", "19 bands + 9 tilt-grad, dip-offset concordance, flank asym, Hessian & rad edges", pv["exp1_msptcd_core"]),
        ("EXP-2 (MSPTCD-StrainPU)", "exp2_msptcd_strain_pu", "31 features (+ strain/seismicity) + fold-local cover/relief PU weights", pv["exp2_msptcd_strain_pu"]),
        ("EXP-3 (MSPTCD-SubmodGreedy)", "exp3_msptcd_submod_greedy", "Ridge-coherent 0.5 EXP-1 + 0.5 EXP-2 OOF + multi-round 300 m greedy_allocate", pv["exp3_msptcd_submod_greedy"]),
    ]
    trs = []
    for label, key, desc, delta in arms:
        s = sc[key]
        d_det = det[key]["detached"]["pooled_dti"]
        delta_html = (
            '<span class="status-muted">Baseline</span><span class="small-meta">reference control</span>'
            if delta is None
            else f'<span class="score">{delta["delta"]:+.4f}</span><span class="small-meta">95% CI [{delta["ci95"][0]:+.4f}, {delta["ci95"][1]:+.4f}]</span>'
        )
        row_cls = ' class="champion"' if key == msptcd["winning_experiment"] else ""
        trs.append(
            f'<tr{row_cls}>'
            f'<td data-label="Experiment"><strong>{e(label)}</strong><span class="small-meta">{e(desc)}</span></td>'
            f'<td data-label="HOLDOUT-DTI"><span class="score">{s["dti"]:.4f}</span><span class="small-meta">95% CI [{s["ci95"][0]:.4f}, {s["ci95"][1]:.4f}]</span></td>'
            f'<td data-label="Paired Δ vs 19B">{delta_html}</td>'
            f'<td data-label="Detached splays"><span class="score">{d_det:.4f}</span><span class="small-meta">11,307 px (≥400 m)</span></td>'
            f'<td data-label="Evidence label"><span class="tag">HOLDOUT-DTI</span><span class="small-meta">gems57-pooled-hide-v2 · 60,988 px</span></td>'
            f'</tr>'
        )
    return f'''<section class="card table-card" id="msptcd-experiments"><div class="table-heading"><div><h2>Controlled 3-experiment campaign (WBG2-MSPTCD)</h2><p>Zero-leakage evaluation on unmodified <code>gems57.evaluate_holdout</code> (<code>gems57-pooled-hide-v2</code>, 4 spatial quadrants, <code>8.0 km</code> buffer, <code>60,988</code> withheld fault pixels, 1,000 paired 20 km spatial-cluster draws). Note: whole-quadrant blind holdout scores are ~6–10× stricter numerically than interleaved public DTI and are never projected as leaderboard scores.</p></div><div class="table-tools"><span class="tag">3 experiments · 307 s</span><a class="text-link" href="data/wbg2_msptcd_results.json">Full JSON receipt ↗</a></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Experiment arm</th><th scope="col">Pooled HOLDOUT-DTI</th><th scope="col">Paired Δ vs CTRL-19B</th><th scope="col">Detached-splay DTI</th><th scope="col">Provenance</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>'''


def focus_table():
    art = msptcd["artifact"]
    best_sc = msptcd["holdout_pooled"]["scores"][msptcd["winning_experiment"]]
    tif_rel = "downloads/" + Path(art["tif_path"]).name
    recent_20261026 = {
        "GEMSDOE28": "2026-10-26 update: s21-puhgb reported 0.1628 (36.1% overlap w/ MSPTCD)",
        "GEMSDOE33": "2026-10-26 update: s33-seisdil reported 0.0363 (48.4% overlap w/ MSPTCD)",
        "GEMSDOE36": "2026-10-26 update: kpl36-exp3 reported 0.2314 (59.1% overlap w/ MSPTCD)",
        "GEMSDOE27": "2026-10-25 update: h29-piedmont-celf reported 0.2190",
        "GEMSDOE30": "2026-10-25 update: MSDB1-edge44090 reported 0.1462",
        "GEMSDOE24": "2026-10-25 update: gvc1-submod reported 0.0859",
        "GEMSDOE25": "2026-10-25 update: h66-mgd-flank reported 0.0742",
    }
    msptcd_vs_focus = {
        r["id"]: r for r in msptcd["registry_comparison"]["rows"] if r["category"] == "focus_champion"
    }

    trs = [
        f'''<tr><td data-label="Site / file"><strong>WBGGEMSDOE2 (NEW · MSPTCD E3)</strong><a class="file-link" href="{e(tif_rel)}" title="Research GeoTIFF only — DO NOT SUBMIT">{e(Path(art['tif_path']).name)} ↓</a><span class="small-meta">SHA-256: {e(art['tif_sha256'][:16])}… · {art['dots']:,} dots</span></td><td data-label="Score / HOLDOUT-DTI"><span class="score">{best_sc['dti']:.4f}</span><span class="small-meta">HOLDOUT-DTI · 95% CI [{best_sc['ci95'][0]:.4f}, {best_sc['ci95'][1]:.4f}] ({best_sc['withheld_positive_pixels']:,} px)</span></td><td data-label="Estimate"><span class="status-muted">Unavailable</span><span class="small-meta">no organizer truth</span></td><td data-label="Unique?"><span class="status-no">Focus: YES · Reg: NO</span><span class="small-meta">≤68.1% vs 9 focus; 100% vs 13GEMSDOE lattice</span></td><td data-label="OK to Submit?"><span class="status-no">DO NOT SUBMIT</span><span class="small-meta">research download only</span></td></tr>'''
    ]

    rows = sorted(portfolio["sites"], key=lambda r: float(r["user_reported_score"]), reverse=True)
    for row in rows:
        site = row["site"]
        filename = row["path"].rsplit("/", 1)[-1]
        exact = row.get("decoded_exact_matches_in_focus") or []
        explanation = (
            ("Exact decoded match: " + ", ".join(exact))
            if exact
            else f"{row['max_3px_overlap_vs_other_focus']*100:.1f}% near {row['max_overlap_witness_site']}"
        )
        vs_ours = msptcd_vs_focus.get(site)
        ours_note = f" · MSPTCD vs {site}: {vs_ours['forward_overlap_3px']*100:.1f}%" if vs_ours else ""
        extra_note = recent_20261026.get(site, "")
        extra_html = f'<span class="small-meta">{e(extra_note)}</span>' if extra_note else ""
        trs.append(
            f'''<tr{(' class="champion"' if site=='GEMSDOE32' else '')}><td data-label="Site / file"><a class="site-name" href="../site/sites/{e(site)}.html">{e(site)} ↗</a><a class="file-link" href="{e(row['download_url'])}" title="{e(filename)} — historical research only">{e(filename)} ↗</a>{extra_html}</td><td data-label="Score / HOLDOUT-DTI"><span class="score">{e(row['user_reported_score'])}</span><span class="small-meta">USER-REPORTED (not receipt)</span></td><td data-label="Estimate"><span class="status-muted">Unavailable</span><span class="small-meta">no valid forecast</span></td><td data-label="Unique?"><span class="status-no">No</span><span class="small-meta">{e(explanation + ours_note)}</span></td><td data-label="OK to Submit?"><span class="status-no">DO NOT SUBMIT</span><span class="small-meta">historical duplicate</span></td></tr>'''
        )

    changed = int(fresh.get("changed_count", 0))
    unknown = int(fresh.get("unknown_count", 0))
    checked = fresh.get("checked_utc", "")
    freshness_copy = (
        f"{changed} of 9 site HEADs updated through 2026-10-27 ({unknown} unknown); "
        f"all newly added 2026-10-26/27 rasters (GEMSDOE28 S21, GEMSDOE33 S33, GEMSDOE36 KPL36, KANLER2, WBG1, WBG3) were fetched and audited by blob SHA."
    )
    return f'''<section class="card table-card" id="priority-sites"><div class="table-heading"><div><h2>Executive scorecard: WBG2-MSPTCD &amp; nine priority sites</h2><p>Compare our newly generated cross-fitted research GeoTIFF against the highest-scoring submission from each priority site (<code>GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36</code>). Every score carries its exact evidence class; zero projections are reported as scores.</p><p class="fresh-warning">{e(freshness_copy)} <a href="data/focus-freshness.json">HEAD check ↗</a> · <span class="freshness" data-captured="{e(checked)}" data-status="{('stale' if unknown else 'snapshot')}">Checked {e(checked)}</span></p></div><div class="table-tools"><span class="tag">1 new + 9 focus</span><a class="text-link" href="data/portfolio.json">Audit JSON ↗</a></div></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Site &amp; downloadable file</th><th scope="col">Score / HOLDOUT-DTI</th><th scope="col">Estimated live score</th><th scope="col">Unique vs registry?</th><th scope="col">OK to download &amp; submit?</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div><div class="table-footer"><div>All 21 audited rasters checked on pre-placement surface Spearman ρ and 3-px dot overlap.</div><div><a href="data/user-reported-ledger.csv">Download full 144-row user-reported ledger (through GEMSDOE92 &amp; KANLER/EUG/WBG/GINNY) ↓</a></div></div></section>'''


def recent_cohort_section() -> str:
    cohort = [
        ("GEMSDOE36 (2026-10-26)", "gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros", "0.2314", "59.12% (ρ=+0.0994)", "Strongest Oct 26 sibling update; still below GEMSDOE32 B2 (0.2778)"),
        ("KANLERGEMSDOE2 (2026-10-26)", "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros", "0.1973", "53.63% (ρ=+0.0571)", "37,654-dot tilt/curvature/anisotropic stepover candidate"),
        ("GEMSDOE91 (2026-10-25/26)", "gems91-s17-lftg / S18-UNIQUE-curvtilt-20000dots / s20-cws", "0.1823 / 0.1578 / 0.1302", "Audited in ledger", "20,000-dot S18 budget illustrates lattice-feasible low-budget trade-off"),
        ("EUGGEMSDOE1–3 (2026-10-26)", "eug3-c3-29-exp2-oobisotonic-dink37654", "0.1782 (best of 3)", "Audited in ledger", "OOB isotonic + Dinkelbach 37,654-dot calibration"),
        ("KANLERGEMSDOE1 (2026-10-25)", "kanler1-hgb32-pu-submod-37654", "0.1753", "Audited in ledger", "32-feature PU HGB + submodular decoder"),
        ("GEMSDOE28 (2026-10-26)", "gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite", "0.1628", "36.07% (ρ=+0.0532)", "All-finite PU-HGB; unique vs MSPTCD"),
        ("WBGGEMSDOE3 (2026-10-26)", "wbggems3-lst1-hybrid-20261026-0a0229da-zeros", "0.1597", "32.92% (ρ=+0.0035)", "Listric hybrid 37k-class candidate; unique vs MSPTCD"),
        ("GINNYGEMSDOE1–2 (2026-10-26)", "ginny2-e3-splay-hybrid / ginny1-exp3-listric", "0.1045 / 0.0956", "Audited in ledger", "Splay & listric paired submodular experiments"),
        ("WBGGEMSDOE1 (2026-10-26)", "wbg1-m3-listric-worm-aniso / wbg-c1-commutator", "0.0882 / blank", "100.0% (continuous C1)", "C1 is a full-footprint continuous surface (ρ=+0.6857 vs MSPTCD)"),
        ("WBGGEMSDOE2 (2026-10-26 archived)", "wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros", "0.0725", "33.70% (ρ=+0.0387)", "Rejected here: nodata=0 masked 5,132,809 interior px & leaky private holdout"),
        ("GEMSDOE33 (2026-10-26)", "gemsdoe33-s33-seisdil-strain-seismicity-37654", "0.0363", "48.35% (ρ=+0.0628)", "Coarse strain/seismicity over-weighting degraded precision"),
    ]
    trs = "".join(
        f'<tr><td data-label="Repo"><strong>{e(repo)}</strong><span class="small-meta">{e(sub)}</span></td>'
        f'<td data-label="Reported DTI"><span class="score">{e(sc)}</span><span class="small-meta">USER-REPORTED</span></td>'
        f'<td data-label="MSPTCD 3px / ρ"><span>{e(ov)}</span></td>'
        f'<td data-label="Forensic takeaway"><span>{e(note)}</span></td></tr>'
        for repo, sub, sc, ov, note in cohort
    )
    return f'''<section class="card table-card" id="recent-siblings"><div class="table-heading"><div><h2>Newly reported 2026-10-25..27 fleet submissions</h2><p>Forensic synthesis of the 17 new prompt entries across <code>GEMSDOE28/33/36/91/92</code> and <code>KANLER / EUG / WBG / GINNY</code>, including why the archived parallel <code>WBGGEMSDOE2</code> file dropped to <code>0.0725</code>.</p></div><span class="tag">144-row ledger</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Site &amp; submission</th><th scope="col">Reported DTI</th><th scope="col">MSPTCD overlap / ρ</th><th scope="col">Forensic takeaway</th></tr></thead><tbody>{trs}</tbody></table></div></section>'''


def home():
    body = (
        intro(
            "Executive overview",
            "Clarity before a <span>submission.</span>",
            "Verified 2026-10-27 DOE GEMS Prize research, 3-experiment MSPTCD holdout evaluation, and fail-closed registry audit.",
        )
        + decision()
        + stats()
        + compare_section()
        + focus_table()
        + '<div style="height:20px"></div>'
        + experiment_table()
        + '<div style="height:20px"></div>'
        + recent_cohort_section()
    )
    body += '''<section class="brief-grid" aria-label="Research resources"><article class="card brief"><div class="brief-number">01</div><h3>Understand the stop</h3><p>Our WBG2-MSPTCD candidate is unique against all 9 priority champions (≤68.06%), but 13GEMSDOE's stride-5 lattice and 17GEMSDOE's continuous prior trigger the literal >70% stop.</p><a href="executive-summary.html#novelty">Explore the proof →</a></article><article class="card brief"><div class="brief-number">02</div><h3>Five ranked hypotheses</h3><p>Exact layers, geophysical signatures, non-fault mimics, Band 6 radiometric discovery, and zero-leakage holdout results.</p><a href="research.html">View research →</a></article><article class="card brief"><div class="brief-number">03</div><h3>Check the evidence</h3><p>Competition rules, [0, 1] validation safeguards, SHA-256 provenance, and official USGS/DOE GDR links.</p><a href="sources.html">Browse sources →</a></article></section><section class="dark-card"><p class="eyebrow">Arena Core Values · Maximize P(Win) &amp; Own the Outcome</p><h2>Protect the slot. Advance the physics.</h2><p>Negative competition promotion is a valid, slot-preserving scientific outcome when literal registry witnesses block upload. <a href="data/run-card.json">Read the canonical run card →</a> · <a href="executive-summary/">See both rejected parallel files →</a> · <a href="../site/">Open nine individual site briefs →</a></p></section>'''
    return page(
        "Overview",
        "index.html",
        body,
        "Evidence-first DOE GEMS Prize research, WBG2-MSPTCD holdout results, and submission status.",
    )


def guide():
    w = portfolio["literal_registry_witness"]
    d = portfolio["dense_probability_witness"]
    art = msptcd["artifact"]
    body = (
        intro(
            "Executive summary",
            "From research to <span>submission.</span>",
            "Clear status for every candidate and historical file, [0, 1] validation rules, and exact contest upload instructions.",
        )
        + decision()
    )
    body += f'''<div class="guide-layout"><article class="card guide-card"><div class="section-header"><div><h2>Step-by-step contest submission guide (when a file clears all gates)</h2><p>Today's verdict is <strong>DO NOT SUBMIT</strong> (0 slots spent). Use these exact steps only after a future candidate clears a clarified registry policy and selector review.</p></div><span class="tag red">Currently locked</span></div><ol><li><strong>Verify machine-gate clearance.</strong> Confirm <code>verdict == "promote"</code> and <code>ok_to_submit == true</code> in <code>data/run-card.json</code>: all leakage canaries <code>≤ 0.90</code>, paired <code>HOLDOUT-DTI</code> improvement on <code>gems57-pooled-hide-v2</code>, pre-placement &amp; final-dot registry clearance (<code>|ρ| ≤ 0.90</code>, 3-px overlap <code>≤ 70%</code>), and selector slot authorization.</li><li><strong>Download the single approved GeoTIFF (or single-TIFF ZIP).</strong> Verify its local SHA-256 via <code>sha256sum &lt;file&gt;.tif</code> before upload. Never upload historical reference files or research-only files such as <code>{e(art['stem'])}.tif</code>.</li><li><strong>Run automated byte-level [0, 1] &amp; mask validation (zero manual steps).</strong> Run <code>.venv/bin/python scripts/validate_submission.py &lt;file&gt;.tif --sample data/official/sample_submission.tif</code> to confirm single-band <code>float32</code>, <code>EPSG:32611</code>, <code>3730×3292</code>, <code>100 m</code>, <code>min ≥ 0.0</code>, <code>max ≤ 1.0</code>, <code>0</code> NaN/Inf inside footprint, and <code>0</code> interior NoData masks.</li><li><strong>Upload on DrivenData.</strong> Sign in at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData DOE GEMS</a>, click <em>Submit → Make new submission</em>, upload the verified <code>.tif</code> or <code>.zip</code>, and paste the ≤140-character submission note. Confirm remaining weekly quota (max 3 scored uploads/week per official rules §3.2).</li><li><strong>Record the organizer receipt.</strong> Save the exact DrivenData score receipt before labeling any number <code>ORGANIZER-CONFIRMED</code>, and select one final submission before the prize deadline (disclosing generative-AI tooling per official rules §§3.3–3.5).</li></ol><div class="callout"><strong>How we prevent “Predicted values must be in range [0, 1]”:</strong> That portal error is triggered by unclipped logits/gradients (&lt;0 or &gt;1), unfiltered NaN/±Inf pixels inside the scored footprint, or broken NoData masks (such as <code>nodata=0</code> masking 5.13M interior cells in the rejected parallel TIFF). Our writer emits explicit <code>float32</code> values in <code>[0.0, 1.0]</code> with <code>nodata=None</code>, and <code>validate_submission.py</code> re-reads saved bytes from disk without silent clipping.</div><p><a class="text-link" href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Read the official format specification ↗</a></p></article>
<aside class="card guide-card" id="novelty"><div class="section-header"><div><h2>Why the competition gate is blocked</h2><p>Novel vs all 9 focus champions, stopped by blanket registry witnesses.</p></div></div><p><strong>1. Genuine novelty vs all 9 focus champions.</strong> Across <code>GEMSDOE24..36</code>, <code>WBG2-MSPTCD</code> (<code>25,594</code> off-catalogue dots) achieves <strong>64.45%–68.06%</strong> forward 3-px overlap (all <code>≤ 70%</code>; <code>64.45%</code> vs <code>GEMSDOE32 B2</code>) and surface <code>|ρ| ≤ 0.0904</code> (all <code>≤ 0.90</code>).</p><p><strong>2. Binary lattice witness (<code>13GEMSDOE</code>).</strong> {w['within_3px_pixels']:,} of {w['footprint_pixels']:,} footprint cells (<code>99.87%</code>) sit within 3 px of a registered stride-5 lattice dot; only {w['outside_3px_pixels']:,} interior/edge cells are uncovered (<code>100.00%</code> forward overlap on our interior fault ridges, <code>ρ = -0.0001</code>). At <code>37,654</code> dots, minimum possible overlap is <strong>{w['minimum_possible_overlap_at_example_budget']*100:.2f}%</strong>.</p><p><strong>3. Continuous-prior &amp; halo witnesses.</strong> <code>17GEMSDOE</code> and <code>WBGGEMSDOE1_C1</code> are positive on <code>100%</code> of footprint cells (<code>100%</code> overlap under literal <code>value &gt; 0</code> support), and <code>GEMSDOE27_H31</code> (<code>56,161</code>-dot unpruned halo) reaches <code>78.34%</code>.</p><p><a href="{e(w['source'])}">13GEMSDOE lattice ↗</a> · <a href="{e(d['source'])}">17GEMSDOE continuous prior ↗</a> · <a href="data/wbg2_msptcd_results.json">21-raster overlap matrix ↗</a></p></aside></div>'''
    body += '<div style="height:20px"></div>' + focus_table() + '<div style="height:20px"></div>' + experiment_table()
    body += '''<section class="card guide-card"><h2>Known limitations &amp; remaining work</h2><p>Private organizer truth labels, per-file organizer upload receipts for historical claims, authenticated DrivenData <code>sample_submission.tif</code> bytes (the public mirror carries 60,988 positive catalogue cells rather than an all-absence template), and USGS 3DEP 1 m LiDAR / raw GeoDAWN line CSV downloads (blocked by sandbox outbound host rules) remain unavailable here. Upstream <code>gems57.gates.format_report</code> also still needs an upstream patch for finite-zero interior NoData masks (caught locally by our additive validator).</p><p><a href="data/run-card.json">Download canonical run card ↗</a> · <a href="data/wbg2_msptcd_canaries.json">124-check canary receipt ↗</a> · <a href="sources.html">Official sources &amp; irregularities ↗</a></p></section>'''
    return page(
        "Executive summary",
        "executive-summary.html",
        body,
        "Executive summary table, WBG2-MSPTCD scorecard, novelty proof, and step-by-step submission guide.",
    )


def research():
    body = (
        intro(
            "Scientific research",
            "Five ranked hypotheses. <span>Three tested cleanly.</span>",
            "Grounded in verified GeoDAWN physics, zero-leakage buffered spatial folds, and exact submodular DTI optimization.",
        )
        + decision()
        + experiment_table()
        + '<div style="height:20px"></div>'
    )
    cards = [
        (
            "H1 · RANK #1 · EXECUTED IN EXP-1 & EXP-3",
            "Depth-shifted potential-field tilt & gravity–magnetic concordance",
            "Layers: rtp (B2), tmi_vg (B9), iso_grav_anom (B13), iso_grav_anom_vg (B11), depth_to_base_surf (B15). Computes true Miller–Singh tilt horizontal gradients (since Band 6 tc is positive radiometric counts, not tilt angle!) and symmetric ±δ(depth) cross-normal gravity–magnetic concordance to capture 45°–65° dipping concealed basin-bounding faults under both magnetic polarities.",
            "Unfaulted pluton/caldera margins, feeder dikes, paleochannels, and drape clearance steps.",
            "Tested · +49.4% HOLDOUT-DTI (EXP-1)",
        ),
        (
            "H2 · RANK #2 · EXECUTED IN EXP-1 & EXP-3",
            "Conductive-flank asymmetry, terrain-normalized radiometric edge & Hessian scarps",
            "Layers: cond_surf (B17), depth_to_base_surf (B15), tc (B6), det_elev (B12), det_elev_slope (B19). Measures cross-strike cond_surf asymmetry across log-depth normals, slope-damped radiometric edges |∇tc|/(1+0.2·slope), and principal negative Hessian scarp ridges at 150 m and 350 m.",
            "Playal evaporite/smectite pans, Lahontan shoreline risers, tuff contacts, and steep-terrain clearance variations.",
            "Tested · +61.2% detached-splay DTI",
        ),
        (
            "H3 · RANK #3 · EXECUTED IN EXP-2 & EXP-3",
            "Active transtensional strain-rate & log-seismicity gate + PU cover debiasing",
            "Layers: geod_2ndinv (B4), geod_shearrate (B7), geod_dilaterate (B8), deq_n100a15 (B10), ieq_n100a15 (B16), det_elev_slope (B19), depth_to_base_surf (B15). Conditions sharp geophysical edges on dilatation ratio and log-compressed seismicity with fold-local low-relief/deep-cover positive weights (strongest in Walker Lane Fold 1: 0.0536 vs 0.0278 control).",
            "Broad GPS interpolation lobes, volcanic/mining swarms, and basin over-emission under heavy cover weights.",
            "Tested · Blended in EXP-3",
        ),
        (
            "H4 · RANK #4 · EXECUTED IN EXP-3",
            "Bayes prior-odds recalibration + 300 m submodular greedy allocation",
            "Layers: Cross-fitted 31-feature OOF posteriors + gems57.emit.greedy_allocate. Recalibrates subsampled posteriors (π_s=0.20) to fold-local grid fault density (π_0≈0.0118) before multi-round 300 m triangular-kernel greedy selection so neighboring pixels never double-pay the α=0.2 false-positive penalty.",
            "Probability floor miscalibration in low-SNR basins; still subject to literal 13GEMSDOE lattice overlap at normal budgets.",
            "Tested · 0.0426 HOLDOUT-DTI (+81.8%)",
        ),
        (
            "H5 · RANK #5 · EXTERNAL DATA BLOCKED IN SANDBOX",
            "Catchment-normalized 1 m LiDAR drainage deflection & flight-line repeatability",
            "External official layers: USGS 3DEP 1 m LiDAR (1m_DEM_links.csv in DOE GDR #1391) & USGS GeoDAWN flight/tie-line CSVs (CC0). Targets multi-drainage alluvial-fan knickpoints/deflections and rejects single-pass airborne leveling artifacts.",
            "Wave-cut shorelines, road/canal embankments, lithologic hogbacks, and uneven tie-line spacing.",
            "Verified free · Blocked in sandbox",
        ),
    ]
    body += (
        '<div class="research-list">'
        + "".join(
            f'''<article class="card research-item"><span class="num">{e(n)}</span><h2>{e(t)}</h2><p>{e(p)}</p><p><strong>Non-fault mimic:</strong> {e(m)}</p><span class="tag">{e(st)}</span></article>'''
            for n, t, p, m, st in cards
        )
        + '</div><div style="height:20px"></div>'
    )
    body += '''<section class="card guide-card"><div class="section-header"><div><h2>Leakage guardrails &amp; scientific references</h2><p>Every feature tested fold-locally across 60,988 withheld positives before model trust.</p></div><a class="text-link" href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses.md">Full hypotheses &amp; equations on GitHub →</a></div><p>All 12 MSPTCD features are strictly label-free functions of raw GeoDAWN bands; <code>existing_faults.tif</code> is never read during feature construction. Across 31 features × 4 spatial folds (<code>buffer_px=80</code>, <code>8.0 km</code> buffer), all 124 single-feature ROC-AUC canaries scored <code>≤ 0.6131</code> (well below the <code>0.90</code> leakage stop).</p><ul class="source-list"><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN data release (CC0) ↗</a> — magnetic and radiometric survey design and terrain-clearance characteristics.</li><li><a href="https://pubs.usgs.gov/publication/70271418">USGS Argenta Rise study ↗</a> — joint gravity, magnetic and magnetotelluric imaging of blind Great Basin geothermal structure.</li><li><a href="https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and">USGS Great Basin play-fairway synthesis ↗</a> — structural controls on blind hydrothermal systems.</li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS compilation (CC BY 4.0) ↗</a> — regional fault, geodetic, temperature, and <code>1m_DEM_links.csv</code> archive.</li><li><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP elevation products ↗</a> — public-domain DEM/LiDAR terms (raw tile host blocked in sandbox).</li></ul></section>'''
    return page(
        "Research",
        "research.html",
        body,
        "Five ranked geothermal fault-mapping hypotheses, Band 6 forensic discovery, mimics, and WBG2-MSPTCD holdout results.",
    )


def sources():
    body = (
        intro(
            "Evidence & sources",
            "Trace each <span>claim.</span>",
            "Official competition specifications, forensic irregularities discovered in the raw rasters, and machine-verified receipts.",
        )
        + decision()
    )
    rows = [
        (
            "Target",
            "Predict previously unmapped faults indicative of geothermal resources; a fault prediction is not proof of a geothermal vent.",
            "DrivenData problem description",
            "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
        ),
        (
            "Format",
            "Single float32 band, EPSG:32611, 100 m grid (3730×3292), matching bounds and values in [0,1]; public text describes null/NaN outside bounds.",
            "Official submission format",
            "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format",
        ),
        (
            "Metric",
            "Distance-weighted Tversky uses a 300 m triangular kernel with alpha=0.2 and beta=0.8.",
            "Official metric and equations",
            "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric",
        ),
        (
            "Fault masking",
            "Staff confirmed existing USGS/INGENIOUS fault pixels are excluded in both rounds; no surrounding buffer exclusion was stated.",
            "Organizer staff clarification",
            "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2",
        ),
        (
            "Official rules",
            "Up to 3 scored submissions/week; one final submission for both rounds; finalist code reproducibility and AI-use disclosure (§§3.2–3.5).",
            "NLR Official Rules PDF",
            "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
        ),
        (
            "Leaderboard",
            "Verified 2026-10-27 UTC: #1 xiaofanhu = 0.4544, #2 cfld__ = 0.3916, #3 Batik Shirt Brothers = 0.3911 (team scores, not file receipts).",
            "Official public leaderboard",
            "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
        ),
        (
            "Reference model",
            "Organizer baseline repository; supports CPU and GPU execution.",
            "Organizer reference solution",
            "https://github.com/drivendataorg/gems-prize-reference-solution",
        ),
        (
            "Geophysics",
            "GeoDAWN airborne magnetic & gamma-ray radiometric surveys (CC0); confirms Band 6 tc is total radiometric counts.",
            "USGS GeoDAWN release",
            "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
        ),
        (
            "INGENIOUS archive",
            "Great Basin compilation (CC BY 4.0) including 1m_DEM_links.csv; raw external hosts not reachable from this sandbox.",
            "DOE GDR #1391",
            "https://gdr.openei.org/submissions/1391",
        ),
    ]
    trs = "".join(
        f'<tr><td data-label="Topic"><strong>{e(topic)}</strong></td><td data-label="Claim"><span>{e(claim)}</span></td><td data-label="Source"><a href="{e(url)}">{e(label)} ↗</a></td></tr>'
        for topic, claim, label, url in rows
    )
    body += f'''<section class="card table-card"><div class="table-heading"><div><h2>Official source inventory</h2><p>Every rule, physical channel interpretation, and benchmark figure traced to an official primary source.</p></div><span class="tag">Sources</span></div><div class="table-scroll"><table class="data-table"><thead><tr><th scope="col">Topic</th><th scope="col">What the source supports</th><th scope="col">Verify</th></tr></thead><tbody>{trs}</tbody></table></div></section>'''
    body += '''<section class="card guide-card"><h2>Flagged irregularities verified directly from bytes</h2><ul class="source-list"><li><strong>1. Band 6 (<code>tc</code>) mirror mislabeling:</strong> Public mirror metadata strings call Band 6 “Tilt angle or total curvature”, whereas the official DrivenData problem page lists GeoDAWN radiometric total counts (<code>tc</code>). Direct byte inspection across all 5,164,300 finite footprint pixels shows <code>q01 = 7.637</code>, <code>median = 18.490</code>, <code>q99 = 29.020</code> (0 negative pixels), proving Band 6 is positive gamma-ray total counts rather than a <code>[-π/2, π/2]</code> tilt angle.</li><li><strong>2. Band 15 (<code>depth_to_base_surf</code>) wording conflict:</strong> Official problem text says “depth to conductive base surface”; mirror metadata says “depth to basement surface”. We treat Band 15 strictly as an electrical/cover thickness proxy.</li><li><strong>3. Mirrored <code>sample_submission.tif</code> vs organizer description:</strong> The DrivenData problem page describes an all-absence sample submission, whereas the public mirror's <code>sample_submission.tif</code> has 60,988 ones matching <code>existing_faults.tif</code>. Obtain an authenticated portal download before final contest submission.</li><li><strong>4. Upstream <code>gems57.gates.format_report</code> mask gap:</strong> Finite zeros tagged <code>nodata=0</code> inside the footprint pass <code>gems57.gates.format_report</code> alone (as seen in the rejected parallel TIFF that scored <code>0.0725</code> user-reported); our additive <code>validate_submission.py</code> check catches and blocks interior NoData masks.</li></ul></section>'''
    body += '''<section class="card guide-card"><h2>Machine-verified JSON receipts</h2><ul class="source-list"><li><a href="data/run-card.json">Canonical negative run card (<code>run-card.json</code>) ↗</a> — synced across <code>evidence/</code>, <code>docs/</code>, and <code>site/</code>.</li><li><a href="data/wbg2_msptcd_results.json">WBG2-MSPTCD 3-experiment &amp; 21-raster audit receipt ↗</a> — full per-fold, bootstrap, detached-splay, and SHA-256 records.</li><li><a href="data/wbg2_msptcd_canaries.json">124-check single-feature leakage canary receipt ↗</a> — all 31 features × 4 spatial folds.</li><li><a href="data/portfolio.json">Nine-focus-site &amp; B2 lineage receipt ↗</a> — exact pairwise 3-px overlaps and decoded hashes.</li><li><a href="data/data_preparation.json">Data restoration receipt ↗</a> &amp; <a href="data/feature_cache.json">19-band cache inventory ↗</a>.</li></ul></section>'''
    return page(
        "Sources",
        "sources.html",
        body,
        "Official competition and scientific sources, flagged byte-level irregularities, and JSON receipts.",
    )


for name, content in [
    ("index.html", home()),
    ("executive-summary.html", guide()),
    ("research.html", research()),
    ("sources.html", sources()),
]:
    (DOCS / name).write_text(content, encoding="utf-8")
    print(f"built {DOCS / name}")
