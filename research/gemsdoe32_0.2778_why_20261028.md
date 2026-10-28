# Why did GEMSDOE32 `h33-h33-2-b2` score 0.2778, and can we beat it? — 2026-10-28

**Decision: NO FILE IS OK TO DOWNLOAD OR SUBMIT FROM THIS SESSION.** No new TIFF was generated. The method lane is still `UNASSIGNED`, the registry is not fully covered, and no holdout improvement has been measured. Evidence class for every number below is stated inline.

## 1. Sources (all checked 2026-10-28)

| Item | Link | Verified how |
|---|---|---|
| Official problem and metric page | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Fetched; DTI definition, α=0.2, β=0.8, triangular kernel R=300 m, float32 [0,1] submission rules |
| Competition rules / leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/rules/ · https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | Linked from the official page; not fetched in this session |
| Raster studied (GEMSDOE32 `h33-h33-2-b2`) | https://github.com/buffedlizard55-lab/GEMSDOE32/blob/45ee207185f72804497f7a7a392ad2c43e168f02/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif | Downloaded via `gh api` at that commit; SHA-256 `c55bafc4…ab6fa9` matches the repo's recorded hash |
| Pinned shared metric code | https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d (`src/gems57/metric.py`) | Mirror; hash-pinned in `registry/template_pins.json` |
| Catalogue and sample grids | `data/official/existing_faults.tif`, `sample_submission.tif` | Owner mirror, hash-verified; **not** organiser-authenticated |
| Measurement script and receipt | `scripts/analyze_gemsdoe32_structure.py` → `evidence/gemsdoe32_structure_20261028.json` | Reproducible; read-only |

The user-reported leaderboard value **0.2778** is `USER-REPORTED`. It is not an organiser receipt for this file.

## 2. What the official metric rewards

From the official page (Tversky-type score, distance-weighted):

- `k(d) = max(1 − d/R, 0)`, `R = 300 m = 3 px`.
- `TP_w = Σ_g max_x p(x)·k(d(x,g))` over truth pixels `g`.
- `FP_w = Σ_{p(x)>0} p(x)·[1 − max_g k(d(x,g))]`.
- `FN_w = Σ_g [1 − max_x p(x)·k(d(x,g))]`.
- `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)`.

Two consequences follow directly from this definition:

1. **A dot only helps if it is within 300 m of a truth fault.** A dot 300 m or more away has zero kernel credit and is a full false positive (weight 0.2 per unit).
2. **Recall is weighted four times more than precision (β = 0.8 vs α = 0.2).** A missed truth pixel costs 0.8. An extra dot far from truth costs only 0.2. So the metric favours broad, dense coverage of the footprint, even at a high false-positive rate.

The bar for adding one more binary dot is approximately `k_self > α·DTI`. At DTI ≈ 0.28 that is ≈ 0.056, which means almost any dot within about 2.9 px of truth still improves the score. This is the mechanism a greedy submodular allocator exploits.

## 3. Measured structure of the 0.2778 raster (HOLDOUT-DTI: none; this is a structure measurement)

Source: `evidence/gemsdoe32_structure_20261028.json`.

| Measurement | Value |
|---|---|
| CRS / shape / transform | EPSG:32611, 3730 × 3292, 100 m, origin (243350, 4508550) |
| NaN pixels | 0 |
| Unique values | {0, 1} — strictly binary |
| Positive pixels | **37,654** (matches the `37654` in the filename) |
| Positives outside the sample footprint | 0 |
| Cells outside the footprint | 0.0 (the file is zero-filled, not NaN-filled) |
| Positives on the mapped USGS/INGENIOUS fault raster | **0** of 37,654 |
| Positives strictly within 300 m of a mapped fault (kernel credit exists) | **4.28%** (1,611 of 37,654) |
| Positives at exactly 300 m (kernel weight k(R)=0, so no credit) | 560 |
| Median distance of a positive to the nearest mapped fault | **1,965 m** |
| Nearest-neighbour spacing between positives (cells) p5 / p50 / p95 | 2.83 / 3.00 / 7.21 |

Cumulative distance of positives to the mapped catalogue (strict <, metres): <300: 1,611 · <500: 4,848 · <1000: 11,140 · <2000: 19,048 · <5000: 30,125 · ≥5000: 7,529.

## 4. Why it probably scored highest (inference, labelled as such)

