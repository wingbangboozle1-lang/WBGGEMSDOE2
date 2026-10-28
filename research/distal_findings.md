# WBG2-DISTAL findings — 100% spatial-OOF successor to DPHS (2026-10-28 UTC)

Evidence classes used below, exactly: **HOLDOUT-DTI** (shared
`gems57-pooled-hide-v2`, α=0.2, β=0.8, 300 m triangular kernel, 60,988
withheld positives), **USER-REPORTED** (fleet ledger; no organizer receipt
in Git), **EMPIRICAL-ESTIMATE** (fleet regression; not a score), and
**ORGANIZER-PUBLISHED OBSERVATION** (public leaderboard page fetch).
Nothing is ORGANIZER-CONFIRMED; no submission receipt exists for any file
discussed. Zero weekly slots were spent.

## 1. Decision (selector-ready, one file)

**Recommended file for the selector:**
`wbg2-distaloof-natural_oof-38000dots-20261028T003000Z-8237e99a-zeros.tif`
(SHA-256 `512609c135676fbd8d1a44c43aa37ec88e6da9b76dab6af76ec929ab71b0aa9c`,
38,000 dots, note: `WBG2-DISTAL natural_oof 100pctOOF CELF300m 38000dots gt32=0.19 HOLDOUT-DTI=0.1770`).

- **HOLDOUT-DTI 0.1770** (95% CI [0.1549, 0.1976]) — above the previous repo
  best, DPHS EXP-3 0.1735 [0.1525, 0.1944] (same evaluator/features; this
  run used a 38,000-dot cap vs DPHS 36,500, so treat as replication-plus,
  not a new-modelling claim).
- **Format PASS on written bytes** (independent strict validator:
  1 band float32, EPSG:32611, 3730×3292, transform
  `[100,0,243350,0,-100,4508550]`, nodata null, **0 NaN and 0 values
  outside [0,1] in the whole array** — the DrivenData
  `Predicted values must be in range [0, 1]` error cannot fire on this file;
  `evidence/distal_strict_validation.json`).
- **Unique vs every sparse peer:** across 477 measured fleet rasters, exact
  SHA-256 new, pre-placement surface max |Spearman ρ| = **0.6984 ≤ 0.90**,
  all 9 focus champions ≤ **0.6307** within-3px (B2 itself: 0.5448), and all
  **437 sparse peer-budget rasters (≤65,000 reference dots) ≤ 0.6785 ≤ 0.70**
  (worst: GEMSDOE63 `cvarlw-thin` 54,864 dots, 0.2303 USER-REPORTED).
- **Literal any-registry gate FAIL — and it also rejects the champion:**
  measured here, GEMSDOE32 B2's own dots are 99.95% within 3 px of
  GEMSDOE22's dense 336k emission, 99.92% of the 13GEMSDOE lattice, 78.6%
  of GEMSDOE77, 72.6% of GEMSDOE23 (`evidence/distal_b2_gate_diagnostic.json`).
  A rule that rejects every known-good submission measures reference
  *coverage*, not copying. Promotion is therefore **to the selector only**,
  contingent on the documented sparse-peer interpretation; the lane run
  card keeps `ok_to_submit: false` because slot selection is a separate step.

## 2. Executive table — what to download, estimated score, unique?

| File (this repo) | HOLDOUT-DTI | Estimated leaderboard score (EMPIRICAL-ESTIMATE) | Unique vs 9 focus sites? | Unique vs 437 sparse peers? | Format / portal-safe? | Decision |
|---|---:|---:|---|---|---|---|
| ⭐ `wbg2-distaloof-natural_oof-38000dots-…-8237e99a-zeros.tif` | **0.1770** [0.1549, 0.1976] | 0.1067, 95% PI [0.0000, 0.2276] | **Yes** (max 0.6307) | **Yes** (max 0.6785) | **PASS** (0 NaN anywhere) | **PROMOTE TO SELECTOR** |
| `wbg2-distaloof-quota35-37988dots-…-cbdb172d-zeros.tif` | 0.1548 [0.1315, 0.1774] | 0.1090, 95% PI [0.0000, 0.2312] | Yes (max 0.6427) | Yes (max 0.6935) | PASS | Research alternative (B2-like composition; paired Δ vs natural −0.0223 [−0.0292, −0.0153]) |
| `wbg2-distaloof-piedmont40-37870dots-…-8163a5dc-zeros.tif` | 0.1515 [0.1286, 0.1743] | 0.0953, 95% PI [0.0000, 0.2194] | Yes (max 0.6307*) | Yes (max 0.6799) | PASS | Research only |
| DPHS EXP-3 (previous lane) | 0.1735 [0.1525, 0.1944] | 0.0713, 95% PI [0.0000, 0.1941] | Yes (0.4268–0.5823) | **No** (45 discrete >0.70; max 0.9587) | PASS | DO NOT SUBMIT (superseded) |

