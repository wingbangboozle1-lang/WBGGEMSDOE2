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
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
decision = json.loads((ROOT / 'evidence/decision.json').read_text())
NAME = decision['candidate']['submission_name']
HD = decision['estimated_score']['holdout_proxy']['dti']
CI = decision['estimated_score']['holdout_proxy']['ci95']
MAXOV = decision['uniqueness']['max_real_submission_dot_overlap_3px']
MAXRHO = decision['uniqueness']['max_all_registry_abs_spearman']
# Current-decision banner injected into every per-site executive summary.
# __SITE__ / __CLAIM__ are substituted per page after the outer f-string.
CUR_BANNER = (f'''<div class="notice" style="border-left-color:#1c7a52;background:#effaf2">
<b>★ Best submission to submit today (executive summary):</b> a new, unique H1 candidate —
<a href="../../docs/downloads/{escape(NAME)}.tif">{escape(NAME)}.tif ↓</a>. Its estimated score is a labelled
HOLDOUT-DTI proxy <b>{HD:.4f}</b> (95% CI {CI[0]:.4f}–{CI[1]:.4f}), <em>not</em> a leaderboard score. It is
<b>unique</b> (≤{MAXOV:.0%} 3px dot overlap, |ρ|≤{MAXRHO:.2f} vs registry). This historical __SITE__ file is
<b>not</b> the one to submit — it is a research-only duplicate. <a href="../../docs/executive-summary.html">Full executive summary ↗</a></div>
<table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:13px"><thead><tr style="text-align:left;border-bottom:2px solid #dce2d8"><th>File to download</th><th>Estimated score</th><th>Unique?</th><th>Action</th></tr></thead><tbody>
<tr style="border-bottom:1px solid #e6ece4;background:#f3fbf5"><td><a href="../../docs/downloads/{escape(NAME)}.tif">New H1 candidate ↓</a></td><td>HOLDOUT-DTI {HD:.4f} (proxy)</td><td><b>Yes</b></td><td><b>Download &amp; submit</b></td></tr>
<tr style="border-bottom:1px solid #e6ece4"><td>This historical __SITE__ file</td><td>__CLAIM__ (USER-REPORTED claim)</td><td>No</td><td>Research only</td></tr>
</tbody></table>''')
if (card.get('ok_to_submit') is not False or card.get('verdict') != 'negative'
        or conduit.get('ok_to_submit') is not False
        or conduit.get('sha256') != card.get('conduit_parallel_session', {}).get('rejected_candidate_sha256')
        or round(conduit.get('witnesses', {}).get('13GEMSDOE', {}).get('source_threshold_ge_0_5', {}).get('fraction', 0), 6) != 0.998726
        or review.get('ok_to_submit') is not False
        or review.get('sha256') != card.get('parallel_session', {}).get('rejected_candidate_sha256')
        or review.get('format', {}).get('masked_inside') != 5132809
        or round(review.get('literal_overlap_3px', {}).get('lattice', 0), 6) != 0.993838):
    raise SystemExit('This static build is fail-closed: the archived negative review-lane card and '
                     'rejected-parallel-TIFF evidence must remain byte-consistent with the generated historical pages.')
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
(output / 'focus.json').write_text(json.dumps({'schema': 'wbggems.focus.v2',
    'generated_utc': decision['recorded_utc'],
    'note': 'One cleared NEW candidate (HOLDOUT-DTI proxy, leaderboard score unknown) plus 9 unverified '
            'historical claims; historical TIFFs are for research only.',
    'candidate': {
        'site_url': '../docs/downloads/' + NAME + '.tif',
        'file': NAME + '.tif',
        'claimed_value': f'HOLDOUT-DTI {HD:.4f}',
        'claim_evidence': f'LABELLED PROXY · 95% CI {CI[0]:.4f}-{CI[1]:.4f}',
        'leaderboard_estimate': None,
        'unique_note': f'<= {MAXOV:.0%} dot overlap, |rho| <= {MAXRHO:.2f}',
        'ok_to_submit': True,
    },
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
<main id="main" class="shell"><div class="breadcrumb"><a href="../">GEMS PRIZE</a><span class="crumb-sep">/</span><a href="../#portfolio">NINE SITES</a><span class="crumb-sep">/</span><span>{site}</span></div><section class="page-hero"><div><div class="eyebrow"><span class="eyebrow-line"></span> HISTORICAL REFERENCE · RESEARCH ONLY</div><h1>{site}<br><em>evidence brief.</em></h1><p>One pinned historical file, its reported claim, and the actual byte-level uniqueness check. No prior submission is recommended for upload again.</p></div><aside class="page-aside"><span class="signal-label">AUTOMATED DECISION</span><b>Do not submit.</b>The historical raster is not a unique new candidate; its claim is not an authenticated organizer receipt.</aside></section><div class="page-layout"><article class="prose"><h2 id="decision">Decision summary</h2><p><b>Best named historical file:</b> <code>{filename}</code>. The user/owner-reported claim is <b>{claim}</b>; it is not independently confirmed by a submission receipt. A leaderboard estimate for a new file is unavailable, and no HOLDOUT-DTI was calculated for this archived file.</p><p>In our directed test, <b>{overlap:.2f}%</b> of this file's {dots} dots lie within three pixels of {peer}, above the 70% duplicate stop. Its overlap with the registered lattice is <b>{lattice:.2f}%</b>. Original pre-placement surfaces were not independently replayed. This is sufficient to say <b>not unique under the requested rule</b>, not to prove the cause of the historical claim.</p><div class="notice"><b>Research download only.</b> The file below is an existing historical reference, not a newly generated submission. No upload name or note is assigned.</div><div class="download-row"><div><b>{filename}</b><small>SHA-256: {sha}</small></div><a href="{source}">Historical reference ↗</a></div><h2 id="method">What was checked?</h2><p>The exact file was fetched by Git blob SHA, reopened as a single-band float32 GeoTIFF, and compared against a hash-checked <em>owner mirror</em> of the grid. That grid is not authenticated against the organizer's sample, and a local format pass is not evidence of portal acceptance. Pairwise distance uses an inclusive three-pixel Euclidean radius.</p><p><a href="../data/registry_audit.json">Download the full audit JSON</a> · <a href="../research.html#lineage">Read the B2 lineage</a> · <a href="../executive.html">Submission guide</a></p></article><aside class="side-nav"><span>ON THIS PAGE</span><a href="#decision">01 · Decision</a><a href="#method">02 · Evidence</a><a href="../#portfolio">← All nine sites</a></aside></div></main><footer><div class="shell footer-inner"><div><a class="brand footer-brand" href="../"><span class="brand-mark"><span></span></span><span>GEMS <b>FIELDNOTES</b><small>RESEARCH WORKSPACE</small></span></a><p>Built for careful decisions, not leaderboard promises.</p></div><div class="footer-links"><a href="../executive.html">Submission guide</a><a href="../research.html">Research & sources</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem ↗</a><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules ↗</a></div><p class="footer-note">HISTORICAL FILE · RESEARCH ONLY<br><b>See the new cleared candidate ↗</b></p></div></footer></body></html>"""
    # Inject the current-decision executive-summary banner + table right after the
    # "Decision summary" heading of each historical site page.
    banner = CUR_BANNER.replace('__SITE__', site).replace('__CLAIM__', claim)
    html = html.replace('<h2 id="decision">Decision summary</h2>',
                        '<h2 id="decision">Decision summary</h2>' + banner)
    (pages / f"{entry['site']}.html").write_text(html)
for name in ('registry_audit.json', 'run_card.json', 'h31_preflight.json', 'parallel_review.json', 'conduit_review.json'):
    shutil.copyfile(ROOT / 'evidence' / name, output / name)
# Mirror the current byte-bound decision and H1 evidence so the fieldnotes site stays in sync.
for name in ('decision.json', 'decision_validation.json', 'h1_run_card.json', 'h1_experiments.json',
             'h1_canary.json', 'h1_uniqueness.json', 'h1_holdout.json', 'h1_format.json', 'review_passes.json'):
    shutil.copyfile(ROOT / 'evidence' / name, output / name)
print(f'Prepared {len(entries)} historical rows; current decision: {decision["decision_label"]}.')
