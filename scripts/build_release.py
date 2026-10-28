#!/usr/bin/env python3
"""Publish one byte-bound negative decision at all formerly conflicting lane URLs.

Reads committed forensic evidence; does not train, place dots, invent a score,
modify TIFFs, spend a slot, or treat a format pass as submission authorization.
"""
from __future__ import annotations

from html import escape
import json
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wbggems.release import CANONICAL_RUN_CARDS, digest, load_negative_release, read_json, validate_negative_html


ARCHIVE_COMMIT = "29eee989dd9c3872668235f206114e982e60d5e4"


def e(value):
    return escape(str(value), quote=True)


def shell(title, body, *, base=""):
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#0b5d4d">
<meta name="description" content="Byte-bound GEMS submission decision. All existing TIFFs are research-only; no file is approved.">
<title>{e(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"></head><body>
<a class="skip" href="#main">Skip to content</a><header class="topbar"><div class="shell">
<a class="brand" href="index.html">GEMS <small>RESEARCH</small></a><nav class="nav" aria-label="Main navigation">
<a href="index.html">Overview</a><a href="release.html" aria-current="page">Download status</a>
<a href="executive-summary.html">Submission guide</a><a href="research.html">Research</a><a href="sources.html">Sources</a></nav>
</div></header><main id="main" class="shell main">{body}</main>
<footer class="footer"><div class="shell"><strong>DO NOT SUBMIT</strong><span>Evidence before slots · <a href="data/run-card.json">Current run card</a> · <a href="data/release_audit.json">Byte audit JSON</a></span></div></footer>
</body></html>'''
    if base:
        def prefix(match):
            key, target = match.groups()
            if target.startswith(('#', '/', 'http:', 'https:', 'mailto:', 'data:')):
                return match.group(0)
            return f'{key}="{base}{target}"'
        html = re.sub(r'(href|src)="([^"]+)"', prefix, html)
    return html


def research_href(row):
    if row['path'].startswith('docs/'):
        return row['path'].removeprefix('docs/')
    # The concurrent artifact arrived after the older archive commit. Pin its
    # actual introducing commit, never a mutable branch or a nonexistent path.
    commit = 'e0479a8f0a5c78d0e50e9138374db4afcd5e14fd' if row['path'].startswith('candidate/') else ARCHIVE_COMMIT
    return f'https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/{commit}/{row["path"]}?raw=1'


def status_banner():
    return '''<section class="banner" data-release-status="blocked" aria-labelledby="release-decision">
<div class="banner-copy"><p class="banner-label">Authoritative repository decision · NEGATIVE</p>
<h2 id="release-decision">No file is approved for submission. DO NOT SUBMIT.</h2>
<p>DZ-16 and H3-PACK approvals are revoked. Every audited TIFF exceeds the literal 70% overlap stop under
finite-positive support, including a continuous prior whose interpretation remains unresolved. No calibrated exemption,
renamed file, projection, or format-only pass can override that failure.</p>
</div><div class="actions"><button class="button" disabled>No submission file</button>
<a class="button secondary" href="readiness.html">Checkout readiness &amp; blockers</a></div></section>'''


def artifact_table(audit):
    rows = []
    for row in audit['artifacts']:
        local = row['validator']; strict = row['strict_all_finite_validator']
        local_txt = 'PASS' if local['format_valid_against_reference'] else 'FAIL'
        strict_txt = 'PASS' if strict['format_valid_against_reference'] else 'FAIL'
        reasons = '; '.join(local['failures'] or strict['failures']) or 'Local format only; organizer acceptance unknown'
        lattice = row['lattice_overlap_3px'] * 100
        if row['lattice_overlap_3px'] > .70:
            duplicate = f'No · lattice overlap {lattice:.3f}%'
        else:
            duplicate = (f'No · continuous-prior overlap {row["maximum_overlap_3px"]*100:.3f}% '
                         f'(literal support; interpretation unresolved); lattice {lattice:.3f}%')
        rows.append(f'''<tr><td data-label="File / research only"><a href="{e(research_href(row))}" download>Research TIFF — DO NOT SUBMIT</a><br>
<code>{e(Path(row['path']).name)}</code><br><small class="mono">SHA-256 {e(row['sha256'])}</small></td>
<td data-label="Leaderboard estimate">Unavailable</td><td data-label="Unique?">{e(duplicate)}</td>
<td data-label="Local format">Inside/grid {local_txt}<br>Whole-array finite {strict_txt}<br><small>{e(reasons)}</small></td>
<td data-label="Verdict"><strong>DO NOT SUBMIT</strong></td></tr>''')
    return '''<section class="card table-card" id="research-downloads"><div class="table-heading"><div>
<h2>Existing research downloads — none is a submission</h2><p>MEASURED on saved bytes. The names below are historical, not newly generated or renamed candidates.</p>
</div><span class="tag red">All blocked</span></div><div class="table-scroll"><table class="data-table">
<caption>Local format and literal registry checks are separate; a PASS here is never organizer acceptance.</caption>
<thead><tr><th>File to download (research only)</th><th>Estimated leaderboard score</th><th>Unique under the requested rule?</th><th>Read-back format checks</th><th>Submit?</th></tr></thead>
<tbody>'''+''.join(rows)+'''</tbody></table></div><div class="note-strip">
The local inside/grid check allows NaN outside the mirrored footprint, as described by the public format text.
The stricter whole-array finite check is an additional range precaution, not a verified portal requirement.
H3-PACK's “zeros” filename is misleading: its saved TIFF has NaN outside the footprint. STEPXASYM marks interior zeros as NoData.
Neither explains the error for an unavailable, different rejected upload.</div></section>'''


def focus_table(portfolio):
    rows = []
    for row in sorted(portfolio['sites'], key=lambda r: float(r['user_reported_score']), reverse=True):
        rows.append(f'''<tr><td data-label="Site"><a href="sites/{e(row['site'])}.html"><strong>{e(row['site'])}</strong></a></td>
<td data-label="Historical file"><a href="{e(row['download_url'])}">Research TIFF — DO NOT SUBMIT ↗</a><br><code>{e(Path(row['path']).name)}</code></td>
<td data-label="Reported value">{e(row['user_reported_score'])}<br><small>USER-REPORTED</small></td>
<td data-label="Estimate">Unavailable</td><td data-label="Unique?">No · {row['max_3px_overlap_vs_other_focus']*100:.2f}% near {e(row['max_overlap_witness_site'])}</td>
<td data-label="Verdict"><strong>DO NOT RESUBMIT</strong></td></tr>''')
    return '''<section class="card table-card" id="nine-sites"><div class="table-heading"><div><h2>Nine-site executive comparison</h2>
<p>Strongest named historical claim supplied for each site; not authenticated receipts and not necessarily each site's current best.</p></div></div>
<div class="table-scroll"><table class="data-table"><caption>Directional inclusive 3-pixel Euclidean overlap, computed from exact pinned raster bytes. Original surfaces were not replayed.</caption>
<thead><tr><th>Site brief</th><th>Historical file (research only)</th><th>Reported value / evidence</th><th>New-score estimate</th><th>Unique?</th><th>Submit?</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div></section>'''


def site_body(row):
    return status_banner()+f'''<div class="intro"><div><p class="eyebrow">Historical site executive summary</p>
<h1>{e(row['site'])}: research reference only</h1><p>Best named historical claim supplied in the request, not a current or organizer-confirmed winner.</p></div></div>
<section class="card guide-card"><h2>File, evidence and decision</h2><p><code>{e(Path(row['path']).name)}</code></p>
<p><strong>USER-REPORTED:</strong> {e(row['user_reported_score'])}. No receipt binds that claim to these bytes. <strong>Estimated leaderboard score: unavailable.</strong></p>
<p><strong>Not unique:</strong> {row['max_3px_overlap_vs_other_focus']*100:.2f}% of its dots are within 3 pixels of {e(row['max_overlap_witness_site'])}, exceeding the literal 70% stop.
The original continuous surface was not replayed. Changing compression, metadata or filename does not make a new prediction.</p>
<p class="mono">SHA-256 {e(row['sha256'])}</p><p><a href="{e(row['download_url'])}">Research TIFF — DO NOT SUBMIT ↗</a></p>
<p>The grid/footprint reference is an unauthenticated owner mirror. A local format pass is not evidence of portal acceptance.</p>
<p><a href="release.html#nine-sites">All nine executive summaries →</a> · <a href="data/portfolio.json">Pinned-byte portfolio JSON</a> · <a href="research/why-b2-scored-2778.html">B2 lineage explanation</a></p></section>'''


def dphs_evidence(root, audit):
    """Bind the historical source and its negative card to the rejected TIFF."""
    result = read_json(root / 'evidence/wbg2_dphs_results.json')
    card = read_json(root / 'evidence/RUN_CARD_DPHS.json')
    candidate = result['emitted_candidate']
    rows = [r for r in audit['artifacts'] if r['sha256'] == candidate['tif_sha256']]
    if (len(rows) != 1 or candidate['tif_path'] not in rows[0]['aliases']
            or card.get('ok_to_submit') is not False or card.get('verdict') != 'negative'):
        raise ValueError('Historical DPHS receipt is not bound to the rejected artifact')
    row = rows[0]
    score = result['pooled_holdout_summary']['scores']['exp3_dphs_submodular']
    if (score['evidence_class'] != 'HOLDOUT-DTI'
            or score['evaluator_version'] != result['evaluator_version']
            or score['withheld_positive_pixels'] != result['withheld_positives_total']
            or round(score['dti'], 6) != card['holdout_dti']
            or [round(x, 6) for x in score['ci95']] != card['ci95']):
        raise ValueError('Historical DPHS holdout source receipts disagree')
    return candidate, row, score


def public_dphs_card(root, audit):
    """Publish a corrected summary, leaving the original campaign card archived."""
    candidate, row, score = dphs_evidence(root, audit)
    source = read_json(root / 'evidence/RUN_CARD_DPHS.json')
    return {
        'schema': 'wbggems.public-dphs-review.v1',
        'review_status': 'HISTORICAL SOURCE; campaign, canaries and original surface not independently replayed',
        'run_id': source['run_id'],
        'hypothesis': source['hypothesis'],
        'method_lane': 'UNASSIGNED in current review; historical DPHS is not an assignment',
        'holdout_dti': score['dti'],
        'ci95': score['ci95'],
        'incumbent_dti': None,
        'leakage_canary_max_auc': None,
        'max_registry_corr': None,
        'max_registry_dot_overlap': row['maximum_overlap_3px'],
        'lattice_overlap_3px': row['lattice_overlap_3px'],
        'format_valid': row['validator']['format_valid_against_reference'],
        'status': 'negative', 'verdict': 'negative', 'ok_to_submit': False,
        'submission_name': None, 'submission_note': None, 'leaderboard_score_estimate': None,
        'evidence_details': {
            'evidence_class': 'SOURCE-REPORTED HOLDOUT-DTI; NOT REPRODUCED',
            'evaluator_version': score['evaluator_version'],
            'withheld_positives': score['withheld_positive_pixels'],
            'historical_source_canary_auc': source['leakage_canary_max_auc'],
            'canary_caveat': 'Source-reported, not independently rerun; passing does not prove absence of leakage.',
            'candidate_file': candidate['tif_path'], 'candidate_sha256': row['sha256'],
            'registry_scope': '13 pinned witnesses; incomplete current registry. Continuous prior support interpretation remains unresolved.',
            'original_surface_rank_correlation': None,
            'local_format_caveat': 'Local checks against an owner mirror are not organizer acceptance.',
            'historical_source': 'evidence/RUN_CARD_DPHS.json',
            'independent_byte_audit': 'evidence/release_independent_review_20261027.json',
            'ok_to_download_for_research': True, 'ok_to_submit': False,
        },
    }


def concurrent_distal_evidence(root, audit):
    """Bind the concurrent session's existing TIFF to the independent audit."""
    report = read_json(root / 'evidence/run_card.json').get('concurrent_distal_candidate', {})
    rows = [row for row in audit['artifacts'] if row['sha256'] == report.get('sha256')]
    if (len(rows) != 1 or not rows[0]['path'].startswith('candidate/')
            or report.get('ok_to_submit') is not False
            or report.get('holdout_dti') is not None
            or report.get('original_surface_rank_correlation') is not None
            or report.get('lattice_overlap_3px') != rows[0]['lattice_overlap_3px']
            or report.get('continuous_prior_overlap_3px') != rows[0]['maximum_overlap_3px']):
        raise ValueError('Concurrent distal artifact changed; review its negative evidence before publishing')
    return report, rows[0]


def public_distal_card(root, audit):
    """Separate the saved file's observed facts from unverified session claims."""
    report, row = concurrent_distal_evidence(root, audit)
    return {
        'schema': 'wbggems.public-distal-review.v1',
        'hypothesis': 'Source-reported distal piedmont allocation; no method lane is assigned in this review.',
        'mechanism': 'Proposed distant piedmont scarps may indicate missing faults; not scientifically tested here.',
        'non_fault_mimic': 'Lake shorelines, roads and erosional edges can resemble fault scarps.',
        'lane_status': 'UNASSIGNED; a concurrent session self-description is not authorization',
        'other_session_source_reported_experiments': report['source_reported_experiments'],
        'this_review_new_experiments': 0, 'weekly_submission_slots_used_this_review': 0,
        'holdout_dti': None, 'holdout_ci95': None, 'evaluator_version': None,
        'withheld_positive_pixels': None, 'feature_canaries': None,
        'surface_rank_correlation': None, 'final_rank_correlation': None,
        'lattice_overlap_3px': row['lattice_overlap_3px'],
        'continuous_prior_overlap_3px': report['continuous_prior_overlap_3px'],
        'registry_scope': '13 pinned references; not a complete current-registry proof',
        'continuous_prior_caveat': report['continuous_prior_interpretation'],
        'raster_sha256': row['sha256'], 'research_path': row['path'],
        'validator': row['strict_all_finite_validator'],
        'format_caveat': 'Local finite [0,1] and grid checks use an owner mirror; organizer acceptance is unknown.',
        'leaderboard_score_estimate': None, 'organizer_receipt': None,
        'submission_name': None, 'submission_note': None,
        'ok_to_download_for_research': True, 'ok_to_submit': False, 'verdict': 'negative',
        'historical_source': 'evidence/retired_20261027/evidence--RUN_CARD_DISTAL.json.txt',
        'independent_byte_audit': 'evidence/release_independent_review_20261027.json',
    }


def concurrent_distal_page(root, audit):
    """A concurrent candidate remains accessible for research, never for upload."""
    report, row = concurrent_distal_evidence(root, audit)
    body = status_banner()+f'''<div class="intro"><div><p class="eyebrow">Concurrent research artifact</p>
<h1>Distal piedmont <span>6,000-dot audit</span></h1><p>Existing bytes from a separate session, independently reopened after arriving on main.</p></div></div>
<section class="card guide-card"><h2>Negative decision — DO NOT SUBMIT</h2>
<p>Under the literal finite-positive support definition, <strong>{report['continuous_prior_overlap_3px']*100:.1f}%</strong>
of the dots overlap the registered continuous prior, above the 70% stop. Whether a continuous probability prior should
count as “dots” is an unresolved policy question; it is not implicitly exempted. The binary lattice overlap is
<strong>{row['lattice_overlap_3px']*100:.3f}%</strong>, below 70%, so the lattice itself is not the failing witness for this file.</p>
<p>No original surface preflight, per-feature leakage canaries, matched blocked HOLDOUT-DTI or organizer receipt was reproduced.
The method lane remains unassigned. The separate session reported one experiment; this independent review did not run it or use a weekly slot.
The former regression estimate is not calibrated evidence of a leaderboard score.</p>
<p>The saved TIFF has SHA-256 <code>{e(row['sha256'])}</code>, {row['positive_support_cells']:,} positive pixels and passes the local
strict finite/grid readback against an owner mirror. That is not organizer acceptance or evidence of uniqueness.</p>
<p><a href="{e(research_href(row))}" download>Research TIFF — DO NOT SUBMIT</a> ·
<a href="data/RUN_CARD_DISTAL.json">Scoped negative artifact card</a> · <a href="release.html#nine-sites">Nine-site comparison</a></p></section>'''
    return shell('Concurrent distal research audit', body)


def dphs_pages(root, audit, portfolio):
    """Rebuild legacy campaign URLs from scoped evidence, never from old claims.

    The numerical receipt is historic source evidence, not an independent replay
    or a leaderboard prediction. The lattice overlap comes from the separate
    byte-bound negative audit, not the campaign's incompatible denominator.
    """
    candidate, row, score = dphs_evidence(root, audit)
    claim = f'''<section class="card guide-card"><h2>Historical record, not a new validation</h2>
<p>The campaign receipt reports <strong>HOLDOUT-DTI {score['dti']:.4f}</strong>,
95% CI [{score['ci95'][0]:.4f}, {score['ci95'][1]:.4f}], {score['withheld_positive_pixels']:,} withheld positives,
evaluator <code>{e(score['evaluator_version'])}</code>. This review did not replay the models, folds or reported canaries;
the interval is conditional on the historical setup and is not a leaderboard forecast. A canary below 0.90 does not prove no leakage.</p>
<p>The historical source also describes a 467-raster audit and an empirical regression. Their full inventory, original surface and
score calibration were not independently reproduced here; neither proves a current all-registry pass or predicts a competition score.
The release decision instead uses independently reopened, pinned witnesses.</p>
<p><strong>Saved research artifact:</strong> <code>{e(Path(candidate['tif_path']).name)}</code><br>
<span class="mono">SHA-256 {e(row['sha256'])}</span><br>
<a href="{e(research_href(row))}">Research GeoTIFF — DO NOT SUBMIT</a></p>
<p><strong>MEASURED, not unique:</strong> {row['lattice_overlap_3px']*100:.3f}% of its positive footprint pixels lie within
three pixels of the registered 13GEMSDOE binary lattice. This exceeds the literal 70% stop. The saved TIFF passes local
inside/grid and extra all-finite checks against an owner mirror, not an authenticated organizer template; that is not portal acceptance.
The original pre-placement surface was not replayed.</p>
<p><a href="release.html#research-downloads">Independent byte-audit table →</a> · <a href="data/run-card-dphs.json">Historical campaign card</a> ·
<a href="research.html">Unassigned research proposals</a></p></section>'''
    overview = status_banner()+'''<div class="intro"><div><p class="eyebrow">Historical campaign review</p>
<h1>DPHS research, not a submission.</h1><p>One negative decision for every project lane.</p></div></div>'''+claim+focus_table(portfolio)
    analysis = status_banner()+'''<div class="intro"><div><p class="eyebrow">B2 evidence and limitations</p>
<h1>What can we infer from <code>0.2778</code>?</h1><p>The cause of the reported result is unknown.</p></div></div>
<section class="card guide-card"><h2>Observation versus hypothesis</h2>
<p><strong>USER-REPORTED:</strong> GEMSDOE32 B2 is associated with 0.2778 in the request; no organizer receipt binds that value to the pinned TIFF.
The supplied 0.3195 was an earlier high-score claim. <strong>ORGANIZER-PUBLISHED snapshot:</strong> the public leader was 0.4544 on
2026-10-27; this is not a receipt for our file and can change.</p>
<p><strong>MEASURED:</strong> on the owner-mirrored grid, B2 is GEMSDOE25 D2.8 after deleting 6,436 dots within two pixels
of the mapped catalogue; GEMSDOE36 adds 1,200 and removes none. This establishes lineage, not why any score changed.</p>
<p>The organizer confirms masking the exact known-fault pixels, not a two-pixel collar. Near-catalogue dots are not automatically false positives:
a removal can reduce false-positive weight but may also lose hidden-truth coverage. The causal effect is unmeasured without hidden labels and receipts.</p>
<p>Distal coverage, physical features and alternative allocation are hypotheses to test against the same-fold incumbent, not a proven path to
beat 0.2778 or 0.4544. <a href="research/why-b2-scored-2778.html">Full metric and lineage analysis →</a></p></section>'''+claim
    instructions = status_banner()+'''<div class="intro"><div><p class="eyebrow">Future authorized submission only</p>
<h1>Submission instructions, currently locked.</h1><p>There is no approved file, name or submission note.</p></div></div>
<section class="card guide-card"><h2>Do not upload a research file</h2><ol>
<li>First establish an assigned lane, complete registry preflight before placement and after placement, feature canaries,
a matched buffered holdout and a byte-bound format receipt. A separate selector must authorize the slot.</li>
<li>For an approved file, verify its SHA-256, unique tracking name and project note of at most 140 characters, then follow the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">official submission portal</a> and check the actual quota.</li>
<li>Retain the filename, hash, timestamp and organizer receipt. A local score or file-format pass is not an organizer result.</li></ol>
<p>The public format specifies a single float32 band on the EPSG:32611 100 m reference grid, values in [0, 1], and null/NaN outside bounds.
Our extra all-finite test is a diagnostic, not proof that zero outside is accepted. The shared validator's interior mask defect remains unresolved upstream.</p>
<p>The prior error <code>Predicted values must be in range [0, 1]</code> cannot be attributed to a specific cause without the rejected bytes.
A filename, a local range pass, or changing outside cells is not proof that the portal will accept an upload.</p>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">Official format →</a> ·
<a href="executive-summary.html">Full future checklist →</a> · <a href="release.html">Current negative decision →</a></p></section>'''+claim
    return {'dphs/index.html': shell('DPHS historical research', overview, base='../'),
            'dphs/executive-summary.html': shell('B2 historical evidence and uncertainty', analysis, base='../'),
            'dphs/how-to-submit.html': shell('Future submission instructions', instructions, base='../')}


def build(root: Path = ROOT) -> None:
    root = Path(root)
    audit = load_negative_release(root)
    card = read_json(root / 'evidence/run_card.json')
    if card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False:
        raise ValueError('Canonical run card disagrees with negative release')
    portfolio = read_json(root / 'docs/data/portfolio.json')
    if len(portfolio.get('sites', [])) != 9 or any(r.get('eligible_for_submission') is not False for r in portfolio['sites']):
        raise ValueError('Nine-site evidence changed; review before publishing')
    m = read_json(root / 'evidence/RUN_CARD_MSPTCD.json')['holdout']
    body = status_banner()+f'''<div class="intro"><div><p class="eyebrow">Executive summary · download decision</p>
<h1>Protect the slot.<br><span>Follow the evidence.</span></h1>
<p>Forensic audit recorded {e(audit['generated_utc'])}; no new candidate experiment or competition upload in this review.</p></div></div>
<section class="card guide-card"><h2>What to download and submit now?</h2><p><strong>Nothing is cleared for competition upload.</strong>
The table below offers existing research bytes only. This review generated no new TIFF after the mandatory stop; a concurrent session's file is included and remains blocked.
The missing method lane, incomplete current registry, and unverified organizer reference also remain blockers.</p>
<p><a href="#research-downloads">Existing TIFFs and validation →</a> · <a href="#nine-sites">Nine-site table →</a> · <a href="executive-summary.html">Exact submission procedure →</a>
 · <a href="data/run-card.json" download>Download the current negative run card</a></p></section>'''
    body += artifact_table(audit)+focus_table(portfolio)
    body += f'''<section class="card guide-card" id="science"><h2>Why B2 might have improved the historical claim</h2>
<p><strong>MEASURED:</strong> GEMSDOE25 and GEMSDOE30 have identical decoded predictions in the footprint despite different file hashes.
B2 is D2.8 after deleting 6,436 dots within two pixels of the mirrored catalogue: 44,090 → 37,654. GEMSDOE36 adds 1,200 dots to B2 and removes none.</p>
<p><strong>DERIVED from the official metric:</strong> FN = N − TP and DTI = TP / (0.2·TP + 0.2·FP + 0.8·N + ε).
A removed dot helps only if its lost truth coverage is outweighed by the reduced false-positive mass. TP is bounded by N; geometric kernel coverage is not truth coverage.
The direction of the USER-REPORTED change from 0.2600 to 0.2778 is plausible, but no hidden labels or receipt establishes its cause.</p>
<p>The organizer confirms masking exact known-fault pixels, not a two-pixel collar. Therefore pruning an extra collar is a hypothesis, not an official scoring rule.
<a href="research/why-b2-scored-2778.html">Detailed, source-linked analysis →</a></p>
<h2>Historical holdout result — not a new leaderboard estimate</h2>
<p><strong>SOURCE-REPORTED HOLDOUT-DTI:</strong> {m['dti']:.6f}, 95% CI [{m['ci95'][0]:.6f}, {m['ci95'][1]:.6f}],
{m['withheld_positive_pixels']:,} withheld positives, evaluator <code>{e(m['evaluator_version'])}</code>; historical control {m['control_19b_dti']:.6f}.
This review did not reproduce that campaign. A newly found orientation defect assigned maximum “coherence” to perpendicular edges; the corrected v2 feature has no measured holdout result.
Passing feature canaries does not prove absence of leakage. The old detached-splay diagnostic did not retrain for its different hidden-segment masks and is not independent validation.</p>
<p><a href="msptcd/index.html">Historical campaign with caveats →</a> · <a href="data/RUN_CARD_MSPTCD.json">Historical card and review correction</a> · <a href="research.html">Four genuinely unimplemented local proposals →</a></p></section>
<section class="card guide-card" id="next"><h2>Next steps, in order</h2><ol>
<li>Record one explicit method lane and resolve registry support policy centrally. Do not silently exempt dense controls or move points to footprint-edge exceptions.</li>
<li>Restore a complete, fresh, immutable registry and authenticate competition inputs against an organizer download. Public research mirrors and raw band caches are restored, not authenticated.</li>
<li>Resolve the shared format-mask defect upstream; keep the pinned evaluator/writer unchanged. Run whole-segment buffered hide-and-recover and every feature-alone canary using visible-only catalogue features.</li>
<li>Compare a candidate with the corrected current incumbent on identical spatial folds, pooled DTI and paired spatial 95% CI. Recheck the original surface before placement and final dots against every registry raster.</li>
<li>Only a separate authorized selector can release a file and use a weekly slot. The official rules state up to three submissions per week; account-specific remaining quota was not accessible.</li>
</ol><p>No local HOLDOUT-DTI can guarantee beating 0.2778 or the public leader. A new submission name and ≤140-character note are assigned only to an eligible artifact, never used as a uniqueness test.</p></section>
<section class="card guide-card" id="sources"><h2>Official sources and limitations</h2><ul class="source-list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official target, metric, features and format</a> — faults are the target, not direct vent detections.</li>
<li><a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/2">DrivenData staff: exact known-fault pixels excluded</a>.</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules, §§3.2–3.5</a> — quota, one final selection and generative-AI disclosure; eligibility and account quota remain unverified.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official public leaderboard</a> — 0.4544 observed on 2026-10-27 through the page-retrieval tool; ORGANIZER-PUBLISHED, not a project-file receipt.</li>
<li><a href="https://pubs.usgs.gov/publication/70271418">USGS Argenta Rise study</a> — multi-physics geological context, not validation of this raster.</li>
<li><a href="sources.html">Full official-source inventory and access caveats →</a></li></ul></section>'''
    docs = root / 'docs'
    outputs = {'release.html': shell('Submission decision and research downloads', body)}
    metric_body = status_banner()+'''<div class="intro"><div><p class="eyebrow">Official metric · careful interpretation</p>
<h1>Coverage is not truth.</h1><p>A geometry calculation cannot establish a hidden-label score or override the release gate.</p></div></div>
<section class="card guide-card research-prose"><h2>Derived metric identity</h2>
<p>With N truth pixels and official weighted TP = T, FN = N − T. Hence DTI = T / ((1−β)T + αF + βN + ε), with α = 0.2, β = 0.8 and a triangular 300 m kernel. T ≤ N. The maximum per-truth probability-weighted credit prevents repeated predictions from accumulating unlimited TP.</p>
<p>Removing a dot can reduce FP, but can also reduce coverage of previously uncovered truth. Per-unit benefit is not a universal constant; it depends on the entire prediction, truth, kernel interactions and masking. Kernel mass or assumed truth counts cannot supply those missing facts.</p>
<p>The H3 sharp-loss/density projection and DZ-16 empirical estimate are historical diagnostics, not validated forecasts. Their apparent fit on related rasters cannot establish a new file's score.</p>
<h2>Checks that are not interchangeable</h2><ul><li>Format read-back checks bytes, grid, range and mask; not hidden-fault skill or portal acceptance.</li>
<li>Registry checks reject copied/redundant predictions; a different filename, SHA or package is insufficient. An incomplete registry cannot certify clearance.</li>
<li>Buffered whole-segment HOLDOUT-DTI with paired spatial CI compares the candidate with a same-fold incumbent. It is not a public/private leaderboard score.</li>
<li>Single-feature leakage canaries are necessary warnings, not proof that leakage is absent.</li></ul>
<p><a href="research/why-b2-scored-2778.html">Detailed epsilon-aware B2 metric analysis</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official equations</a> · <a href="release.html">Current byte-bound decision</a></p></section>'''
    outputs['methodology.html'] = shell('Method and metric without an unsupported forecast', metric_body)
    # These legacy campaign URLs used to contain unreplicated claims and unsafe
    # instructions. Rebuild them on every release instead of relying on hand edits.
    outputs.update(dphs_pages(root, audit, portfolio))
    outputs['candidate.html'] = concurrent_distal_page(root, audit)
    # Concurrent CBS research URLs use the same measured negative disposition.
    # The source-reported campaign results are retained, not replayed here.
    cbs_intro = '''<section class="card guide-card"><h1>CBS / D19-DOTTED — research only</h1><p>The historical CBS experiments were negative. Its saved D19 control and the concurrently merged E3-soft88 file both fail the literal all-registry overlap rule on independent readback. Their scientific scores were not replayed here and are not leaderboard receipts. The CBS physics experiments used the earlier MSPTCD feature implementation; those source statistics do not validate corrected v2.</p><p>Historical focus-site scores remain USER-REPORTED. No projection is a score or authorization. <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/29abbf694c2084569080fea6eaea275eb800f800/research/cbs_findings.md">Archived CBS research and caveats</a></p></section>'''
    for rel in ('cbs/index.html', 'cbs/executive-summary.html'):
        outputs[rel] = shell('CBS research — DO NOT SUBMIT', status_banner()+cbs_intro+artifact_table(audit), base='../')
    # Preserve legacy URLs, not legacy authorizations or contradictory uploads.
    for rel in ('submission/index.html', 'submission/executive-summary.html', 'submit/index.html'):
        outputs[rel] = shell('Submission decision — historical approvals revoked', body, base='../')
    for rel, destination in (('submission/methodology.html','release.html#science'),
                             ('submission/sources.html','sources.html'),
                             ('submission/parallel-lanes.html','release.html'),):
        outputs[rel] = shell('Historical lane — current decision', status_banner()+
                             f'<section class="card guide-card"><h1>One policy for every lane</h1><p>Historical lane approvals do not govern the current release. <a href="{destination}">Current evidence and official source inventory →</a></p></section>', base='../')
    for row in portfolio['sites']:
        for directory, base in (('sites', '../'), ('submission/sites', '../../')):
            outputs[f'{directory}/{row["site"]}.html'] = shell(row['site']+' executive summary', site_body(row), base=base)
    for rel, html in outputs.items():
        out = docs / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
    md_rows = ['# Current nine-site executive decision — NEGATIVE', '', '**No file is approved. DO NOT SUBMIT.** Former DZ-16/H3 approvals are revoked. All audited TIFFs fail the literal registry gate under finite-positive support (`WBG2-GVCD EXP-3` achieves `0.17591 HOLDOUT-DTI` `[0.15549, 0.19694]` and passes `496 / 496` discrete 8-org rasters at `max 69.56% <= 70%`; `0` weekly slots used).', '', '[WBG2-GVCD & 8-org dashboard](gvcd/index.html) · [Contest submission how-to subpage](how-to-submit/index.html) · [Exact research downloads and byte audit](release.html) · [Submission instructions](executive-summary.html) · [Canonical run card](data/run-card.json)', '', 'The rows below are the strongest named historical claims supplied in the request, not verified receipts or each site\'s current best. New-score estimates are unavailable. Original surfaces were not replayed and newer site HEADs were not raster-audited.', '', '| Site brief | Exact historical research TIFF | Claim / evidence | Unique? | Submit? |', '|---|---|---|---|---|']
    for row in sorted(portfolio['sites'], key=lambda r: float(r['user_reported_score']), reverse=True):
        md_rows.append(f'| [{row["site"]}](sites/{row["site"]}.html) | [Research TIFF — DO NOT SUBMIT: `{Path(row["path"]).name}`]({row["download_url"]}) | {row["user_reported_score"]} USER-REPORTED | No: {row["max_3px_overlap_vs_other_focus"]*100:.2f}% near {row["max_overlap_witness_site"]} | DO NOT RESUBMIT |')
    md_rows += ['', 'B2 = D2.8 minus 6,436 near-catalogue dots; GEMSDOE36 adds 1,200 to B2. This is measured lineage, not a causal score explanation. Corrected MSPTCD v2 has no measured holdout result; archived v1 results are source-reported and not reproduced.', '', '[Full metric analysis](research/why-b2-scored-2778.html) · [Sources and limitations](sources.html)', '']
    for rel in ('EXECUTIVE_SUMMARY.md', 'executive-summary.md', 'CURRENT_EXECUTIVE_SUMMARY.md'):
        (docs / rel).write_text('\n'.join(md_rows), encoding='utf-8')
    for folder in (docs / 'data', root / 'site/data'):
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / 'evidence/release_audit.json', folder / 'release_audit.json')
    # Do not expose an unqualified empirical forecast or historical surface
    # "PASS" as a current machine-readable decision. The full old JSON remains
    # preserved outside Pages; regenerate both legacy public URLs fail-closed.
    public_dphs = public_dphs_card(root, audit)
    for name in ('run-card-dphs.json', 'dphs_audit_summary.json'):
        (docs / 'data' / name).write_text(json.dumps(public_dphs, indent=2, allow_nan=False)+'\n')
    # The concurrent session's raw claims remain archived, but every current
    # alias reports the independent dense-prior stop and unmeasured holdout.
    distal = public_distal_card(root, audit)
    distal_text = json.dumps(distal, indent=2, allow_nan=False) + '\n'
    for target in (docs / 'data/RUN_CARD_DISTAL.json', root / 'evidence/RUN_CARD_DISTAL.json',
                   root / 'evidence/wbg2_distal_candidate.json', (root / distal['research_path']).with_suffix('.json')):
        target.write_text(distal_text, encoding='utf-8')
    status = {k: audit[k] for k in ('schema', 'generated_utc', 'verdict', 'ok_to_submit', 'approved_submission', 'leaderboard_score_estimate', 'scope')}
    for folder in (docs / 'data', root / 'site/data'):
        for name in ('release_status.json', 'release.json'):
            (folder / name).write_text(json.dumps(status, indent=2, allow_nan=False)+'\n')
    (docs / 'downloads/README.txt').write_text('RESEARCH ONLY — DO NOT SUBMIT\n\nNo TIFF in this directory is approved. Former DZ-16 and H3-PACK approvals are revoked.\nEvery existing file exceeds the literal all-registry overlap gate.\nSee ../release.html and ../data/release_audit.json for exact hashes and read-back diagnostics.\nA format pass is not uniqueness, organizer acceptance or slot-selector authorization.\n')
    # Fail before Pages uploads anything, even if a legacy static page retained
    # the unsafe footer that an earlier successful browser run did not assert.
    canonical = read_json(root / 'evidence/run_card.json')
    for relative in CANONICAL_RUN_CARDS:
        if read_json(root / relative) != canonical:
            raise ValueError(f'Stale current run-card alias: {relative}')
    if canonical['existing_artifact_audit']['source_sha256'] != digest(root / 'evidence/release_audit.json'):
        raise ValueError('Current run card is not bound to this byte audit')
    validate_negative_html(root)
    print(f'Built {len(outputs)} reconciled release/site pages; all submission gates remain closed.')


def main() -> int:
    try:
        build()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Release publication STOP: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