*primary-champion rows; variant-file maxima are in the audit JSONs.
Estimates come from the 11-feature fleet model (n=95 USER-REPORTED scores;
grouped LOSO R² +0.4303, Spearman +0.6488; strict 9-focus external Spearman
+0.7554, RMSE 0.0995). **No arm can honestly be claimed to beat 0.2778**:
the model under-predicts B2 (LOSO 0.1973 vs 0.2778 reported) and all three
95% PIs cross both values. The public leaderboard snapshot re-fetched this
session is still **0.4544 (`xiaofanhu`, ORGANIZER-PUBLISHED OBSERVATION,
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)**;
0.3195/0.4413 in the prompt remain USER-SUPPLIED.

### Nine focus sites (strongest claim each; all USER-REPORTED; none resubmittable)

| Site | Historical file (dots) | Claim | Frac ≤2px cat | Frac >32px | Natural-OOF within 3px of it | Verdict |
|---|---|---:|---:|---:|---:|---|
| GEMSDOE32 | `h33-h33-2-b2-…-e5eb6e7e-zeros` (37,654) | 0.2778 | 0.00% | 34.0% | 0.5448 | DO NOT RESUBMIT |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-…` (38,854) | 0.2750 | 0.00% | 33.4% | 0.5489 | DO NOT RESUBMIT |
| GEMSDOE28 | `h36-1-rung30-blind-r1-…-nan` (37,660) | 0.2710 | 1.95% | 33.8% | 0.5650 | DO NOT RESUBMIT (NaN file) |
| GEMSDOE31 | `h27-4-solo-d28-…-nan` (40,199) | 0.2708 | 6.33%* | 31.8%* | 0.5725 | DO NOT RESUBMIT (NaN file) |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-…` (41,865) | 0.2632 | 9.3%* | 30.8%* | 0.5865 | DO NOT RESUBMIT |
| GEMSDOE25 | `dotted-h19-5-d2-8-…-nan/zeros` (44,090) | 0.2600 | 14.6% | 29.0% | 0.6029 | DO NOT RESUBMIT |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-…` (44,090) | 0.2600 | 14.6% | 29.0% | 0.6029 | DO NOT RESUBMIT (same support as GEMSDOE25) |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-…-nan` (60,069) | 0.2477 | 14.6% | 28.9% | 0.6252 | DO NOT RESUBMIT (NaN file) |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-…-nan` (61,328) | 0.2449 | 14.5% | 28.3%* | 0.6307 | DO NOT RESUBMIT (NaN file) |

*from the DPHS fleet table where the focus-table field differs by file
variant; see `evidence/dphs_uniqueness_and_fleet_audit.json`.

## 3. Why B2 (0.2778 USER-REPORTED) won — and what would actually beat it

Byte lineage (measured previously, unchanged): B2 = the 44,090-dot D2.8
Poisson thinning of H19-5's **4-quadrant spatial-OOF** surface, minus the
6,436 dots within 2 px of the catalogue. Three compounding effects:
(1) **kernel economy** — 2.8 px spacing stops paying repeated 0.2·FP costs
inside one 300 m triangular kernel; (2) **collar pruning** — catalogue
pixels are masked by the organizer, so ≤2 px dots are ~pure FP cost;
(3) **OOF distal recall** — because no pixel was scored by a model that had
seen its quadrant's faults, one-third of the budget landed >3.2 km from
mapped faults. The official problem page confirms the test population is
*new expert faults not in the USGS/INGENIOUS catalogue*
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
which is exactly the population an OOF surface can find and an in-sample
refit cannot (DPHS's 55% in-sample blend collapsed to 3.64% distal and
duplicated 45 fleet range-front rasters despite winning holdout).

Beating 0.2778 credibly requires a *better OOF surface*, not a forced
composition: this session's quota arms prove the point — forcing B2's exact
composition (quota35: 35.0% >32px, median 18.0 px vs B2's 18.03 px) on the
DPHS surface **cost** HOLDOUT-DTI (−0.0223 paired) and slightly *lowered*
off-catalogue SGMC coverage (C_pied 0.0574 vs B2 0.0888; natural 0.0616).
Composition is a fingerprint of a good surface, not an independent lever.

## 4. Campaign record (3 experiments, 1 aborted pilot, 0 slots)

Preregistration + Amendment A1: `research/distal_preregistration_20261027.md`.
Pilot fold 0 (absolute-px quotas: natural 0.1541 / quota 0.0809) exposed
that in-quadrant distances to *visible* faults make absolute quotas
mechanically invalid; quotas were restated as area-normalized band
densities (identical policy on the full map) before any pooled result
existed (`evidence/wbg2_distal_run_pilot.log`).

| Arm | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Pooled HOLDOUT-DTI [95% CI] | Full-map >32px | Median px |
|---|---:|---:|---:|---:|---:|---:|---:|
| natural_oof | 0.1541 | 0.2210 | 0.1698 | 0.1934 | **0.1770 [0.1549, 0.1976]** | 18.7% | 10.63 |
| quota35 | 0.1237 | 0.1957 | 0.1597 | 0.1885 | 0.1548 [0.1315, 0.1774] | 35.0% | 18.00 |
| piedmont40 | 0.1192 | 0.1938 | 0.1594 | 0.1846 | 0.1515 [0.1286, 0.1743] | 39.8% | 21.21 |

Leakage canary: PASS, 61/61 features, max symmetric AUC 0.61795
(`demag_along_strike_s3`) — identical to DPHS, as required by reuse.
Full-map packaging is the only change from DPHS that matters: pure OOF
(zero in-sample pixels), per-quadrant quantile matching, full-catalogue
relay/tip modulator. Named non-fault mimic: alluvial fan channels, playas
and Lake Lahontan shoreline benches.

Gate outcomes vs preregistration: (a) holdout ≥0.15 **PASS** (natural);
(b) full-map >32px in [0.30, 0.42] **FAIL for natural (0.187), PASS for
quota arms**; (c) strict format **PASS all arms**; (d) ≤0.70 vs every
discrete raster **FAIL literal for all arms (dense refs), PASS for all arms
under the sparse-peer class**; (e) estimate reported with PI **done**.
The selector is therefore choosing between the holdout-best natural map
and the composition-matching quota35 map with a measured −0.022 holdout
cost and indistinguishable empirical estimate (0.1067 vs 0.1090). This
report recommends natural_oof: composition forcing did not buy SGMC
alignment or uniqueness, only holdout loss.

## 5. Irregularities flagged

1. The fleet audit prints a legacy header ("DPHS EXP-3 …") even when run
   with the DISTAL candidate env overrides — cosmetic; all inputs/outputs
   are the DISTAL files recorded in each audit JSON's `candidate` block.
2. Focus "primary" overlap maxima computed by token-matching include
   duplicate packaging variants; the tables here use SHA-pinned primary
   files from `data_public/focus_table.json`.
3. Fleet model external R² on the 9 focus sites is negative (−0.1387)
   despite Spearman +0.7554 — rank-informative, level-unreliable. Treat
   point estimates as order-of-magnitude only.
4. Several prompt-ledger scores conflict with earlier snapshots
   (e.g. GEMSDOE28 S21 0.0206 vs 0.1628) and many prompt entries are blank;
   blanks are preserved as missing, never zero.
5. Piedmont-boost percentiles differ at the 4th decimal between the pilot
   (fresh cache) and A1 (loaded cache) logs — immaterial, recorded.
6. Competition inputs remain a hash-pinned public owner mirror, not an
   organizer-authenticated DrivenData download; the data page requires
   login and no credentials were used.

## 6. Official sources (for manual review)

- DrivenData GEMS problem/metric/submission format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Public leaderboard (0.4544 observed this session): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Rules (3/week, single final selection, AI-use disclosure): https://www.drivendata.org/competitions/306/competition-doe-gems/rules/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DOE GDR #1391 (INGENIOUS): https://gdr.openei.org/submissions/1391
- USGS 3DEP: https://www.usgs.gov/3d-elevation-program/about-3dep-products-services
- DOE/NLR submission guide PDF 96647: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- EPSG:32611: https://epsg.io/32611 · Tversky index: https://en.wikipedia.org/wiki/Tversky_index
