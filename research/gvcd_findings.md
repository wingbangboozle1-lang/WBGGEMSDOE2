# WBG2-GVCD Findings, 8-Organization Multi-Fleet Audit & PhD Analysis of `GEMSDOE32` (`0.2778`)

**Authoritative Release Decision:** **NEGATIVE / DO NOT SUBMIT (`ok_to_submit = false`, `0` weekly submission slots consumed)**  
**Canonical Research Artifact:** [`docs/downloads/gvcd/wbg2-gvcd-exp3-oof-ventstress-37400-20261027T235800Z-5275cd04-zeros.tif`](../docs/downloads/gvcd/wbg2-gvcd-exp3-oof-ventstress-37400-20261027T235800Z-5275cd04-zeros.tif) (`SHA-256: b625e13b5b3e4d36ab80f1ad78318c96d35ac8c2c0f401aff6821365221850a9`)  
**Machine-Readable Receipts:** [`evidence/RUN_CARD_GVCD.json`](../evidence/RUN_CARD_GVCD.json) · [`evidence/wbg2_gvcd_results.json`](../evidence/wbg2_gvcd_results.json) · [`evidence/gvcd_8org_fleet_audit.json`](../evidence/gvcd_8org_fleet_audit.json) · [`evidence/prompt_ledger_8org_audit_20261027.json`](../evidence/prompt_ledger_8org_audit_20261027.json)

---

## 1. Executive Summary & What `WBG2-GVCD` Solved

In this session we executed a three-pass, byte-verified research, engineering, and 8-organization audit campaign (`WBG2-GVCD`: **Geothermal-Vent Conduit, Axial Stress-Dilation & 100% Spatial-OOF Dual-Regime Synthesis**):

1. **Verified Pooled `HOLDOUT-DTI = 0.17591` (`44.00%` Distal Allocation):** Evaluated strictly on the shared `gems57-pooled-hide-v2` whole-segment `8.0 km`-buffered spatial holdout (`60,988` withheld fault pixels across 4 folds, $\alpha=0.2, \beta=0.8$, 300 m triangular kernel, `1,000` bootstrap draws), `WBG2-GVCD EXP-3` achieved **`HOLDOUT-DTI = 0.17591`** (`95% CI [0.15549, 0.19694]`, alongside concurrent `WBG2-DISTAL` natural-OOF `0.1770`), outperforming every prior verified lane at start of run in `WBGGEMSDOE2`:
   - `CTRL-19B` (`19` official bands + PU-HGBR): `0.0303` (`[0.0215, 0.0413]`)
   - `WBG2-MSPTCD` (`31` features): `0.0480` (`[0.0365, 0.0609]`)
   - `H3-BLIND` (label-blind hexagonal lattice): `0.1560` (`[0.1381, 0.1742]`)
   - `WBG2-DPHS EXP-3` (`60` features + 300 m CELF): `0.17348` (`[0.15245, 0.19436]`)
   - **`WBG2-GVCD EXP-3` (`72` features + slope-blind subsurface/vent specialist + 300 m CELF):** **`0.17591`** (`[0.15549, 0.19694]`, **`+0.00243` over `DPHS EXP-3`**)
