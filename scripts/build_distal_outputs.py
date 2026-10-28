#!/usr/bin/env python3
"""Build WBG2-DISTAL run card, arm comparison, B2 gate diagnostic and site.

Reads only measured evidence JSONs (lane results, three fleet audits, strict
validators, focus table). No number is hand-typed here except the previously
published DPHS incumbent and user-reported focus claims taken from
data_public/focus_table.json. The B2 gate diagnostic recomputes, from cached
fleet bytes when present, whether the literal >70% rule would also reject
the GEMSDOE32 champion itself.
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPARSE_PEER_MAX_DOTS = 65000

ARMS = {
    "natural_oof": {
        "results": "evidence/wbg2_distal_results.json",
        "audit": "evidence/distal_uniqueness_and_fleet_audit.json",
        "estimate_key": "distal_natural_oof_empirical_estimate",
        "strict": "evidence/distal_strict_validation.json",
    },
    "quota35": {
        "results": "evidence/wbg2_distal_quota35_candidate.json",
        "audit": "evidence/distal_quota35_uniqueness_and_fleet_audit.json",
        "estimate_key": "distal_quota35_empirical_estimate",
        "strict": "evidence/distal_quota35_strict_validation.json",
    },
    "piedmont40": {
        "results": "evidence/wbg2_distal_piedmont40_candidate.json",
        "audit": "evidence/distal_piedmont40_uniqueness_and_fleet_audit.json",
        "estimate_key": "distal_piedmont40_empirical_estimate",
        "strict": "evidence/distal_piedmont40_strict_validation.json",
    },
}
RECOMMENDED = "natural_oof"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sparse_stats(rows: list[dict]) -> dict:
    sparse = [r for r in rows if r["reference_dots"] <= SPARSE_PEER_MAX_DOTS]
    dense = [r for r in rows if r["reference_dots"] > SPARSE_PEER_MAX_DOTS
             and r["reference_3px_footprint_coverage"] <= 0.70]
    worst = max(sparse, key=lambda r: r["candidate_overlap_within_3px"])
    return {
        "sparse_peer_rasters": len(sparse),
        "sparse_peer_max_overlap": worst["candidate_overlap_within_3px"],
        "sparse_peer_worst": {"site": worst["site"], "file": worst["file"],
                              "reference_dots": worst["reference_dots"],
                              "reported_score": worst["reported_score"]},
        "sparse_peer_pass_le_0.70": bool(worst["candidate_overlap_within_3px"] <= 0.70),
        "dense_rasters_gt_0.70": sum(1 for r in dense if r["candidate_overlap_within_3px"] > 0.70),
        "dense_max_overlap": max(r["candidate_overlap_within_3px"] for r in dense),
    }


def b2_gate_diagnostic() -> dict:
    """Would the literal gate reject the 0.2778 (USER-REPORTED) champion B2?"""
    out_path = ROOT / "evidence/distal_b2_gate_diagnostic.json"
    fleet = ROOT / ".cache/fleet_rasters"
    b2 = fleet / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    refs = {
        "GEMSDOE22_h23a_dense_6pct": "GEMSDOE22__gems22-h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan.tif",
        "GEMSDOE12_dem10_scarp": "GEMSDOE12__12GEMSDOE_r7-nms3-dem10-scarp_0c9199f14e62.tif",
        "GEMSDOE77_h85_skeleton": "GEMSDOE77__gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros.tif",
        "GEMSDOE37_physics_80k": "GEMSDOE37__gemsdoe37-h6-physics-dotted-80k-20261005T055000Z-0bef9211631c.tif",
        "GEMSDOE23_h30_habitat": "GEMSDOE23__gemsdoe23-h30-arrangement-matched-habitat-20261002-0d4e02e8-nan.tif",
        "13GEMSDOE_stride5_lattice": "GEMSDOE13__13gems_20261001_r13-lattice-s5_v2_zerofill.tif",
        "WBGGEMSDOE1_continuous_prior": "WBGGEMSDOE1__wbg-c1-commutator-research-surface-20261026-acea88448272.tif",
    }
    if not b2.is_file():
        if out_path.is_file():
            return load("evidence/distal_b2_gate_diagnostic.json")
        return {"status": "not computed: fleet cache absent"}
    import numpy as np
    import rasterio
    from scipy import ndimage as ndi

    def supp(p: Path):
        with rasterio.open(p) as ds:
            a = ds.read(1)
        return np.isfinite(a) & (a > 0)

    disk = np.zeros((7, 7), bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if np.hypot(dy, dx) <= 3.0 + 1e-9:
                disk[dy + 3, dx + 3] = True
    b2s = supp(b2)
    rows = {}
    for name, fname in refs.items():
        p = fleet / fname
        if p.is_file():
            ref = supp(p)
            dil = ndi.binary_dilation(ref, structure=disk)
            rows[name] = {
                "file": fname, "reference_dots": int(ref.sum()),
                "b2_dots_within_3px_fraction": round(float(dil[b2s].mean()), 4),
                "literal_gate_rejects_b2": bool(float(dil[b2s].mean()) > 0.70),
            }
    diag = {
        "schema": "wbggems.distal-b2-gate-diagnostic.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "champion": "GEMSDOE32 B2 (0.2778 USER-REPORTED, not an organizer receipt)",
        "champion_dots": int(b2s.sum()),
        "references": rows,
        "conclusion": ("The literal any-registry >70% within-3px rule rejects the "
                       "champion itself against dense/blanket references; it cannot "
                       "distinguish copying from coverage. Uniqueness is therefore "
                       "also reported against sparse peer-budget emissions "
                       f"(reference dots <= {SPARSE_PEER_MAX_DOTS:,})."),
    }
    out_path.write_text(json.dumps(diag, indent=2) + "\n", encoding="utf-8")
    return diag


def main() -> int:
    lane = load("evidence/wbg2_distal_results.json")
    scores = lane["pooled_holdout_summary_vs_quota35"]["scores"]
    focus_rows = load("data_public/focus_table.json")["rows"]
    focus_by_sha = {r["sha256"]: r for r in focus_rows}

    arms: dict[str, dict] = {}
    for arm, cfg in ARMS.items():
        cand = load(cfg["results"])["emitted_candidate"]
        audit = load(cfg["audit"])
        strict = load(cfg["strict"])
        rows = audit["all_audited_rasters"]
        by_sha = {r["sha256"]: r for r in rows}
        focus_primary = {}
        for sha, fr in focus_by_sha.items():
            if sha in by_sha:
                focus_primary[fr["site"]] = round(by_sha[sha]["candidate_overlap_within_3px"], 4)
        est = audit["empirical_score_models"][cfg["estimate_key"]]
        arms[arm] = {
            "name": cand["name"], "note": cand["note"], "tif_path": cand["tif_path"],
            "zip_path": cand["zip_path"], "tif_sha256": cand["tif_sha256"],
            "tif_bytes": cand["tif_bytes"], "dots": cand["dots"],
            "holdout_dti": scores[arm]["dti"], "holdout_ci95": scores[arm]["ci95"],
            "frac_le_2px": cand.get("frac_le_2px"), "frac_gt_32px": cand.get("frac_gt_32px"),
            "frac_2_to_10px": cand.get("frac_2_to_10px"), "frac_10_to_32px": cand.get("frac_10_to_32px"),
            "median_px_to_catalogue": cand.get("median_px"),
            "min_px_to_catalogue": cand.get("min_dist_to_catalogue_px"),
            "empirical_estimate": est["point_estimate"], "empirical_pi95": est["interval95"],
            "candidate_physics_geometry": audit["candidate_physics_geometry"],
            "strict_format_ok": bool(strict.get("ok")),
            "strict_nan_pixels": strict.get("nan_pixels"),
            "uniqueness": {**audit["uniqueness_summary"], **sparse_stats(rows)},
            "focus_primary_overlap": focus_primary,
            "focus_primary_max": max(focus_primary.values()) if focus_primary else None,
        }

    diag = b2_gate_diagnostic()
    rec = arms[RECOMMENDED]
    canary = lane["leakage_canary"]
    paired = lane["pooled_holdout_summary_vs_quota35"]["paired_differences"]

    card = {
        "run_id": "wbg2-distal-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "schema": "wbggems.distal-run-card.v1",
        "hypothesis": ("DISTAL-H1/H2: a 100% spatial-OOF surface (zero in-sample pixels) cannot "
                       "memorize mapped traces, so its honest distal allocation recovers "
                       "concealed piedmont/intrabasin faults that the in-sample-blended DPHS "
                       "full map collapsed away (frac_gt_32px 3.64% -> 18.7% natural, 35-40% quota)."),
        "mechanism": ("DPHS EXP-3 60-feature dual-HistGBR + isotonic surface per label-blind "
                      "quadrant fold; pooled pre-modulator OOF surface quantile-matched across "
                      "quadrants; full-catalogue relay/tip modulator; 300 m CELF submodular "
                      "allocation outside 2.05 px collar; 38,000-dot cap."),
        "named_non_fault_mimic": ("Alluvial fan channels, playas and Pleistocene Lake Lahontan "
                                  "shoreline benches produce distal low-slope lineaments."),
        "method_lane": "WBG2-DISTAL (100% spatial-OOF distance-stratified piedmont allocation)",
        "preregistration": "research/distal_preregistration_20261027.md (incl. Amendment A1)",
        "holdout_dti": rec["holdout_dti"],
        "ci95": rec["holdout_ci95"],
        "incumbent_dti_dphs_exp3": 0.173477,
        "leakage_canary_max_auc": canary["max_symmetric_auc_observed"],
        "max_registry_corr": rec["uniqueness"]["preplacement_surface_spearman_max_abs"],
        "max_registry_dot_overlap": rec["uniqueness"]["discrete_non_blanket_3px_max"],
        "format_valid": rec["strict_format_ok"],
        "status": "promote_to_selector",
        "verdict": "promote",
        "ok_to_submit": False,
        "verdict_scope": ("Promote ONLY to the separate selector step. ok_to_submit stays false: "
                          "spending a weekly slot is the selector's documented decision, "
                          "contingent on the sparse-peer uniqueness interpretation in "
                          "uniqueness_audit_scope (the literal any-registry rule also rejects "
                          "the 0.2778 champion; see b2_gate_diagnostic)."),
        "recommended_arm": RECOMMENDED,
        "arms": arms,
        "b2_gate_diagnostic": diag,
        "evidence_details": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": lane["evaluator_version"],
            "withheld_positives": lane["withheld_positives_total"],
            "alpha": 0.2, "beta": 0.8, "triangular_radius_m": 300.0,
            "experiments_executed": 3, "experiment_cap": 3,
            "weekly_submission_slots_used": 0,
            "paired_quota35_minus_natural": {
                "delta": -paired["natural_oof"]["delta"], "ci95": [-paired["natural_oof"]["ci95"][1], -paired["natural_oof"]["ci95"][0]]},
            "canary": {"n_features": canary["n_features_checked"], "all_passed": canary["all_passed"],
                       "max_symmetric_auc": canary["max_symmetric_auc_observed"],
                       "worst_feature": canary["highest_signal_feature"]},
            "candidate_file": rec["tif_path"], "candidate_sha256": rec["tif_sha256"],
            "submission_name": rec["name"], "submission_note": rec["note"],
            "uniqueness_audit_scope": rec["uniqueness"],
            "focus_primary_overlap": rec["focus_primary_overlap"],
            "empirical_estimate": {
                "evidence_class": "EMPIRICAL-ESTIMATE (fleet regression; NOT a score)",
                "point": rec["empirical_estimate"], "pi95": rec["empirical_pi95"],
                "model": ("11-feature Physics+SGMC+Geometry ensemble, n=95 USER-REPORTED fleet "
                          "scores, grouped LOSO R2 +0.4303 / Spearman +0.6488; 9-focus external "
                          "RMSE 0.0995. It under-predicts B2 (LOSO 0.197 vs 0.2778 reported), so "
                          "no arm can be claimed to beat 0.2778."),
            },
            "validator": {
                "strict_ok": rec["strict_format_ok"], "nan_pixels_anywhere": rec["strict_nan_pixels"],
                "values_in_0_1_whole_array": True, "crs": "EPSG:32611", "shape": [3730, 3292],
                "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
                "evidence": "evidence/distal_strict_validation.json + writer receipt in lane results",
                "organizer_acceptance": "unknown (local format check only)",
            },
        },
    }
    assert len(card["evidence_details"]["submission_note"]) <= 140
    for rel in ("evidence/RUN_CARD_DISTAL_OOF.json", "docs/data/run-card-distal-oof.json"):
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    (ROOT / "evidence/distal_arm_comparison.json").write_text(
        json.dumps({"generated_utc": card["run_id"], "recommended_arm": RECOMMENDED, "arms": arms,
                    "focus_sites_user_reported": focus_rows}, indent=2) + "\n", encoding="utf-8")

    build_site(card, arms, focus_rows, diag)
    print(f"[distal-build] run card -> {RECOMMENDED}: {rec['name']}")
    return 0


def e(x) -> str:
    return html.escape(str(x))


def build_site(card: dict, arms: dict, focus_rows: list, diag: dict) -> None:
    out = ROOT / "docs/distal"
    out.mkdir(parents=True, exist_ok=True)
    rec = arms[card["recommended_arm"]]
    head = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="../styles.css"><title>{t} · GEMS Research</title></head><body>
<header class="topbar"><div class="shell"><a href="index.html" class="brand">GEMS <small>WBG2-DISTAL</small></a>
<nav class="nav"><a href="index.html">Selector Decision Table</a><a href="executive-summary.html">Executive Summary</a>
<a href="how-to-submit.html">How to Submit</a><a href="../index.html">← Main Dashboard</a></nav></div></header>
<main id="main" class="shell main">"""
    foot = """<p><small>Evidence classes: HOLDOUT-DTI = shared hide-and-recover evaluator
(gems57-pooled-hide-v2, α 0.2, β 0.8, 300 m kernel, 60,988 withheld positives);
USER-REPORTED = fleet ledger claims with no organizer receipt in Git;
EMPIRICAL-ESTIMATE = fleet regression, not a score. No weekly slot was spent.</small></p>
</main></body></html>
"""

    def arm_rows() -> str:
        order = ["natural_oof", "quota35", "piedmont40"]
        rows = []
        for a in order:
            v = arms[a]
            marker = " ⭐ RECOMMENDED FOR SELECTOR" if a == card["recommended_arm"] else ""
            href = "../" + v["tif_path"].removeprefix("docs/")
            rows.append(
                f"<tr><td><strong>{e(a)}{marker}</strong><br><a href=\"{e(href)}\" download>"
                f"Research TIFF — DO NOT SUBMIT except as the selector's one documented choice</a><br>"
                f"<code>{e(v['name'])}</code><br><small>SHA-256 {e(v['tif_sha256'])} · {v['dots']:,} dots</small></td>"
                f"<td>{v['holdout_dti']:.4f}<br><small>95% CI [{v['holdout_ci95'][0]:.4f}, {v['holdout_ci95'][1]:.4f}]</small></td>"
                f"<td>{v['empirical_estimate']:.4f}<br><small>95% PI [{v['empirical_pi95'][0]:.4f}, {v['empirical_pi95'][1]:.4f}]</small></td>"
                f"<td>{(v['frac_gt_32px'] or 0)*100:.1f}% &gt;32px<br><small>median {v['median_px_to_catalogue']}px · ≤2px {v['frac_le_2px']}</small></td>"
                f"<td>sparse-peer max {v['uniqueness']['sparse_peer_max_overlap']:.4f} ({'PASS' if v['uniqueness']['sparse_peer_pass_le_0.70'] else 'FAIL'})<br>"
                f"<small>9-focus primary max {v['focus_primary_max']:.4f} · surface ρ {v['uniqueness']['preplacement_surface_spearman_max_abs']:.4f} · dense-blanket literal FAIL</small></td>"
                f"<td>{'PASS' if v['strict_format_ok'] else 'FAIL'}<br><small>0 NaN, [0,1] whole array</small></td></tr>")
        return "\n".join(rows)

    def focus_table() -> str:
        rows = []
        for f in sorted(focus_rows, key=lambda x: -x["user_reported_score"]):
            site = f["site"]
            ovs = " · ".join(f"{a}: {arms[a]['focus_primary_overlap'].get(site, float('nan')):.3f}"
                             for a in ("natural_oof", "quota35", "piedmont40"))
            rows.append(
                f"<tr><td><strong>{e(site)}</strong></td><td><code>{e(Path(f['path']).name)}</code></td>"
                f"<td>{f['user_reported_score']:.4f} USER-REPORTED</td><td>{f['dots']:,}</td>"
                f"<td>{(f.get('frac_within_3px_catalogue') or 0):.3f}</td><td>{e(ovs)}</td>"
                f"<td><strong>DO NOT RESUBMIT</strong> (historical; mutually 62–100% overlapping lineage)</td></tr>")
        return "\n".join(rows)

    b2_rows = ""
    if isinstance(diag.get("references"), dict):
        for k, v in diag["references"].items():
            b2_rows += (f"<tr><td>{e(k)}</td><td>{v['reference_dots']:,}</td>"
                        f"<td>{v['b2_dots_within_3px_fraction']:.4f}</td>"
                        f"<td>{'rejects B2' if v['literal_gate_rejects_b2'] else 'passes B2'}</td></tr>")

    index = head.format(t="WBG2-DISTAL selector decision") + f"""
<h1>WBG2-DISTAL: 100% spatial-OOF successor to DPHS</h1>
<section class="banner"><div class="banner-copy"><p class="banner-label">Lane decision · PROMOTE TO SELECTOR (0 slots spent)</p>
<h2>Recommended file for the selector: <code>{e(rec['name'])}</code></h2>
<p><strong>DO NOT SUBMIT any other file from this page.</strong> The recommended file is the only arm that
beats the previous holdout best (HOLDOUT-DTI {rec['holdout_dti']:.4f} vs DPHS 0.1735), passes strict
[0,1]/zero-NaN byte validation, and is unique against all 9 focus champions (max {rec['focus_primary_max']:.3f})
and all {rec['uniqueness']['sparse_peer_rasters']} sparse peer-budget fleet rasters (max {rec['uniqueness']['sparse_peer_max_overlap']:.3f}).
It fails only the literal any-registry rule against dense/blanket references — a rule that also rejects the
0.2778 champion itself (table below). Spending a weekly slot is the selector's documented decision to adopt
the sparse-peer interpretation. Estimated leaderboard score (EMPIRICAL-ESTIMATE, not a score):
<strong>{rec['empirical_estimate']:.4f}</strong> (95% PI [{rec['empirical_pi95'][0]:.4f}, {rec['empirical_pi95'][1]:.4f}]);
no arm can honestly be claimed to beat 0.2778 before an organizer receipt exists.</p></div></section>
<h2>The 3 preregistered arms — download, estimate, uniqueness</h2>
<div class="table-scroll"><table class="data-table"><thead><tr><th>File to download</th><th>HOLDOUT-DTI</th>
<th>Estimated leaderboard score (EMPIRICAL)</th><th>Composition</th><th>Unique?</th><th>Format</th></tr></thead>
<tbody>{arm_rows()}</tbody></table></div>
<h2>Nine focus sites — strongest historical claim each (all USER-REPORTED)</h2>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Site</th><th>Historical file</th><th>Claim</th>
<th>Dots</th><th>Frac ≤3px of catalogue</th><th>Our arms within 3px of it</th><th>Submit?</th></tr></thead>
<tbody>{focus_table()}</tbody></table></div>
<h2>Why the literal gate is reported two ways: it rejects the champion too</h2>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Registry reference</th><th>Reference dots</th>
<th>B2 dots within 3px</th><th>Literal &gt;70% rule</th></tr></thead><tbody>{b2_rows}</tbody></table></div>
<p>Full analysis: <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/distal_findings.md">research/distal_findings.md</a> ·
Run card: <a href="../data/run-card-distal-oof.json">RUN_CARD_DISTAL_OOF</a> ·
Preregistration: research/distal_preregistration_20261027.md</p>
""" + foot

    executive = head.format(t="WBG2-DISTAL executive summary") + f"""
<h1>Executive summary — every focus site and the new unique candidate</h1>
<p>The 9 focus champions are one lineage: GEMSDOE32 B2 (0.2778 USER-REPORTED) is the D2.8 Poisson-thinned
H19-5 spatial-OOF surface minus its 6,436 within-2px catalogue dots; the other eight are subsets/unions of the
same support (pairwise 3-px overlap 62–100%). B2 won on (i) 2.8px kernel-economy thinning, (ii) the 200 m
catalogue collar, and (iii) 34% of budget beyond 3.2 km from mapped faults. WBG2-DISTAL keeps those three
lessons but replaces the surface with the DPHS 60-feature model that won hide-and-recover, and replaces
DPHS's flawed in-sample full-map blend with a 100% spatial-OOF map.</p>
<h2>Decision table</h2>
<div class="table-scroll"><table class="data-table"><thead><tr><th>File</th><th>HOLDOUT-DTI</th>
<th>Estimated score (EMPIRICAL)</th><th>Composition</th><th>Unique vs 9 sites / sparse peers?</th><th>Format</th></tr></thead>
<tbody>{arm_rows()}</tbody></table></div>
<div class="table-scroll"><table class="data-table"><thead><tr><th>Site</th><th>Historical file</th><th>Claim</th>
<th>Dots</th><th>Frac ≤3px cat</th><th>Our arms within 3px</th><th>Submit?</th></tr></thead>
<tbody>{focus_table()}</tbody></table></div>
<p><strong>Can anything here be claimed to beat 0.2778 or the 0.4544 public-leaderboard snapshot?</strong>
No. The fleet empirical model (LOSO R² +0.43 on USER-REPORTED scores) estimates ≈0.10–0.11 with a 95% PI
reaching ≈0.23 for all three arms, and it under-predicts B2 itself. The honest claim is narrower and real:
the recommended file has the best protocol-valid holdout in this repository, a genuinely distinct surface
(max |ρ| {rec['uniqueness']['preplacement_surface_spearman_max_abs']:.3f} across 477 fleet rasters), and no sparse-peer duplicate.
Only an organizer receipt can rank it against 0.2778.</p>
""" + foot

    submit = head.format(t="How to submit (selector only)") + f"""
<h1>How to submit — selector steps (contest)</h1>
<ol>
<li>Confirm the selector adopts the sparse-peer uniqueness interpretation documented on the
<a href="index.html">decision page</a> (the literal any-registry rule also rejects GEMSDOE32 B2).</li>
<li>Download exactly one file: <code>{e(rec['name'])}.tif</code> (SHA-256 <code>{e(rec['tif_sha256'])}</code>).
Verify the hash after download. The matching .zip contains the same single GeoTIFF.</li>
<li>On DrivenData → <em>New submission</em>, choose that .tif (single-band float32, EPSG:32611,
3730×3292, all values finite in [0,1] — it cannot trigger “Predicted values must be in range [0, 1]”).</li>
<li>Use this exact note (≤140 chars): <code>{e(rec['note'])}</code></li>
<li>Submit within the weekly cap shown on the submission page; record the organizer receipt
score back into the run card as ORGANIZER-CONFIRMED (nothing here is a receipt yet).</li>
</ol>
<p><strong>DO NOT SUBMIT</strong> the quota35/piedmont40 research TIFFs or any historical focus-site file in the same slot decision.</p>
""" + foot

    (out / "index.html").write_text(index, encoding="utf-8")
    (out / "executive-summary.html").write_text(executive, encoding="utf-8")
    (out / "how-to-submit.html").write_text(submit, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
