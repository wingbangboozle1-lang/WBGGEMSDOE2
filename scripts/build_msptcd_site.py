#!/usr/bin/env python3
"""Render reviewed HISTORICAL campaign evidence, not a new validated model.

The previous renderer invented band names/indices and overstated canary proof.
Its source is archived. The new pages use actual committed receipts and feature
names; no holdout is rerun, projection calibrated, or research TIFF promoted.
"""
from __future__ import annotations

import ast
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.release import load_negative_release, read_json


def e(value):
    return escape(str(value), quote=True)


def shell(title, body):
    notice = '''<section class="banner" data-release-status="blocked"><div class="banner-copy">
<p class="banner-label">Historical source-reported campaign · not independently reproduced</p>
<h2>No file is approved for submission. DO NOT SUBMIT.</h2><p>All local TIFFs fail the literal registry gate. The corrected v2 orientation feature has no measured holdout result.
Passing AUC canaries is not proof of zero leakage. <a href="../release.html">Current byte-bound release decision →</a></p></div></section>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · Historical MSPTCD · GEMS Research</title><meta name="description" content="Historical MSPTCD evidence with corrections and a negative submission verdict.">
<link rel="stylesheet" href="../styles.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="shell"><a class="brand" href="../index.html">GEMS <small>RESEARCH</small></a><nav class="nav" aria-label="Main navigation">
<a href="index.html">Historical overview</a><a href="executive-summary.html">Review findings</a><a href="research.html">Actual features</a><a href="sources.html">Sources</a><a href="../release.html">Download status</a></nav></div></header>
<main id="main" class="shell main">{notice}{body}</main><footer class="footer"><div class="shell"><strong>Research only · DO NOT SUBMIT</strong>
<a href="../data/RUN_CARD_MSPTCD.json">Historical card with correction</a> · <a href="../data/run-card.json">Current review card</a></div></footer></body></html>'''


def feature_names(root):
    # Read constants without importing a scientific module into the light Pages build.
    parsed = ast.parse((root / 'src/wbggems/msptcd.py').read_text())
    names = {}
    for node in parsed.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in ('RAW_BAND_NAMES', 'CORE_PHYSICS_NAMES', 'STRAIN_SEIS_NAMES'):
                names[node.target.id] = ast.literal_eval(node.value)
    if len(names.get('RAW_BAND_NAMES', [])) != 19 or len(names.get('CORE_PHYSICS_NAMES', [])) != 9 or len(names.get('STRAIN_SEIS_NAMES', [])) != 3:
        raise ValueError('MSPTCD feature schema changed; review the historical narrative')
    return names