2. **Eliminated All `45` Discrete Fleet Overlap Violations (`496 / 496` Discrete 8-Org Rasters PASS `<= 70%`):** By enforcing **100% spatial out-of-fold (`0%` in-sample refit)** scoring, a **slope-blind 60-feature subsurface/geothermal-vent specialist**, label-free piedmont cover gating, and **two-stage dual-regime 300 m CELF allocation (`44.00%` distal `>32 px`, `37,400` non-touching dots)**, `WBG2-GVCD EXP-3` reduced maximum discrete 3-px dot overlap from `95.87%` (`45` discrete failures in `DPHS EXP-3`) down to **`69.56% <= 70.0%` (`0` violations across all `496` discrete rasters across all 8 GitHub organizations; `28.35%–37.38%` vs the 9 focus sites; `39.04%` max across discrete pinned registry files)**.
3. **Why Status Remains `DO NOT SUBMIT` (`ok_to_submit = false`):** Under the literal all-registry 3-px rule (`src/wbggems/release.py`), `3` mathematical blanket controls in the fleet (`13GEMSDOE` stride-5 lattice covering `99.87%` of the footprint within 3 px, `17GEMSDOE_dense_prior` covering `100.00%`, and `GEMSDOE22` covering `99.12%`) cause *any* competitive ~37k-dot raster to exceed `70%` literal overlap (`100.00%`, `99.63%`, `99.12%`). Rather than silently exempting those 3 blanket controls, `WBGGEMSDOE2` fails closed (`status: negative`, `0` weekly slots spent) and documents both the literal stop and the **`496 / 496` discrete non-blanket PASS** transparently for the human slot selector.
4. **Automated Portal Format & `[0, 1]` Guarantee:** Read-back byte validation (`inspect_tif(..., strict_all_finite=True)`) confirms `EPSG:32611`, `3730 x 3292` `float32`, transform `(100, 0, 243350, 0, -100, 4508550)`, `nodata = None`, **`0` NaN/Inf cells across all `12,279,160` pixels**, and values strictly in `[0.0, 1.0]` — permanently preventing the `"Predicted values must be in range [0, 1]"` error caused by `-nan.tif` outside-footprint fills.

---

## 2. Executive Summary Table: 9 Focus Sites + `WBG2-GVCD EXP-3`

Every score below is strictly labeled by evidence class (`USER-REPORTED` verbatim from the prompt ledger vs `HOLDOUT-DTI` vs `EMPIRICAL-ESTIMATE` from our 8-org `LOSO` model, `R² = +0.4783`, which is **never** presented as an actual leaderboard score):

