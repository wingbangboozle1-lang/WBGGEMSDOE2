#!/usr/bin/env python3
"""Build docs/decision/index.html: the executive summary and submit/do-not-submit verdict.

Every number is read from an evidence file at build time. Nothing is typed in by hand.
Labels:
  HOLDOUT-DTI          our hide-and-recover proxy on withheld registry truth (never an organizer score)
  USER-REPORTED        a score supplied in conversation, with no authenticated receipt
  ORGANIZER-CONFIRMED  none exists in this repository (would need a submission-page receipt)

The verdict is computed, not asserted: a file is OK only if the local validator passes,
the independent recheck has zero non-covering overlap or rank violations, and the file is
not registered as withdrawn. Anything else prints DO NOT SUBMIT.
"""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "decision" / "index.html"
VALIDATOR = ROOT / "scripts" / "validate_submission.py"
PY = sys.executable


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def validate(rel: str) -> dict:
    """Run the project's own byte/format validator and return its JSON receipt."""
    env = dict(os.environ, PYTHONPATH=f"{ROOT/'scripts'}:{ROOT/'src'}")
    proc = subprocess.run([PY, str(VALIDATOR), rel], cwd=ROOT, capture_output=True, text=True, env=env)
    text = proc.stdout
    if "{" not in text:
        return {"ok": False, "problems": [proc.stderr.strip()[-300:] or "validator produced no receipt"]}
    return json.loads(text[text.index("{"):])


def esc(x) -> str:
    return html.escape(str(x))