def main() -> int:
    load_negative_release(ROOT)
    card = read_json(ROOT / 'evidence/RUN_CARD_MSPTCD.json')
    res = read_json(ROOT / 'evidence/wbg2_msptcd_results.json')
    cache = read_json(ROOT / 'evidence/feature_cache.json')
    if (card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False
            or card.get('post_review', {}).get('promotion_evidence_valid') is not False
            or cache.get('count') != 19):
        raise ValueError('Historical MSPTCD evidence changed; refusing to publish an approval')
    scores = res['holdout_pooled']['scores']
    out = ROOT / 'docs/msptcd'
    out.mkdir(parents=True, exist_ok=True)
    art = card['research_candidate']
    rows = []
    for arm, score in scores.items():
        rows.append(f'''<tr><td data-label="Historical arm"><code>{e(arm)}</code></td><td data-label="HOLDOUT-DTI">{score['dti']:.6f}</td>
<td data-label="95% CI">[{score['ci95'][0]:.6f}, {score['ci95'][1]:.6f}]</td><td data-label="Withheld positives">{score['withheld_positive_pixels']:,}</td></tr>''')
    index = f'''<div class="intro"><div><p class="eyebrow">Historical campaign record</p><h1>MSPTCD: evidence, not approval</h1>
<p>Three prior experiments and a control are source-reported. No candidate experiment was run in the current review.</p></div></div>
<section class="card table-card"><div class="table-heading"><div><h2>SOURCE-REPORTED HOLDOUT-DTI</h2>
<p>Evaluator <code>{e(res['holdout_pooled']['evaluator_version'])}</code>; four label-blind quadrant folds, whole intersecting components hidden, 8 km buffer, pooled 300 m triangular DTI.
Intervals are conditional paired spatial-cluster bootstrap intervals, not leaderboard intervals.</p></div></div><div class="table-scroll"><table class="data-table">
<thead><tr><th>Historical arm</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Withheld positives</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section class="card guide-card"><h2>Existing research artifact</h2><p><code>{e(art['name'])}</code></p><p class="mono">SHA-256 {e(art['tif_sha256'])}</p>
<p><a href="../{e(art['tif_path'].removeprefix('docs/'))}" download>Download existing research TIFF — DO NOT SUBMIT</a></p>
<p>Independent saved-byte recheck: local format passes against an unauthenticated owner mirror; all of its positive cells fall within three pixels of the registered lattice.
The original pre-placement surface was not replayed. No new leaderboard estimate or organizer receipt exists.</p>
<p><a href="../data/release_audit.json">Current forensic byte audit</a> · <a href="../data/wbg2_msptcd_results.json">Historical results JSON</a></p></section>'''
    review_items = ''.join(f'<li><strong>{e(key.replace("_", " "))}:</strong> {e(val)}</li>' for key, val in card['post_review'].items()
                           if key.endswith(('defect', 'caveat', 'correction')))
    review = f'''<div class="intro"><div><p class="eyebrow">Independent code review</p><h1>What changed after review</h1>
<p>The old numeric results are preserved, not silently reattributed to corrected code.</p></div></div>
<section class="card guide-card"><h2>Corrections and limitations</h2><ul>{review_items}</ul>
<p>The shared evaluator and writer remain pinned and unchanged; these corrections affect a local scientific feature, its cache safety and publication claims.
The campaign entry point is guarded before data/model/evidence writes because no method lane is currently assigned.</p>
<h2>Band semantics: evidence, not identity proof</h2><p>The official illustration identifies radiometric total counts, and the mirror's Band 6 values are inconsistent with an unscaled tilt angle in radians.
Positive values alone cannot establish channel identity, units, or a universal sign distribution for tilt. The previous renderer also invented <code>heat_flow</code>, Bouguer and aspect bands absent from this stack; those claims have been removed.</p>
<p>Band 15 retains the official description “depth to conductive base.” It is not authenticated as geological basement depth.</p>
<h2>B2 lineage</h2><p>The nine-site byte audit supports B2 = D2.8 minus its 6,436 dots within 2 pixels of the mirrored catalogue. It does not prove the cause of the USER-REPORTED 0.2778.
<a href="../research/why-b2-scored-2778.html">Full metric analysis and official sources →</a></p>
<p><a href="../release.html#nine-sites">Nine current executive summaries</a> · <a href="../data/RUN_CARD_MSPTCD.json">Historical run card with corrections</a></p></section>'''
    names = feature_names(ROOT)
    band_rows = ''.join(f'<tr><td data-label="Band">{i}</td><td data-label="Local alias"><code>{e(name)}</code></td><td data-label="Mirror description">{e(cache["bands"][i-1]["description"])}</td></tr>'
                        for i, name in enumerate(names['RAW_BAND_NAMES'], 1))
    operator_list = ''.join(f'<li><code>{e(name)}</code></li>' for name in names['CORE_PHYSICS_NAMES'] + names['STRAIN_SEIS_NAMES'])
    research = f'''<div class="intro"><div><p class="eyebrow">Actual source schema</p><h1>Which features really exist?</h1>
<p>Names below are read from source constants and the pinned 19-band cache receipt, not inferred from a generic geological schema.</p></div></div>
<section class="card table-card"><div class="table-heading"><h2>Raw owner-mirror bands</h2></div><div class="table-scroll"><table class="data-table"><thead><tr><th>Band</th><th>Local alias</th><th>Mirror description (not independently authenticated)</th></tr></thead><tbody>{band_rows}</tbody></table></div></section>
<section class="card guide-card"><h2>Local derived operators</h2><ul>{operator_list}</ul>
<p><code>grav_mag_orient_coherence</code> now uses squared axial cosine; historical v1 used absolute double-angle cosine and treated perpendicular normals as parallel.
No HOLDOUT-DTI is measured for the correction. Cache entries are bound to input bytes, footprint, implementation and outputs.</p>
<h2>Next research proposals</h2><p>Depth-shifted concordance, conductive-flank asymmetry, strain/seismicity conditioning and greedy placement have already been tried locally.
They are not presented as new hypotheses. <a href="../research.html">The revised four-item N1–N4 shortlist</a> is unimplemented, unvalidated and not assigned as a lane.</p>
<p>A new-data hypothesis is not viable merely because a source page exists. Exact 3DEP tiles and independent GeoDAWN line-level data were not restored in this session.</p></section>'''
    sources = '''<div class="intro"><div><p class="eyebrow">Official and measured evidence</p><h1>Sources and provenance</h1></div></div>
<section class="card guide-card"><h2>What official sources support</h2><ul class="source-list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, metric and format</a> — fault target, listed feature families, single float32 band, EPSG:32611, 100 m and [0,1]. It does not authenticate the mirror's band numbering.</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2">DrivenData staff clarification</a> — known fault pixels excluded; no broader collar confirmed.</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release, DOI 10.5066/P93LGLVQ</a> — magnetic/radiometric data, flight geometry, variable clearance; release marked CC0.</li>
<li><a href="https://pubs.usgs.gov/publication/70271418">USGS Argenta Rise study</a> — multi-physics structural interpretation, not validation of our transforms.</li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS compilation</a> — regional resources and attribution terms, not proof of binary availability or study-area coverage here.</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules</a> — quota, single final choice and AI disclosure.</li></ul>
<h2>Audit data</h2><p><a href="../data/feature_cache.json">Restored raw-band cache receipt</a> · <a href="../data/release_audit.json">Independent raster recheck</a> ·
<a href="../data/wbg2_msptcd_canaries.json">Historical feature-canary results</a> · <a href="../data/RUN_CARD_MSPTCD.json">Historical card with review</a> ·
<a href="../sources.html">Full source register</a></p><p>The public mirror was restored by SHA-256, not by authenticated DrivenData access. Neither a good canary nor a local format pass proves competition performance.</p></section>'''
    for name, title, body in [('index.html','Historical MSPTCD results',index), ('executive-summary.html','MSPTCD review findings',review),
                              ('research.html','Actual MSPTCD feature schema',research), ('sources.html','MSPTCD sources',sources)]:
        (out / name).write_text(shell(title, body), encoding='utf-8')
    print('Built four corrected, research-only historical MSPTCD pages.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
