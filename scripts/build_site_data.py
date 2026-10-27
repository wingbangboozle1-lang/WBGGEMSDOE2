#!/usr/bin/env python3
"""Build static, byte-audited dashboard data from committed evidence."""
from pathlib import Path
import json
import shutil
from html import escape

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'config/registry_inputs.json').read_text())
hypothesis_data = json.loads((ROOT / 'config/research_hypotheses.json').read_text())
audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
card = json.loads((ROOT / 'evidence/run_card.json').read_text())
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
# A promoted card must still be receipt-bound: the historical parallel rejections
# are preserved verbatim, and the promoted raster hash must be present.
if (card.get('schema') != 'wbggems.run-card.v2'
        or card.get('verdict') not in ('promote-to-selector-only', 'negative')
        or (card.get('ok_to_submit') and not card.get('raster_sha256'))
        or conduit.get('ok_to_submit') is not False
        or conduit.get('sha256') != card.get('conduit_parallel_session', {}).get('rejected_candidate_sha256')
        or round(conduit.get('witnesses', {}).get('13GEMSDOE', {}).get('source_threshold_ge_0_5', {}).get('fraction', 0), 6) != 0.998726
        or review.get('ok_to_submit') is not False
        or review.get('sha256') != card.get('parallel_session', {}).get('rejected_candidate_sha256')
        or review.get('format', {}).get('masked_inside') != 5132809
        or round(review.get('literal_overlap_3px', {}).get('lattice', 0), 6) != 0.993838):
    raise SystemExit('This static build is fail-closed; an independently implemented selector is required for promotion.')
cap = audit.get('lattice_capacity', {})
lineage = audit.get('lineage', {})
if (cap.get('budget') != 37654 or cap.get('footprint_cells') != 5167373
        or cap.get('covered_cells') != 5160724 or cap.get('uncovered_cells') != 6649
        or cap.get('uncovered_within_3px_of_footprint_exterior') != 6485
        or round(cap.get('minimum_overlap', 0), 4) != 0.8234
        or cap.get('feasible_under_limit') is not False
        or audit.get('dense_probability_prior', {}).get('full_footprint_positive') is not True
        or not lineage.get('GEMSDOE25_and_30_identical_in_footprint')
        or not lineage.get('GEMSDOE32_equals_GEMSDOE25_pruned_at_2px')
        or lineage.get('GEMSDOE36_additions_to_32') != 1200
        or lineage.get('GEMSDOE36_removals_from_32') != 0):
    raise SystemExit('Audit evidence changed; review the static narrative before publishing.')
entries = []
for item in manifest['inputs']:
    if item['user_reported_claim'] is None:
        continue
    facts = audit['items'][item['id']]
    if facts['sha256'] != item['sha256'] or facts['max_focus_peer_overlap_3px']['fraction'] <= 0.70:
        raise SystemExit(f"Historical audit mismatch for {item['id']}")
    entries.append({'site': item['id'], 'site_url': 'sites/' + item['id'] + '.html', 'file': Path(item['path']).name, 'url': item['url'],
                    'sha256': item['sha256'], 'claimed_value': f"{item['user_reported_claim']:.4f}",
                    'claim_evidence': item['claim_evidence'], 'leaderboard_estimate': None,
                    'max_peer_overlap': facts['max_focus_peer_overlap_3px'],
                    'lattice_overlap': facts['fraction_within_3px_of_lattice'],
                    'unique_under_literal_rule': False, 'ok_to_submit': False})
if len(entries) != 9:
    raise SystemExit('Exactly nine priority historical inputs are required.')
entries.sort(key=lambda e: float(e['claimed_value']), reverse=True)
output = ROOT / 'site/data'
output.mkdir(exist_ok=True, parents=True)
(output / 'focus.json').write_text(json.dumps({'schema': 'wbggems.focus.v1',
    'generated_utc': audit['generated_utc'], 'note': 'Claims are unverified; historical TIFFs are for research only.',
    'entries': entries}, indent=2) + '\n')
