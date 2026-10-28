# WBG2-DISTAL preregistration — 2026-10-27 (written before any DISTAL experiment was run)

Lane: **WBG2-DISTAL = 100% spatial-OOF, distance-stratified piedmont allocation**.
This is the explicit next step prescribed by the previous session
(`research/dphs_findings.md` §5 item 5: *"Next-session runs must emit 100%
spatial-OOF regime-calibrated surfaces enforcing 30%–40% distal piedmont
(>32 px) budget allocation"*). It is not a new feature stack.

## Why this lane exists (measured, not speculative)

- WBG2-DPHS EXP-3 won the shared hide-and-recover holdout
  (`HOLDOUT-DTI = 0.1735`, 95% CI [0.1525, 0.1944], `gems57-pooled-hide-v2`,
  60,988 withheld positives; `evidence/wbg2_dphs_results.json`) but its
  **full-map packaging blended 55% in-sample predictions**, which collapsed
  96.36% of dots into 2–32 px of mapped range fronts
  (`frac_gt_32px = 3.64%`, median 4.0 px). It therefore duplicated 45 discrete
  fleet range-front rasters (>70% 3-px overlap) and its fleet
  `EMPIRICAL-ESTIMATE` was only 0.0713 (95% PI [0.0000, 0.1941]).
- The 9-focus champion lineage (GEMSDOE32 B2, 0.2778 USER-REPORTED) is the
  opposite composition: 37,654 dots, 0.00% within 2 px of catalogue,
  **34.01% beyond 32 px (3.2 km)**, 2.8 px thinning of a 4-quadrant
  spatial-OOF surface (H19-5). Byte lineage and numbers:
  `research/dphs_findings.md` §2. Every later in-sample PU-HGBR wave with
  `frac_gt_32px < 4%` reported ≤0.086.
- Interpretation (hypothesis, not receipt): the hidden expert-labelled test
  faults are a *new* population, not redrawn catalogue segments. A model
  refit on all labels memorizes mapped traces; a spatial-OOF surface cannot,
  so it spends budget on independent geophysical/topographic evidence in
  concealed piedmont/intrabasin ground where unmapped faults plausibly sit.

## Five candidate hypotheses, ranked (expected gain vs cost)

| Rank | ID | Layers (exact, already cached) | Physical signature | Why it can catch an *uncatalogued* fault | Difference from this repo | Named non-fault mimic |
|---:|---|---|---|---|---|---|
| 1 | DISTAL-H1 (IMPLEMENTED, EXP-2) | All 60 zero-catalogue DPHS features; fold-visible distance transform only for strata | Distance-stratified 300 m CELF budget (30% 2–10 px, 35% 10–32 px, 35% >32 px from *visible* faults) on a 100% spatial-OOF surface | Hidden faults are not segments of mapped ones; the >32 px stratum is >3.2 km from any mapped trace, so dots there can only be earned by geophysics/topography, not by trace continuation | Every prior full map here (DPHS, MSPTCD, CBS) blended in-sample predictions; none emitted a pure-OOF full map and none enforced a distal quota | Alluvial fan channels and playas also produce distal lineaments; quota can spend budget on fan morphology |
| 2 | DISTAL-H2 (IMPLEMENTED, EXP-3) | `dem10_deconfounded_piedmont_scarp`, `det_elev_slope` (band 19), 60-feature OOF surface | Low-slope piedmont scarp boost `(1 + 0.75·scarp_pct·low_slope_ramp)` applied only beyond 10 px, quotas 25/35/40 | Degraded Holocene scarps cross low-slope bajadas below 1:250k mapping thresholds; boost elevates exactly those cells inside the distal stratum | DPHS used the scarp layers as ordinary model features; it never used them as a regime gate on allocation | Pleistocene Lake Lahontan shoreline benches are low-slope scarps (de-confounding is the DEM10 layer's purpose, but imperfect) |
| 3 | DISTAL-H3 (NOT implemented) | `iso_grav_anom_hg` (18), `depth_cover_log_step`, `cond_flank_asymmetry` | Intrabasin gravity-bench ridge co-located with conductive-base step: buried range-bounding fault under basin fill | A bench/step pair persists where the fault has no surface expression at all, i.e. precisely the blind population | Existing features feed a global model; no intrabasin-only bench+step conjunction was ever allocated on its own | Unfaulted basin-margin onlap and volcanic tableland edges produce bench+step pairs |
| 4 | DISTAL-H4 (NOT implemented) | `cond_surf` (17), `hydro_cond_coupling`, GDR #1391 halos | Shallow clay-cap conductor edge terminating against a deep conductor root (MT phase split) distal to mapped faults | Blind hydrothermal upflow needs a permeable structure; a terminating clay cap is fluid evidence independent of any mapped trace | Hydrothermal layers were additive model features, never a distal-only conjunction gate | Playa evaporite brine sheets are shallow conductors with no fault |
| 5 | DISTAL-H5 (NOT implemented) | `mag_anom` (1), `rtp` (2), `tc_radiometric` (6), USGS flight-line metadata | Survey-axis spectral notch-stability: edges surviving attenuation along documented E–W flight / N–S tie axes | Removes acquisition lineament false positives, freeing budget for real unmapped structures | No spectral artefact stress-test exists in this repo (raised as N4 in `research/hypotheses.md`) | Real E–W/N–S faults are attenuated by the same notch |

DISTAL-H3/H4/H5 need new derived features and therefore new leakage canaries;
they are **deferred**, not part of this run's 3-experiment budget.

## The 3 experiments (allocation-only, one shared OOF surface per fold)

Training per fold replicates DPHS EXP-3 exactly (60 features, dual HistGBR +
single HistGBR blend, isotonic calibration on a 20 km-block split, Gauss
smoothing σ=0.75, fold-visible relay/tip modulator, same seeds). Only the
**allocation** differs, so any DTI delta is attributable to allocation:

- **EXP-1 `natural_oof` (control):** DPHS EXP-3 CELF allocation unchanged
  (`allocate_submodular_300m`, min gain 0.020, collar `d_vis > 2.05 px`),
  budget 38,000 (DPHS used 36,500; 38,000 is inside the fleet-winner range
  37,654–38,854 and is fixed here before running).
- **EXP-2 `quota35` (DISTAL-H1):** stratified CELF, bands
  (2.05,10]/(10,32]/(32,∞) px from visible faults, quotas 30/35/35,
  band min-gains 0.020/0.012/0.006, allocated distal→mid→proximal with a
  ≥2.2 px exclusion around already-placed dots.
- **EXP-3 `piedmont40` (DISTAL-H2):** piedmont boost on the same surface,
  quotas 25/35/40, same band min-gains and ordering.

Evaluator: unchanged shared `gems57-pooled-hide-v2` (α=0.2, β=0.8, 300 m
triangular kernel), 4 label-blind quadrants, 80 px buffer, whole components
withheld, catalogue features (relay modulator, distance strata, collar)
derived from **visible faults only** per fold. Leakage canary: all 60
features + modulator, single-feature AUC per fold, stop if max symmetric
AUC > 0.90.

## Full-map packaging (the actual change under test)

1. Pool the per-fold **pre-modulator** OOF smooth surfaces (100% OOF, zero
   in-sample pixels anywhere on the map).
2. Quantile-match each quadrant's OOF distribution to the pooled
   distribution (monotone, label-free; removes quadrant seams without
   changing within-quadrant ranking).
3. Apply the full-catalogue relay/tip modulator and the winning
   experiment's allocation with full-catalogue distance bands,
   collar `d_cat > 2.05 px`, cap 38,000 dots.
4. Emit with the unchanged shared `submission_writer` (`-zeros`, all-finite
   float32 in [0,1], EPSG:32611, 3730×3292).

## Preregistered selection and promotion gates

- **Winner selection (automatic, in-script):** among EXP-2/EXP-3, an arm is
  eligible if its pooled HOLDOUT-DTI is non-inferior to EXP-1 within 0.02
  (domain-shift margin justified above: hide-and-recover rewards
  catalogue-proximal placement that the fleet evidence shows *hurts* the
  real leaderboard). Pick the eligible arm with the higher DTI; if neither
  is eligible, emit EXP-1's OOF-natural map as research-only.
- **Promotion requires ALL of:** (a) winner pooled HOLDOUT-DTI ≥ 0.15 and
  canary PASS; (b) full-map `frac_gt_32px` in [0.30, 0.42] and
  `frac_le_2px = 0`; (c) strict format validation PASS on written bytes
  (values in [0,1] incl. outside footprint, 0 NaN anywhere, CRS/shape/
  transform match to `sample_submission.tif`); (d) uniqueness vs the fleet:
  final-dot 3-px overlap ≤ 0.70 against **every discrete** registry raster
  (3-px footprint coverage ≤ 0.70) **and** ≤ 0.70 vs each of the 9 focus
  champions, pre-placement surface |Spearman| ≤ 0.90, exact SHA-256 new;
  (e) fleet empirical estimate reported with its 95% PI and never written
  as a score.
- **Literal-blanket caveat (must be disclosed, never silently exempted):**
  registered blanket rasters (stride-5 lattice covering 99.87% of the
  footprint within 3 px; continuous priors positive everywhere) make a
  literal all-registry ≤0.70 gate mathematically impossible for any
  geological emission of ≥22,164 dots (proof in
  `docs/research/why-b2-scored-2778.md`). Gate (d) is therefore stated
  against discrete peer emissions — the same class as every scored fleet
  submission — and the blanket witnesses will be reported explicitly in
  the run card so the human selector sees the open interpretation
  (issue #23) rather than a hidden exemption.

## Amendment A1 (2026-10-27, after a 1-fold pilot, before any pooled result)

The pilot fold exposed a mechanical flaw in the absolute-pixel quota
operationalization: inside a holdout quadrant, 98% of natural dots are
already >32 px from *visible* faults (which live in the other quadrants),
so forcing 35% of the budget beyond 32 px and 30% within 10 px of visible
faults dumps most of the budget into a thin quadrant-border strip
(pilot fold 0: natural 0.1541 vs quota35 0.0809, piedmont40 0.0828 —
recorded in `evidence/wbg2_distal_run_pilot.log`). The quota *policy* is
therefore restated in its fold-consistent form, with the same target
fractions: each band's allocation **density** (dots per allowed pixel) is
fixed by the target fractions relative to the band areas measured over the
whole footprint from the same (visible-only in folds, full on the full map)
distance field; the fold share of each band is that density times the
band's allowed area in the fold. On the full map this reduces exactly to
the original 30/35/35 and 25/35/40 dot fractions. No other parameter
changed. The aborted absolute-pixel pilot is reported as a design
diagnostic, not as one of the 3 pooled experiments.

## Budget

3 experiments, 0 weekly slots. Slot promotion remains a separate selector
step. Numbers will be labelled HOLDOUT-DTI (evaluator version, withheld
positives, 95% CI), USER-REPORTED (fleet ledger), or EMPIRICAL-ESTIMATE
(fleet regression) — never ORGANIZER-CONFIRMED without a receipt.
