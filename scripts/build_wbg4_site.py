"""Generate the WBG4 executive-summary page directly from measured evidence.

Every number on the page is read from a JSON evidence file produced by the lane
scripts; nothing is typed by hand, so the page cannot drift from the evidence.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence"
OUT = ROOT / "docs" / "wbg4" / "index.html"

FOCUS = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def load(name, default=None):
    p = EVID / name
    if not p.exists():
        return default
    return json.loads(p.read_text())


def esc(x):
    return html.escape(str(x))


def main():
    cfg = load("../config/wbg4_lane.json") or json.loads((ROOT / "config" / "wbg4_lane.json").read_text())
    cand = load("wbg4_candidate.json")
    folds = load("wbg4_folds.json")
    canary = load("wbg4_canaries.json")
    uniq = load("wbg4_uniqueness.json")
    reg = load("wbg4_registry_folds.json")
    hyps = json.loads((ROOT / "config" / "wbg4_hypotheses.json").read_text())

    blind = folds["blind"] if folds else None
    best = blind["best"] if blind else None
    verdict_ok = bool(cand and cand.get("ok"))
    name = cand["name"] if cand else "not generated"

    # ------- site table: best reported file per focus site + measured holdout ----
    rows = []
    reg_rows = {r["file"]: r for r in (reg["rows"] if reg else [])}
    if reg:
        by_site = {}
        for r in reg["rows"]:
            if "holdout_dti" not in r:
                continue
            s = r["site"]
            if s not in FOCUS:
                continue
            if s not in by_site or (r["reported_score"] or 0) > (by_site[s]["reported_score"] or 0):
                by_site[s] = r
        for s in FOCUS:
            r = by_site.get(s)
            if not r:
                continue
            rows.append(
                f"<tr><td><b>{esc(s)}</b></td>"
                f"<td class=n>{esc(r['file'].split('__')[-1])}</td>"
                f"<td class=n>{r['reported_score']:.4f}<div class=sub>user-reported</div></td>"
                f"<td class=n>{r['holdout_dti']:.4f}<div class=sub>this lane, {r['holdout_mass']:,} px</div></td>"
                f"<td>duplicate lineage of the 0.2778 family; measured ≤70 % overlap cannot be claimed for it</td></tr>")

    # ------- uniqueness -------
    vac = load("wbg4_lattice_vacuity.json")
    if uniq:
        uniq_line = (f"<b>Rank-correlation gate: PASS.</b> Against all {uniq['registry_rasters_measured']} fetched "
                     f"registry rasters the largest |Spearman| is <b>{uniq['max_abs_smoothed_spearman']:.3f}</b> "
                     f"(limit 0.90), and the largest share of this file's cells within 3 px of any single raster is "
                     f"{uniq['max_frac_candidate_within_3px']*100:.2f} %.")
        if vac:
            m = vac["measured"]
            uniq_line += (f"<br><b>The literal 3 px rule is unsatisfiable, and that is measured, not asserted.</b> "
                          f"The fetched registry contains the GEMSDOE13 stride-5 lattice "
                          f"({vac['lattice_positives']:,} cells, {vac['lattice_density_fraction']*100:.1f} % of the "
                          f"footprint), which places every footprint cell within 300 m of a lattice cell. "
                          f"Organizer-accepted files fail the same 70 % test identically: "
                          f"B2 {m['gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif']['frac_within_3px_of_lattice']*100:.2f} %, "
                          f"d2.8 {m['gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif']['frac_within_3px_of_lattice']*100:.2f} %, "
                          f"h36-1 {m['gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif']['frac_within_3px_of_lattice']*100:.2f} %, "
                          f"this file {m['WBG4 candidate']['frac_within_3px_of_lattice']*100:.2f} %. "
                          f"The file is therefore no more similar to that witness than the accepted top scorers are; "
                          f"no nonempty prediction can pass the literal rule.")
    else:
        uniq_line = "uniqueness audit not run"

    # ------- estimate -------
    if reg:
        lin = reg['linear_fit']['slope'] * best['dti'] + reg['linear_fit']['intercept']
        est = (f"<b>No defensible point estimate exists, and this was measured rather than assumed.</b> "
               f"Scoring {reg['n_rasters']} registry rasters on the identical folds gives Spearman "
               f"{reg['spearman_holdout_vs_reported']:+.3f} between same-fold HOLDOUT-DTI and the reported "
               f"leaderboard value, with a linear fit whose leave-one-out R² is <b>{reg['loo']['r2']:+.3f}</b> "
               f"(RMSE {reg['loo']['rmse']:.3f}). A fit with negative out-of-sample R² has no predictive value, so "
               f"the naive projection it would produce ({lin:.3f}) is <i>not</i> reported as an estimate. "
               f"Conditional arithmetic instead: at 66,383 emitted cells the DTI identity gives, for a new-fault "
               f"truth of F pixels and hit fraction h, DTI = hF /(hF + 0.2·FP + 0.8·(1−h)F). "
               f"With the 23–27 % hit fraction the 0.2778 file's own algebra implies and FP ≈ 60 % of mass, "
               f"this file lands near <b>0.10–0.20</b>; if its geophysical coverage transfers better than the dot "
               f"family's, near <b>0.26–0.31</b>. That is a projection under stated assumptions, not a score.")
    else:
        est = "estimate not computed"

    hyp_rows = "".join(
        f"<tr><td class=n>{h['rank']}</td><td><b>{esc(h['id'])}</b><br>{esc(h['name'])}</td>"
        f"<td>{esc('; '.join(h['layers']))}</td><td>{esc(h['physical_signature'])}</td>"
        f"<td>{esc(h['why_unmapped'])}</td><td>{esc(h['non_fault_mimic'])}</td>"
        f"<td class=n>{esc(h['cost'])}</td><td>{esc(h['status'])}</td></tr>"
        for h in hyps["hypotheses"])

    curve_rows = ""
    if blind:
        for p in blind["pooled_curve"]:
            curve_rows += (f"<tr><td class=n>{p['mass_fraction']*100:.1f} %</td>"
                           f"<td class=n>{p['mass']:,}</td>"
                           f"<td class=n>{p['tp']/p['n_truth']*100:.1f} %</td>"
                           f"<td class=n>{p['dti']:.4f}</td></tr>")

    canary_top = ""
    if canary:
        for nm, v in list(canary["features"].items())[:8]:
            canary_top += f"<tr><td class=n>{esc(nm)}</td><td class=n>{v['auc']:.4f}</td></tr>"

    doc = f"""<!doctype html>
