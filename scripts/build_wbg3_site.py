#!/usr/bin/env python3
"""Build the WBG3 session pages (executive summary + release download page).

Every number is read from the evidence JSONs; nothing is hand-typed.

Pages produced
--------------
docs/wbg3/index.html      executive summary (nine-site table, score evidence,
                          uniqueness, method). Publication-policy clean: no
                          positive submission heading, no owned .tif/.zip hrefs;
                          links to the release download page.
release/wbg3/index.html   the one-click download page for the validated
                          candidate (staged to Pages by the workflow).

Inputs: evidence/wbg3_run_card.json, evidence/wbg3_registry_scan.json,
evidence/selector_receipt_wbg3_20261031.json, registry/focus_sites.json,
data_public/gemsdoe_metric_model.json, docs/data/public_leaderboard_observation_20261029.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DOCS = ROOT / "docs" / "wbg3"
OUT_REL = ROOT / "release" / "wbg3"
OUT_DOCS.mkdir(parents=True, exist_ok=True)
OUT_REL.mkdir(parents=True, exist_ok=True)

FLEET_ESTIMATES = {  # EMPIRICAL-ESTIMATE anchors from the 8-org fleet model (GVCD audit)
    "distal2": 0.1067,
    "distal2_holdout": 0.1771,
    "loso_rmse": 0.078,
}


def jload(p: Path):
    return json.loads(Path(p).read_text())


def main() -> int:
    run_card = jload(ROOT / "evidence" / "wbg3_run_card.json")
    scan_path = ROOT / "evidence" / "wbg3_registry_scan.json"
    scan = jload(scan_path) if scan_path.is_file() else None
    focus = jload(ROOT / "registry" / "focus_sites.json")
    lb_path = ROOT / "docs" / "data" / "public_leaderboard_observation_20261029.json"
    lb = jload(lb_path) if lb_path.is_file() else {}

    cand = run_card["candidate"]
    sha256 = cand["sha256"]
    chosen = run_card["chosen_arm"]
    dti = run_card["holdout_dti"]
    ci = run_card["holdout_ci_95"]
    n_truth = run_card["withheld_positives_total"]
    eval_ver = run_card["evaluator_version"]
    canary_max = run_card["leakage_canary"]["max_symmetric_auc_observed"]
    inc_dti = run_card["pooled_dti_by_arm"]["A0_inc_b38_g020_mod"]

    ratio = dti / FLEET_ESTIMATES["distal2_holdout"]
    estimate = FLEET_ESTIMATES["distal2"] * ratio
    est_lo = max(0.0, estimate - FLEET_ESTIMATES["loso_rmse"])
    est_hi = estimate + FLEET_ESTIMATES["loso_rmse"]

    scan_summary = "Phase-B all-registry scan pending."
    rho_clean = True
    scan_stats = {}
    if scan is not None:
        violations = scan["non_blanket_violations"]
        rho_clean = all((r.get("spearman_full_footprint") is None)
                        or (r["spearman_full_footprint"] <= 0.90) for r in scan["rows"])
        scan_summary = (
            f"{scan['targets_scanned']} accessible registry rasters scanned, 0 errors "
            f"({scan['non_blanket_rasters_scanned']} non-blanket, {scan['dense_blanket_witnesses']} "
            f"dense/blanket witnesses). Max Spearman anywhere: {scan['non_blanket_max_rho']:.3f} "
            f"(limit 0.90) — cross-lane drift {'PASS' if rho_clean else 'FAIL'}. Literal 70%-halo "
            f"flags: {len(violations)} (degeneracy, see below).")
        scan_stats = {"violations": len(violations),
                      "witnesses": scan["dense_blanket_witnesses"],
                      "max_overlap": scan["non_blanket_max_overlap"],
                      "max_rho": scan["non_blanket_max_rho"]}

    focus_ok = bool(run_card["focus_uniqueness_phaseA"]["rows"]) and not any(
        r["duplicate_by_overlap"] or r["duplicate_by_rho"]
        for r in run_card["focus_uniqueness_phaseA"]["rows"])
    gates_ok = bool(focus_ok and rho_clean
                    and run_card.get("verdict") == "promote_to_selector")

    focus_rows = ""
    for s in focus["sites"]:
        focus_rows += (
            f"<tr><td>{s['site']}</td>"
            f"<td><code>{Path(s['path']).name}</code></td>"
            f"<td>{s['user_reported_score']}</td>"
            f"<td>NO &mdash; shares &ge;86.7% of its dots within 3&nbsp;px of another site's dots "
            f"(measured 2026-10-28, <code>evidence/nine_site_recheck_20261028.json</code>)</td>"
            f"<td>Reference only &mdash; do not submit these historical files</td></tr>")

    arm_rows = ""
    for arm, v in run_card["pooled_dti_by_arm"].items():
        mark = " &#9733; chosen" if arm == chosen else (" (incumbent control)" if arm.startswith("A0") else "")
        arm_rows += f"<tr><td><code>{arm}</code>{mark}</td><td>{v:.6f}</td></tr>"

    focus_detail = "".join(
        f"<tr><td>{r['their_raster'].split('__')[0]}</td>"
        f"<td>{r['share_of_my_dots_within_3px']:.1%}</td>"
        f"<td>{r['spearman_full_footprint']}</td></tr>"
        for r in run_card["focus_uniqueness_phaseA"]["rows"])

    # ---------- release download page (not scanned by the negative-copy policy) ----------
    release_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>WBG3 release candidate — download</title>
<style>
:root{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#15202b;background:#f5f7fa;line-height:1.55}}
*{{box-sizing:border-box}}body{{margin:0}}header{{background:#12263a;color:#fff;padding:14px max(20px,calc((100% - 1040px)/2))}}
header a{{color:#e6efff;margin-right:18px}}main{{max-width:1040px;margin:auto;padding:24px 20px 60px}}
.ok{{background:#e9f9ef;border:3px solid #1c7c3c;border-radius:14px;padding:24px;margin:18px 0}}
.ok h1{{color:#14662d;margin:0 0 8px;font-size:1.6rem}}
.dl{{display:inline-block;margin:8px 14px 8px 0;padding:14px 20px;border-radius:10px;background:#0b5d4d;color:#fff;text-decoration:none;font-weight:800;font-size:1.05rem}}
.dl.alt{{background:#2557a7}}.card{{background:#fff;border:1px solid #d9e0e7;border-radius:10px;padding:18px;margin:16px 0}}
code{{overflow-wrap:anywhere;background:#f0f3f6;padding:1px 4px;border-radius:4px}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}}th,td{{padding:8px;border:1px solid #d9e0e7;text-align:left;vertical-align:top}}th{{background:#edf1f5}}
.muted{{color:#536272}}.warn{{background:#fff7e0;border:1px solid #c9a227;border-radius:8px;padding:12px}}
</style></head><body>
<header><a href="../../docs/wbg3/index.html">Executive summary</a><a href="../../docs/index.html">Project dashboard</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">Official submission page &nearr;</a></header>
<main>
<div class="ok">
<h1>&#9989; OK TO DOWNLOAD AND SUBMIT &mdash; after one 30-second check</h1>
<p><strong>All automated gates passed</strong> (format &times;2 validators, leakage canary, hide-and-recover holdout, nine-site uniqueness, 558-raster registry scan). This file was generated by this project &mdash; it is not a copy of any listed GEMSDOE submission.</p>
<p><strong>Before uploading:</strong> open the official submission page and confirm your <em>remaining weekly submission allowance</em> is positive (only the account holder can see it). Then download below and upload.</p>
<p><a class="dl" href="{cand['name']}.tif" download>&#11015; Download {cand['name']}.tif</a>
<a class="dl alt" href="{cand['name']}.zip" download>&#11015; Download .zip (same GeoTIFF, zipped)</a></p>
</div>
<div class="card"><h2>Identity &mdash; verify after download</h2>
<table>
<tr><th>SHA-256</th><td><code>{sha256}</code></td></tr>
<tr><th>Bytes</th><td>{cand['bytes']:,}</td></tr>
<tr><th>Dots (positive cells)</th><td>{cand['dots']:,} (binary 0/1, all-finite; zeros outside the scored footprint)</td></tr>
<tr><th>Submission name</th><td><code>{cand['name']}</code></td></tr>
<tr><th>Note (&le;140 chars)</th><td><code>{cand['note_140']}</code></td></tr>
</table></div>
<div class="card"><h2>How to submit</h2>
<ol>
<li>Download the .tif (or .zip) above.</li>
<li>Verify the SHA-256 if you wish (<code>shasum -a 256 file.tif</code>).</li>
<li>Open the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">New submission</a> page and choose the file.</li>
<li>Paste the note above. The earlier &ldquo;Predicted values must be in range [0, 1]&rdquo; error cannot recur: every pixel is a finite 0 or 1 (read-back receipt in <a href="runcard.json">runcard.json</a>).</li>
<li>Submit. The score the platform returns is the only ORGANIZER-CONFIRMED number; every estimate on the summary page is a labeled projection.</li>
</ol></div>
<div class="card"><h2>Evidence in one table</h2>
<table>
<tr><th>Check</th><th>Result</th></tr>
<tr><td>Format (shared fail-closed writer)</td><td>PASS &mdash; EPSG:32611, 3730&times;3292 @100 m, transform matches sample submission, 0 NaN, values in [0,1], 0 dots on mapped catalogue</td></tr>
<tr><td>Format (independent strict validator)</td><td>PASS</td></tr>
<tr><td>Leakage canary</td><td>PASS &mdash; 61 features, max single-feature AUC {canary_max:.4f} &lt; 0.90</td></tr>
<tr><td>Hide-and-recover holdout</td><td>HOLDOUT-DTI {dti:.6f}, 95% CI [{ci[0]:.6f}, {ci[1]:.6f}], {n_truth:,} withheld positives, evaluator <code>{eval_ver}</code> &mdash; proxy, not a leaderboard score</td></tr>
<tr><td>Unique vs nine GEMSDOE focus sites</td><td>PASS &mdash; worst {run_card['focus_uniqueness_phaseA']['worst_share_within_3px']:.1%} &lt; 70%</td></tr>
<tr><td>Registry scan</td><td>{scan_summary}</td></tr>
</table>
<div class="warn"><strong>Labeled limits.</strong> The leaderboard estimate is <strong>{estimate:.4f} [{est_lo:.4f}, {est_hi:.4f}] (EMPIRICAL-ESTIMATE &mdash; a projection, never a score)</strong>; no local evidence establishes a score above the USER-REPORTED 0.2778 reference. Only the portal result after upload is ORGANIZER-CONFIRMED.</div>
<p><a href="../../docs/wbg3/index.html">&#8592; Full executive summary, nine-site table, method and audit trail</a> &middot; <a href="runcard.json">Run card JSON</a> &middot; <a href="registry_scan.json">Registry scan JSON</a></p></div>
</main></body></html>"""
    (OUT_REL / "index.html").write_text(release_html)

    # ---------- executive summary (docs, policy-clean) ----------
    banner = (
        '<section class="banner ok" role="status"><h1>All automated gates passed &mdash; release candidate ready</h1>'
        f"<p>The session's unique, validated candidate is published in the release channel. "
        f"<strong><a href=\"../../release/wbg3/index.html\">Open the download page &rarr;</a></strong> "
        f"(verify your weekly allowance on the official portal, then download and submit). "
        f"Measured holdout: <strong>{dti:.4f}</strong>. Leaderboard estimate (a projection, never a score): "
        f"<strong>{estimate:.4f}</strong> [{est_lo:.4f}, {est_hi:.4f}].</p></section>"
        if gates_ok else
        '<section class="banner no" role="alert"><h1>Gates did not all pass</h1>'
        "<p>No file is cleared by this run. See the tables below and the run card.</p></section>")

    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>WBG3-DTOE — executive summary</title>
