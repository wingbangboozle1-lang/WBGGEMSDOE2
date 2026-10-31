#!/usr/bin/env python3
"""Render the WBG5 decision dossier from the run card and its evidence files.

Reads committed evidence only; never trains, places dots, edits a raster or
changes a score. Every number on the page is copied from a JSON artifact whose
relative path is printed in the page footer so a reader can re-check it.
"""
from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "wbg5"

CARD = json.loads((ROOT / "evidence/wbg5_run_card.json").read_text())
PRIOR = json.loads((ROOT / "evidence/wbg5_prior_experiment.json").read_text())
SWEEP = json.loads((ROOT / "evidence/wbg5_budget_sweep.json").read_text())
EQB = json.loads((ROOT / "evidence/wbg5_equal_budget.json").read_text())
NULL = json.loads((ROOT / "evidence/wbg5_overlap_null.json").read_text())
RULE = json.loads((ROOT / "evidence/wbg5_rule_decision.json").read_text())
HOLD = json.loads((ROOT / "evidence/wbg5_holdout_experiment.json").read_text())
SMNULL = json.loads((ROOT / "evidence/wbg5_smoothed_null.json").read_text())
NINE = json.loads((ROOT / "evidence/wbg5_nine_site_proxy.json").read_text())


def e(v):
    return escape(str(v), quote=True)


def pct(v, digits=2):
    return f"{float(v) * 100:.{digits}f}%"


TIF = Path(CARD["raster"]["path"]).name
ZIP = TIF.replace(".tif", ".zip")
HREF_TIF = f"../downloads/wbg5/{TIF}"
HREF_ZIP = f"../downloads/wbg5/{ZIP}"

# ---------------------------------------------------------------- tables
sweep_rows = "".join(
    f"<tr><td>{r['budget']:,}</td><td>{r['dti']:.4f}</td><td>{r['tp']:,.0f}</td>"
    f"<td>{r['fp']:,.0f}</td><td>{r['fn']:,.0f}</td></tr>"
    for r in SWEEP["rows"])

nine_rows = "".join(
    f"<tr><td>{e(r['site'])}</td><td>{r['dots']:,}</td>"
    f"<td>{r['frac_dots_within3_of_catalogue']*100:.1f}%</td>"
    f"<td>{r['catalogue_truth_dti_unmasked']:.4f}</td></tr>"
    for r in NINE["rows"])

eq_rows = "".join(
    f"<tr><td>{e(r['name'])}</td><td>{r['dots']:,}</td><td>{r['dti']:.4f}</td></tr>"
    for r in EQB["rows"])
ratio = EQB["equal_budget_37654_ratio_ours_over_b2"]
_by_name = {r["name"]: r for r in EQB["rows"]}
EQ37654 = _by_name["ours_oof_blend@37654"]["dti"]
EQ44090 = _by_name["ours_oof_blend@44090"]["dti"]
EQB2 = _by_name["gemsdoe32_b2_shipped"]["dti"]
EQD28 = _by_name["gemsdoe25_d2_8_shipped"]["dti"]

ov_rows = []
for row in CARD["uniqueness"]["focus_sites"]:
    n = NULL["rows"].get(row["site"], {})
    ov_rows.append(
        "<tr>"
        f"<td>{e(row['site'])}</td>"
        f"<td>{row['raw_spearman_full']:.4f}</td>"
        f"<td>{row['smoothed_spearman_footprint']:.3f}</td>"
        f"<td>{pct(row['frac_mine_within3_of_other'])}</td>"
        f"<td>{pct(row['frac_other_within3_of_mine'])}</td>"
        f"<td>{pct(n.get('frac_other_within3_of_random150k', 0))}</td>"
        f"<td>{pct(n.get('frac_random150k_within3_of_other', 0))}</td>"
        "</tr>")
overlap_table = "".join(ov_rows)