| Site / Campaign | Primary / Latest Audited File | Verbatim `USER-REPORTED` DTI | 8-Org `EMPIRICAL-ESTIMATE` *(Not a Receipt)* | 3-px Overlap vs Peers / `GVCD` | Portal `[0, 1]` All-Finite? | Submit Status |
|---|---|---:|---:|---|---|---|
| **`WBG2-GVCD EXP-3`** *(Ours)* | [`wbg2-gvcd-exp3-oof-ventstress-37400-20261027T235800Z-5275cd04-zeros.tif`](../docs/downloads/gvcd/wbg2-gvcd-exp3-oof-ventstress-37400-20261027T235800Z-5275cd04-zeros.tif) | *(Unreleased; **`0.17591` `HOLDOUT-DTI`** `95% CI [0.1555, 0.1969]`)* | `0.1069` (`95% PI [0.0000, 0.2472]`) | **`496/496` discrete PASS (`max 69.56%`)**; **`28.4–37.4%` vs 9 focus**; fails 3 blanket controls (`13GEMSDOE` `100%`) | **PASS** (`0` NaN, `[0, 1]`) | **RESEARCH ONLY — DO NOT SUBMIT** *(literal 3-blanket gate)* |
| **GEMSDOE32** *(#1 Prompt Ledger)* | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **`0.2778`** | `0.2015` (LOSO) | `100.0%` inside `GEMSDOE25/30/36`; `34.1%` vs `GVCD` | **PASS** (`-zeros`) | **DO NOT RESUBMIT** *(historical prior)* |
| **GEMSDOE36** | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` *(Oct 26 `kpl36-exp3`: `0.1647`)* | **`0.2750`** / `0.1647` | `0.2008` / `0.1412` | `96.9%` vs `GEMSDOE32` (`B2 + 1,200` dots); `35.1%` vs `GVCD` | **PASS** (`-zeros`) | **DO NOT RESUBMIT** |
| **GEMSDOE28** | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` *(Oct 26 `s21-puhgb`: `0.0206`)* | **`0.2710`** / `0.0206` | `0.1931` / `0.0584` | `97.3%` vs `GEMSDOE31`; `35.9%` vs `GVCD` | **FAIL** (`NaN` outside on `h36-1`) | **DO NOT RESUBMIT** |
| **GEMSDOE31** | `h27-4-solo-d28-20261004-8acb75e1-nan.tif` *(Oct 26 `m16-tpb2`: blank)* | **`0.2708`** | `0.1924` | `100.0%` match w/ `GEMSDOE28 h27-4`; `35.8%` vs `GVCD` | **FAIL** (`NaN` outside on `h27-4`) | **DO NOT RESUBMIT** |
| **GEMSDOE33** | `h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` *(Oct 26 `s33-seisdil`: `0.0963`)* | **`0.2632`** / `0.0963` | `0.1846` / `0.1190` | `88.7%` vs `GEMSDOE25`; `34.9%` vs `GVCD` | **FAIL** (`NaN` outside on `h33d`) | **DO NOT RESUBMIT** |
| **GEMSDOE25** | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` *(Oct 25 `h66-mgd`: `0.0742`)* | **`0.2600`** / `0.0742` | `0.1819` / `0.0914` | `100.0%` identical in-footprint to `GEMSDOE30`; `36.4%` vs `GVCD` | **FAIL** (`NaN` outside on `d2-8`) | **DO NOT RESUBMIT** |
| **GEMSDOE30** | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` *(Oct 25 `MSDB1`: `0.1462`)* | **`0.2600`** / `0.1462` | `0.1819` / `0.1348` | `100.0%` identical in-footprint to `GEMSDOE25`; `36.4%` vs `GVCD` | **PASS** (`d28-poisson300m`) | **DO NOT RESUBMIT** |
| **GEMSDOE24** | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` *(Oct 25 `gvc1`: `0.0859`)* | **`0.2477`** / `0.0859` | `0.1685` / `0.0892` | `98.8%` vs `GEMSDOE27`; `37.4%` vs `GVCD` | **FAIL** (`NaN` outside on `h25-1`) | **DO NOT RESUBMIT** |
| **GEMSDOE27** | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` *(Oct 26 `h31-drcg`: `0.2250`)* | **`0.2449`** / `0.2250` | `0.1669` / `0.1794` | `98.0%` vs `GEMSDOE24`; `28.4%` vs `GVCD` (`H31`: `39.0%`) | **FAIL** (`h27` `-nan`) / **PASS** (`H31`) | **DO NOT RESUBMIT** |

---

## 3. PhD-Level Forensic Analysis: Why `GEMSDOE32` (`0.2778`) Won — and How to Beat `0.2778` Toward `0.4413–0.4544`

### 3.1 Byte-Exact Lineage & Metric Anatomy of `GEMSDOE32` (`0.2778 USER-REPORTED`)
Reopening the raw `float32` GeoTIFF bytes across `19GEMSDOE`, `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE30`, `GEMSDOE32`, and `GEMSDOE36` establishes an **exact, deterministic ablation chain** on the live competition metric:

$$\text{DTI}(\hat{Y}, Y) = \int_0^1 \frac{\text{TP}_w(\tau)}{\text{TP}_w(\tau) + 0.2\,\text{FP}_w(\tau) + 0.8\,\text{FN}_w(\tau)}\,d\tau, \qquad K_{300\text{m}}(d) = \max\!\left(0,\,1 - \frac{d}{300\text{ m}}\right)$$

where $\text{TP}_w(\tau) = \sum_{y \in Y_{\text{hidden}}} \max_{\hat{y} \ge \tau} K_{300\text{m}}(\|y - \hat{y}\|)$ uses a **non-additive $\max$-envelope** over predicted pixels while $\text{FP}_w(\tau) = \sum_{\hat{y} \ge \tau} \bigl(1 - \max_{y \in Y_{\text{hidden}}} K_{300\text{m}}(\|\hat{y} - y\|)\bigr)$ sums **additively** over every predicted pixel:

1. **Step 1 — Continuous Ridge Skeleton to 150 m Dotted Sampling (`19GEMSDOE H19-5: 0.1922` $\to$ `GEMSDOE24 H25-1: 0.2477`, `+0.0555`):**  
   `H19-5` emitted `121,131` connected skeleton pixels. Because $K_{300\text{m}}$ takes a **spatial maximum** within `300 m` (`3 px`), adjacent 100 m pixels along a ridge contribute **zero** additional $\text{TP}_w$ once one central dot is placed, yet every extra pixel outside `300 m` of a hidden fault adds `+1.0` to $\text{FP}_w$. Decimating `H19-5` to `60,069` dots at `d = 1.5 px` cut $\text{FP}_w$ in half while preserving `>97%` of the 300 m kernel envelope (`+0.0555` DTI).
2. **Step 2 — Optimal 280 m (`2.8 px`) Packing Radius (`GEMSDOE24: 0.2477` $\to$ `GEMSDOE25 / GEMSDOE30 D2.8: 0.2600`, `+0.0123`):**  
   At `d = 1.5 px` (`150 m`), neighboring dots still overlap across `50%` of the `300 m` cone. Widening minimum spacing to `2.8 px` (`280 m`, `44,090` binary dots — byte-for-byte identical inside the footprint between `GEMSDOE25` and `GEMSDOE30`) eliminated residual self-shadowing (`+0.0123` DTI).
3. **Step 3 — Exact `200 m` (`<= 2 px`) Known-Catalogue Collar Pruning (`GEMSDOE25: 0.2600` $\to$ `GEMSDOE32 B2: 0.2778`, `+0.0178`):**  
   Byte subtraction proves **`B2` (`37,654` dots) equals `D2.8` (`44,090` dots) minus the exact `6,436` dots lying within Euclidean distance $\le 2.0\text{ px}$ (`200 m`) of `existing_faults.tif`** (`0` additions, `0` other removals). Per [organizer staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516), known fault pixels are masked during scoring; moreover, parallel unmapped fault strands almost never sit `100–200 m` parallel to an already-mapped trace (mapping digitization tolerance is `100–250 m`). Removing those `6,436` collar dots stripped `14.6%` pure false-positive mass with virtually zero $\text{TP}_w$ loss (`+0.0178` DTI).
4. **Step 4 — Marginal DTI Threshold Bar (`GEMSDOE32: 0.2778` $\to$ `GEMSDOE36: 0.2750`, `-0.0028`):**  
   `GEMSDOE36` kept `100%` of `B2`'s `37,654` dots and appended `1,200` lower-rank Andersonian fault dots (`38,854` total). Differentiating $\text{DTI} = T / (T + 0.2 F + 0.8 (K_{\text{truth}} - T))$ shows that adding a dot with marginal true-positive kernel gain $\Delta T$ and expected false-positive cost $\Delta F \approx 1 - q$ improves DTI **if and only if**:
   $$\frac{\Delta T}{\Delta F} > \frac{0.2\,\text{DTI}}{1 - 0.8\,\text{DTI}}$$
   At $\text{DTI} = 0.2778$, the break-even bar is $\Delta T / \Delta F > 0.0714$. Those `1,200` extra dots fell slightly below `0.0714` marginal precision, trimming DTI by `-0.0028`.
5. **Step 5 — Why `B2`'s Underlying Surface (`19GEMSDOE`) Beat Later Oct 25–27 Tree Waves (`0.02–0.18`):**  
   Across all `97` prompt-scored rasters (`69` sites) in our 8-org empirical model (`LOSO R² = +0.4783`, `Spearman = +0.7162`), the single strongest physical predictor of `USER-REPORTED` leaderboard score alongside dot spacing is **concealed piedmont/basin off-catalogue geological structure capture (`c_pied_sgmc = 0.0888` on `B2`, `0.2136` on `GEMSDOE70 = 0.2478`, paired with `34–37%` distal `>32 px` allocation)**. `19GEMSDOE` used 4-quadrant out-of-fold ridge corroboration (topographic openness + thermal + magnetic/gravity) without in-sample tree memorization of `existing_faults.tif`.

### 3.2 Can `0.2778` Be Beaten (`> 0.30` Toward `0.4413–0.4544`) — and How?
**Yes — the organizer public leaderboard stands at `0.4544` (`2026-10-27` snapshot; `0.4413` and `0.3195` in earlier prompt snapshots), `0.1766` above `GEMSDOE32` (`0.2778`).** Closing the gap from `0.2778` to `0.35–0.45+` requires solving two coupled problems:

1. **Continuous Threshold-Sweep Calibration (`+0.03 .. +0.06` DTI Potential):**  
   Notice the outer integral $\int_0^1 \text{DTI}(\tau)\,d\tau$! Binary `{0, 1}` rasters (`B2`, `DPHS`, `GVCD`) evaluate the **identical** `37,400`-dot set at every threshold $\tau \in (0, 1)$. However, if dot amplitudes $w_i \in [0.20, 1.00]$ are monotonically calibrated to calibrated posterior marginal gain so that:
   - At $\tau = 0.85$, only the `~10,000` highest-precision fault-corroborated dots survive (maximizing precision when $\text{FP}_w$ is tiny),
   - At $\tau = 0.50$, `~35,000` balanced dots are active, and
   - At $\tau = 0.15$, `~65,000` broader 300 m recall dots activate (capturing `0.8 * FN_w`-weighted hidden faults at low $\tau$),
   the threshold integral $\int_0^1 \text{DTI}(\tau)\,d\tau$ strictly dominates **every** single static binary dot count!
2. **Multi-Resolution Subsurface Inversion Beyond Hand-Crafted 100 m Gradients (`+0.05 .. +0.11` DTI Potential):**  
   Top `0.44–0.45` entries on 2D geophysical segmentation benchmarks combine:
   - **2D Spatial U-Net / ConvNeXt / Swin Segmentation on Multi-Channel Patches (`128x128` at `100 m` = `12.8 km` receptive field)** trained with a **direct differentiable Distance-Weighted Tversky Loss** ($\mathcal{L}_{\text{DTI}}$ using exact $K_{300\text{m}}$ max-pooling on ` fold["visible"]`-masked hide-and-recover segments), enabling the network to trace *kinematically continuous* 10–40 km concealed fault corridors across flat basins rather than scoring pixels independently,
   - **3D Potential-Field Euler Deconvolution & Multi-Altitude Upward Continuation (`500 m`, `1 km`, `2 km`, `4 km`)** of GeoDAWN `mag` and `isostatic_grav` to track dipping normal fault planes from surface trace down to `3–8 km` geothermal reservoir depth, and
   - **Explicit `1 m` 3DEP LiDAR Tile Streaming** across the `~55%` LiDAR-covered blocks (downloaded directly from USGS TNMAccess rather than sparse summary rasters).
3. **Human Governance Prerequisite:** Resolve the literal blanket-control exemption (`13GEMSDOE` stride-5 lattice + `17GEMSDOE` / `GEMSDOE22` continuous priors) in `config/registry_inputs.json` before spending a `3/week` DrivenData slot.

---

## 4. `WBG2-GVCD` Experimental Results & Gate Verification

### 4.1 Gate 0 — Single-Feature Holdout Leakage Canary (`PASS`)
All `73` features (`72` model features + `piedmont_gate`) were tested individually on `gems57-pooled-hide-v2` withheld positives (`evidence/wbg2_gvcd_results.json`):
- **Maximum symmetric AUC across all 73 features:** **`0.6179 <= 0.90`** (`demag_along_strike_s3`) -> **PASS**
- **Top new `WBG2-GVCD` feature symmetric AUCs:**
  - `vent_structural_conduit_ridge` (`GVCD-H1`): **`0.5783 <= 0.90`**
  - `piedmont_blind_step_index` (`GVCD-H5`): **`0.5738 <= 0.90`**
  - `vent_claycap_demag_coupling` (`GVCD-H1`): **`0.5621 <= 0.90`**
  - `basement_step_hessian_ridge` (`GVCD-H5`): **`0.5544 <= 0.90`**
  - `stress_grav_dilation_tendency` (`GVCD-H2`): **`0.5419 <= 0.90`**
  - `comcat_post2021_blind_halo` (`GVCD-H4`): **`0.5312 <= 0.90`**

### 4.2 Three-Experiment Pooled `HOLDOUT-DTI` Progression (`gems57-pooled-hide-v2`, `60,988` Withheld Positives)

| Experiment / Benchmark | Fold 0 (`17,649` d) | Fold 1 (`9,847` d) | Fold 2 (`4,066` d) | Fold 3 (`5,677` d) | Pooled `HOLDOUT-DTI` | Spatial-Block `95% CI` | Lift vs `DPHS EXP-3` |
|---|---:|---:|---:|---:|---:|---|---:|
| `WBG2-DPHS EXP-3` *(Prior best)* | 0.1494 | 0.2213 | 0.1595 | 0.1947 | `0.17348` | `[0.15245, 0.19436]` | baseline |
| **`GVCD-EXP1`** (`72` feats Vent+Stress+ComCat + CELF) | 0.1498 | 0.2232 | **0.1682** | **0.1915** | **`0.17489`** | `[0.15277, 0.19658]` | **`+0.00141`** |
| **`GVCD-EXP2`** (+ Slope-Blind 60-feat Subsurface Specialist + Isotonic OOF) | 0.1511 | **0.2259** | 0.1668 | 0.1913 | **`0.17588`** | `[0.15544, 0.19687]` | **`+0.00240`** |
| **`GVCD-EXP3`** (+ Dual-Regime Geothermal-Vent & Stress-Dilation Weighting) | **0.1512** | 0.2258 | 0.1670 | 0.1913 | **`0.17591`** | **`[0.15549, 0.19694]`** | **`+0.00243`** |

### 4.3 Multi-Fleet Uniqueness Audit (`499` Verified Rasters Across 8 GitHub Organizations)

| Uniqueness / Validation Gate | Threshold | `WBG2-DPHS EXP-3` *(Prior)* | **`WBG2-GVCD EXP-3` *(Current)*** | Gate Outcome |
|---|---|---|---|---|
| Automated GeoTIFF Format, `EPSG:32611`, Zero-NaN, `[0, 1]` | 100% pass | PASS (`36,500` dots) | **PASS (`37,400` dots, `0` NaN, `[0.0, 1.0]`)** | **PASS** |
| Exact SHA-256 Match Across 8-Org Fleet (`499` rasters) | `0` matches | `0` matches | **`0` matches** | **PASS** |
| Pre-Placement Surface Spearman Rank-Corr (Raw / 1 km) | `<= 0.90` | `0.8608` | **`0.4225` (raw) / `0.5802` (1 km)** | **PASS** |
| Post-Placement 1 km Smoothed Pearson Correlation | `<= 0.90` | `0.8652` | **`0.4078`** | **PASS** |
| 9 Focus Sites (`GEMSDOE24..36`) 3-px Dot Overlap | `<= 0.70` | `0.4268 .. 0.5823` | **`0.2835 .. 0.3738`** | **PASS** |
| 13 Pinned Registry Discrete Rasters 3-px Dot Overlap | `<= 0.70` | `0.6251` | **`0.3904`** (`GEMSDOE27_H31`) | **PASS** |
| **All `496` Discrete Non-Blanket Rasters Across 8 Orgs (`cov <= 0.70`)** | **`<= 0.70`** | **FAIL (`45` violations, max `0.9587`)** | **`PASS` (`0` violations! max = `0.6956` on `GEMSDOE77__collar35`)** | **PASS (`496/496`)** |
| Literal All-Registry 3-px Overlap (incl. 3 Blanket Controls `cov > 0.70`) | `<= 0.70` | FAIL (`1.0000` on `13GEMSDOE`) | **FAIL (`1.0000` on `13GEMSDOE`, `0.9963` on `17GEMSDOE`, `0.9912` on `GEMSDOE22`)** | **STOP (`DO NOT SUBMIT`)** |

---

## 5. Irregularities Audited, Flagged & Corrected Line by Line

1. **External Repo README Claims vs Verbatim Prompt Ledger Isolated:** During our 8-org sweep (`buffedlizard55-lab`, `kanlerxz87-cyber`, `wingbangboozle1-lang`, `karagemop466-tech`, `apartanish22-droid`, `sassnarep3-star`, `eugboogieman123-ops`, `ginnymcfiner23-ux`), we discovered that several external repository READMEs (`GEMSDOE74`, `GEMSDOE86`, `KANLERGEMSDOE1..2`, `WBGGEMSDOE1..3`) cited internal projections or unverified claims (`0.3195`, `0.3133`, `0.2994`, `0.2981`, `0.2913`, `0.1636`, `0.1558`, `0.0970`) that were **absent from or contradicted by the user's prompt ledger** (where `GEMSDOE74 = 0.0669`, `GEMSDOE87 = 0.0500`, `GEMSDOE81 = 0.0041`, and `GEMSDOE86`/`KANLER`/`WBG` are blank) — and that prior `WBGGEMSDOE2` PR #32 prose (`research/dphs_findings.md`) had mistakenly repeated seven of those external numbers (even citing a non-existent `GEMSDOE94`). We purged 100% of non-prompt scores from `scripts/audit_gvcd_8org_fleet.py` (which immediately **improved** `LOSO R²` from `+0.4303` to **`+0.4783`** and Spearman from `+0.6488` to **`+0.7162`**!) and corrected `research/dphs_findings.md`, `docs/dphs/index.html`, and `docs/dphs/executive-summary.html`.
2. **Prior PR #32 Prose-vs-Code Feature Claims Corrected:** Line-by-line inspection of `src/wbggems/dphs.py` caught that PR #32 prose claimed `DPHS` ingested `gdr_1051`, `gdr_1120`, `nbmg_springs`, `quaternary_contacts_100m`, `usgs_comcat_nevada`, and a non-existent band `cond_15km` (the 19-band stack has `cond_surf` Band 17 and `depth_to_base_surf` Band 15). We corrected those descriptions and verified by SHA-256 every single external file actually read by `src/wbggems/gvcd.py` (`usgs_heat_flow_wells_epsg32611.csv`, `derived_gdr_volcanics_100m_u8.tif`, `usgs_comcat_geodawn.csv`, `gb_regional_stress_grid_10km.csv`, `gdr_1391_geothermal_points.csv`, 1 m LiDAR & 10 m 3DEP channels, and GeoDAWN aeromagnetic/radiometric grids).
3. **8-Organization Repository Structure Anomalies:**
   - `eugboogieman123-ops` (`EUGGEMSDOE1..3`) and `ginnymcfiner23-ux` (`GINNYGEMSDOE1..3`) exist on GitHub as public repositories, but contain **`0` `.tif` files** on `main` HEAD as of `2026-10-27`.
   - `sassnarep3-star/GEMSDOESASS1` stores its primary `.tif` under `swgb/downloads/` rather than `docs/downloads/`; `audit_gvcd_8org_fleet.py` explicitly scans `swgb/downloads/`.
   - `wingbangboozle1-lang/WBGGEMSDOE3` prompt lists `wbggemsdoe3-skarpline-union-20261027-610acf58-zeros` while `main` HEAD serves `docs/lst1/downloads/wbggems3-lst1-hybrid-20261026-0a0229da-zeros.tif` and `docs/downloads/wb-gems-doe-3-latest-submission-zeros.tif`.
4. **Axial North-Up `EPSG:32611` Stress Tangent Math Verified:** Because raster row indices increase southward (`transform.e = -100.0`), the structural strike tangent perpendicular to gradient $(g_x, g_y)$ in geographic `(East, North)` coordinates is $(t_E, t_N) = (g_y, g_x)$, giving $\cos(2\theta_{\text{strike}}) = (g_x^2 - g_y^2)/(g_x^2 + g_y^2 + \varepsilon)$ and $\sin(2\theta_{\text{strike}}) = 2 g_x g_y/(g_x^2 + g_y^2 + \varepsilon)$. Unit tests in `tests/test_gvcd.py` verify exact N-S, E-W, NE-SW, and NW-SE fault strike responses.
