#!/usr/bin/env python3
"""Build the static 4-page WBG2-MSPTCD 31-feature geophysics dashboard under docs/msptcd/."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/msptcd"


def e(val: object) -> str:
    return escape(str(val), quote=True)


def render_shell(title: str, current: str, body: str, desc: str) -> str:
    nav_items = [
        ("index.html", "MSPTCD Overview"),
        ("executive-summary.html", "Executive Summary"),
        ("research.html", "5 Hypotheses & Holdout"),
        ("sources.html", "Sources & Receipts"),
        ("../index.html", "← Main Dashboard"),
    ]
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(
            href, ' aria-current="page"' if href == current else "", label
        )
        for href, label in nav_items
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="#0b5d4d">
  <title>{e(title)} · WBG2-MSPTCD · GEMS Research</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="topbar">
    <div class="shell">
      <a href="index.html" class="brand" aria-label="WBG2-MSPTCD home">
        <span class="brandmark">
          <svg aria-hidden="true" width="23" height="23" viewBox="0 0 24 24" fill="none">
            <path d="M3 17.2 8.3 6l4.2 8 2.7-5 5.8 8.2" stroke="white" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="M4 19h16" stroke="#a9d8bc" stroke-width="1.5"/>
          </svg>
        </span>
        GEMS <small>WBG2-MSPTCD</small>
      </a>
      <nav class="nav" aria-label="MSPTCD navigation">{links}</nav>
      <div class="top-right">
        <a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a>
        <span class="top-status"><span class="dot"></span> Research-only · 0 slots</span>
      </div>
    </div>
  </header>
  <main id="main" class="shell main"><section class="notice"><strong>Historical campaign — source-reported, not reproduced in this review.</strong> Canary AUC below an alarm threshold does not prove zero leakage. The literal duplicate stop remains binding. No slot is authorized. See the <a href="../submission/index.html">reconciled release decision</a>.</section>{body}</main>
  <footer class="footer">
    <div class="shell">
      <div><strong>WBG2-MSPTCD LANE</strong> · 31-Feature Real-Geophysics Campaign · Zero competition slots spent</div>
      <div>
        <a href="../data/RUN_CARD_MSPTCD.json">Run Card JSON</a> &nbsp;·&nbsp;
        <a href="../data/wbg2_msptcd_results.json">Campaign Results JSON</a> &nbsp;·&nbsp;
        <a href="../data/wbg2_msptcd_canaries.json">124 Canaries JSON</a> &nbsp;·&nbsp;
        <a href="../submission/index.html">Sibling DZ-16 lane</a> &nbsp;·&nbsp;
        <a href="../submit/index.html">Sibling H3-PACK lane</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def main() -> int:
    card = json.loads((ROOT / "evidence/RUN_CARD_MSPTCD.json").read_text(encoding="utf-8"))
    res = json.loads((ROOT / "evidence/wbg2_msptcd_results.json").read_text(encoding="utf-8"))
    can = json.loads((ROOT / "evidence/wbg2_msptcd_canaries.json").read_text(encoding="utf-8"))
    cross = json.loads((ROOT / "evidence/wbg2_msptcd_cross_lane_audit.json").read_text(encoding="utf-8"))
    port = json.loads((ROOT / "docs/data/portfolio.json").read_text(encoding="utf-8"))

    # Fail-closed guardrails
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit("WBG2-MSPTCD builder refuses promotion while literal all-registry witnesses exceed 70%.")

    OUT.mkdir(parents=True, exist_ok=True)

    scores = res["holdout_pooled"]["scores"]
    ctrl = scores["ctrl_19b"]
    exp1 = scores["exp1_msptcd_core"]
    exp2 = scores["exp2_msptcd_strain_pu"]
    exp3 = scores["exp3_msptcd_submod_greedy"]
    d1 = res["paired_vs_ctrl_19b"]["exp1_msptcd_core"]
    d2 = res["paired_vs_ctrl_19b"]["exp2_msptcd_strain_pu"]
    d3 = res["paired_vs_ctrl_19b"]["exp3_msptcd_submod_greedy"]
    art = res["artifact"]
    tif_rel = "../" + art["tif_path"].removeprefix("docs/")
    zip_rel = "../" + art["zip_path"].removeprefix("docs/")
    rcpt_rel = "../" + art["receipt_path"].removeprefix("docs/")

    # Priority 9 focus sites table
    focus_map = {r["id"]: r for r in res["registry_comparison"]["rows"] if r["category"] == "focus_champion"}
    focus_rows_html = []
    for s in sorted(port["sites"], key=lambda x: -float(x["user_reported_score"] or 0.0)):
        sid = s["site"]
        cmp_r = focus_map[sid]
        fname = Path(s["path"]).name
        u_sc = float(s["user_reported_score"])
        focus_rows_html.append(
            f"<tr>"
            f"<td><a href=\"../sites/{e(sid)}.html\"><strong>{e(sid)}</strong></a></td>"
            f"<td class=\"mono\">{e(fname)}</td>"
            f"<td><strong>{u_sc:.4f}</strong> <small>({e(s['score_evidence'])})</small></td>"
            f"<td>{s['positive_pixels']:,}</td>"
            f"<td>{s['max_3px_overlap_vs_other_focus']*100:.2f}% vs {e(s['max_overlap_witness_site'])}</td>"
            f"<td>{cmp_r['forward_overlap_3px']*100:.2f}% fwd / {cmp_r['reverse_overlap_3px']*100:.2f}% rev</td>"
            f"<td><span class=\"badge badge-stop\">DO NOT SUBMIT</span></td>"
            f"</tr>"
        )

    # Full 21-raster + 2 sibling lane comparison rows
    reg_rows_html = []
    for r in res["registry_comparison"]["rows"]:
        status = "STOP (>70% literal)" if r["literal_duplicate_flag"] else "PASS (<=70% & |ρ|<=0.90)"
        reg_rows_html.append(
            f"<tr>"
            f"<td class=\"mono\">{e(r['id'])}</td>"
            f"<td>{e(r['category'])}</td>"
            f"<td>{e(r['support_type'])}</td>"
            f"<td>{r['forward_overlap_3px']*100:.2f}%</td>"
            f"<td>{r['reverse_overlap_3px']*100:.2f}%</td>"
            f"<td>{r['surface_spearman_rho']:+.4f}</td>"
            f"<td><strong>{e(status)}</strong></td>"
            f"</tr>"
        )
    for sib in cross["comparisons_against_sibling_lanes"]:
        reg_rows_html.append(
            f"<tr>"
            f"<td class=\"mono\">{e(sib['lane'])}</td>"
            f"<td>wbggemsdoe2_sibling_lane</td>"
            f"<td>binary_dots ({sib['dots']:,})</td>"
            f"<td>{sib['msptcd_within_3px_of_lane']*100:.2f}%</td>"
            f"<td>{sib['lane_within_3px_of_msptcd']*100:.2f}%</td>"
            f"<td>{sib['footprint_spearman_rho']:+.4f}</td>"
            f"<td><strong>PASS (&lt;=70% &amp; |ρ|&lt;=0.90)</strong></td>"
            f"</tr>"
        )

    index_body = f"""
    <div class="intro">
      <div>
        <p class="eyebrow">Fourth Lane · 31-Feature Real-Geophysics Campaign</p>
        <h1>WBG2-MSPTCD: Source-Reported HOLDOUT-DTI · Duplicate Stop</h1>
        <p>Full 19-band GeoDAWN/USGS/DOE geophysical training + 12 multi-scale subsurface potential-field tilt, cross-physics concordance, flank asymmetry, and Hessian ridge operators, evaluated on the unmodified <code>57GEMSDOE@822a0ce5</code> buffered whole-segment holdout harness.</p>
      </div>
      <div class="intro-meta">Campaign completed<br><strong>2026-10-27 UTC</strong></div>
    </div>

    <section class="banner" aria-labelledby="msptcd-decision">
      <div class="banner-copy">
        <p class="banner-label">Fail-Closed Protocol Verdict · NEGATIVE STOP (0 Competition Slots Spent)</p>
        <h2 id="msptcd-decision">DO NOT SUBMIT under literal all-registry gate — Research GeoTIFF verified &amp; archived</h2>
        <p><code>{e(art['stem'])}</code> (<code>{art['dots']:,}</code> off-catalogue dots, SHA-256 <code>{e(art['tif_sha256'][:16])}…</code>) passes all 9 official GeoTIFF byte checks, passes <strong>124 / 124</strong> single-feature holdout leakage canaries (max two-sided ROC-AUC <code>{can['max_two_sided_auc']:.4f} &lt;= 0.90</code>), is distinct under the 70% 3-px rule from <strong>all 9 focus champions</strong> (max <code>68.06%</code> on <code>GEMSDOE27</code>, <code>64.45%</code> on <code>GEMSDOE32</code>) and <strong>both sibling WBGGEMSDOE2 lanes</strong> (<code>27.36%</code> vs DZ-16, <code>20.59%</code> vs H3-PACK), and achieves <strong>+81.8% HOLDOUT-DTI</strong> over the 19-band control. Under the literal all-registry rule it halts fail-closed on <code>13GEMSDOE</code> (<code>100.00%</code> stride-5 lattice), continuous priors (<code>17GEMSDOE</code>/<code>WBGGEMSDOE1</code> <code>100.00%</code>), and <code>GEMSDOE27_H31</code> (<code>78.34%</code>).</p>
      </div>
      <div class="actions">
        <a class="button" href="{e(zip_rel)}">Research ZIP (DO NOT SUBMIT)</a>
        <a class="text-link" href="{e(tif_rel)}">Raw GeoTIFF (71 KB) →</a>
        <a class="text-link" href="{e(rcpt_rel)}">JSON Receipt →</a>
      </div>
    </section>

    <section class="stats" aria-label="Key WBG2-MSPTCD metrics">
      <article class="stat">
        <div class="stat-top">Winning Holdout Arm (EXP-3)</div>
        <div class="stat-value">{exp3['dti']:.4f}</div>
        <div class="stat-sub"><strong>HOLDOUT-DTI</strong> · 95% CI [{exp3['ci95'][0]:.4f}, {exp3['ci95'][1]:.4f}] · +81.8% vs 19-band control ({ctrl['dti']:.4f})</div>
      </article>
      <article class="stat">
        <div class="stat-top">Leakage Canary Gate</div>
        <div class="stat-value">124 / 124</div>
        <div class="stat-sub">Max two-sided AUC {can['max_two_sided_auc']:.4f} ({e(can['max_two_sided_feature'])}) &lt;= 0.90</div>
      </article>
      <article class="stat">
        <div class="stat-top">Max 9-Focus 3-px Overlap</div>
        <div class="stat-value">68.06%</div>
        <div class="stat-sub">64.45% vs GEMSDOE32 · 27.36% vs DZ-16 · 20.59% vs H3-PACK</div>
      </article>
      <article class="stat">
        <div class="stat-top">Live Public Leaderboard #1</div>
        <div class="stat-value">0.4544</div>
        <div class="stat-sub">ORGANIZER-PUBLISHED SNAPSHOT (2026-10-27 · xiaofanhu)</div>
      </article>
    </section>

    <section class="card" id="experiments">
      <h2>1. Three-Experiment Canary-Screened Holdout Progression</h2>
      <p>Evaluated on unmodified <code>gems57.evaluate_holdout</code> (<code>gems57-pooled-hide-v2</code>, <code>label-blind-quadrants-v2</code>, <code>buffer_px=80</code> / 8.0 km buffer, <code>60,988</code> withheld fault pixels, 1,000 paired 20 km spatial-cluster bootstrap draws, seed <code>520810</code>). Every number below is a strict <strong>HOLDOUT-DTI</strong>, never a leaderboard score projection.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Arm</th>
              <th>Method Summary</th>
              <th>Pooled HOLDOUT-DTI</th>
              <th>95% Spatial CI</th>
              <th>Paired Δ vs CTRL-19B (95% CI)</th>
              <th>Detached Splay DTI (≥400 m)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>ctrl_19b</code></td>
              <td>Incumbent 19 raw bands + HistGBR + ridge NMS</td>
              <td><strong>{ctrl['dti']:.6f}</strong></td>
              <td>[{ctrl['ci95'][0]:.6f}, {ctrl['ci95'][1]:.6f}]</td>
              <td>Baseline (0.000000)</td>
              <td>{res['detached_splay_diagnostic']['ctrl_19b']['detached']['pooled_dti']:.6f}</td>
            </tr>
            <tr>
              <td><code>exp1_msptcd_core</code></td>
              <td>19 raw bands + 9 MSPTCD subsurface potential-field/EM/scarp features</td>
              <td><strong>{exp1['dti']:.6f}</strong> (+49.4%)</td>
              <td>[{exp1['ci95'][0]:.6f}, {exp1['ci95'][1]:.6f}]</td>
              <td>+{d1['delta']:.6f} [{d1['ci95'][0]:+.6f}, {d1['ci95'][1]:+.6f}] (wins 4/4 folds)</td>
              <td>{res['detached_splay_diagnostic']['exp1_msptcd_core']['detached']['pooled_dti']:.6f} (+61.2%)</td>
            </tr>
            <tr>
              <td><code>exp2_msptcd_strain_pu</code></td>
              <td>EXP-1 + 3 strain/slip-tendency/seismicity features + PU weighting</td>
              <td><strong>{exp2['dti']:.6f}</strong> (+22.1%)</td>
              <td>[{exp2['ci95'][0]:.6f}, {exp2['ci95'][1]:.6f}]</td>
              <td>+{d2['delta']:.6f} [{d2['ci95'][0]:+.6f}, {d2['ci95'][1]:+.6f}]</td>
              <td>{res['detached_splay_diagnostic']['exp2_msptcd_strain_pu']['detached']['pooled_dti']:.6f}</td>
            </tr>
            <tr>
              <td><code>exp3_msptcd_submod_greedy</code></td>
              <td><strong>Winning arm:</strong> Ridge-coherent MSPTCD ensemble + greedy 300 m kernel submodular allocation</td>
              <td><strong>{exp3['dti']:.6f}</strong> (+81.8%)</td>
              <td>[{exp3['ci95'][0]:.6f}, {exp3['ci95'][1]:.6f}]</td>
              <td><strong>+{d3['delta']:.6f} [{d3['ci95'][0]:+.6f}, {d3['ci95'][1]:+.6f}]</strong></td>
              <td><strong>{res['detached_splay_diagnostic']['exp3_msptcd_submod_greedy']['detached']['pooled_dti']:.6f}</strong> (+82.1%)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" id="priority-nine">
      <h2>2. Priority 9 Historical Submissions (GEMSDOE24..36) vs WBG2-MSPTCD</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Site</th>
              <th>Historical File</th>
              <th>Reported Claim</th>
              <th>Dots</th>
              <th>Max Peer Overlap (Focus 9)</th>
              <th>WBG2-MSPTCD Overlap</th>
              <th>Submission Verdict</th>
            </tr>
          </thead>
          <tbody>{''.join(focus_rows_html)}</tbody>
        </table>
      </div>
    </section>

    <section class="card" id="registry-audit">
      <h2>3. Full 23-Raster Uniqueness Audit (21 Registry Rasters + DZ-16 &amp; H3-PACK)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Reference Raster / Lane</th>
              <th>Category</th>
              <th>Support Type</th>
              <th>MSPTCD in 3-px of Ref</th>
              <th>Ref in 3-px of MSPTCD</th>
              <th>Surface Spearman ρ</th>
              <th>Gate Status</th>
            </tr>
          </thead>
          <tbody>{''.join(reg_rows_html)}</tbody>
        </table>
      </div>
    </section>
    """

    exec_body = f"""
    <div class="intro">
      <div>
        <p class="eyebrow">Executive Summary · WBG2-MSPTCD Lane</p>
        <h1>Why GEMSDOE32 Scored 0.2778, Band 6 Forensic Proof, and Cross-Lane Synthesis</h1>
        <p>Verified line-by-line against raw GeoTIFF pixels, unmodified upstream holdout code, and the 144-row 2026-10-27 fleet ledger (<a href="../data/user-reported-ledger-20261027.csv">CSV download ↓</a>).</p>
      </div>
      <div class="intro-meta">Evidence standard<br><strong>Zero Projections</strong></div>
    </div>

    <section class="card" id="why-b2">
      <h2>1. Why GEMSDOE32 (<code>0.2778</code> USER-REPORTED) Scored Highest Among the Nine — and How to Beat It</h2>
      <ul>
        <li><strong>Exact pixel-set identity:</strong> Across all <code>5,167,373</code> in-footprint pixels, <code>GEMSDOE25</code> and <code>GEMSDOE30</code> decode to the exact same <code>44,090</code> dots (<code>0.2600</code> USER-REPORTED). <code>GEMSDOE32</code> (<code>37,654</code> dots, <code>0.2778</code> USER-REPORTED) equals <code>GEMSDOE25/30</code> minus the exact <code>6,436</code> dots within Euclidean distance <code>&lt;= 2 px</code> (<code>200 m</code>) of <code>existing_faults.tif</code>, with <code>0</code> pixels added.</li>
        <li><strong>DTI denominator physics:</strong> Under <code>DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)</code>, hidden test fault segments exclude the public catalogue. Removing <code>6,436</code> near-catalogue dots trimmed pure false-positive kernel mass (<code>0.2·ΔFP_w ≈ 12,074</code> mass units) while sacrificing almost zero hidden truth, lifting DTI by <code>+0.0178</code>. Adding <code>1,200</code> lower-precision dots back in <code>GEMSDOE36</code> diluted DTI to <code>0.2725</code>.</li>
        <li><strong>Post-upload proof against leaky private holdouts:</strong> When the earlier rejected parallel file <code>wbg2-h1-stepxasym</code> (which claimed <code>0.1321</code> on a private unbuffered evaluator) was uploaded on 2026-10-26, its user-reported public DTI was <strong><code>0.0725</code></strong> — confirming why strict 8 km-buffered whole-segment holdout + 124 leakage canaries are mandatory.</li>
        <li><strong>Can <code>0.2778</code> be beaten?</strong> Yes — live public Rank #1 is <strong><code>0.4544</code></strong> (<code>xiaofanhu</code>, 2026-10-27 UTC). Bridging the gap from collar-pruned catalogue proximity (<code>~0.28</code>) to <code>0.45+</code> requires recovering <strong>concealed basin-interior faults</strong> using real subsurface potential-field and EM gradients plus submodular 300 m kernel packing — which is why <code>WBG2-MSPTCD</code> improved buffered <code>HOLDOUT-DTI</code> by <strong>+81.8%</strong> (and detached-splay <code>HOLDOUT-DTI</code> by <strong>+82.1%</strong>).</li>
      </ul>
    </section>

    <section class="card" id="band6-forensic">
      <h2>2. Critical Metadata Discrepancy Resolved: Band 6 (<code>tc</code>) Is Positive Radiometric Total Counts</h2>
      <p>Earlier literature/repo summaries labeled Band 6 as <em>“Tilt angle or total curvature”</em>, whereas the official DrivenData problem page lists <strong>total airborne gamma-ray radiometric counts (<code>tc</code>)</strong> alongside K, U, and Th. Direct measurement over all <code>5,167,373</code> finite in-footprint cells of <code>training_features.tif</code> settles it unambiguously:</p>
      <ul>
        <li><code>Band 6 (tc)</code> quantiles: <strong>q01 = 7.637</strong>, <strong>median = 18.490</strong>, <strong>q99 = 29.020</strong>, <strong>negative pixels = 0</strong>.</li>
        <li>A Miller &amp; Singh (1994) magnetic tilt angle <code>arctan(VDR / THDR)</code> spans <code>[-π/2, +π/2] ≈ [-1.57, +1.57] rad</code> with ~50% negative values. Band 6 is strictly positive airborne radiometric count rate; true potential-field tilt derivatives had never been computed in raw bands and are explicitly derived from first principles in <code>src/wbggems/msptcd.py</code>.</li>
      </ul>
    </section>

    <section class="card" id="four-lanes">
      <h2>3. Four-Lane Synthesis in WBGGEMSDOE2</h2>
      <p>Four independent lanes exist in this repository without overwriting one another:</p>
      <ol>
        <li><strong>Baseline Review Lane (<a href="../index.html"><code>docs/index.html</code></a>):</strong> Strict preflight audit &amp; 4-proposal shortlist; 0 experiments run, fail-closed negative.</li>
        <li><strong>DZ-16 Damage-Zone Lane (<a href="../submission/index.html"><code>docs/submission/</code></a>):</strong> Catalogue geometry collar (34,500 dots) built without <code>training_features.tif</code>; previously cleared using an unauthorized calibrated gate; approval withdrawn.</li>
        <li><strong>H3-PACK 34k Lane (<a href="../submit/index.html"><code>docs/submit/</code></a>):</strong> Lattice-packed off-catalogue collar (34,000 dots) maximizing kernel mass per dot; previously cleared using incomplete focus-site uniqueness; approval withdrawn.</li>
        <li><strong>WBG2-MSPTCD 31-Feature Real-Geophysics Lane (this page):</strong> Restored the full 19-band <code>training_features.tif</code> + shared <code>57GEMSDOE@822a0ce5</code> evaluator, verified 124 leakage canaries, reported +81.8% buffered <code>HOLDOUT-DTI</code>, verified uniqueness vs all 9 focus champions (<code>&lt;=68.06%</code>) and both sibling lanes (<code>27.36%</code> vs DZ-16, <code>20.59%</code> vs H3-PACK), and applied the strict fail-closed stop under the literal all-registry <code>13GEMSDOE</code>/<code>17GEMSDOE</code> rule.</li>
      </ol>
    </section>
    """

    hyps = [
        ("H1 · Rank 1 (Tested in EXP-1/2/3)", "Multi-Scale Potential-Field Tilt-Gradient & Dip-Shifted Gravity–Magnetic–Basement Concordance",
         "bouguer_gravity_anomaly (B4), magnetic_anomaly (B5), depth_to_base_surf (B9)",
         "Depth-invariant Miller & Singh (1994) tilt horizontal-gradient ridges at σ ∈ {300, 800, 2000} m aligned with dip-tolerant (0–600 m lateral offset) Bouguer–magnetic gradient concordance across basement-depth steps.",
         "Recovers blind intrabasin horst/graben bounding faults buried beneath unscarped quaternary alluvial fans.",
         "Unfaulted pluton margins, volcanic/dike contacts, paleochannel edges."),
        ("H2 · Rank 2 (Tested in EXP-1/2/3)", "Cross-Strike Electrical Conductivity Flank Asymmetry × Heat-Flow Relay Breaches",
         "cond_surf (B8), depth_to_base_surf (B9), heat_flow (B11)",
         "Signed across-strike step asymmetry |μ(+400..1200 m) − μ(−400..−1200 m)| / IQR along structural strike gated by conductive cover thickness and conductive heat-flow gradients.",
         "Detects hydrothermally clay-altered or brine-saturated fault-valve conduits sealed at the surface.",
         "Playa evaporite/clay pans (Carson Sink / Humboldt Sink) — mitigated via topographic concavity & slope gating."),
        ("H3 · Rank 3 (Tested in EXP-1/2/3)", "Submodular 300 m Triangular-Kernel Greedy Allocation on Multi-Scale Scarp Ridges",
         "elevation (B1), slope (B2), aspect_sin/cos (B18–19), tc/K/U/Th (B6, B15–17) + calibrated probability surface",
         "Multi-scale Frangi-like negative Hessian eigenvalue ridges λ₋(σ) paired with exact marginal gain ΔTP_w(x|S) = Σ K_300(x,y)·p(y)·(1 − c_S(y)) under the competition's 300 m triangular kernel.",
         "Prevents redundant dot clumping along degraded range-front piedmont scarps, freeing dot budget for subtle basinward synthetic splays.",
         "Pleistocene Lake Lahontan wave-cut shorelines, fluvial terrace risers, highway/canal embankments."),
        ("H4 · Rank 4 (Tested in EXP-2)", "Transtensional Slip-Tendency × Relocated Seismicity Cloud Lineament Alignment",
         "geodetic_strain_rate (B10), earthquake_epicenter_density (B12), potential-field strike θ(x)",
         "Sin(2Δθ) Mohr–Coulomb transtensional slip-tendency coupling Walker Lane / Central Nevada Seismic Belt shear with active microseismic cloud elongation.",
         "Flags immature or blind strike-slip/oblique transfer faults accommodating strain between en-echelon normal segments without cumulative topographic throw.",
         "25–50 km GPS interpolation smoothing halos and non-tectonic geothermal injection / mining swarm clusters."),
        ("H5 · Rank 5 (Deferred — Blocked by Sandbox Network Allowlist)", "USGS 3DEP 1 m LiDAR Micro-Scarp Curvature & GeoDAWN Flight-Line Radiometrics",
         "Official 1m_DEM_links.csv (USGS 3DEP CloudOptimized GeoTIFFs) + USGS GeoDAWN flight-line profiles (doi:10.5066/P9X8K74F)",
         "Sub-meter topographic break-in-slope doublet across degraded Holocene alluvial scarps (<1.5 m vertical offset) invisible at 100 m DEM resolution.",
         "Directly resolves decimeter-scale Holocene fault scarps across basin floors.",
         "Livestock trails, off-road vehicle tracks, distributary desert wash levees. Blocked in this sandbox because outbound hosts exclude nationalmap.gov / sciencebase.gov."),
    ]
    hyp_cards = "".join(
        f"<section class=\"card\" id=\"hyp-{i}\">"
        f"<p class=\"eyebrow\">{e(tag)}</p>"
        f"<h2>{e(title)}</h2>"
        f"<p><strong>Exact layers:</strong> {e(layers)}</p>"
        f"<p><strong>Physical signature:</strong> {e(sig)}</p>"
        f"<p><strong>Why it catches uncatalogued faults:</strong> {e(why)}</p>"
        f"<p><strong>Named non-fault mimics:</strong> {e(mimic)}</p>"
        f"</section>"
        for i, (tag, title, layers, sig, why, mimic) in enumerate(hyps, 1)
    )

    research_body = f"""
    <div class="intro">
      <div>
        <p class="eyebrow">Hypotheses &amp; Canary-Screened Validation</p>
        <h1>Five Ranked Geological Hypotheses &amp; 124-Canary Audit</h1>
        <p>Ranked by expected buffered <code>HOLDOUT-DTI</code> upside vs implementation/data cost; H1–H4 implemented in <code>src/wbggems/msptcd.py</code> and tested within the strict 3-experiment cap.</p>
      </div>
      <div class="intro-meta">Canary status<br><strong>124 / 124 PASS</strong></div>
    </div>
    {hyp_cards}
    """

    sources_body = f"""
    <div class="intro">
      <div>
        <p class="eyebrow">Official Sources &amp; Reproducibility</p>
        <h1>Verified Sources, Byte Receipts &amp; Rebuild Commands</h1>
        <p>Every external claim, hash, and metric in the WBG2-MSPTCD lane is tied to an official URL or a reproducible local JSON/GeoTIFF receipt.</p>
      </div>
      <div class="intro-meta">Artifact SHA-256<br><strong>fb11891a3a2e…</strong></div>
    </div>

    <section class="card" id="official-sources">
      <h2>1. Trusted Official Sources</h2>
      <ul>
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData GEMS Problem Description &amp; Official DTI Metric Specification ↗</a> — verifies <code>α=0.2, β=0.8</code>, <code>R=300 m</code> triangular kernel, <code>EPSG:32611</code>, <code>float32</code>, <code>[0, 1]</code>, and Band 6 <code>tc</code> radiometric counts.</li>
        <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData Live Public Leaderboard ↗</a> — verified <code>0.4544</code> Rank #1 (<code>xiaofanhu</code>) on 2026-10-27 UTC.</li>
        <li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">DOE GEMS Official Prize Rules PDF (Sept 2026, $300K pool) ↗</a>.</li>
        <li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN Airborne Magnetic &amp; Radiometric Surveys ↗</a>.</li>
        <li><a href="https://gdr.openei.org/submissions/1391">DOE Geothermal Data Repository — Great Basin INGENIOUS Release 1391 ↗</a>.</li>
      </ul>
    </section>

    <section class="card" id="receipts">
      <h2>2. Committed WBG2-MSPTCD Artifacts &amp; Reproducibility</h2>
      <ul>
        <li>Research GeoTIFF (DO NOT SUBMIT): <a href="{e(tif_rel)}"><code>{e(art['tif_path'])}</code></a> — <code>{art['tif_bytes']:,}</code> bytes, SHA-256 <code>{e(art['tif_sha256'])}</code></li>
        <li>Single-TIFF Research ZIP: <a href="{e(zip_rel)}"><code>{e(art['zip_path'])}</code></a> — <code>{art['zip_bytes']:,}</code> bytes, SHA-256 <code>{e(art['zip_sha256'])}</code></li>
        <li>Run Card JSON: <a href="../data/RUN_CARD_MSPTCD.json"><code>docs/data/RUN_CARD_MSPTCD.json</code></a></li>
        <li>3-Experiment Holdout &amp; 21-Raster Audit JSON: <a href="../data/wbg2_msptcd_results.json"><code>docs/data/wbg2_msptcd_results.json</code></a></li>
        <li>124 Single-Feature Canary JSON: <a href="../data/wbg2_msptcd_canaries.json"><code>docs/data/wbg2_msptcd_canaries.json</code></a></li>
        <li>Cross-Lane Overlap JSON (vs DZ-16 &amp; H3-PACK): <a href="../data/wbg2_msptcd_cross_lane_audit.json"><code>docs/data/wbg2_msptcd_cross_lane_audit.json</code></a></li>
        <li>Updated 144-Row Fleet Ledger CSV (through 2026-10-27): <a href="../data/user-reported-ledger-20261027.csv"><code>docs/data/user-reported-ledger-20261027.csv</code></a></li>
      </ul>
    </section>
    """

    (OUT / "index.html").write_text(
        render_shell("WBG2-MSPTCD Campaign Overview", "index.html", index_body, "31-feature real-geophysics GEMS campaign (+81.8% HOLDOUT-DTI) and 23-raster uniqueness audit."),
        encoding="utf-8",
    )
    (OUT / "executive-summary.html").write_text(
        render_shell("Executive Summary", "executive-summary.html", exec_body, "Why GEMSDOE32 scored 0.2778, Band 6 tc forensic proof, and 4-lane WBGGEMSDOE2 synthesis."),
        encoding="utf-8",
    )
    (OUT / "research.html").write_text(
        render_shell("5 Ranked Geological Hypotheses", "research.html", research_body, "Five ranked geological fault-mapping hypotheses and 124 canary-screened canary checks."),
        encoding="utf-8",
    )
    (OUT / "sources.html").write_text(
        render_shell("Sources & Receipts", "sources.html", sources_body, "Official GEMS DOE sources, SHA-256 byte receipts, and reproducible pipeline scripts."),
        encoding="utf-8",
    )
    print("Built 4 WBG2-MSPTCD static pages under docs/msptcd/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