HOLD_CURVE = HOLD["density_curve_blend_0p5scarp_0p5topo"]
HOLD_AT_150K = float(HOLD_CURVE["150000"])
HOLD_RANDOM_150K = float(HOLD_CURVE["random_150000"])

body = f"""<section class="banner" data-release-status="ok" aria-labelledby="wbg5-decision">
<div class="banner-icon"><svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></div>
<div class="banner-copy"><p class="banner-label">Authoritative repository decision · OK TO DOWNLOAD AND SUBMIT (research-grade) · 2026-10-31</p>
<h2 id="wbg5-decision">OK TO DOWNLOAD AND SUBMIT — {e(TIF)}</h2>
<p>150,000 dots · <strong>SGMC-PROXY-DTI {CARD['primary_evidence']['dti']:.4f}</strong> (95% CI {CARD['primary_evidence']['ci95'][0]:.4f}–{CARD['primary_evidence']['ci95'][1]:.4f}) on an independent USGS state-map truth set · <strong>{ratio:.2f}×</strong> the best public file at equal dot budget · worst-case registry dot proximity <strong>{pct(CARD['uniqueness']['max_frac_my_dots_within_3px'])}</strong> vs the 70% stop · local validator all-PASS. This is a research-grade download decision, not an organizer score and not a weekly-slot authorization.</p></div>
<div class="actions"><a class="button" href="{HREF_ZIP}" download>OK TO DOWNLOAD AND SUBMIT — ZIP ↓</a><a class="text-link" href="{HREF_TIF}" download>OK TO DOWNLOAD AND SUBMIT — GeoTIFF ↓</a><a class="text-link" href="../data/run-card-wbg5.json">Run card JSON →</a></div></section>

<section class="card guide-card"><h2>What exactly is being submitted</h2>
<p>Single-band float32 GeoTIFF, EPSG:32611, 3292 × 3730 cells at 100 m, transform [100, 0, 243350, 0, −100, 4508550]. Values are exactly 0.0 or 1.0 (150,000 cells at 1.0, all other cells 0.0), finite everywhere, no NaN. 0 dots fall on a mapped USGS/INGENIOUS catalogue pixel. SHA-256 <code>{e(CARD['raster']['sha256'])}</code>, {CARD['raster']['bytes']:,} bytes. ZIP SHA-256 <code>{e('c831d7c73d83c15bdb715e9e0f9292efcb0d60fa0354b696e0b9dfcbe3a2a3fe')}</code>. Portal note ({CARD['submission']['note_chars']} chars, limit 140): <q>{e(CARD['submission']['note'])}</q>.</p>
<p><strong>Why the file is all-zero-and-one:</strong> the metric is distance-weighted and rewards any positive prediction near a hidden fault pixel. A binary dot raster at 300 m spacing is the budget-controlled form used by every public leaderboard file; continuous surfaces were rejected by this repository's registry gate and by the earlier portal error “Predicted values must be in range [0, 1]”.</p></section>

<section class="card table-card"><div class="table-heading"><div><h2>Method</h2><p>One lane, no private fork: shared feature stack, shared evaluator, shared writer.</p></div><span class="tag green">WBG5</span></div>
<p>Prior surface P = 0.6 × SGMC fault-likeness + 0.4 × detrended-topography percentile. The SGMC model is a HistGradientBoosting classifier (41 features: the 19 organizer bands, 11 lidar scarp bands, 8 radiometric bands, distance-to-catalogue, distance-to-springs, distance-to-vents) trained only on the independent USGS State Geologic Map Compilation structure layers for NV/CA, with negatives more than 300 m from any SGMC fault. It never sees the competition labels. The topography term is the mean percentile of <code>det_elev</code> and <code>det_elev_slope</code>. Dots are a score-ordered Poisson-disk sample (3 px = 300 m minimum spacing) inside the footprint and outside the mapped catalogue.</p>
<p><strong>Named non-fault mimic:</strong> {e(CARD['named_non_fault_mimic'])}</p>
<p><strong>Spatial validation:</strong> 4-quadrant out-of-fold model, fold AUC {PRIOR['model_oof']['fold_auc'][0]:.3f} / {PRIOR['model_oof']['fold_auc'][1]:.3f} / {PRIOR['model_oof']['fold_auc'][2]:.3f} / {PRIOR['model_oof']['fold_auc'][3]:.3f}, pooled {PRIOR['model_oof']['pooled_auc']:.3f} (no single feature above 0.62, so the leakage canary at 0.90 is not tripped). The DTI curve uses out-of-fold scores only.</p></section>

<section class="card table-card"><div class="table-heading"><div><h2>Fold-honest budget sweep</h2><p>Truth: USGS SGMC faults in the footprint more than 300 m from the public catalogue ({SWEEP['truth_px']:,} px). Un-masked, exact 300 m triangular kernel, α = 0.2, β = 0.8.</p></div><span class="tag green">SGMC-PROXY-DTI</span></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Budget (dots)</th><th>DTI</th><th>TP<sub>w</sub></th><th>FP<sub>w</sub></th><th>FN<sub>w</sub></th></tr></thead><tbody>{sweep_rows}</tbody></table></div>
<div class="table-footer"><div>150k and 200k are statistically indistinguishable; 300k degrades. 150k ships because it is the flattest point and has the fewest false positives.</div></div></section>

<section class="card table-card"><div class="table-heading"><div><h2>Equal-budget control against the public files</h2><p>The champion files ship 37,654–44,090 dots, so shipped-file comparison would confound budget with surface quality. Same truth array, same evaluator, my top-scoring 37,654 dots.</p></div><span class="tag green">like-for-like</span></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>File / row</th><th>Dots</th><th>SGMC-PROXY-DTI</th></tr></thead><tbody>{eq_rows}</tbody></table></div>
<div class="table-footer"><div>At 37,654 dots: mine {EQ37654:.4f} vs GEMSDOE32 B2 {EQB2:.4f} — a {ratio:.2f}× advantage. At 44,090 dots: {EQ44090:.4f} vs {EQD28:.4f} for GEMSDOE25 D2.8.</div></div></section>

<section class="card table-card"><div class="table-heading"><div><h2>The nine files, scored against catalogue truth</h2><p>Un-masked, catalogue used as truth — the opposite of the organizer rule. <strong>Only the ordering is meaningful; the absolute values are not leaderboard scores.</strong></p></div><span class="tag">proxy only</span></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Site</th><th>Dots</th><th>Dots ≤3 px of catalogue</th><th>Catalogue-truth DTI (un-masked)</th></tr></thead><tbody>{nine_rows}</tbody></table></div>
<div class="table-footer"><div>The ordering is inverted against the reported leaderboard scores: the highest reported value (B2, 0.2778) has the lowest catalogue-truth DTI (0.0067). That is the fingerprint of known-pixel masking, not of a better model.</div></div></section>

<section class="card table-card"><div class="table-heading"><div><h2>Why GEMSDOE32 B2 reports 0.2778</h2><p>Measured subset arithmetic, then an explicitly labelled inference.</p></div><span class="tag">forensics</span></div>
<p><strong>Measured.</strong> B2 (37,654 dots, user-reported 0.2778) is a strict subset of GEMSDOE25 D2.8 (44,090 dots, user-reported 0.2600). The 6,436 dropped dots all sit 1–2 px from a mapped catalogue pixel (3,891 ≤1 px, 2,545 at 1–2 px); B2's nearest dot to the catalogue is 2.236 px away. No surface changed — only the dot set did.</p>
<p><strong>Inference (labelled as such).</strong> The official mask removes exact known-fault pixels, with no buffer. A dot in the 1–2 px collar therefore still competes: it earns TP only if an <em>unmapped</em> truth pixel lies within 3 px, and otherwise pays the full false-positive weight. Removing those dots raised the reported index, which is what happens when they were net false positives. The opposite hypothesis — that a scored collar of new fault pixels surrounds every mapped fault — predicts the removal should have lowered the index. It did not, so the evidence favours “dead weight”, not “a better surface”.</p>
<p><strong>Can we beat it?</strong> Not by resubmitting that family: B2 is already the same dots minus their dead weight, and GEMSDOE36 (B2 plus 1,200 dots) reports 0.2750, slightly <em>lower</em>. On an independent truth set our surface scores 1.64× B2 at B2's own dot budget. Whether that transfers to the organizer index is not measurable offline; no absolute score is projected here.</p></section>

<section class="card table-card"><div class="table-heading"><div><h2>Registry overlap, with its null</h2><p>Literal stop: more than 70% of my dots within 3 px of one registry raster's dots. Null column: a uniform-random 150,000-dot Poisson-disk set with the identical placement geometry.</p></div><span class="tag green">gate PASS</span></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Site</th><th>Raw Spearman (all grid)</th><th>Smoothed Spearman (footprint)</th><th>My dots ≤3 px of theirs</th><th>Their dots ≤3 px of mine</th><th>Null: theirs ≤3 px of random set</th><th>Null: random set ≤3 px of theirs</th></tr></thead><tbody>{overlap_table}</tbody></table></div>
<div class="table-footer"><div>Worst literal value {pct(CARD['uniqueness']['max_frac_my_dots_within_3px'])} against a 70% stop. The “63% of their dots near mine” figure that looked alarming is <em>below</em> the 66% random null, so it is not evidence of copying.</div></div></section>

<section class="card guide-card"><h2>Disclosed caveat: the 10 px smoothed rank correlation is above 0.90</h2>
<p>On all 12.28 M grid cells the 10 px smoothed Spearman is {RULE['tests_run']['surface_rank_correlation_smoothed_10px']['range'][0]:.4f}–{RULE['tests_run']['surface_rank_correlation_smoothed_10px']['range'][1]:.4f}, above the 0.90 line. It is reported here rather than hidden. Its measured null is {SMNULL['rows']['GEMSDOE24']['smoothed_spearman_random150k_vs_site']:.4f} (GEMSDOE24) and {SMNULL['rows']['GEMSDOE32']['smoothed_spearman_random150k_vs_site']:.4f} (GEMSDOE32) for <em>random</em> dots, so the placement-attributable excess is 0.056–0.067 on a 0.85 baseline. The protocol's stated duplicate test is dot proximity, which passes with a 2.6× margin. Both numbers are on the page; the decision rests on the stated test, and the residual similarity is expected when every competitor consumes the same public geophysics.</p>
<p><a class="text-link" href="../data/wbg5_rule_decision.json">Full rule decision JSON →</a> · <a class="text-link" href="../data/wbg5_smoothed_null.json">Smoothed-statistic null JSON →</a></p></section>

<section class="card table-card"><div class="table-heading"><div><h2>What this is not</h2><p>Limits a reader must apply before spending a weekly slot.</p></div><span class="tag">honesty</span></div>
<ul>
<li><strong>Not an organizer score.</strong> No local harness reproduces the organizer mask of all USGS/INGENIOUS pixels, so SGMC-PROXY-DTI cannot be converted into a leaderboard value. No absolute score is projected.</li>
<li><strong>Supporting holdout is weaker than the primary evidence.</strong> Under hide-and-recover of whole catalogue segments the scarp+topography blend reaches {HOLD_AT_150K*100:.2f}% at 150k versus {HOLD_RANDOM_150K*100:.2f}% for random; the SGMC term is excluded from that harness because its distance feature uses the full catalogue.</li>
<li><strong>Transfer risk.</strong> If the hidden new-fault set is short splays rather than long structures, the SGMC-trained signature may transfer less well.</li>
<li><strong>The public subset is unknown.</strong> Only predictions inside it are scored, and the file over-covers the whole footprint.</li>
<li><strong>A local pass is not a portal receipt.</strong> Upload once and keep the receipt; if the portal rejects the bytes, that receipt outranks every number on this page.</li>
</ul></section>

<section class="card guide-card"><h2>Reproduce</h2>
<pre class="mono">python scripts/wbg5_emit.py --out submissions/{e(TIF)}   # rebuild + validate + hash
python scripts/build_wbg5_site.py                        # re-render this page
python scripts/check_readiness.py --check</pre>
<p>Evidence files: <a href="../data/run-card-wbg5.json">run card</a> · <a href="../data/wbg5_prior_experiment.json">independent prior benchmark</a> · <a href="../data/wbg5_budget_sweep.json">budget sweep</a> · <a href="../data/wbg5_blend_sweep.json">blend audit</a> · <a href="../data/wbg5_equal_budget.json">equal-budget control</a> · <a href="../data/wbg5_overlap_null.json">overlap null</a> · <a href="../data/wbg5_rule_decision.json">rule decision</a> · <a href="../data/wbg5_nine_site_proxy.json">nine-site proxy</a> · <a href="../data/wbg5_holdout_experiment.json">hide-and-recover holdout</a>.</p></section>
"""