# One explicit executive page per requested site; these are historical references only.
pages = ROOT / 'site/sites'
pages.mkdir(parents=True, exist_ok=True)
for entry in entries:
    facts = audit['items'][entry['site']]
    site, filename, source = (escape(entry[k], quote=True) for k in ('site', 'file', 'url'))
    sha = escape(entry['sha256'])
    peer = escape(entry['max_peer_overlap']['peer'])
    overlap = entry['max_peer_overlap']['fraction'] * 100
    lattice = entry['lattice_overlap'] * 100
    claim = escape(entry['claimed_value'])
    dots = f"{facts['dots']:,}"
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Historical {site} submission audit"><title>{site} audit | GEMS Fieldnotes</title><link rel="stylesheet" href="../assets/style.css"></head><body>
<a class="skip-link" href="#main">Skip to main content</a><header class="site-header"><div class="shell header-inner"><a class="brand" href="../"><span class="brand-mark"><span></span></span><span>GEMS <b>FIELDNOTES</b><small>RESEARCH WORKSPACE</small></span></a><nav aria-label="Main navigation"><a href="../">Overview</a><a class="active" href="../#portfolio">Portfolio</a><a href="../research.html">Research</a><a href="../executive.html">Submission guide ↗</a></nav><a class="header-github" href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">View repository ↗</a></div></header>
<main id="main" class="shell"><div class="breadcrumb"><a href="../">GEMS PRIZE</a><span class="crumb-sep">/</span><a href="../#portfolio">NINE SITES</a><span class="crumb-sep">/</span><span>{site}</span></div><section class="page-hero"><div><div class="eyebrow"><span class="eyebrow-line"></span> HISTORICAL REFERENCE · RESEARCH ONLY</div><h1>{site}<br><em>evidence brief.</em></h1><p>One pinned historical file, its reported claim, and the actual byte-level uniqueness check. No prior submission is recommended for upload again.</p></div><aside class="page-aside"><span class="signal-label">AUTOMATED DECISION</span><b>Do not submit.</b>The historical raster is not a unique new candidate; its claim is not an authenticated organizer receipt.</aside></section><div class="page-layout"><article class="prose"><h2 id="decision">Decision summary</h2><p><b>Best named historical file:</b> <code>{filename}</code>. The user/owner-reported claim is <b>{claim}</b>; it is not independently confirmed by a submission receipt. A leaderboard estimate for a new file is unavailable, and no HOLDOUT-DTI was calculated for this archived file.</p><p>In our directed test, <b>{overlap:.2f}%</b> of this file's {dots} dots lie within three pixels of {peer}, above the 70% duplicate stop. Its overlap with the registered lattice is <b>{lattice:.2f}%</b>. Original pre-placement surfaces were not independently replayed. This is sufficient to say <b>not unique under the requested rule</b>, not to prove the cause of the historical claim.</p><div class="notice"><b>Research download only.</b> The file below is an existing historical reference, not a newly generated submission. No upload name or note is assigned.</div><div class="download-row"><div><b>{filename}</b><small>SHA-256: {sha}</small></div><a href="{source}">Historical reference ↗</a></div><h2 id="method">What was checked?</h2><p>The exact file was fetched by Git blob SHA, reopened as a single-band float32 GeoTIFF, and compared against a hash-checked <em>owner mirror</em> of the grid. That grid is not authenticated against the organizer's sample, and a local format pass is not evidence of portal acceptance. Pairwise distance uses an inclusive three-pixel Euclidean radius.</p><p><a href="../data/registry_audit.json">Download the full audit JSON</a> · <a href="../research.html#lineage">Read the B2 lineage</a> · <a href="../executive.html">Submission guide</a></p></article><aside class="side-nav"><span>ON THIS PAGE</span><a href="#decision">01 · Decision</a><a href="#method">02 · Evidence</a><a href="../#portfolio">← All nine sites</a></aside></div></main><footer><div class="shell footer-inner"><div><a class="brand footer-brand" href="../"><span class="brand-mark"><span></span></span><span>GEMS <b>FIELDNOTES</b><small>RESEARCH WORKSPACE</small></span></a><p>Built for careful decisions, not leaderboard promises.</p></div><div class="footer-links"><a href="../executive.html">Submission guide</a><a href="../research.html">Research & sources</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem ↗</a><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules ↗</a></div><p class="footer-note">RESEARCH ONLY<br><b>Do not submit.</b></p></div></footer></body></html>"""
    (pages / f"{entry['site']}.html").write_text(html)
for name in ('registry_audit.json', 'run_card.json', 'h31_preflight.json', 'parallel_review.json', 'conduit_review.json'):
    shutil.copyfile(ROOT / 'evidence' / name, output / name)
shutil.copyfile(ROOT / 'docs/data/focus-freshness.json', output / 'focus-freshness.json')
shutil.copyfile(ROOT / 'config/research_hypotheses.json', output / 'research_hypotheses.json')

# Keep the legacy /site/ research page synchronized with the structured shortlist
# used by the primary /docs/ dashboard and the Markdown research record.
hypothesis_cards = []
for h in sorted(hypothesis_data['hypotheses'], key=lambda row: row['potential_rank']):
    layers = escape('; '.join(h['layers']))
    external = h.get('external_data')
    external_html = ''
    if external:
        external_html = (f'<p><b>Official source and access check:</b> '
                         f'<a href="{escape(external["url"], quote=True)}">{escape(external["source"])} ↗</a>. '
                         f'{escape(external["access_check"])}</p>')
    source_links = ''.join(
        f'<li><a href="{escape(url, quote=True)}">Source for manual review ↗</a></li>'
        for url in h.get('sources', [])
    )
    hypothesis_cards.append(f'''<section class="hypothesis" id="{escape(h['id'], quote=True)}"><span>{escape(h['id'])} · QUALITATIVE POTENTIAL RANK {h['potential_rank']} · {escape(h['implementation_cost'].upper())} COST</span><h3>{escape(h['title'])}</h3><p><b>Expected HOLDOUT-DTI potential:</b> {escape(h['potential_label'])}; this is not a score estimate.</p><p><b>Layers:</b> {layers}.</p><p><b>Physical signature:</b> {escape(h['signature'])}</p><p><b>Why it may target an uncatalogued fault:</b> {escape(h['why_uncatalogued'])}</p><p><b>Difference from reviewed methods:</b> {escape(h['difference_from_reviewed_methods'])}</p><p><b>Named non-fault mimic:</b> {escape(h['non_fault_mimic'])}</p><p><b>Data/access status:</b> {escape(h['data_status'])}</p>{external_html}<ul>{source_links}</ul><span class="tag">Proposal only · not tested</span></section>''')
d28_count = int(audit['items']['GEMSDOE25']['dots'])
b2_count = int(audit['items']['GEMSDOE32']['dots'])
g36_additions = int(audit['lineage']['GEMSDOE36_additions_to_32'])
research_page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Four untested, evidence-bounded fault-mapping hypotheses; no lane assigned."><title>Research brief | GEMS Fieldnotes</title><link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip-link" href="#main">Skip to main content</a><header class="site-header"><div class="shell header-inner"><a class="brand" href="./"><span class="brand-mark"><span></span></span><span>GEMS <b>FIELDNOTES</b><small>RESEARCH WORKSPACE</small></span></a><nav aria-label="Main navigation"><a href="./">Overview</a><a href="./#portfolio">Portfolio</a><a class="active" href="research.html">Research</a><a href="executive.html">Submission guide ↗</a></nav><a class="header-github" href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">View repository ↗</a></div></header>
<main id="main" class="shell"><div class="breadcrumb"><a href="./">GEMS PRIZE</a><span class="crumb-sep">/</span><span>RESEARCH BRIEF</span></div><section class="page-hero"><div><div class="eyebrow"><span class="eyebrow-line"></span> MECHANISMS, NOT PROMISES</div><h1>Follow the<br><em>evidence.</em></h1><p>Geothermal systems motivate the work. The competition target is fault traces; an inferred fault is not proof of a geothermal vent.</p></div><aside class="page-aside"><span class="signal-label">METHOD LANE</span><b>UNASSIGNED.</b>Four ranked proposals are listed for review only. No candidate, holdout, or slot has been approved.</aside></section><div class="page-layout"><article class="prose"><h2 id="hypotheses">Four ranked, untested hypotheses</h2><p>{escape(hypothesis_data['ranking_basis'])}</p><p>{escape(hypothesis_data['novelty_scope'])}</p><div class="notice" id="lattice"><b>STOP — no experiment cleared.</b> The pinned binary lattice makes a 37,654-dot map exceed the literal overlap threshold; the registered continuous positive prior gives 100% overlap under the shared finite-positive support definition, subject to an unresolved interpretation. No exception is assumed. The registry is incomplete, and no global uniqueness pass is claimed. A pinned historical index lists 695 raster hashes, 684 outside the local witness manifest; that is metadata only, not a raster audit or proof of current coverage. <a href="../docs/data/shared_registry_index_summary.json">Index scope ↗</a>.</div>{''.join(hypothesis_cards)}<h2 id="lineage">GEMSDOE32 B2: measured historical raster lineage</h2><p>On the hash-checked owner mirrors, the GEMSDOE25 and GEMSDOE30 D2.8 masks are identical. The GEMSDOE32 B2 mask is the D2.8 mask after removing dots within two pixels of the mirrored catalogue: {d28_count:,} to {b2_count:,} positive pixels. GEMSDOE36 adds {g36_additions:,} dots to B2 and removes none. These are <b>REGISTRY-MEASUREMENTS</b> on owner-mirrored bytes—not an organizer receipt, causal explanation, or new-score estimate. See the <a href="data/registry_audit.json">full registry audit ↗</a> and <a href="../docs/research/why-b2-scored-2778.html">B2 forensic analysis ↗</a>.</p><h2 id="validation">Validation before any slot</h2><ol><li>Resolve the continuous-prior interpretation and restore a complete, fresh, immutable registry; do not move predictions to exploit footprint edges.</li><li>Record the explicit assigned method lane. This shortlist does not assign one.</li><li>Restore and authenticate inputs and the pinned shared feature stack/evaluator/writer. Owner-mirrored raw bands were reverified in an ignored session cache, which may not persist; the derived shared feature bank remains absent and mirror hashes do not establish organizer provenance.</li><li>On whole-segment spatial holdouts with a buffer, derive catalogue features from visible faults only, mask visible faults pixel-exactly, and run each feature-alone leakage canary. AUC above 0.90 or its inverse is an alarm.</li><li>Use the shared pooled DTI evaluator (alpha 0.2, beta 0.8, 300 m triangular kernel); compare against a matched same-fold incumbent and report evaluator version, withheld positives, and a spatial-block 95% CI.</li><li>Stop after three experiments or two hours. HOLDOUT-DTI is not a leaderboard score; promotion to a real slot is a separate selector step under the current quota.</li></ol><h2 id="sources">Official sources and limitations</h2><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem and layer inventory ↗</a> — fault traces are the label target.</li><li><a href="https://pubs.usgs.gov/publication/70271418">USGS Argenta Rise study ↗</a> — multi-physics context, not validation of these transforms.</li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release ↗</a> — exact line-file access not confirmed here.</li><li><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP ↗</a> — specific study-area tiles and coverage not checked.</li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS release 1391 ↗</a> — binary files not fetched here.</li></ul><p>For the structured hypothesis record and source/access register, see <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses.md">the repository research notes ↗</a>, <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/sources.md">source register ↗</a>, or <a href="data/research_hypotheses.json" download>download the shortlist JSON ↓</a>.</p></article><aside class="side-nav"><span>ON THIS PAGE</span><a href="#hypotheses">01 · Hypotheses</a>{''.join(f'<a href="#{escape(h["id"], quote=True)}">{escape(h["id"])} · {escape(h["title"][:34])}</a>' for h in hypothesis_data['hypotheses'])}<a href="#lineage">02 · B2 lineage</a><a href="#validation">03 · Validation</a><a href="#sources">04 · Sources</a><a href="./#portfolio">← Nine-site summary</a></aside></div></main><footer><div class="shell footer-inner"><div><a class="brand footer-brand" href="./"><span class="brand-mark"><span></span></span><span>GEMS <b>FIELDNOTES</b><small>RESEARCH WORKSPACE</small></span></a><p>Built for careful decisions, not leaderboard promises.</p></div><div class="footer-links"><a href="./">Overview</a><a href="executive.html">Submission guide</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem ↗</a><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules ↗</a></div><p class="footer-note">METHOD LANE<br><b>Unassigned.</b></p></div></footer></body></html>'''
(ROOT / 'site/research.html').write_text(research_page, encoding='utf-8')
print(f'Prepared {len(entries)} historical rows and {len(hypothesis_cards)} proposal cards; no file approved.')
