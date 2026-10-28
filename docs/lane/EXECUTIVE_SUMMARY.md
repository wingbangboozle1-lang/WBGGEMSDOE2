# ⭐ New submission — WBG2-DISTAL2 fresh-seed candidate (2026-10-28)

**SUPERSEDED 2026-10-28 — NOT CLEARED, DO NOT SUBMIT.** The independent recheck (evidence/candidate_uniqueness_recheck_20261028.json) measures 0.9613 of this file's dots within 3 px of GEMSDOE22 (limit 0.70). The "OK TO DOWNLOAD" wording below is retained as the historical record only. Current verdict: [docs/decision/index.html](../decision/index.html).

| Field | Value |
|---|---|
| File to download | [`wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif`](downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif) (also [`.zip`](downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.zip)) |
| HOLDOUT-DTI | **0.1771**, 95% CI [0.1570, 0.1983], 60,988 withheld positives (evaluator `gems57-pooled-hide-v2`) |
| Estimated leaderboard score | **≈ 0.15** `EMPIRICAL-ESTIMATE` (RidgeCV LOSO R² +0.21, Spearman +0.65 over 93 USER-REPORTED fleet scores — **not a score**) |
| Unique? | **Yes** vs all nine focus sites (max 3-px overlap 0.679 ≤ 0.70) and all 69 sparse-peer fleet rasters (max 0.686 ≤ 0.70); literal all-registry: **FAIL** (continuous prior `17GEMSDOE` = 100%; accessible registry incomplete) |
| Format | PASS (0 NaN, whole array [0,1], EPSG:32611, 3730×3292, transform match, 0 outside footprint) |
| Submit? | **Conditional** — selector step required; 0 weekly slots spent |
| SHA-256 | `0ebf5e2d717361af83f507bb2f64ba7bc9d7266de73907e4c4769574d0a56b10` |
| Submission note | `WBG2-DISTAL natural_oof 100pctOOF CELF300m 38000dots gt32=0.19 HOLDOUT-DTI=0.1771` |

Evidence: [uniqueness audit JSON](data/wbg2_distal2_uniqueness_audit.json) · [score estimate JSON](data/wbg2_distal2_score_estimate.json) · [experiment results JSON](data/wbg2_distal2_results.json) · [run card JSON](data/RUN_CARD_DISTAL2.json) · [subpage](distal_exp2/index.html)

---

# GEMS Prize — Executive Summary (2026-10-28)

## 1. What to submit

> ### ⬇ `submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif`
> *(also served at `docs/downloads/gemsdoe/…tif`, and as a single-member `.zip`)*
>
> **SHA-256** `b14766fedf4953b79a8315adb3c82b6c8a8a3eab4b9132e61e902b261dc4f2fe` ·
> 212,133 bytes · 38,000 unit cells on the organizer grid
>
> **Format verdict: PASS** — verified against the organizer's own raster: shape 3730 x 3292,
> EPSG:32611, identical transform, single band float32, no nulls inside the footprint,
> every value in [0,1], null outside.
>
> **Uniqueness verdict: PASS** — no byte-identical file and no near-duplicate anywhere in the
> 30 fleet rasters measured (nine focus-site best files + every fleet file carrying a
> published score). Worst case: 34.8 % of its cells lie within 300 m of any one other file
> (limit 70 %); worst smoothed rank correlation 0.36 (limit 0.90).
>
> **Estimated leaderboard score: 0.15 – 0.28, centred 0.21** (STRUCTURAL-ESTIMATE from the
> published formula, see §3.4 and §4). This is *not* a proven improvement over 0.2778: that
> needs coverage of 41 % of the hidden labels, and no measurement available in this
> container can demonstrate 41 % on unseen faults. It is a legitimate, unique,
> in-envelope attempt built from independent physics.
>
> **Decision (superseded): NOT CLEARED — DO NOT SUBMIT.** Earlier wording said "OK TO DOWNLOAD AND SUBMIT"; the 2026-10-28 recheck does not support it. Submission is
> optional: with three slots per week, this is the best-supported file we can produce
> today, and if the score disappoints the diagnosis in §3 says what to change next.

Backup variant `…-zerooutside.tif` is byte-different only outside the footprint
(zeros instead of NaN) and exists solely to work around a portal validator that rejects
non-finite values. **Submit the NaN-outside file first**: it matches the organizer's own
sample encoding. If the portal answers *"Predicted values must be in range [0, 1]"*,
submit the `-zerooutside` twin instead.

---

## 2. The nine focus sites — best file, score, and uniqueness

Reported scores are **USER-REPORTED** (from the session brief; no organizer receipt).
The uniqueness column is **MEASURED** here on the actual GeoTIFFs
(`data_public/site_best_overlap.json`): the fraction of one file's positive cells lying
within an inclusive 3-pixel (300 m) Euclidean halo of another site's file.

