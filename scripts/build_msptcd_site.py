#!/usr/bin/env python3
"""Build the archived MSPTCD pages; never authorize a candidate or run a model."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
OUT = DOCS / 'msptcd'


def e(value: object) -> str:
    return escape(str(value), quote=True)


def render(title: str, current: str, body: str) -> str:
    nav = [('index.html', 'Campaign'), ('executive-summary.html', 'Evidence'),
           ('research.html', 'Methods'), ('sources.html', 'Sources')]
    links = ''.join(f'<a href="{href}"' + (' aria-current="page"' if href == current else '')
                    + f'>{label}</a>' for href, label in nav)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Historical MSPTCD research, not a competition submission">
<title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="../styles.css"></head><body>
<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a class="brand" href="../index.html">GEMS <small>RESEARCH</small></a><nav class="nav" aria-label="MSPTCD navigation">{links}</nav>
<a href="../index.html">Main dashboard ↗</a></div></header>
<main id="main" class="shell main"><div class="intro"><div><p class="eyebrow">Historical research · not a new run</p>
<h1>{e(title)}</h1><p>Prior report, preserved with an independent byte-level stop review.</p></div></div>
<section class="banner"><div class="banner-copy"><p class="banner-label">Decision · negative</p>
<h2>DO NOT SUBMIT the archived MSPTCD raster.</h2><p>Its dots overlap the registered binary lattice by 100% within 3 pixels.
The complete registry and source pre-placement gate were not validated. No approval is implied by a format check.</p></div></section>
{body}</main><footer class="footer"><div class="shell"><span>Evidence before submission</span><a href="../index.html">Back to main dashboard</a></div></footer></body></html>'''


def main() -> int:
    card = json.loads((ROOT / 'evidence/RUN_CARD_MSPTCD.json').read_text())
    res = json.loads((ROOT / 'evidence/wbg2_msptcd_results.json').read_text())
    can = json.loads((ROOT / 'evidence/wbg2_msptcd_canaries.json').read_text())
    audited = json.loads((ROOT / 'evidence/local_artifact_audit_20261027.json').read_text())
    artifact = next(x for x in audited['artifacts'] if x['name'] == 'MSPTCD')
    if (card['ok_to_submit'] is not False or card['verdict'] != 'negative'
            or artifact['ok_to_submit'] is not False
            or artifact['sha256'] != res['artifact']['tif_sha256']
            or artifact['final_overlap_3px']['13GEMSDOE'] <= 0.7):
        raise SystemExit('Archived result changed; manual fail-closed review is required.')
    scores = res['holdout_pooled']['scores']
    score_rows = ''.join(
        f'<tr><td data-label="Arm"><code>{e(arm)}</code></td>'
        f'<td data-label="Reported HOLDOUT-DTI">{s["dti"]:.6f}</td>'
        f'<td data-label="Reported 95% CI">[{s["ci95"][0]:.6f}, {s["ci95"][1]:.6f}]</td></tr>'
        for arm, s in scores.items()
    )
    prior = '''<div class="callout"><strong>Evidence class: prior source-reported HOLDOUT-DTI, not independently reproduced here.</strong>
These are mapped-fault holdout measurements, not a competition score. The reported CI is conditional on the fixed folds/fits;
the best of multiple arms was selected, so it is not a selection-adjusted forecast. A feature-alone canary cannot prove zero leakage.</div>'''
    index = f'''<section class="card guide-card"><h2>Prior reported holdout</h2>{prior}
<p>Prior report: <code>gems57-pooled-hide-v2</code>, 60,988 withheld positive pixels, four buffered spatial folds and
1,000 20 km spatial-cluster bootstrap draws. The reported winning arm has HOLDOUT-DTI <strong>0.042554</strong>
(95% CI [0.032059, 0.054765]) versus control <strong>0.023409</strong> ([0.015356, 0.031895]).
No conclusion about organizer performance follows.</p><div class="table-scroll"><table class="data-table"><thead><tr><th>Arm</th>
<th>Reported HOLDOUT-DTI</th><th>Reported 95% spatial CI</th></tr></thead><tbody>{score_rows}</tbody></table></div>
<p>Reported individual-feature canaries: {can['features_tested']} features × {can['folds_tested']} folds, maximum
2-sided AUC {can['max_two_sided_auc']:.4f} against 0.90. These are source-reported, and passing them is not proof of no leakage.</p>
<p><a href="../data/wbg2_msptcd_results.json">Source result JSON ↗</a> · <a href="../data/wbg2_msptcd_canaries.json">Source canaries ↗</a> ·
<a href="../data/local_artifact_audit_20261027.json">Independent saved-byte audit ↗</a></p></section>'''
    evidence = f'''<section class="card guide-card"><h2>What was and was not checked</h2>{prior}
<p>Saved artifact <code>{e(Path(artifact['path']).name)}</code>, SHA-256 <code>{e(artifact['sha256'])}</code>,
contains {artifact['positive_footprint_cells']:,} positive cells. It is finite and matched the mirrored grid in a local read-back;
the mirror is not an authenticated organizer sample. The byte audit found 100% lattice overlap and 100% overlap with the
continuous prior under the shared finite-positive definition; whether continuous fields count as dots remains unresolved.</p>
<p>The historical script computed allocation before running its novelty report. That is not the requested pre-placement stop.
The complete and current registry was not checked. The script entry point is now disabled; the archived TIFF remains research-only.</p>
<p>On the nine historical focus sites, GEMSDOE32's 0.2778 is user-reported, not a receipt. Reopened masks show B2 equals D2.8
with a 2-pixel catalogue collar removed, but hidden truth and the cause of its claimed score remain unknown.
<a href="../research/why-b2-scored-2778.html">Detailed B2 analysis ↗</a></p></section>'''
    research = '''<section class="card guide-card"><h2>What the historical code implements</h2>
<p>The inspected module combines 19 owner-mirrored bands with 12 operators: potential-field tilt gradients, depth-proxy shifted
magnetic/gravity concordance, electrical flank differences, topographic Hessian ridges, total-count/terrain residuals, conductive-base
steps, gradient orientation coherence, strain and seismicity indices. These are <strong>already implemented</strong> ideas, not the new shortlist.</p>
<p>Mirror metadata and the official description disagree on band 15: use the term conductive-base depth, not an assumed basement depth.
The official feature inventory describes <code>tc</code> as radiometric total count while mirror band metadata describes tilt/curvature;
value distributions are suggestive but cannot authenticate physical units or origin.</p>
<p>Lithologic contacts, dikes, acquisition striping, surface cover, shorelines and anthropogenic features can mimic fault signals.
Neither a gradient nor a canary pass is proof of a previously unmapped fault.</p>
<p><a href="../research.html">Four distinct, untested desk proposals ↗</a> ·
<a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/msptcd_findings.md">Revised research findings ↗</a></p></section>'''
    sources = '''<section class="card guide-card"><h2>Official sources and access boundaries</h2><ul class="source-list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem and metric ↗</a> — 300 m kernel, target and file specification.</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">Organizer masking clarification ↗</a> — pixel-exact known-fault mask; no buffer; new truth can be within 300 m.</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release ↗</a> — free survey metadata; external binary access was not verified.</li>
<li><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP ↗</a> — free products; specific study-area tile coverage was not verified.</li></ul>
<p><a href="../data/RUN_CARD_MSPTCD.json">Historical run card ↗</a> · <a href="../data/local_artifact_audit_20261027.json">New audit ↗</a> ·
<a href="../sources.html">Full source register ↗</a></p></section>'''
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, title, body in [('index.html', 'MSPTCD campaign', index),
                                  ('executive-summary.html', 'MSPTCD evidence', evidence),
                                  ('research.html', 'Methods and limits', research),
                                  ('sources.html', 'Sources and provenance', sources)]:
        (OUT / filename).write_text(render(title, filename, body), encoding='utf-8')
    print('Built four archival MSPTCD pages; no model or candidate was run.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