**Measured:** the raster places no dots on mapped faults, and only 4.3% lie within the 300 m kernel support of one. Its dots form a near-regular ~300 m spacing covering the footprint, about one dot per 137 cells.

**Inferred (not proven, because hidden labels are unavailable):**

- Under the official metric, dots that sit on a known fault earn no credit for the *new* faults the competition is scoring. Placing them there wastes budget. The 0.2778 file avoids that entirely.
- Its dots are spread over the study area, so any unmapped fault within about 300 m of a dot picks up kernel credit. The high recall weight (β = 0.8) rewards this spread.
- Its ~3-cell spacing makes the kernel credit overlap across neighbouring dots. A simple greedy allocation converges to roughly this pattern.

**Caveat:** this is one raster and one user-reported number. The "zero catalogue overlap" pattern alone does not explain the score. It must be tested against hidden or holdout truth, and the repo has not done that for this file.

## 5. Can we beat 0.2778? — not demonstrated

- The best holdout DTI in this repo is **WBG2-DISTAL, HOLDOUT-DTI 0.177029, 95% CI [0.154930, 0.197554], 60,988 withheld positives, evaluator `gems57-pooled-hide-v2`** (from `README.md`). The same holdout does not yet report a value for GEMSDOE32, so this figure cannot be compared to 0.2778 directly.
- The repo's own estimate of the distal file is 0.1067 (EMPIRICAL-ESTIMATE, 95% PI [0.0000, 0.2276]). It is not a leaderboard forecast.
- **No candidate has beaten 0.2778 on any measured holdout.**

## 6. Gates a new file must pass before it can be submitted

From `evidence/checkout_readiness.json` (regenerated 2026-10-28 with the owner-mirror inputs restored; overall **BLOCKED**, exit 2):

| Gate | Status | Why |
|---|---|---|
| Method lane | **blocked** | `UNASSIGNED`. The repo's rule is to stop, not to self-assign a lane. |
| Shared code | verified | Pinned hashes only |
| Mirror inputs | verified | Owner-mirror hashes only, not organiser-authenticated |
| Raw band cache | verified | Byte hashes only |
| Registry (uniqueness) | **blocked** | Only 13 pinned witnesses; not every current registry raster. The continuous-prior support rule is unresolved. |
| Shared format validator | **blocked** | A known mask defect is documented upstream. No upstream fix is pinned. |
| Scientific validation | not run | No feature-alone canaries or matched buffered holdout yet |
| Selector / slot | blocked | Account quota and organiser receipts are unavailable |

Local test suite after restoring inputs: **362 passed**, 37 warnings (`pytest -q`).

## 7. Irregularities for manual review

1. **Outside-footprint encoding conflict.** The official page says data outside the bounds "is null or nan". The 0.2778 raster is zero-filled outside the footprint (no NaN at all). The repo's writer also uses finite zeros. The user-reported portal error "Predicted values must be in range [0, 1]" suggests that the portal's check is not the same as the page wording. **Whether NaN or zero fill is accepted is unresolved and must be checked against an organiser receipt.** If the 0.2778 file was accepted, that is evidence that zero fill is accepted. That is user-reported, not verified.
2. **Public vs private score.** The official page says the public leaderboard uses the public test chunk. The initial prize round is scored on a private set, and the final round on an expanded label set (page 967). A public number such as 0.2778 or 0.4413 is therefore not a stable forecast for the prize.
3. **Masking claim unverified.** The pinned template's docstring says mapped catalogue faults are masked from scoring, citing an organiser thread. The official page does not say this. Treat it as unverified.
4. **Two metric-description sources.** The official page and the pinned template match on α, β, R, and the kernel. Use the official page as the reference.
5. **Dependency on the owner mirror.** The catalogue and sample grids come from the owner's GitHub mirror, not from a DrivenData download. They are hash-verified but not authenticated.
6. **Leaderboard numbers.** The 0.4413 and 0.4544 figures in the repo come from user text and a public page capture. They are not receipts.

## 8. Next step (requires a decision, not a guess)

Assign one explicit method lane from `research/hypotheses.md` (N1–N4) and decide how the continuous-prior support rule should be applied. Then run the existing pipeline: feature-alone canaries, a buffered whole-segment holdout against a matched incumbent, the literal duplicate check against every registry raster, and the shared format validator. No slot should be used before those pass.
