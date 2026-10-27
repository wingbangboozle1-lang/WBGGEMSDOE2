#!/usr/bin/env python3
"""Publish consistent negative release decisions from hash-bound review evidence.

Only renders rejected historical candidates. Promotion requires a new reviewed
release path, not changing a boolean in a JSON file or relaxing a duplicate gate.
"""
from hashlib import sha256
from html import escape as e
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def load(rel):
    return json.loads((ROOT / rel).read_text())


def check_evidence(report):
    if report.get('ok_to_submit') is not False or len(report['candidates']) != 2:
        raise ValueError('Only audited negative release decisions can be published')
    for row in report['candidates']:
        if (row.get('ok_to_submit') is not False or row.get('verdict') != 'negative'
                or row.get('literal_duplicate_stop') is not True
                or row['final_dot_overlap_3px']['13GEMSDOE'] <= .70):
            raise ValueError('Release decision contradicts literal duplicate stop')
        if sha256((ROOT / row['file']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Candidate bytes changed; re-audit before publication')
    for rel in ('data_public/final_audit.json', 'data_public/run_card.json', 'evidence/RUN_CARD_H3.json'):
        record = load(rel)
        if record.get('ok_to_submit') is not False or record.get('verdict') != 'negative':
            raise ValueError(f'Conflicting approval: {rel}')


def main():
    report = load('evidence/release_recheck_20261027.json')
    check_evidence(report)
    registry = load('evidence/registry_recheck_20261027.json')
    inputs = load('config/registry_inputs.json')['inputs'][:9]
    for name in ('release_recheck_20261027.json', 'registry_recheck_20261027.json'):
        shutil.copyfile(ROOT / 'evidence' / name, DOCS / 'data' / name)
    for a, b in [('evidence/RUN_CARD_H3.json', 'RUN_CARD_H3.json'),
                 ('data_public/run_card.json', 'run-card-current.json')]:
        shutil.copyfile(ROOT / a, DOCS / 'data' / b)

    def page(title, body, base=''):
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · GEMS release review</title><link rel="stylesheet" href="{base}styles.css"></head><body><div class="wrap"><nav aria-label="Main navigation"><a href="{base}../index.html">Research dashboard</a><a href="{base}index.html">Release decision</a><a href="{base}executive-summary.html">Executive summary</a><a href="{base}sources.html">Official sources</a></nav><main><h1>{e(title)}</h1><div class="card verdict bad"><strong>NO FILE CLEARED — DO NOT SUBMIT</strong><p>No file is approved for submission. No submission file is available for a real slot.</p><p>Format validity, uniqueness, scientific validation and slot selection are separate gates. Existing TIFFs are research artifacts, not approved competition submissions.</p></div>{body}</main><footer>Rechecked {e(report['generated_utc'])}. No experiment or slot used. Historical claims are not organizer receipts. <a href="{base}../data/release_recheck_20261027.json">Download machine-readable review</a>.</footer></div></body></html>'''

    findings = {
        'GEMSDOE24': 'Historical dense dotted-ridge reference. Its positive support fails a focus-peer comparison and the registered lattice gate.',
        'GEMSDOE25': 'Its in-footprint mask is identical to GEMSDOE30, despite different filenames and encoding. Not a new prediction.',
        'GEMSDOE27': 'Historical topo-gap file; fails the literal registry gate. Later H31 is a different file and cannot inherit this claimed result.',
        'GEMSDOE28': 'Rung30 has the highest user-reported historical claim supplied for this site. Later experiments do not prove a higher result.',
        'GEMSDOE30': 'Its in-footprint mask is identical to GEMSDOE25. Byte-level packaging changes are not scientific novelty.',
        'GEMSDOE31': 'Historical solo-D28 file; overlaps the shared family. Its claim is not evidence for a new file.',
        'GEMSDOE32': 'Highest user-reported claim among these nine. Exactly D2.8 with all dots within two pixels of the mirrored catalogue removed.',
        'GEMSDOE33': 'Historical analog-tip/stepover file; fails focus-peer and lattice gates. Its name does not establish its physical mechanism.',
        'GEMSDOE36': 'Its binary support adds 1,200 dots to B2 and removes none. This is a measured lineage relation, not independent evidence for PINN physics.',
    }
    rows = []
    for item in sorted(inputs, key=lambda x: -x['user_reported_claim']):
        ident = item['id']; measurement = registry['items'][ident]
        filename = Path(item['path']).name
        if measurement['sha256'] != item['sha256'] or not measurement['literal_lattice_duplicate']:
            raise ValueError('Focus evidence changed; re-review site narrative')
        rows.append(f'''<tr><td><a href="sites/{e(ident)}.html">{e(ident)}</a></td><td><a href="{e(item['url'])}">{e(filename)}</a><br>Historical research only</td><td>{item['user_reported_claim']:.4f}<br>USER-REPORTED</td><td>Unavailable</td><td>No — literal overlap failure</td><td>DO NOT SUBMIT</td></tr>''')
        body = f'''<p>{e(findings[ident])}</p><h2>Historical file, not a recommendation</h2><p><a href="{e(item['url'])}">{e(filename)}</a> — research download only.</p><p>USER-REPORTED historical claim: <strong>{item['user_reported_claim']:.4f}</strong>. No organizer receipt. No defensible leaderboard estimate. HOLDOUT-DTI: not measured here; evaluator, withheld positives and CI are unavailable.</p><p class="mono">SHA-256 {e(item['sha256'])}</p><h2>REGISTRY-MEASUREMENT</h2><p>{measurement['dots']:,} dots; {measurement['fraction_within_3px_of_lattice']:.2%} within three pixels of the registered binary lattice. Limit: 70%. Unique under the required rule: <strong>NO</strong>. Original pre-placement surface not available.</p><p>Local format pass against the unauthenticated owner mirror: {measurement['format_valid_against_mirror']}. This does not establish portal acceptance.</p><p>All nine repository heads have changed since the prior audited pins. These are exact historical bytes, not a claim about the latest site's best file. <a href="../../data/focus-freshness.json">Freshness record</a>.</p>'''
        dest = DOCS / 'submission/sites' / f'{ident}.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page(f'{ident} executive review', body, '../'))

    table = '<div style="overflow-x:auto"><table><thead><tr><th>Site</th><th>File / download</th><th>Historical claim (not confirmed)</th><th>Estimated leaderboard score</th><th>Unique?</th><th>Submit?</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    candidates = ''.join(f'''<tr><td>{e(r['id'])}</td><td class="mono">{e(Path(r['file']).name)}</td><td>{r['final_dot_overlap_3px']['13GEMSDOE']:.4%}</td><td>{'PASS' if r['validator']['format_valid_against_reference'] else 'FAIL'} against owner mirror only</td><td>No compliant holdout win; rejected</td></tr>''' for r in report['candidates'])
    rationale = '''<h2>Why B2 may have done better — not a causal proof</h2><p>Reopened, hash-checked owner mirrors show D2.8 has 44,090 dots and B2 has 37,654. B2 removes every D2.8 dot at distance ≤2 pixels from the catalogue. GEMSDOE36 then adds 1,200 dots. Sparse placement can reduce false-positive mass while preserving nearby truth coverage under the triangular kernel, but can also remove useful coverage. Without hidden truth and per-file receipts, we cannot say why the user-reported 0.2778 occurred or promise a higher result. A median catalogue distance is not a mandatory exclusion buffer.</p><h2>Why there is no score estimate</h2><p>The old DZ-16 regression has negative out-of-sample R² on the nine focus sites. H3-PACK extrapolates a small, related family and confounds count with packing. Neither is a calibrated prediction interval or a substitute for a matched spatial holdout. Their old projections are withdrawn as decision inputs.</p><h2>Required automated gates</h2><ol><li>Explicit assigned method lane and authenticated inputs; cached shared features, evaluator and writer.</li><li>Complete current registry; pre-placement surface Spearman ≤0.90 and dot overlap ≤70% within three pixels, repeated on final dots. Stop on the first failure; never replace the rule with enrichment or Pearson correlation.</li><li>Whole-segment buffered hide-and-recover; catalogue features from visible faults only and exact visible-pixel masking. Feature-alone AUC above 0.90 is a leakage alarm.</li><li>Pooled HOLDOUT-DTI with α=0.2, β=0.8 and 300 m triangular kernel; evaluator version, withheld-positive count, spatial 95% CI and matched incumbent comparison. A catalogue holdout is a proxy, not the leaderboard, but hidden organizer truth is not required to run this proxy.</li><li>Strict saved-file validation: one float32 band, [0,1], no masked or nonfinite footprint cells, exact CRS/shape/transform; reference provenance and SHA-256 recorded. No silent clipping.</li><li>Only a separate selector can choose a real slot after a compliant holdout win and all other gates; verify quota on the authenticated submission page.</li></ol>'''
    guide = '''<h2>Exactly how a future approved file is submitted</h2><p><strong>Do not upload any current file.</strong> After a future candidate passes every gate and the separate selector approves a slot: open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">official competition</a>, choose New submission, select the exact SHA-256-verified single-band .tif (or ZIP containing just that TIFF), and enter its method/version note of at most 140 characters. Retain the organizer receipt linking the filename and result. File name and note for a new submission: <strong>not issued</strong>.</p><p>The reported “[0,1]” rejection cannot be diagnosed without the rejected bytes. The checker reports NaN, infinity, below-zero, above-one and masked-footprint counts separately. H3-PACK's “zeros” filename actually has NaN outside the footprint. Its local footprint pass does not prove portal acceptance. The authenticated official sample governs outside-footprint encoding.</p>'''
    intro = '''<p>The previously advertised DZ-16 and H3-PACK approvals are withdrawn. Both fail a binary-lattice witness even without relying on the disputed continuous prior. Their files are preserved for reproducibility, not resubmission.</p>'''
    body = intro + '<h2>Existing local TIFFs: rechecked, rejected</h2><div style="overflow-x:auto"><table><tr><th>Artifact</th><th>File</th><th>Lattice overlap</th><th>Format</th><th>Scientific/submit gate</th></tr>' + candidates + '</table></div><h2>Nine priority sites</h2><p>Best historical user-reported file per site. These are not organizer-confirmed receipts or new-file estimates. No new file is cleared for download and submission.</p>' + table + rationale + guide + '<h2>Research shortlist</h2><p><a href="../research.html">Four ranked, untested hypotheses with layers, physical signatures, confounders and access limitations</a>. The promised method lane remains UNASSIGNED; no proposal was self-assigned. Geothermal motivation does not turn a fault prediction into a proven vent.</p>'
    sources = '''<h2>Official source inventory</h2><ul><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b">Organizer reference solution, pinned revision</a> — checked through GitHub this session. README supports CPU-only setup; GPU is recommended for speed, not mandatory.</li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem, metric and file format</a></li><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Live leaderboard</a></li><li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF</a></li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a></li><li><a href="https://gdr.openei.org/submissions/1391">DOE GDR INGENIOUS</a></li></ul><p>Outside-GitHub official pages, PDFs, data binaries and current weekly quota were not fetched in this session: this sandbox's outbound allowlist excludes their hosts. Prior source notes are historical, not renewed verification. The competing user-supplied leaderboard figures are not current verified results. There are no submission-page receipts here.</p><p>Owner mirrors are not official authentication. New external datasets are not called viable until their exact coverage, bytes, rights and access are verified. <a href="../sources.html">Detailed source register</a>.</p>'''
    out = DOCS / 'submission'
    for name, title, text in [('index.html', 'Executive release decision', body), ('executive-summary.html', 'Nine-site executive summary', body), ('methodology.html', 'Validation and scientific limits', rationale + guide), ('sources.html', 'Sources and access limits', sources), ('parallel-lanes.html', 'Parallel approvals reconciled', intro + rationale)]:
        (out / name).write_text(page(title, text))
    # Preserve the existing public URL, but never regenerate its obsolete green approval.
    submit = DOCS / 'submit/index.html'; submit.parent.mkdir(exist_ok=True)
    submit.write_text(page('How to submit — currently blocked', guide + rationale, '../submission/'))
    print('Published nine historical reviews and consistent negative release pages')


if __name__ == '__main__':
    main()
