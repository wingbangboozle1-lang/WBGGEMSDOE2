#!/usr/bin/env python3
"""Build static, byte-audited dashboard data from committed evidence."""
from pathlib import Path
import json
import shutil
from html import escape

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'config/registry_inputs.json').read_text())
audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
card = json.loads((ROOT / 'evidence/run_card.json').read_text())
if card.get('ok_to_submit') is not False or card.get('verdict') != 'negative':
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
for name in ('registry_audit.json', 'run_card.json', 'h31_preflight.json'):
    shutil.copyfile(ROOT / 'evidence' / name, output / name)
print(f'Prepared {len(entries)} historical rows; no file approved.')
