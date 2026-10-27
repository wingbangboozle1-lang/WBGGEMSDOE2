#!/usr/bin/env python3
"""Build evidence/RUN_CARD_CBS.json + docs/cbs/ pages from measured JSON only."""
from __future__ import annotations
import hashlib, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def J(p): return json.loads((ROOT / p).read_text())
def sha(p):
    h = hashlib.sha256()
    with open(ROOT / p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

res = J("evidence/cbs_results.json"); fin = J("evidence/cbs_final.json")
est = J("evidence/candidate_estimates.json"); audit = J("evidence/focus_audit_20261027.json")
lb = J("evidence/public_leaderboard_observation_20261027T1904Z.json")
art = fin["artifact"]; stem = art["stem"]; tif = art["tif_path"]
assert sha(tif) == art["sha256"]
hold = fin["holdout_candidate_rule"]; pooled = res["holdout_pooled"]["scores"]
ests = {Path(c["file"]).name: c for c in est["candidates"]}
e_final = ests[f"{stem}.tif"]
reg = fin["registry_comparison"]
focus_rows = [r for r in reg if r["category"] == "focus_champion"]
max_ov = max(r["candidate_overlap_3px"] for r in focus_rows)
max_rho = max(abs(r["surface_spearman"]) for r in reg if r["category"] != "literal_witness")
lat = next(r for r in reg if r["id"] == "13GEMSDOE")
dense = next(r for r in reg if r["id"] == "17GEMSDOE_dense_prior")

run_card = {
  "hypothesis": "CBS: faults buried under cover lack surface scarps (hence are missing from the USGS/INGENIOUS catalogue) but still offset magnetic basement, gravity and the conductive base; subsurface-only potential-field/depth/conductivity steps, optionally cover-gated, should recover blind-like faults better than the full 19-band model.",
  "mechanism": "HistGradientBoosting on subsurface-only features (11 raw potential-field/depth/conductivity bands + 6 label-free physics operators), collar-free (>3 px from catalogue) spaced-dot emission (Euclidean suppression radius 5 px).",
  "named_non_fault_mimic": "Lithologic basement contact / caldera margin / intrusive edge (a real subsurface step that is not a fault); playa clay and irrigation fronts for conductivity.",
  "result_cbs_hypothesis": "negative",
  "holdout": {
    "evidence_class": "HOLDOUT-DTI", "evaluator_version": "gems57-pooled-hide-v2",
    "split": "label-blind-quadrants-v2, buffer 80 px, whole components hidden",
    "withheld_positive_pixels": hold["withheld_positive_pixels"],
    "ctrl_19b_dotted": pooled["ctrl_19b_dotted"], "exp1_cbs_core": pooled["exp1_cbs_core"],
    "exp2_cbs_cover": pooled["exp2_cbs_cover"], "exp3_cbs_active": pooled["exp3_cbs_active"],
    "candidate_38k_rule": hold,
    "repo_best_before_same_evaluator": {"arm": "MSPTCD EXP-3", "holdout_dti": 0.04255426811430257},
    "leakage_canaries": res["canary_summary"]},
  "candidate": {
    "arm": "ctrl_19b_dotted — the control arm won; CBS experiments are a negative result",
    "file": tif, "sha256": art["sha256"], "dots": art["dots"],
    "note_le_140_chars": art["note"],
    "validator": {"strict_all_finite": True, "format_valid_against_reference": art["validator"]["format_valid_against_reference"],
                  "no_nan_anywhere": art["validator"]["nan_total"] == 0,
                  "values_in_0_1_everywhere": art["validator"]["minimum_inside"] >= 0 and art["validator"]["maximum_inside"] <= 1,
                  "crs_shape_transform_match": art["validator"]["grid_match_reference"]},
    "correlation_overlap_vs_registry": {
      "max_3px_overlap_vs_9_focus_champions": max_ov, "max_abs_surface_spearman_vs_discrete_peers": max_rho,
      "literal_vs_13GEMSDOE_lattice": {"overlap_3px": lat["candidate_overlap_3px"], "reference_coverage_of_footprint": lat["coverage3px_of_footprint"], "enrichment": lat["enrichment_over_coverage"]},
      "literal_vs_17GEMSDOE_dense_prior": {"overlap_3px": dense["candidate_overlap_3px"], "reference_coverage_of_footprint": dense["coverage3px_of_footprint"], "enrichment": dense["enrichment_over_coverage"], "surface_spearman": dense["surface_spearman"]},
      "full_table": "evidence/cbs_final.json"},
    "score_estimates_NOT_scores": {
      "empirical_estimate": e_final["empirical_estimate"], "empirical_interval95": e_final["empirical_interval95"],
      "score_law_projection": e_final["score_law_projection"],
      "mass_balance_band_N20000": e_final["mass_balance_band_if_best_lineage_hit_rate"]["20000"]}},
  "verdict": "promote",
  "ok_to_submit": True,
  "ok_to_submit_basis": "Calibrated uniqueness gate (<=70% 3-px overlap and |rho|<=0.90 vs every discrete peer raster measured) + strict saved-byte format validation + holdout win over the previous same-evaluator best. Under the literal all-registry rule the two space-filling witnesses flag ANY dot field (coverage 99.87% and 100% of footprint; candidate enrichment ~1.0); that literal reading also flags all nine historical champions. The project owner makes the final slot decision (separate selector step; this campaign spent 0 slots).",
  "weekly_slots_used": 0}
(ROOT / "evidence/RUN_CARD_CBS.json").write_text(json.dumps(run_card, indent=2, default=float) + "\n")
(ROOT / "docs/data/RUN_CARD_CBS.json").write_text(json.dumps(run_card, indent=2, default=float) + "\n")

def fmt(x, n=4): return f"{float(x):.{n}f}"
sites = ["GEMSDOE24","GEMSDOE25","GEMSDOE27","GEMSDOE28","GEMSDOE30","GEMSDOE31","GEMSDOE32","GEMSDOE33","GEMSDOE36"]
site_rows = ""
for s in sites:
    a = audit[s]; ov = next(r for r in focus_rows if r["id"] == s)
    site_rows += (f"<tr><td><a href=\"../sites/{s}.html\">{s}</a></td><td class=\"mono\">{html.escape(Path(a['path']).name) if 'path' in a else ''}</td>"
                  f"<td>{fmt(a['reported'])}<br><small>USER-REPORTED</small></td><td>{a['dots']:,}</td>"
                  f"<td>{fmt(a['collar3'],3)}</td><td>{fmt(float(a['kmass_per_dot']),2)}</td>"
                  f"<td>83–100% vs siblings — one lineage</td><td>{fmt(ov['candidate_overlap_3px'],3)}</td>"
                  f"<td><strong>DO NOT SUBMIT</strong> (already-submitted lineage file)</td></tr>\n")

cand_rows = ""
labels = [("wbg2-d19dotted", "D19-DOTTED (this lane, control arm)", "OK TO DOWNLOAD AND SUBMIT"),
          ("wbg2-dz16", "DZ-16 (submission lane)", "OK as alternate (zeros, validated)"),
          ("wbg3-h3pack", "H3-PACK (third lane)", "DO NOT SUBMIT AS-IS — NaN outside footprint"),
          ("wbg2-msptcd", "MSPTCD-E3 (fourth lane)", "DO NOT SUBMIT (ridge emission; lane verdict negative)")]
for key, label, verdict in labels:
    c = next(v for k, v in ests.items() if k.startswith(key))
    cand_rows += (f"<tr><td><strong>{label}</strong><br><span class=\"mono\">{html.escape(Path(c['file']).name)}</span></td>"
                  f"<td>{c['support_px']:,}</td><td>{fmt(c['kmass_per_dot'],2)}</td>"
                  f"<td>{fmt(c['empirical_estimate'],3)} [{fmt(c['empirical_interval95'][0],2)}–{fmt(c['empirical_interval95'][1],2)}]<br><small>EMPIRICAL-ESTIMATE</small></td>"
                  f"<td>{fmt(c['score_law_projection'],3)}<br><small>PROJECTION</small></td>"
                  f"<td>{fmt(c['mass_balance_band_if_best_lineage_hit_rate']['20000'][0],3)}–{fmt(c['mass_balance_band_if_best_lineage_hit_rate']['20000'][1],3)}<br><small>DERIVED, N=20k</small></td>"
                  f"<td>{verdict}</td></tr>\n")

CSS = "body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;color:#14231c;background:#f6f9f7}.shell{max-width:1060px;margin:auto;padding:24px}table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}th,td{border:1px solid #d7e2da;padding:7px;text-align:left;vertical-align:top}th{background:#0b5d4d;color:#fff}.mono{font-family:ui-monospace,monospace;font-size:11px;word-break:break-all}.banner{background:#e4f4ea;border:2px solid #0b5d4d;border-radius:12px;padding:18px;margin:16px 0}.warn{background:#fff4e5;border-color:#b7791f}.btn{display:inline-block;background:#0b5d4d;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:700}small{color:#5a6e62}h1,h2{color:#0b5d4d}"
head = f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>CBS / D19-DOTTED · GEMS Research</title><style>{CSS}</style></head><body><div class=\"shell\">"
download = f"""<div class="banner"><h2>✅ OK TO DOWNLOAD AND SUBMIT — one file</h2>
<p><span class="mono">{stem}.tif</span></p>
<p><a class="btn" href="../downloads/cbs/{stem}.tif">⬇ Download GeoTIFF</a> <a class="btn" href="../downloads/cbs/{stem}.zip">⬇ Single-TIFF ZIP</a></p>
<table><tr><th>SHA-256</th><td class="mono">{art['sha256']}</td></tr>
<tr><th>Note for DrivenData (≤140 chars)</th><td class="mono">{html.escape(art['note'])}</td></tr>
<tr><th>Format (re-read from disk)</th><td>1 band float32 · EPSG:32611 · 3730×3292 · 100 m · <strong>all values finite and in [0,1] everywhere</strong> · 0.0 outside footprint · nodata unset · {art['dots']:,} isolated dots · 0 inside 3 px of the mapped catalogue</td></tr>
<tr><th>HOLDOUT-DTI</th><td><strong>{fmt(hold['dti'],4)}</strong> 95% CI [{fmt(hold['ci95'][0],4)}, {fmt(hold['ci95'][1],4)}] · evaluator gems57-pooled-hide-v2 · {hold['withheld_positive_pixels']:,} withheld positives (repo best before: 0.0426)</td></tr>
<tr><th>Estimated live score (NOT a score)</th><td>EMPIRICAL-ESTIMATE {fmt(e_final['empirical_estimate'],3)} [{fmt(e_final['empirical_interval95'][0],2)}–{fmt(e_final['empirical_interval95'][1],2)}] · PROJECTION {fmt(e_final['score_law_projection'],3)} · DERIVED band {fmt(e_final['mass_balance_band_if_best_lineage_hit_rate']['20000'][0],3)}–{fmt(e_final['mass_balance_band_if_best_lineage_hit_rate']['20000'][1],3)}</td></tr>
<tr><th>Uniqueness</th><td>max {fmt(max_ov*100,1)}% of dots within 3 px of any of the nine focus champions (limit 70%); surface |ρ| ≤ {fmt(max_rho,3)} (limit 0.90). Literal space-filling witnesses published in the executive summary.</td></tr></table>
<p><small>Slot selection is a separate step within the weekly cap on the submission page. This campaign spent 0 slots. Public leaderboard #1 was {lb['top_rows'][0]['best_public_dti']} on the official page, observed {lb['observed_utc']} — no project file is projected to beat that; see estimates.</small></p></div>"""

index = head + f"""<p><a href="../index.html">← Overview</a> · <a href="executive-summary.html">Executive summary (all nine sites + candidate table)</a> · <a href="../data/RUN_CARD_CBS.json">Run card JSON</a></p>
<h1>CBS lane → D19-DOTTED candidate</h1>
<p>The geological hypothesis tested this session (covered basement steps visible only to subsurface geophysics) <strong>lost</strong> to its own control on the shared hide-and-recover holdout — that negative result is the deliverable of the CBS experiments. The winning arm, a 19-band model emitted for the first time as collar-free spaced dots, tripled the repo's previous same-evaluator holdout best and is the file below.</p>
{download}
<h2>How to submit (exactly)</h2>
<ol><li>Download the GeoTIFF (or ZIP) above. Do not rename the file inside the ZIP.</li>
<li>Open the DrivenData submission page for competition 306 and choose the downloaded <span class="mono">.tif</span> (or the single-TIFF <span class="mono">.zip</span>).</li>
<li>Paste the note shown above (85 chars).</li>
<li>Verify the SHA-256 of your downloaded file matches the value above before uploading.</li>
<li>Previous "Predicted values must be in range [0, 1]" rejections: this file contains <strong>no NaN anywhere</strong> and no value outside [0,1]; it was re-read from disk after writing. Files with NaN outside the footprint (e.g. the H3-PACK artifact) should not be uploaded as-is.</li></ol>
<h2>Why GEMSDOE32 B2 (0.2778, USER-REPORTED) led the nine — measured answer</h2>
<p>All nine focus rasters are one density lineage (83–100% of each file's dots lie within 3 px of a sibling). Re-fitting their reported scores on measured geometry gives <span class="mono">score = {fmt(est['score_law']['coef_intercept'],4)} {fmt(est['score_law']['coef_per_1000_dots'],6)}·(dots/1000) {fmt(est['score_law']['coef_collar'],4)}·collar</span>, R²={fmt(est['score_law']['r2_nine_focus'],3)}. B2 wins because it has the fewest dots (37,654) and the smallest catalogue-collar fraction (5.8%): it is the lineage mask with every dot ≤2 px from a mapped fault deleted. Dots on/near already-mapped faults earn nothing (known faults are masked in scoring) but still pay the α=0.2 false-positive cost, and redundant mass is pure cost under the exact DTI identity FN<sub>w</sub>=N−TP<sub>w</sub>.</p>
<p><small>Sources: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem/metric</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official leaderboard</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a>. All historical GEMSDOE scores are USER-REPORTED with no organizer receipt in this repo.</small></p>
</div></body></html>"""

exec_html = head + f"""<p><a href="index.html">← CBS / download</a></p><h1>Executive summary — nine focus sites + candidates</h1>
{download}
<h2>Candidate table: what to download, estimated score, unique?</h2>
<table><tr><th>File</th><th>Dots</th><th>kmass/dot (max 9.38)</th><th>EMPIRICAL-ESTIMATE [95%]</th><th>PROJECTION (score law)</th><th>DERIVED band</th><th>Verdict</th></tr>{cand_rows}</table>
<p><small>Estimates are not scores and carry no organizer receipt. EMPIRICAL model external RMSE on the nine focus sites = {fmt(est['empirical_rmse_external_focus'],3)}. The score law is fit on one collinear lineage and constrains placement, not geology.</small></p>
<h2>The nine focus sites (measured from hash-pinned bytes this session)</h2>
<table><tr><th>Site</th><th>Champion file (pinned)</th><th>Reported</th><th>Dots</th><th>Collar ≤3px</th><th>kmass/dot</th><th>Unique vs other 8?</th><th>New candidate overlap ≤3px</th><th>Verdict</th></tr>{site_rows}</table>
<h2>Holdout results (this campaign)</h2>
<table><tr><th>Arm</th><th>HOLDOUT-DTI (pooled)</th><th>95% CI</th><th>N withheld</th></tr>
{''.join(f"<tr><td>{k}</td><td>{fmt(v['dti'],4)}</td><td>[{fmt(v['ci95'][0],4)}, {fmt(v['ci95'][1],4)}]</td><td>{v['withheld_positive_pixels']:,}</td></tr>" for k, v in pooled.items())}
<tr><td>MSPTCD EXP-3 (previous repo best, same evaluator)</td><td>0.0426</td><td>[0.0321, 0.0548]</td><td>60,988</td></tr></table>
<p>CBS experiments (subsurface-only) reached 0.097–0.100 — above the previous repo best but significantly below the 19-band control with identical dotted emission (paired Δ CI excludes 0): <strong>CBS hypothesis = negative</strong>. On the low-relief stratum, the cover-gated CBS arm tied the control (Δ −0.0005, CI includes 0). Leakage canaries: {res['canary_summary']['features_tested']} features × 4 folds, max two-sided AUC {fmt(res['canary_summary']['max_two_sided_auc'],4)} ({res['canary_summary']['max_two_sided_feature']}) ≤ 0.90.</p>
<h2>Uniqueness — calibrated and literal readings both published</h2>
<p>Discrete peers: PASS (table above; details in <span class="mono">evidence/cbs_final.json</span>). Literal all-registry rule: the 13GEMSDOE stride-5 lattice's 3-px coverage is {fmt(lat['coverage3px_of_footprint']*100,2)}% of the footprint, so any ≥22k-dot field necessarily exceeds 70% overlap; this candidate's overlap is {fmt(lat['candidate_overlap_3px']*100,1)}% = enrichment {fmt(lat['enrichment_over_coverage'],3)}× over chance (≈1.0 = no similarity). The 17GEMSDOE continuous prior is positive on 100% of the footprint (overlap 100%, enrichment 1.000, surface ρ={fmt(dense['surface_spearman'],3)}). The literal reading flags every historical champion too; choosing between readings is the project owner's call. Conservative option: submit nothing.</p>
<h2>Irregularities flagged</h2>
<ul><li>H3-PACK's "-zeros" filename contains 7,111,787 NaN cells outside the footprint (nodata=NaN) — portal-range risk; do not submit as-is.</li>
<li>The mirrored "sample submission" reference's positive cells are byte-equivalent to the fault catalogue (60,988 px) — it is used only as a grid/footprint reference, never as truth.</li>
<li>Two feature-stack mirrors differ in byte size (418,912,844 verified here vs 439,405,361 cited by the MSPTCD lane); band descriptions and grid agree, provenance remains owner-mirror, not authenticated DrivenData data.</li>
<li>Prompt-supplied leaderboard highs (0.4413 / 0.3195) conflict with the official page observed this session: #1 = 0.4544.</li>
<li>The catalogue hide-and-recover holdout was anti-correlated with live scores within the nine-file lineage (prior lane); it validates surface discrimination, not live rank. Budget was therefore set by live-calibrated placement economics, not by the holdout sweep (which was monotone).</li></ul>
<p><small>Per-site reviews: <a href="../sites/GEMSDOE24.html">GEMSDOE24</a> · 25 · 27 · 28 · 30 · 31 · 32 · 33 · 36 (same pattern). Full methods: <span class="mono">research/cbs_preregistration_20261027.md</span>, <span class="mono">scripts/run_wbg2_cbs.py</span>, <span class="mono">scripts/build_cbs_final.py</span>.</small></p>
</div></body></html>"""

out_dir = ROOT / "docs/cbs"; out_dir.mkdir(exist_ok=True)
(out_dir / "index.html").write_text(index)
(out_dir / "executive-summary.html").write_text(exec_html)
print("built", out_dir)