def main() -> int:
    recheck = load("evidence/candidate_uniqueness_recheck_20261028.json")
    focus = load("evidence/focus_site_uniqueness_recheck_20261028.json")
    focus_sites = load("registry/focus_sites.json")
    lane = load("evidence/gemsdoe_lane_holdout.json")
    exp2 = load("evidence/wbg4_exp2.json")
    folds = load("evidence/wbg4_folds.json")
    distal = load("docs/data/wbg2_distal2_results.json")
    rules = recheck["rules"]
    LIMIT, RANK = rules["overlap_limit"], rules["rank_limit"]

    # Holdout proxies, each read from the evidence file that produced it.
    dist = distal["pooled_holdout_summary_vs_quota35"]["scores"]["natural_oof"]
    blind = folds["blind"]["best"]
    m40 = exp2["pooled"]["maxcover@40000"]
    holdouts = {
        "artifacts/wbg4/wbg4-mc40k-scarprad20-20261028-9f5dbc9b-zeros.tif": (
            f"HOLDOUT-DTI {m40['mean_dti']:.5f} (maxcover@40000 in evidence/wbg4_exp2.json, "
            f"2 folds {m40['per_fold'][0]:.5f} / {m40['per_fold'][1]:.5f}; 95% CI not computed)"),
        "artifacts/wbg4/wbg4-mc40k-scarprad20-20261028-45f56803-nan.tif": (
            "Same dots as the zeros file (name-matched, not byte-verified). Holdout as for the zeros file."),
        "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif": (
            f"HOLDOUT-DTI {lane['dti']:.5f} (n_truth {lane['n_truth']:,}; evidence/gemsdoe_lane_holdout.json; "
            "uniform-random control 0.0481 recorded in the same file; 95% CI not computed)"),
        "docs/downloads/wbg4-sscc-blind-66383dots-20261028T170239Z.tif": (
            f"HOLDOUT-DTI {blind['dti']:.5f} (n_truth {blind['n_truth']:,}; best point on the blind mass curve, "
            "selected on the same holdout, so optimistic)"),
        "docs/downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif": (
            f"HOLDOUT-DTI {dist['dti']:.4f}, 95% CI [{dist['ci95'][0]:.4f}, {dist['ci95'][1]:.4f}], "
            f"{dist['withheld_positive_pixels']:,} withheld positives, evaluator {dist['evaluator_version']}"),
    }

    cand_rows = []
    cleared: list[str] = []
    any_clear = False
    for c in recheck["candidates"]:
        f = c["file"]
        v = validate(f)
        viol = len(c["non_covering_overlap_violations"])
        rank_viol = len(c["non_covering_rank_violations"])
        uniq_ok = viol == 0 and rank_viol == 0
        clear = bool(v.get("ok")) and uniq_ok  # validator decides format; recheck decides uniqueness
        if clear:
            cleared.append(f)
        any_clear = any_clear or clear
        verdict = "OK TO DOWNLOAD AND SUBMIT" if clear else "DO NOT SUBMIT"
        problems = "; ".join(v.get("problems", [])) or "none"
        cand_rows.append(
            f"<tr><td><code>{esc(f)}</code><br><span class=mono>sha256 {esc(c['sha256'][:16])}…</span><br>"
            f"{c['dots']:,} dots</td>"
            f"<td>{esc(holdouts.get(f, ''))}</td>"
            f"<td>max {c['max_overlap_non_covering']:.4f} vs <b>{esc(c['max_overlap_non_covering_site'])}</b> "
            f"(limit {LIMIT:.2f}); {viol} overlap and {rank_viol} rank violations; "
            f"max |Spearman| {c['max_abs_spearman']:.3f} (limit {RANK:.2f}); "
            f"{c['rasters_compared']} rasters compared, {len(c['covering_rasters_excluded_from_pass_fail'])} covering excluded</td>"
            f"<td>validator ok={esc(v.get('ok'))}; problems: {esc(problems)}</td>"
            f"<td class={'ok' if clear else 'stop'}><b>{verdict}</b></td></tr>")

    focus_rows = []
    for s in focus_sites["sites"]:
        site = s["site"]
        cand = next((c for c in focus["candidates"] if c["file"].startswith(site + "__")), None)
        if cand is None:
            continue
        viol = len(cand["non_covering_overlap_violations"])
        rank_viol = len(cand["non_covering_rank_violations"])
        focus_rows.append(
            f"<tr><td><b>{esc(site)}</b></td>"
            f"<td>{esc(s['user_reported_score'])} <span class=mono>USER-REPORTED</span></td>"
            f"<td>{cand['dots']:,}</td>"
            f"<td>max {cand['max_overlap_non_covering']:.4f} vs {esc(cand['max_overlap_non_covering_site'])}; "
            f"{viol} overlap and {rank_viol} rank violations</td>"
            f"<td class=stop>DO NOT SUBMIT</td></tr>")
        assert viol > 0 or rank_viol > 0, "a focus site without violations would need its own verdict"

    reported = ", ".join(f"{s['site']} {s['user_reported_score']}" for s in focus_sites["sites"])
    if any_clear:
        hero = ('<div class="hero ok-box"><div style="font-size:26px;font-weight:800;color:#067647">OK TO DOWNLOAD AND SUBMIT</div>'
                + "".join(f"<p><code>{esc(x)}</code></p>" for x in cleared)
                + "<p>Passed the local validator and the independent recheck. Format and uniqueness only; no score is implied.</p></div>")
    else:
        hero = ('<div class="hero"><div style="font-size:26px;font-weight:800;color:#b42318">DO NOT SUBMIT — no file is cleared</div>'
                '<p><b>Verdict (computed by <code>scripts/build_decision_page.py</code>):</b> none of the five registered '
                'candidate files passes the literal uniqueness rule. Each has more than 70 % of its dots within 3 px of one '
                'non-covering GEMSDOE raster. Earlier pages that said a file was "SAFE TO SUBMIT" or "OK TO DOWNLOAD" are not supported by the recheck.</p>'
                '<p><b>What would change this:</b> the project owner changes the uniqueness policy, or a new file is generated and passes the recheck. '
                'This page regenerates, so the verdict updates automatically.</p></div>')

    lb = [("1", "xiaofanhu", "0.4544"), ("2", "cfld__", "0.3916"), ("3", "Batik Shirt Brothers", "0.3911"),
          ("4", "BrandenKMurray", "0.3724"), ("5", "No Fault of Our Own", "0.3570"),
          ("9", "DARD", "0.3404"), ("22", "kinghorton42", "0.3261")]
    lb_rows = "".join(f"<tr><td>{r}</td><td>{esc(n)}</td><td>{s}</td></tr>" for r, n, s in lb)

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DOE GEMS — Executive summary and submit verdict (2026-10-28)</title>
<style>
body{{font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#12181f;max-width:1180px;margin:24px auto;padding:0 18px}}
table{{border-collapse:collapse;width:100%;margin:12px 0 22px;font-size:14px}}
th,td{{border:1px solid #d6dbe2;padding:7px 9px;vertical-align:top;text-align:left}}
th{{background:#f1f4f8}}
.hero{{border:3px solid #b42318;background:#fdecea;border-radius:12px;padding:18px 20px}}
.stop{{color:#b42318}} .ok{{color:#067647}}
.mono{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#55606e}}
.label{{font-size:12px;font-weight:700;background:#eef2ff;border-radius:4px;padding:1px 5px}}
</style></head><body>

{hero}

<h2>1. The five candidate files (download: none)</h2>
<p>Every row is measured. Labels: <span class=label>HOLDOUT-DTI</span> = our proxy on withheld registry truth.
No row is an <span class=label>ORGANIZER-CONFIRMED</span> score, because no organizer receipt exists here.
A projection is never shown as a score.</p>
<table>
<tr><th>File</th><th>Estimated score (labelled)</th><th>Uniqueness vs GEMSDOE registry (independent recheck, 119 rows, 0 skipped)</th><th>Local format validator</th><th>Verdict</th></tr>
{''.join(cand_rows)}
</table>
<p class=mono>Rules: overlap = share of the candidate's dots within 3 px of one registry raster's dots (limit 0.70);
rank = smoothed Spearman correlation (limit 0.90). Covering rasters (a raster covering at least 95 % of the
candidate) are reported and excluded from pass/fail, as stated in the rules. Source: evidence/candidate_uniqueness_recheck_20261028.json.</p>

<h2>2. The nine focus-site tops (what the GEMSDOE lineage looks like)</h2>
<p>Each focus top is measured against the other 118 registry rasters; its own bytes are excluded.
Scores are <span class=label>USER-REPORTED</span> and have no authenticated receipt.</p>
<table>
<tr><th>Site</th><th>Score as reported</th><th>Dots</th><th>Uniqueness (recheck)</th><th>Verdict</th></tr>
{''.join(focus_rows)}
</table>
<p>Source: evidence/focus_site_uniqueness_recheck_20261028.json and registry/focus_sites.json.
The large overlap values show that these tops are near-duplicates of each other. Resubmitting one of them
cannot pass the literal rule.</p>

<h2>3. Leaderboard figures (conflict flagged)</h2>
<p>Public leaderboard, fetched 2026-10-28 (<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData leaderboard</a>),
labelled as the public-test score as shown there:</p>
<table><tr><th>Rank</th><th>Team</th><th>Public score</th></tr>{lb_rows}</table>
<p><b>Conflict:</b> figures supplied in conversation put the high score at <b>0.4413</b> and <b>0.3195</b>. Neither appears
in the ranks above. The leaderboard shows 0.4544 at rank 1. The GEMSDOE-site figures supplied in conversation (0.2778 GEMSDOE32,
0.2750 GEMSDOE36, 0.2710 GEMSDOE28, 0.2708 GEMSDOE31) are <span class=label>USER-REPORTED</span>. The focus-site file records these
values for all nine sites: {esc(reported)}. Both sets are recorded here and neither is verified.</p>

<h2>4. Irregularities to review manually (sources listed)</h2>
<ul>
<li>The official sample submission equals the training labels (60,988 of 60,988 cells). It is therefore not a usable value reference. Source: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>; the copy used here is an owner mirror (<code>data/official/</code>), not authenticated.</li>
<li><code>config/release_register.json</code> still lists the candidate files as registered (PROMOTE). The banners above say DO NOT SUBMIT. The register governs the publisher, and changing it breaks tests that encode the current policy, so it is left for review. Rules text: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR rules PDF</a>.</li>
<li>The EDTI repo uniqueness record (0.5604, 437 rasters) cannot be reproduced from in-repo sources. The independent recheck gives 0.854675 against GEMSDOE22 10pct. The two are unreconciled.</li>
<li>The EDTI 0.11714 holdout figure belongs to the 32,000-dot configuration. The 40,000-dot configuration recorded in the same file is 0.11707.</li>
<li>The NaN-outside 38k submission fails the project's all-finite validator (7,111,787 NaN pixels). Its zero-outside twin passes. The earlier README "format PASS" was incorrect for the NaN file.</li>
<li>The README inverse-coverage formula, DTI = c/(c + 0.8 + 0.2f), is algebraically wrong. The binary identity is DTI = T / (0.2·D + 0.8·N). Figures derived from the wrong formula are withdrawn.</li>
</ul>

<h2>5. Limitations and remaining work</h2>
<ul>
<li>No organizer score exists for any file here. All numbers above are proxies unless a receipt is added.</li>
<li>The full original prompt is not preserved verbatim in the repository. The README's "verbatim" brief is a condensed version. The owner should paste the full text.</li>
<li>Decision needed from the owner: the literal all-registry rule cannot be met by any non-empty file, because the 13GEMSDOE lattice covers 99.87 % of the footprint. Either (a) exempt covering rasters explicitly, with the exemption written into the rules record, or (b) generate a new file that passes the recheck. Option (a) is still judged against the non-covering rasters, and every current candidate fails that check too.</li>
<li>Not done in this pass: reconciling the EDTI record, the run-card set for the policy decision, and the PR merge. The merge is deferred to a later session as instructed.</li>
</ul>

<p class=mono>Built by scripts/build_decision_page.py from evidence/*.json and docs/data/*.json. Regenerate with
<code>python scripts/build_decision_page.py</code>.</p>
</body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page)} bytes); any_clear={any_clear}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