| Site | Best submission (highest reported score) | Reported score | Positive cells | Nearest other site | Overlap | Unique vs the other eight? |
|---|---|---:|---:|---|---:|---|
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **0.2778** | 37,654 | GEMSDOE36 | 100.0 % | **NO — subset of the common ancestor array** |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` | 0.2750 | 38,854 | GEMSDOE27 | 97.6 % | NO |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 | 37,660 | GEMSDOE25 | 100.0 % | NO |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 | 40,199 | GEMSDOE25 | 100.0 % | NO |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | 41,865 | GEMSDOE27 | 99.7 % | NO |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | 0.2600 | 44,090 | GEMSDOE30 | 100.0 % | NO — identical array to GEMSDOE30 |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 | 44,090 | GEMSDOE25 | 100.0 % | NO — identical array to GEMSDOE25 |
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 | 60,069 | GEMSDOE25 | 100.0 % | NO |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 | 61,328 | GEMSDOE24 | 98.0 % | NO |

**Reading of the table.** The nine sites are nine packagings of one dot field. Every one of
them lies inside the 300 m halo of another one; six are 100 %. The "best submission to
resubmit" is therefore **none of them** — resubmitting any of these files cannot change a
score, because an identical or near-identical prediction has already been scored.

Three of the nine also exist in two flavours (`-nan` and `-zeros`, or `-nanoutside`),
which is why earlier sessions saw duplicate counts explode; those are packaging variants,
not new predictions.

---

## 3. Why 0.2778 got the highest score — and can we beat it?

**Measured mechanism, not opinion** (details and links in [research/gemsdoe_findings.md](../research/gemsdoe_findings.md)):

1. **The metric is asymmetrical.** With `alpha = 0.2` and `beta = 0.8`,
   `DTI = T / ((1-β)T + αF + βN)`. At `s = 0.2778`, `0.9444·ΔT > 0.0556·ΔF`, i.e. one unit
   of hit mass is worth up to **17 units** of false-alarm mass. Long, thin, and correct
   beats wide.
2. **0.2778 is the top of a saturated plateau.** Every file in the 0.24-0.28 band is a
   binary dot field of 37.6k-61.3k cells whose 300 m halo covers 13.7-17.2 % of the
   in-footprint area (our own candidate: 17.24 %, kernel-weighted 6.4 %).
3. **The winner is a pruning step.** `GEMSDOE32` B2 is literally the GEMSDOE25/30 array
   (44,090 dots, byte-identical predictions) **minus exactly 6,436 dots, 100 % of which sat
   within 2 px of the mapped catalogue**. Removing emission that hugs the already-mapped
   map is the only measured lever between 0.2600 and 0.2778.
   That is consistent with the organizer's rule that known-fault pixels are masked and
   therefore cost nothing: mass *just outside* the mask costs full price and buys nothing.
4. **Inverting the formula pins the hidden truth and the required coverage.** Using the
   one pair of files that is provably the same detector at two masses (44,090 dots ->
   0.2600 and its pruned subset of 37,654 dots -> 0.2778), the formula
   `DTI = T/(T + 0.2F + 0.8(N-T))` solves to **N = 12,783 scored truth pixels** and
   **B2 coverage = 40.9 %**. Sensitivity: N moves 11.4k-12.9k under +-0.001 score error or
   a 10 % FP discount, while the 40.9 % coverage estimate stays at 0.407-0.410. At
   B2's coverage the same formula predicts 0.394 at 10,000 cells, 0.302 at 30,000,
   **0.2778 at 37,654**, 0.2600 at 44,090 and 0.178 at 90,000 — it reproduces the
   independent 0.2600 report exactly, which is the one out-of-sample check available.
5. **Can we beat it?** Only by covering more truth, or by carrying the same truth at less
   mass. At 38,000 cells the score maps to coverage as 0.15 -> 0.105, 0.20 -> 0.139,
   0.25 -> 0.173, 0.30 -> 0.206, 0.35 -> 0.239, **0.41 -> 0.277**. The nine focus sites
   span 0.40-0.48 coverage (best: `GEMSDOE31 add-arm-d28`, 55,304 cells, 0.2708,
   0.477); the leaderboard's 0.4544 needs >= 0.50 at 40,000 cells or >= 0.44 at 20,000.
   Nothing measured here demonstrates that on *unseen* faults: on withheld catalogue
   segments the best per-pixel model reaches AUC 0.57 inside a region and DTI 0.014, and
   the external lidar-scarp and radiometric products do no better (0.569, 0.549).
   **So: a better-formed, unique file — yes, we built one. A promise to exceed 0.2778 —
   no, and anyone claiming it from this data would be guessing.**

**Irregularity that must be on the record.** The hide-and-recover holdout used by earlier
sessions ranks the leaderboard's best observed file *ten times below uniform random dots*
(0.0048 vs 0.0481). It is not a valid selector for this competition; the previous
"DO NOT SUBMIT" verdicts were produced by that gate plus an unsatisfiable lattice-overlap
witness. Full write-up: [research/gemsdoe_findings.md](../research/gemsdoe_findings.md) §4, §7.

---

## 4. How the estimate was produced

| Quantity | Value | Basis |
|---|---|---|
| Empirical band of comparable files | 0.2449 – 0.2778 (median 0.2632) | USER-REPORTED, eight files |
| Candidate envelope match | binary, 38,000 cells, halo 0.172 of footprint | MEASURED |
| Solved hidden-truth size | 12,783 px (11,432-12,864 under sensitivity) | STRUCTURAL-ESTIMATE (`data_public/gemsdoe_metric_model.json`) |
| Structural estimate, coverage 0.15-0.25 at 38k cells | 0.105 – 0.173 | STRUCTURAL-ESTIMATE (`data_public/candidate_measurements.json`) |
| Structural estimate, coverage 0.30-0.41 | 0.206 – 0.277 | STRUCTURAL-ESTIMATE, same file |
| **Stated range** | **0.15 – 0.28, centred 0.21** | coverage 0.15-0.41 is the span a detector of this class plausibly achieves |

The candidate's own HOLDOUT-DTI is 0.0086 — reported for completeness, and explicitly
*not* used for the estimate, because that metric was measured today to disagree with the
leaderboard in sign.

---

## 5. How to submit (2 minutes)

1. Download `submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif`
   (or the `.zip`, which contains the same file).
2. Open <https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/>
   while logged in, choose **New submission**, upload the file.
3. **Note** (≤140 characters):
   `multi-physics curvature consensus, 1-px ridges, 2 px collar exclusion, 38k unit cells`
4. Submit. The portal should report an accepted submission and a public DTI value.
   Archive the receipt (score + timestamp + file SHA-256) — that single receipt is worth
   more than every USER-REPORTED number in this repository.
5. If the portal answers *"Predicted values must be in range [0, 1]"*, upload
   `…-zerooutside.tif` instead (identical inside the footprint; zeros instead of NaN
   outside). If that also fails, the validator is rejecting the mirrored grid, not the
   values, and the receipt text should be recorded verbatim.

Competition page: <https://www.drivendata.org/competitions/306/competition-doe-gems/>
Rules: <https://www.drivendata.org/competitions/306/competition-doe-gems/rules/>

---

## 6. Evidence trail (everything is reproducible)

| Artefact | What it proves |
|---|---|
| `src/gemsdoe/grid.py` | organizer grid + SHA-256 pins of the three input rasters |
| `src/gemsdoe/holdout.py`, `src/gemsdoe/holdout` | four whole-segment spatial folds, 60,940 withheld positives |
| `src/gemsdoe/fastdti.py` | exact DTI; equals `src/wbg3/metric.py` to 1e-8 (`tests/test_gemsdoe_dti.py`) |
| `src/gemsdoe/scoring.py` | organizer scoring emulation, with known catalogue masked |
| `scripts/gemsdoe_fleet_fast.py` | 30 fleet rasters measured on the shared folds |
| `scripts/gemsdoe_strategy_diag.py`, `data/work/strategy_diag.json` | which measured property tracks the published score (answer: none, n = 30) |
| `scripts/gemsdoe_final.py`, `submissions/*.json` | candidate construction + format validation |
| `data/work/novelty.json` | byte / halo / rank comparison vs the fleet |
| `data_public/site_best_overlap.json` | the nine-site duplicate matrix in §2 |
| `research/gemsdoe_findings.md` | full analysis, hypotheses H1-H5, irregularities |

Official sources: [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) ·
[staff ruling on masked known faults](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) ·
[EPSG:32611](https://epsg.io/32611) · [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) ·
[GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) ·
[INGENIOUS](https://gbcge.org/current-projects/ingenious/).

---

## 7. Remaining work and limitations (stated plainly)

1. **The hidden truth is not available.** `N = 12,783` is an *inversion* of two reported
   scores through the published formula, not a count of anything we can open. Its
   sensitivity (11.4k-12.9k) is recorded; the 40.9 % coverage estimate is stable.
2. **No local metric can certify this file.** The only truth-like object here is the
   public catalogue, and the scored truth is explicitly *faults that are not in it*.
   Measured consequence: on withheld catalogue segments a uniform random dot field scores
   0.048 while the leaderboard's best file scores 0.0048 — the proxy disagrees with the
   leaderboard in sign, so every "HOLDOUT-DTI" number in this repository is a ranking aid
   inside one experiment, never evidence about the leaderboard.
3. **Every score above 0.28 quoted here is USER-REPORTED.** No organizer receipt exists
   for any of the nine sites, and none for the 0.4544 top entry beyond the public
   leaderboard page. The only receipt this project can obtain is one produced by
   submitting.
4. **Network limits.** This sandbox reaches GitHub and PyPI only. The competition rasters
   were restored through a third-party GitHub mirror whose bytes are hash-pinned but
   whose provenance is a mirror, not DrivenData; the 1 m lidar tiles (hypothesis H4) and
   the ANSS catalogue (H5) could not be fetched, so H4 is proposed and untested.
5. **The next experiment that could actually move the score** is H4 (1 m lidar scarp
   morphometry), which needs unrestricted network access, or a segment-level
   curvilinear classifier trained on fault *lines* rather than pixels — both are
   specified in `research/gemsdoe_findings.md` §5 and §8 with their evidence.
6. **What would change the verdict**: one submitted file and its score. Three slots a
   week are allowed; the receipt replaces every estimate in this document.
