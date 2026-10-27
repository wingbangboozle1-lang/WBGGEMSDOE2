# CBS campaign findings — 2026-10-27 (fifth lane)

Full machine records: `evidence/cbs_results.json`, `evidence/cbs_final.json`,
`evidence/cbs_canaries.json`, `evidence/RUN_CARD_CBS.json`. Pre-registration:
`research/cbs_preregistration_20261027.md` (including its amendment).

## What was tested
Subsurface-only blind-fault detection (Covered Basement Step): 11 potential-field /
depth / conductivity bands + 6 label-free physics operators, no topographic predictors,
vs a 19-raw-band control — all arms emitted identically as collar-free (>3 px from
visible catalogue) spaced dots (suppression radius 5 px, kmass/dot ≈ 9.31 of max 9.38).
Evaluator: unmodified shared `gems57-pooled-hide-v2`, `label-blind-quadrants-v2` folds,
buffer 80 px, 60,988 withheld positives, paired 20 km spatial-cluster bootstrap.
Canaries: 28 features × 4 folds, max two-sided AUC 0.6134 (`tc_radiometric`) ≤ 0.90.

## Results (HOLDOUT-DTI, pooled)
- CTRL-19B-dotted **0.1349** [0.1214, 0.1467] — 3.2× the previous same-evaluator repo
  best (MSPTCD EXP-3, 0.0426). The gain is overwhelmingly an *emission* effect:
  MSPTCD's final mask is 389 connected ridges at kmass/dot 1.606 (measured from its
  bytes this session), so ~83% of its kernel coverage was spent on redundant
  neighbours. Same-budget dots cover ~5.8× more kernel mass per dot.
- EXP-1 CBS-core 0.0990, EXP-2 CBS-cover 0.0995, EXP-3 CBS-active 0.0971 — all beat the
  previous repo best but lose to the control with paired CIs excluding 0.
  **The CBS geological hypothesis is a negative result**: removing topographic
  predictors hurts catalogue hide-and-recover, because the catalogue itself is a
  surface-expression product. On the low-relief stratum (withheld positives with
  slope ≤ catalogue median; N=30,494) the cover-gated CBS arm ties the control
  (0.0920 vs 0.0915; Δ CI includes 0) — the gate works on the subpopulation it was
  designed for, but the surface behind it is weaker elsewhere.

## Candidate built (Pass 2)
`wbg2-d19dotted-38000dots-20261027T191824Z-cb2f6ff4-zeros.tif`
(sha256 `7c9915f6…6a36`): cross-fitted CTRL surface, 38,000 dots, zero within 3 px of
the catalogue, all-finite [0,1] everywhere (0.0 outside footprint, nodata unset).
The campaign's holdout budget sweep was monotone to 64,284 dots; that artifact was
superseded and deleted because every live measurement penalises dot count
(score law −0.000775/1,000 dots, refit this session, R²=0.988 on the nine champions).
Holdout validates *where*; live-calibrated mass balance sets *how many*.
Candidate 38k-rule HOLDOUT-DTI = 0.1336 [0.1219, 0.1463].
Estimates (never scores): EMPIRICAL-ESTIMATE 0.268 [0.085, 0.452]; PROJECTION
(score law) 0.282; DERIVED mass-balance band 0.270–0.311 at N=20,000.
Central tendency ≈ 0.27–0.28: around/above the best historical GEMSDOE file
(0.2778 USER-REPORTED), below the current public top-20 (≥0.3273 observed
2026-10-27; #1 = 0.4544). No claim of beating 0.3195/0.4413/0.4544 is supported.

## Uniqueness
Max 32.8% of candidate dots within 3 px of any of the nine focus champions (limit 70%);
22.6% vs DZ-16, 19.9% vs H3-PACK, 4.6% vs MSPTCD-E3; max |surface Spearman| vs discrete
peers 0.116 (limit 0.90). Literal witnesses: 13GEMSDOE lattice 99.2% overlap against a
99.87% footprint coverage (enrichment 0.993); 17GEMSDOE dense prior 100% against 100%
coverage (enrichment 1.000, ρ=0.525). The literal rule is mathematically unsatisfiable
by any ≥22k-dot field and flags all nine champions; both readings are published.

## Why B2 (0.2778 USER-REPORTED) led the nine — verified again this session
Nine rasters re-fetched by pinned git blob, SHA-256 all match. They are one lineage:
83–100% mutual 3-px overlap. Score law refit on measured (dots, collar):
`0.3120 − 0.000776·(dots/1000) − 0.0901·collar`, R²=0.988, max residual 0.0025.
B2/GEMSDOE32 = fewest dots (37,654) + smallest collar (5.8%); its mask is the shared
44,090-dot mask with ≤2 px-to-catalogue dots deleted. Under the exact identity
FN_w = N − TP_w, mass that does not add a new hit within 300 m is pure α=0.2 cost,
and dots on already-mapped faults can never earn (organizers mask known faults).

## Irregularities flagged
1. H3-PACK "-zeros" file actually carries 7,111,787 NaNs (nodata=NaN) outside the
   footprint — a plausible cause of the user's portal "[0,1]" rejection. Not submittable as-is.
2. Feature-stack mirror size differs between lanes (418,912,844 B verified here,
   sha256 4371c82e…; MSPTCD lane cited 439,405,361 B). Grid/bands agree; source is an
   owner mirror, not an authenticated DrivenData download.
3. The mirrored sample grid's positives equal the catalogue exactly — grid reference only.
4. Prompt leaderboard highs 0.4413 and 0.3195 are both superseded by the official page
   observation of 0.4544 on 2026-10-27 (`evidence/public_leaderboard_observation_20261027T1904Z.json`).

## Next steps / limitations
- Owner/selector decides the weekly slot; submit D19-DOTTED first, keep DZ-16 as the
  independent alternate (different surface, overlap 22.6%).
- The one experiment that could change the ranking: a rank-blend of CTRL and CBS-cover
  surfaces (they tie exactly on low-relief truths) — needs a new pre-registered
  3-experiment budget; do not silently blend an untested arm into a submission.
- Live truth size N is unknown; all live estimates inherit ±0.09 RMSE. One organizer
  receipt for the D19 file would replace every estimate in this repo with a measurement.