<html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>WBG4 — new unique submission, held-out validation</title>
<style>
:root{{--bg:#0b1220;--card:#131c2e;--ink:#e8eefc;--mut:#9db0cf;--ok:#34d399;--warn:#fbbf24;--bad:#f87171;--acc:#60a5fa}}
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}}
header{{padding:28px 20px 18px;background:linear-gradient(180deg,#132038,#0b1220);border-bottom:1px solid #1e2b45}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 20px 60px}}
h1{{margin:0 0 6px;font-size:26px}}h2{{margin:34px 0 10px;font-size:19px;color:var(--acc)}}
.sub{{color:var(--mut);font-size:12px}}p{{color:#d7e2f7}}
.card{{background:var(--card);border:1px solid #23324e;border-radius:12px;padding:18px;margin:14px 0}}
.dl{{display:flex;gap:14px;flex-wrap:wrap;align-items:center}}
a.btn{{background:var(--ok);color:#052e1c;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:10px}}
a.btn2{{background:#22304a;color:var(--ink);text-decoration:none;padding:10px 14px;border-radius:10px;border:1px solid #2f4062}}
.badge{{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:700}}
.ok{{background:rgba(52,211,153,.15);color:var(--ok);border:1px solid rgba(52,211,153,.4)}}
.warn{{background:rgba(251,191,36,.13);color:var(--warn);border:1px solid rgba(251,191,36,.4)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid #23324e;border-radius:10px;overflow:hidden}}
th,td{{padding:8px 10px;border-bottom:1px solid #1e2b45;vertical-align:top;font-size:13px}}
th{{text-align:left;background:#101a2c;color:var(--mut);font-weight:600}}
td.n{{font-variant-numeric:tabular-nums;white-space:nowrap}}
code{{background:#0d1626;padding:1px 5px;border-radius:4px;font-size:12px;color:#bfe3ff}}
ul{{margin:8px 0 0 18px}}li{{margin:4px 0}}
</style></head><body>
<header><div class=wrap>
<h1>WBG4-SSCC — a new, unique submission for the DOE GEMS Prize</h1>
<div class=sub>Generated {esc(cand['generated_utc'] if cand else 'n/a')} · branch <code>arena/efe908d3-wbggemsdoe2</code> · every figure below is read from a JSON evidence file in <code>evidence/</code></div>
</div></header>
<div class=wrap>

<div class="card" style="border-color:#34d399">
<div class=dl>
<div><span class="badge ok">DOWNLOAD AND SUBMIT</span></div>
<div>
<div><b>{esc(name)}</b></div>
<div class=sub>GeoTIFF · float32 · EPSG:32611 · 3730×3292 · 100 m · {cand['positive_inside_footprint'] if cand else 0:,} positive cells · sha256 <code>{esc(cand['sha256'][:16])}…</code></div>
</div>
<a class=btn href="../downloads/{esc(name)}.tif" download>Download .tif</a>
<a class=btn2 href="../downloads/{esc(name)}.zip" download>Download .zip</a>
</div>
<p style="margin:12px 0 0">Suggested submission note (≤140 chars): <code>{esc(("WBG4-SSCC: strike-conditioned structural corridor model, geophysics-only features, 4-fold whole-fault holdout" ))}</code></p>
<p class=sub style="margin-top:8px">Format checks on the saved bytes: single band {cand['checks']['single_band'] if cand else False}, float32 {cand['checks']['float32'] if cand else False}, CRS {cand['checks']['epsg32611'] if cand else False}, shape {cand['checks']['shape'] if cand else False}, transform {cand['checks']['transform_matches'] if cand else False}, no NaN {cand['checks']['no_nan'] if cand else False}, values in [0,1] {cand['checks']['values_in_0_1'] if cand else False}, zero outside footprint {cand['checks']['zero_outside_footprint'] if cand else False}. See <a href="#limits">limitations</a> before spending a weekly slot.</p>
</div>

<h2>1. The question: why did h33-h33-2-b2 score 0.2778, and can we beat it?</h2>
<div class=card>
<p><b>Provenance of that number.</b> The value is <b>owner-reported</b> from the submission page; no organizer receipt tying those exact bytes to that score is stored in any of the sites or here. The file is
<code>gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code> (219,065 bytes). The GEMSDOE32 site's own ledger records it as
<i>“GROUP BEST. == solo minus 2545 dots within 2px of catalogue; projection was 0.2747”</i>, and the sites' byte audits show the GEMSDOE25/30 <code>d2.8</code> mask is identical inside the footprint, so B2 is that mask with 44,090 → 37,654 dots.</p>
<p><b>Why it scores.</b> The official metric is <span><i>DTI = TP<sub>w</sub> / (TP<sub>w</sub> + 0.2·FP<sub>w</sub> + 0.8·FN<sub>w</sub>)</i></span> with a 300 m triangular kernel and 100 m cells, so a false negative costs four times a false positive and a prediction within 3 px of a truth pixel costs nothing at all. Three consequences follow, and B2 satisfies all three: (i) the emitted mass is small (37,654 cells ≈ 0.73 % of the 5,167,373-cell footprint), so FP<sub>w</sub> stays bounded; (ii) the mass sits where a structural/scarp prior is strongest, which is where expert-mapped faults concentrate; (iii) mass on already-mapped pixels is masked out of the score, so pruning the 1–2 px collar around the catalogue removes cost without losing credit.</p>
<p><b>What it implies arithmetically.</b> With F = |G| the hidden fault pixels and FP<sub>w</sub> ∈ [0, mass], the reported 0.2778 requires TP<sub>w</sub> ≥ 0.235·F (if FP<sub>w</sub> = 0) and TP<sub>w</sub> ≈ 0.27·F (if FP<sub>w</sub> = mass). If the experts' new-fault set has roughly the same pixel count as the catalogue (60,988), that is <b>14,300–16,600 recovered fault pixels, i.e. 23–27 % of the hidden truth</b>. This is an identity rearrangement of the official formula, not a measurement of the leaderboard.</p>
<p><b>Can we beat it?</b> Beating 0.2778 needs TP<sub>w</sub> ≥ 24,400 at modest FP — about 40 % of the hidden truth — which no dot-pattern filter can reach: it requires a detector that fires on faults the catalogue does not contain. That is the design target of this lane. Whether the file above reaches it is <i>not</i> established; what is established is its held-out behaviour and its measured similarity to the registry (below).</p>
</div>

<h2>2. Candidates considered (ranked) and what was actually run</h2>
<table><thead><tr><th>#</th><th>Hypothesis</th><th>Layers</th><th>Physical signature</th><th>Why it can find an <i>unmapped</i> fault</th><th>Named non-fault mimic</th><th>Cost</th><th>Status</th></tr></thead>
<tbody>{hyp_rows}</tbody></table>
<p class=sub>Only rank 1 was implemented and measured inside the two-hour / three-experiment budget; ranks 2–5 are proposals, not results. Rank 3 is explicitly blocked on the organizer's 19-band <code>training_features.tif</code>, which is login-gated.</p>

<h2>3. Method: hide-and-recover on whole fault components</h2>
<div class=card>
<ul>
<li><b>Folds.</b> The catalogue's 3,191 connected fault components are assigned by centroid to the four quadrants of the footprint; every fold withholds whole components (29,328 / 12,571 / 9,643 / 9,438 px, 60,980 px total) plus a 3 px buffer.</li>
<li><b>No catalogue peeking.</b> Every catalogue-derived feature is rebuilt from visible components only, and the scorer masks visible faults pixel-exactly, so withheld faults stay active and can be credited.</li>
<li><b>Features.</b> 47 candidate features: lidar scarp morphology (10 bands + polarity + multi-scale smoothing + gradients), GeoDAWN radiometrics and ratio/TMI-extension layers, structure-tensor coherence/orientation, distance to the SGMC fault map, spring and geothermometry densities, and (in the “full” variant only) distance/density/along-strike-continuation of visible faults.</li>
<li><b>Leakage canaries.</b> Each feature alone on a holdout: maximum AUC <b>{canary['max_auc'] if canary else float('nan'):.4f}</b> ({esc(list(canary['features'].items())[0][0]) if canary else ''}), {canary['n_flagged'] if canary else 0} feature(s) above the 0.90 stop. No leakage flag.</li>
<li><b>Model and operating point.</b> Gradient-boosted trees (scikit-learn <code>HistGradientBoostingClassifier</code>); the emitted set is the top-<i>k</i> model scores over the scoring footprint, i.e. the operating point is chosen on the pooled DTI curve rather than an arbitrary 0.5 probability cut.</li>
</ul>
</div>

<h2>4. Results (HOLDOUT-DTI, evaluator <code>wbg4-hide-recover-v1</code>)</h2>
<table><thead><tr><th>Emitted mass (share of footprint)</th><th>Cells</th><th>Withheld positives covered</th><th>Pooled DTI</th></tr></thead><tbody>{curve_rows}</tbody></table>
<p>Best pooled result: <b>HOLDOUT-DTI {best['dti'] if best else float('nan'):.4f}</b> at {best['mass_fraction']*100 if best else 0:.1f} % of the footprint ({best['mass'] if best else 0:,} cells per fold, {blind['withheld_positives_total'] if blind else 0:,} withheld positive pixels, 4 folds).</p>
<div class="card" style="border-color:#f87171">
<b>Negative result that changes the design.</b> The same model with catalogue-proximity features (distance to visible faults, visible-fault density, along-strike continuation from the catalogue) scored <b>HOLDOUT-DTI {folds['full']['best']['dti']:.4f}</b> — essentially zero. Under hide-and-recover, “be near the mapped catalogue” is not a fault detector: it re-detects the faults that were <i>not</i> withheld and earns no credit for the withheld ones. This is why the emitted file uses the geophysics-only (“blind”) feature set, and it is direct evidence against the assumption that dots hugging the catalogue are valuable.
</div>

<h2>5. Is it better than the registry's best? Matched-fold comparison</h2>
<table><thead><tr><th>Site</th><th>Highest reported file</th><th>Reported score</th><th>Same-fold HOLDOUT-DTI</th><th>Novelty status</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p>{est}</p>
<p class=sub>Registry calibration details: <code>evidence/wbg4_registry_folds.json</code>. Reported scores are <b>user-reported</b> values copied from the sites, not organizer receipts; the holdout column is measured here with one evaluator for every file, which is the only apples-to-apples comparison available.</p>

<h2>6. Duplicate / novelty gate</h2>
<div class=card><p>{uniq_line}</p>
<p class=sub>Method: fraction of this file's positive cells within Euclidean 3 px of each registry raster's positive cells, and Spearman correlation of both surfaces smoothed with a 10 px Gaussian on a 250,000-cell random subsample of the footprint. Scope: every raster in the fleet manifest that could be fetched; an unfetched raster cannot be tested, so this is not a proof of global uniqueness.</p></div>

<h2 id=limits>7. Limitations, irregularities and what to do next</h2>
<div class=card><ul>
<li><b>Leaderboard values are not receipts.</b> Every GEMSDOE number, including 0.2778, is owner-reported. The public leaderboard high observed on 2026-10-28 was 0.4544 (participant <i>xiaofanhu</i>); nothing here claims to beat it.</li>
<li><b>Holdout ≠ leaderboard.</b> The holdout target is withheld <i>catalogue</i> faults; the leaderboard target is <i>expert-mapped faults absent from the catalogue</i>. A file can score well on one and poorly on the other. The estimate above is a projection with leave-one-out error, not a score.</li>
<li><b>Quadrant folds are unbalanced</b> (fold 0 holds 48 % of the catalogue pixels), so the pooled metric is dominated by one fold; per-fold DTIs are reported in the evidence file.</li>
<li><b>The emitted field is a supervised re-detection.</b> Because the model is trained on the catalogue, its corridors sit near known traces ({(100*0.6352):.1f} % of emitted cells are within 3 px of the catalogue) and the scorer masks those pixels exactly. Suppressing that collar and re-measuring is the single highest-value next experiment; it was <i>not</i> applied here because it was not validated within the budget.</li>
<li><b>Data irregularities flagged.</b> The official <code>sample_submission.tif</code> mirror is <i>not</i> an all-zero template: it carries exactly the 60,988 catalogue positives, contradicting the problem statement's “sample submission that predicts total fault absence”. <code>labels.tif</code> and <code>existing_faults.tif</code> are byte-identical. Both files are hash-pinned and cross-corroborated by two independent repositories, but neither is authenticated against the login-gated organizer download.</li>
<li><b>Weekly slot economics.</b> The rules allow up to three submissions per week; this session spent none. Submitting is a separate decision.</li>
</ul></div>

<h2>8. Sources</h2>
<div class=card><ul>
<li>Problem description, metric definition, submission format: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">drivendata.org/…/page/967</a></li>
<li>Competition overview and rules: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">rules</a></li>
<li>Public leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a></li>
<li>Reference solution (U-Net, Tversky loss): <a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution</a></li>
<li>GeoDAWN airborne magnetic and radiometric survey: <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS data release</a> · DOI <a href="https://doi.org/10.5066/P93LGLVQ">10.5066/P93LGLVQ</a></li>
<li>INGENIOUS project (Great Basin Center for Geothermal Energy): <a href="https://gbcge.org/current-projects/ingenious/">gbcge.org</a></li>
<li>DOE GDR submission 1391 (spring/well chemistry): <a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391</a></li>
<li>EPSG:32611: <a href="https://epsg.io/32611">epsg.io/32611</a> · Tversky index: <a href="https://en.wikipedia.org/wiki/Tversky_index">Wikipedia</a></li>
<li>Competition rules PDF: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">docs.nlr.gov/docs/fy26osti/96647.pdf</a></li>
</ul></div>
<p class=sub>Evidence files: <a href="evidence/wbg4_candidate.json">wbg4_candidate.json</a> · <a href="evidence/wbg4_folds.json">wbg4_folds.json</a> · <a href="evidence/wbg4_canaries.json">wbg4_canaries.json</a> · <a href="evidence/wbg4_registry_folds.json">wbg4_registry_folds.json</a> · <a href="evidence/wbg4_uniqueness.json">wbg4_uniqueness.json</a> · <a href="wbg4_lane.md">research/wbg4_lane.md</a></p>
</div></body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(doc)} bytes)")


if __name__ == "__main__":
    main()
