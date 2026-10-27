# CBS lane pre-registration — 2026-10-27 (written BEFORE any CBS experiment is run)

Lane for this session (single method): **Covered Basement Step (CBS)** — subsurface-only
blind-fault detection, emitted as collar-free spaced dots. Budget: ≤3 experiments, ≤2 h,
0 submission slots spent by this script.

## Five candidate hypotheses considered (ranked before implementation)

| Rank | Hypothesis | Layers (band# in the 19-band GeoDAWN stack) | Physical signature | Why it should catch a fault MISSING from USGS/INGENIOUS | Differs from this repo's prior lanes | Named non-fault mimic | Cost |
|---|---|---|---|---|---|---|---|
| 1 | **CBS: covered basement step** | rtp(2), tmi_hg(3), iso_grav_slope(5), tmi_vg(9), iso_grav_vg(11), iso_grav(13), tmi(14), depth_to_base(15), cond_surf(17), iso_grav_hg(18), mag_anom(1); slope(19) as cover gate only | Potential-field tilt gradients (Miller & Singh 1994 / Verduzco 2004 computed from derivatives), dip-offset Bouguer–magnetic concordance, log-step in depth-to-base, conductivity flank asymmetry | A fault buried under alluvium/cover has **no scarp** for surface mapping or lidar, so it is absent from a surface-expression catalogue, but it still offsets magnetic basement, gravity and the conductive base. Subsurface steps persist where topography is silent. | DZ-16 = catalogue-distance geometry only; H3-PACK = area-uniform packing only; MSPTCD = 31 features **including** topographic scarp Hessian ridges, emitted as connected ridges (measured this session: 389 components, kmass/dot 1.606). CBS **excludes** all topographic predictors and emits spaced dots. | Lithologic basement contact / caldera margin / intrusive edge — a real subsurface step that is not a (geothermally relevant) fault | Low: reuses hash-pinned stack + `src/wbggems/msptcd.py` label-free operators; no new external data |
| 2 | Active blind strain | geod_2ndinv(4), geod_shearrate(7), geod_dilaterate(8), deq(10), ieq(16) + CBS | Ridge/step in GPS/InSAR strain-rate field; seismicity density elongation | A creeping/locked blind fault still localises interseismic strain and microseismicity even with no surface break | MSPTCD EXP-2 added these as 3 auxiliary features on top of scarp-inclusive model (+22%, worse than EXP-1); never tested as the primary signal on a subsurface base | Volcanic inflation, groundwater-withdrawal subsidence, geothermal production deformation | Low (same stack) |
| 3 | Radiometric alteration lineament | tc(6) terrain-residual, rtp(2) | Linear low in terrain-detrended total-count radiometrics (clay alteration leaches K/Th/U along fluid conduits) | Hydrothermal alteration follows the permeable fault, including segments with no topographic offset; alteration is a *geothermal* discriminator, not just structure | Band 6 was misread as "tilt" in mirror metadata; MSPTCD used its edge (`rad_terrain_residual_edge`) as one of 31 features; nobody has modelled signed residual lows as the primary target. Note: band 6 had the highest single-feature canary AUC in MSPTCD (0.6131, still ≪0.90) | Playa/lacustrine clay pans, lithologic radiometric lows, soil-moisture/radon effects | Low |
| 4 | Conductivity-front offset | cond_surf(17), depth_to_base(15) | Lateral step in near-surface conductivity discordant with topography (fault-juxtaposed saturated vs resistive blocks; clay cap edge) | Groundwater ponding against a sealing blind fault creates a conductivity front in flat basin fill where no scarp exists | `cond_flank_asymmetry` existed as 1/31 MSPTCD features; never gated to flat basin floors | Playa margins, irrigation/perched water, lithologic clay lenses | Low |
| 5 | Scarp Hessian / lidar lineament (rejected for this lane) | det_elev(12), det_elev_slope(19) | Hessian ridge crest / slope break | Would mostly re-find surface-expressed faults already catalogued (and expert labels were made with the same topography) | This is the most-tried family in the fleet (scores 0.02–0.16 USER-REPORTED); it is the lane CBS deliberately departs from | Shorelines (Lahontan), roads, dune crests, terrace edges | Low but duplicate-prone |

## Pre-registered experiments (evaluator: unmodified `gems57-pooled-hide-v2`, folds:
## `label-blind-quadrants-v2`, buffer 80 px, $\alpha$=0.2, $\beta$=0.8, 300 m triangular kernel)

- **CTRL-19B-dotted**: 19 raw bands + HistGradientBoosting (same hyper-parameters as MSPTCD
  campaign) + dotted emission. Isolates emission economics from surface choice.
- **EXP-1 CBS-core**: 11 subsurface raw bands + 6 subsurface physics operators
  (`mag_tilt_grad`, `grav_tilt_grad`, `dip_offset_concordance`, `cond_flank_asymmetry`,
  `depth_cover_log_step`, `grav_mag_orient_coherence`) + dotted emission.
- **EXP-2 CBS-cover**: EXP-1 surface, eligibility additionally gated to
  `det_elev_slope ≤` 70th percentile over the footprint (label-free cover gate).
- **EXP-3 CBS-active**: EXP-1 features + strain/seismicity raw bands (4,7,8,10,16) +
  3 strain/seismic physics operators, dotted emission, no cover gate.

Emission for every arm (identical, so arms differ only in surface/gate):
eligible = footprint ∩ eval-region ∩ (distance-to-visible > 3 px); greedy descending
surface; Euclidean suppression radius 5 px (target kmass/dot ≈ 9.3 of max 9.38);
per-fold budget = round(0.0082 · eligible) (the MSPTCD campaign's budget rule).

Primary endpoint: pooled HOLDOUT-DTI (all withheld positives, N stated, 95% paired
spatial-cluster bootstrap CI from the shared evaluator). Secondary (descriptive, same
evaluator): "low-relief stratum" = withheld positives with `det_elev_slope ≤` median slope
at catalogue positives — the subpopulation that most resembles blind targets.

Leakage canaries: every feature used by any arm, alone, per fold; two-sided AUC must be
≤ 0.90 or the campaign stops. Catalogue-derived features: none are used as predictors
(distance-to-visible is used only for negative sampling and emission eligibility, both
recomputed per fold from visible faults only).

Promotion gates (all required, else verdict = negative / DO NOT SUBMIT):
1. Best EXP beats CTRL-19B-dotted with paired 95% CI on Δ excluding 0, **and** its pooled
   HOLDOUT-DTI exceeds the repo's current same-evaluator best (MSPTCD EXP-3 = 0.042554).
2. Final dots: ≤70% within 3 px of **each** of the nine focus-site champions and of each
   sibling lane in this repo (DZ-16, H3-PACK, MSPTCD-E3); |Spearman ρ| ≤ 0.90 of the
   pre-placement surface against each of those rasters. The literal result against the
   two space-filling witnesses (13GEMSDOE stride-5 lattice, 17GEMSDOE continuous prior)
   is **also published**, with coverage-calibrated enrichment; no silent exemption.
3. Saved-byte validation: 1 band, float32, EPSG:32611, 3730×3292, transform match,
   all values finite and in [0,1] **everywhere** (0.0 outside footprint, nodata unset) —
   the portal rejects out-of-range values and NaN-outside is therefore not used.
4. Score estimates labelled EMPIRICAL-ESTIMATE / PROJECTION with intervals; never a score.

Final candidate (only if gates pass): winning arm refit on the full catalogue
(cross-fitted OOF surface), full-footprint emission, distance-to-catalogue > 3 px,
budget chosen from the OOF budget sweep (factors 0.5/0.75/1.0/1.33/1.66), written with
the unmodified shared `submission_writer.py`.

## Amendment (same day, before pooled results existed)

The first run was stopped after fold 0 printed (CTRL-dotted 0.1236, EXP-1 0.0939,
EXP-2 0.0938, EXP-3 0.0861 on that single fold) solely to (a) persist OOF surfaces for
audit and (b) make candidate construction use the best arm overall. No feature set,
fold, budget or evaluator changed. Consequence, stated in advance of the pooled
numbers: if the control arm wins pooled, the CBS geological hypothesis is recorded
**negative**, and the control arm (19 raw bands + collar-free dotted emission — itself
never previously emitted in this repo: MSPTCD used ridge/submodular emission measured
at kmass/dot 1.606) becomes the candidate. Fold-0 was seen before this amendment;
pooled results were not.