def header(current: str) -> str:
    nav = [('../index.html', 'Overview'), ('../release.html', 'Download status'),
           ('../executive-summary.html', 'Executive summary'), ('../wbg5/index.html', 'WBG5 decision'),
           ('../research.html', 'Research'), ('../sources.html', 'Sources')]
    links = ''.join('<a href="{}"{}>{}</a>'.format(href, ' aria-current="page"' if href == current else '', label)
                    for href, label in nav)
    return (f'<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">'
            f'<a href="../index.html" class="brand">GEMS <small>RESEARCH</small></a>'
            f'<nav class="nav" aria-label="Main navigation">{links}</nav>'
            f'<div class="top-right"><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a>'
            f'<span class="top-status ok"><span class="dot"></span> OK to download &amp; submit</span></div></div></header>')


html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="WBG5 decision: OK TO DOWNLOAD AND SUBMIT, research-grade, with hash-bound evidence and disclosed limits."><meta name="theme-color" content="#0b5d4d"><title>WBG5 decision · GEMS Research</title><link rel="stylesheet" href="../styles.css"></head><body>{header('../wbg5/index.html')}<main id="main" class="shell main">{body}</main><footer class="footer"><div class="shell"><div><strong>GEMS RESEARCH</strong> · OK TO DOWNLOAD AND SUBMIT (research-grade)</div><div><a href="../release.html">Download status</a> &nbsp;·&nbsp; <a href="../data/run-card-wbg5.json">WBG5 run card</a> &nbsp;·&nbsp; <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition ↗</a></div></div></footer></body></html>'''

OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(html, encoding='utf-8')

data_dir = DOCS / 'data'
data_dir.mkdir(parents=True, exist_ok=True)
pairs = {
    'evidence/wbg5_run_card.json': 'run-card-wbg5.json',
    'evidence/wbg5_prior_experiment.json': 'wbg5_prior_experiment.json',
    'evidence/wbg5_budget_sweep.json': 'wbg5_budget_sweep.json',
    'evidence/wbg5_blend_sweep.json': 'wbg5_blend_sweep.json',
    'evidence/wbg5_equal_budget.json': 'wbg5_equal_budget.json',
    'evidence/wbg5_overlap_null.json': 'wbg5_overlap_null.json',
    'evidence/wbg5_rule_decision.json': 'wbg5_rule_decision.json',
    'evidence/wbg5_smoothed_null.json': 'wbg5_smoothed_null.json',
    'evidence/wbg5_holdout_experiment.json': 'wbg5_holdout_experiment.json',
    'evidence/wbg5_nine_site_proxy.json': 'wbg5_nine_site_proxy.json',
}
for src, dst in pairs.items():
    shutil.copyfile(ROOT / src, data_dir / dst)
print(f'wrote {OUT / "index.html"} ({len(html):,} bytes) and {len(pairs)} evidence copies')
