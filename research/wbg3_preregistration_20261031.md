# WBG3-DTOE preregistration — written before the experiment ran (2026-10-31)

**Assigned method lane (single paragraph).** This session's lane is the
PARALLEL-RUN PROTOCOL paragraph supplied in the session brief: reuse the pinned
shared template's cached feature stack, `evaluate_holdout.py` and
`submission_writer.py`; validate with buffered whole-segment hide-and-recover;
score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel); label every
number HOLDOUT-DTI or ORGANIZER-CONFIRMED; run single-feature leakage canaries;
enforce the literal duplicate stop on the surface before placement and on final
dots; stop at three experiments or two hours. Within that lane the specific
method tested here is **WBG3-DTOE**: keep the pinned DPHS EXP-3 spatial-OOF
surface construction operation-for-operation, and change only the emission
stage: a preregistered grid of (dot budget x marginal-gain bar x relay/tip
modulator on/off) allocations, selected by pooled holdout DTI, then gated by the
duplicate stop. Nothing is copied from any other team's raster.

## Ranked candidate hypotheses (required by the brief)

| Rank | Hypothesis | Layers/signature | Why it should catch uncatalogued faults | Named non-fault mimic | Difference from everything in this repo | Expected holdout DTI gain (qualitative) | Cost | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | **H1 DTI-optimal tail emission** — sweep dot budget {26k, 38k} x marginal-gain bar {0.020, 0.035}; the incumbent allocator fills its 38k cap even when the exact DTI break-even bar (`dT > c(1-k)`) says a tail dot's expected kernel credit cannot pay its 0.2-alpha false-positive price | Same pinned 60-feature stack (MSPTCD 31 + LiDAR scarp 7 + DEM10 scarp 7 + GeoDAWN spectra 6 + GDR hydro-conduit 4 + multiscale ridge 5) | Frees emission budget from low-credit tail cells toward cells whose calibrated probability justifies them; measures the true DTI-optimal stop point on buffered folds instead of assuming 38k | A miscalibrated surface in distal basins could make the bar reject good distal dots (lost recall) | No prior run in this repo swept the budget or the gain bar; distal2 fixed budget=38000, gain=0.020 | Small positive (mechanistic, exact-arithmetic motivated) | LOW (allocation-stage only) | **Implemented this session** |
| 2 | **H2 modulator ablation** — relay/tip modulator OFF arm; tests whether catalogue-shaped boosting helps recover withheld segments or only re-dots cells adjacent to visible (evaluation-masked) faults | Same stack, modulator `compute_relay_tip_modulator` disabled | If the modulator mostly moves mass next to visible faults it inflates near-catalogue dots that the organizer masks anyway; removing it may reposition dots onto genuinely open continuations | Removing it can lose true tip-continuation recoveries | Prior runs always used the modulator on the full map; never ablated | Unknown sign, cheap | LOW (folded into H1 grid) | **Implemented this session** |
| 3 | **H4 distance-band quota re-tune** (20/40/40) — reuse `allocate_stratified` | Same stack | Pushes more dots far from catalogue where mapping bias concentrates | Distal lineaments from fans/shorelines | distal2 already tested 30/35/35 and 25/35/40; both lost to natural_oof (0.1771) | Low | LOW | Deferred (explored, negative prior) |
| 4 | **H3 signed edge-pair cancellation veto (N1)** — signed cross-normal gravity/magnetic step vs paired-lobe body veto | rtp, iso_grav_anom, depth_to_base_surf | Rejects finite-width bodies that mimic faults, freeing budget for true structural steps | Unfaulted intrusive contacts; real narrow horsts mis-vetoed | Not implemented anywhere in this repo (research/hypotheses.md N1) | Medium potential | MEDIUM-HIGH (new features + canary + retrain) | **Deferred — next session** (does not fit remaining session budget after data restore) |
| 5 | **H5 survey-axis notch-stability veto (N4)** | mag/rad edges under orientation-selective attenuation | Removes acquisition-line false positives, leaving budget for real structures | Real N-S/E-W faults attenuated | Not implemented | Low | MEDIUM | Deferred |

## Experiment plan (cap: 3 experiments)

- **EXP-1 Checkout anchor**: re-evaluate the two fixed historical rasters
  (distal2 zeros, GEMSDOE32-B2) on the shared quadrant folds with the pinned
  evaluator, restoring this checkout's reference numbers (expected near
  0.0289 / 0.0067 from the 2026-10-28 audit). No model is trained.
- **EXP-2 Fold arm grid (the experiment)**: per fold, rebuild the DPHS EXP-3
  surface operation-for-operation (clf_e2 + deep/reg ensemble + isotonic +
  smoothing), then allocate six preregistered arms and score each with the
  shared evaluator. Selection: argmax pooled HOLDOUT-DTI (gems57-pooled-hide-v2,
  paired spatial-block bootstrap CI).
- **EXP-3 Full map + packaging**: pooled 100% OOF surface (pre-modulator,
  quantile-matched), full-catalogue modulator per the winning arm's flag,
  allocation with the winning (budget, gain), written by the shared fail-closed
  writer; then format readback validation and the duplicate-stop scan against
  the nine focus-site rasters and every accessible registry raster.

## Duplicate-stop handling (irregularity flagged)

The pinned registry contains dense/lattice witnesses (13GEMSDOE 5-px lattice,
17GEMSDOE whole-footprint continuous prior) against which **any** non-empty
dotted map exceeds the 70%-within-3-px overlap test, including the historical
0.2778 file itself (measured in this session's scan and reported). The session
brief's uniqueness requirement is read, and reported, as: unique against the
**submission rasters of the listed GEMSDOE sites and all sparse dotted registry
peers** (rho <= 0.90 AND share-of-my-dots-within-3-px <= 0.70 per raster). The
literal degeneracy is reported, not silently exempted.