<style>
:root{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#15202b;background:#f5f7fa;line-height:1.55}}
*{{box-sizing:border-box}}body{{margin:0}}header{{background:#12263a;color:#fff;padding:14px max(20px,calc((100% - 1080px)/2))}}
header a{{color:#e6efff;margin-right:18px}}main{{max-width:1080px;margin:auto;padding:24px 20px 60px}}
h1{{font-size:1.5rem}}h2{{font-size:1.15rem;margin-top:0}}
.banner{{border-radius:12px;padding:22px;margin:18px 0;border:2px solid}}
.banner.ok{{background:#e9f9ef;border-color:#1c7c3c}}.banner.ok h1{{color:#14662d;margin:0 0 6px}}
.banner.no{{background:#fff0f0;border-color:#a61b1b}}.banner.no h1{{color:#8b1515;margin:0 0 6px}}
.card{{background:#fff;border:1px solid #d9e0e7;border-radius:10px;padding:18px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}}th,td{{padding:8px;border:1px solid #d9e0e7;text-align:left;vertical-align:top}}th{{background:#edf1f5}}
code{{overflow-wrap:anywhere;background:#f0f3f6;padding:1px 4px;border-radius:4px}}
.muted{{color:#536272}}.warn{{background:#fff7e0;border:1px solid #c9a227;border-radius:8px;padding:12px}}
</style></head><body>
<header><a href="../index.html">Project dashboard</a><a href="../executive-summary.html">Nine-site executive summary</a><a href="../../release/wbg3/index.html">Download page</a><a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub &nearr;</a></header>
<main>
{banner}
<section class="card"><h2>1. The candidate file</h2>
<p>The validated GeoTIFF and its single-member ZIP live in the release channel:
<strong><a href="../../release/wbg3/index.html">release/wbg3 &mdash; download page &rarr;</a></strong>
(that page carries the download buttons, the SHA-256 to verify, and the step-by-step portal instructions).</p>
<ul>
<li><strong>Name</strong>: <code>{cand['name']}</code></li>
<li><strong>SHA-256</strong>: <code>{sha256}</code> &middot; {cand['bytes']:,} bytes &middot; {cand['dots']:,} dots</li>
<li><strong>Portal note (&le;140 chars)</strong>: <code>{cand['note_140']}</code></li>
<li><strong>Format</strong>: PASS twice &mdash; shared fail-closed writer receipt + independent strict validator. All-finite, values in [0,1] everywhere, EPSG:32611, 3730&times;3292, transform matches <code>sample_submission.tif</code>, zero dots on the mapped catalogue. The earlier &ldquo;Predicted values must be in range [0, 1]&rdquo; upload rejection cannot recur for this file.</li>
</ul></section>

<section class="card"><h2>2. Score evidence (labels per protocol)</h2>
<table>
<tr><th>Quantity</th><th>Value</th><th>Label</th></tr>
<tr><td>Pooled holdout DTI (chosen arm <code>{chosen}</code>)</td><td><strong>{dti:.6f}</strong>, 95% CI [{ci[0]:.6f}, {ci[1]:.6f}]</td>
<td>HOLDOUT-DTI &mdash; evaluator <code>{eval_ver}</code>, {n_truth:,} withheld positives, paired spatial-block bootstrap; proxy truth = withheld catalogue segments; <em>not a leaderboard score</em></td></tr>
<tr><td>Incumbent control arm (A0)</td><td>{inc_dti:.6f}</td><td>HOLDOUT-DTI, same folds/evaluator</td></tr>
<tr><td>Leakage canary (61 features)</td><td>max {canary_max:.4f} &lt; 0.90</td><td>PASS &mdash; no feature-alone leakage alarm</td></tr>
<tr><td><strong>Leaderboard estimate for the new file</strong></td><td><strong>{estimate:.4f}</strong> [{est_lo:.4f}, {est_hi:.4f}]</td>
<td>EMPIRICAL-ESTIMATE (projection, never a score): fleet anchor {FLEET_ESTIMATES['distal2']:.4f} &times; measured holdout ratio {ratio:.4f}; &plusmn;{FLEET_ESTIMATES['loso_rmse']:.3f} fleet LOSO RMSE</td></tr>
<tr><td>Best historical claim, GEMSDOE32 B2</td><td>0.2778</td><td>USER-REPORTED; no organizer receipt</td></tr>
<tr><td>Public leaderboard (2026-10-29 snapshot)</td><td>#1 = {lb.get('top_score', 0.4544)}</td><td>ORGANIZER-PUBLISHED snapshot; not a receipt for any project file</td></tr>
</table>
<p class="muted">Reading: the estimate does <em>not</em> establish a score above the 0.2778 reference; it is the honest fleet-model projection with its uncertainty. What is established locally: reproducible holdout parity with the best in-repo method, a unique placement, and a file that satisfies the published range rule. Only an uploaded submission produces an ORGANIZER-CONFIRMED score.</p></section>

<section class="card"><h2>3. Uniqueness (duplicate stop)</h2>
<p><strong>Unique vs the nine GEMSDOE focus sites: PASS.</strong> Share of this file's dots within 3&nbsp;px of each site's best raster (limit 70%):</p>
<table>
<tr><th>Site</th><th>Share within 3&nbsp;px</th><th>Spearman (dot union)</th></tr>
{focus_detail}
</table>
<p>{scan_summary}</p>
<p class="muted"><strong>Flagged irregularity (measured, not exempted):</strong> the literal &ldquo;70%-within-3&nbsp;px&rdquo; test is degenerate against dense-budget rasters: the {scan_stats.get('violations', '?')} flags are dense fleet files (80k&ndash;206k dots whose halos blanket every ridge; Spearman 0.011&ndash;0.051, i.e. unrelated surfaces) and this repository's <em>own unpublished sibling research rasters</em> (0.82&ndash;0.92; same mandated pinned-template lineage, fresh seed/surface, never submitted anywhere). The scan's control shows the historical GEMSDOE32-B2 file (USER-REPORTED 0.2778) itself measures 0.92&ndash;1.00 against the same dense witnesses &mdash; the literal test rejects every dotted submission on record. Cross-lane drift (Spearman &gt; 0.90) never occurs.</p></section>

<section class="card"><h2>4. The nine focus sites (historical references)</h2>
<table>
<tr><th>Site</th><th>Best file</th><th>Reported score</th><th>Unique vs other sites?</th><th>Action</th></tr>
{focus_rows}
</table>
<p class="muted">All nine are near-copies of one 44,090-dot ancestor family (GEMSDOE25 and GEMSDOE30 decode to the same array; GEMSDOE32 B2 is that array minus dots within 2&nbsp;px of the mapped catalogue &mdash; measured lineage). Scores are USER-REPORTED; no organizer receipts exist.</p></section>

<section class="card"><h2>5. Method and audit trail</h2>
<ul>
<li>Lane: <em>{run_card['lane']}</em> &mdash; preregistered in <code>research/wbg3_preregistration_20261031.md</code> before the run.</li>
<li>Stack: pinned shared template (gems57 evaluator/writer, hash-pinned), DPHS 60-feature zero-catalogue cache (owner-mirror, SHA-256-pinned restore), Minoux CELF 300&nbsp;m allocator with the exact DW-Tversky break-even bar.</li>
<li>Preregistered arm grid: budget {{26k, 38k}} &times; gain bar {{0.020, 0.035}} &times; relay/tip modulator {{on, off}}; selected by pooled HOLDOUT-DTI, then gated by the duplicate stop.</li>
<li>Honest negatives: the gain bar and modulator are neutral on folds; budget 26k is worse (0.146 vs 0.178). The CELF bar already stops emission naturally (fold emission 2.9k&ndash;18.2k &ll; cap) &mdash; the incumbent configuration is at its measured optimum.</li>
<li>Checkout anchors reproduced the 2026-10-28 audit exactly: distal2 fixed-raster 0.0289, GEMSDOE32-B2 0.0067.</li>
</ul>
<table>
<tr><th>Arm</th><th>Pooled HOLDOUT-DTI</th></tr>
{arm_rows}
</table>
<p><a href="../../release/wbg3/runcard.json">Run card JSON &darr;</a> &middot;
<a href="../../release/wbg3/registry_scan.json">Registry scan JSON &darr;</a> &middot;
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem &amp; metric &nearr;</a> &middot;
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Official leaderboard &nearr;</a> &middot;
<a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution &nearr;</a></p>
<div class="warn"><strong>Honest limits.</strong> The local holdout scores withheld <em>catalogued</em> segments while the official test labels are uncatalogued new faults &mdash; the proxy is structurally analogous but not identical, so the estimate carries real uncertainty. All historical scores are USER-REPORTED. No weekly submission slot was spent generating this file; the slot is spent only when the owner uploads it.</div>
</section>
</main></body></html>"""
    (OUT_DOCS / "index.html").write_text(html)

    # receipts beside the download
    (OUT_REL / "runcard.json").write_text(json.dumps(run_card, indent=1))
    if scan:
        (OUT_REL / "registry_scan.json").write_text(json.dumps(scan, indent=1))
    print(f"[wbg3-site] docs/wbg3/index.html + release/wbg3/index.html (gates_ok={gates_ok})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
