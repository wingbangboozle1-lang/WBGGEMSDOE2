# Executive summary — GEMS Prize Challenge (DOE / DrivenData competition #306)

**Repo:** https://github.com/wingbangboozle1-lang/WBGBGEMSDOE2
**Branch:** `arena/3dc38570-wbggemsdoe2`
**Competition:** https://www.drivendata.org/competitions/306/competition-doe-gems/
**Metric:** distance-weighted Tversky index (DW-Tversky), α=0.2 (FP), β=0.8 (FN), triangular kernel R=300 m (3 px at 100 m) — see [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric).
**Submission format:** single-band float32 GeoTIFF, EPSG:32611, 100 m, identical bounds/transform to the training grid, values in [0, 1], no NaN (zeros outside footprint) — [format spec](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format).
**Live leaderboard (fetched 2026-10-26):** #1 xiaofanhu **0.4437** DW-Tversky (public leaderboard; round 1 is scored on a *private* expert-labeled test set) — https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

---

## 1. File to download — our generated submission

| | |
|---|---|
| **GeoTIFF (click to download)** | [wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif](../downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif) (17.5 MB) |
| **.zip (single TIFF inside)** | [wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.zip](../downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.zip) (17.5 MB) |
| **Run card (JSON)** | [reports/wbg-h1-..._run_card.json](../reports/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros_run_card.json) |
| **Uniqueness audit (JSON)** | [reports/wbg-h1-..._audit.json](../reports/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros_audit.json) |
| **SHA-256** | `95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad` |
| **Submission name** | `wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros` |
| **Submission note (121/140 chars)** | `WB-H1 blind-conduit-breach unique | format-valid | holdout-DTI blocked: labels.tif needs DrivenData login | DO NOT SUBMIT` |

### ⚠️ Is it OK to download and submit this TIF?

**Download: YES.** **Submit to DrivenData: NO — not yet.**

| Gate | Result |
|---|---|
| Format (strict validator: CRS/shape/transform/float32, finite [0,1], zeros outside footprint) | ✅ PASS |
| Lane uniqueness vs 58-raster registry (Spearman |ρ| ≤ 0.90; ≤ 70% of dots within 3 px of any one registry raster) | ✅ PASS (max \|ρ\| = 0.0021; max 3-px overlap = 21.72%) |
| HOLDOUT-DTI (hide/recover, α 0.2, β 0.8, 300 m triangular kernel, 95% spatial-block CI) | ❌ BLOCKED — `labels.tif` requires DrivenData login; not available in this environment |
| Verdict | **negative — do not spend a weekly submission slot** until holdout-DTI beats the repo best |

This file is **unique**: it is *not* a copy of any previous GEMSDOE submission (the GEMSDOE32 champion family, `h33-h33-2-b2-...-zeros`, the `dotted-h19-5` family, the `topo-gap-closure` family, the `anderson-geothermal-pinn` family, etc.). It was generated from hypothesis **H1 — blind-conduit hydrothermal breach** (see `hypotheses.md`), which targets faults missing from the USGS/INGENIOUS catalogue and is not seeded from any catalogue fault.

> **No score is claimed for this file.** Per the parallel-run protocol rule 3, a projection is never written as a score. HOLDOUT-DTI cannot be computed without `labels.tif` (DrivenData login required — see `scripts/download_competition_data.sh`). Any number you see elsewhere for this raster would be a fabrication until holdout scoring runs.

---

## 2. Focus sites — highest-scoring submissions (GEMSDOE24/25/27/28/30/31/32/33/36)

Scores below are **owner-reported live scores from the submission pages** as listed on the GEMSDOE sites (no organizer receipts linking raster hash → score are present in those repositories; treat as owner-reported, not ORGANIZER-CONFIRMED). Estimates are source-page LLI leave-one-out **projections, not scores**. Uniqueness is as reported by the source site vs other listed GEMSDOE submissions.

| Site | Best file (download) | Live score | Estimate (projection, not a score) | Unique vs listed GEMSDOE sites? |
|---|---|---|---|---|
| GEMSDOE32 | [h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE32/8953b986b2ce6eb5ee8b7eda23fe3ad529720986/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | **0.2778** (owner-report) | 0.285 projection | ❌ No — duplicate family (25 listed files >70% within 3 px) |
| GEMSDOE36 | [anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE36/b90418f852615aa0974cf9a53b92fa569ed133fc/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | **0.2750** (owner-report) | 0.283 projection | ❌ No — duplicate family |
| GEMSDOE28 | [h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE28/9c1be21e8f1be707347f737e42abf62ea669c819/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | **0.2710** (owner-report) | 0.277 projection | ❌ No — duplicate family |
| GEMSDOE31 | [h27-4-solo-d28-20261004-8acb75e1-nan](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE31/78f9bf3ae82e5c78ca348aa37c0660c339e72f0e/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | **0.2708** (owner-report) | 0.279 projection | ❌ No — byte-identical to GEMSDOE28 submission; duplicate family |
| GEMSDOE33 | [h33d-analog-tip-stepover-r30-20261004-cb490425926e](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE33/a24fb7c5031ee08b12440af4593057858fecef8e/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | **0.2632** (owner-report) | 0.278 projection | ❌ No — duplicate family |
| GEMSDOE25 | [dotted-h19-5-d2-8-20261002-e56ea318af89-nan](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE25/bfb2dfdbdf1b87d67afc6facd422180f56ebc455/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | **0.2600** (owner-report) | 0.271 projection | ❌ No — byte-identical to GEMSDOE29 submission; duplicate family |
| GEMSDOE30 | [d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE30/35ce8911e2c3287eed973eacd12c252e8cb3f34c/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | **0.2600** (owner-report) | 0.271 projection | ❌ No — byte-identical to GEMSDOE25 submission; duplicate family |
| GEMSDOE24 | [h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE24/5cfab74597cd1d0a271e4640b4cc34511e56ca59/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | **0.2477** (owner-report) | 0.268 projection | ❌ No — duplicate family |
| GEMSDOE27 | [topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan](https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE27/f1e32af867d9cf0081af20866c8241ec8678a432/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | **0.2449** (owner-report) | 0.266 projection | ❌ No — duplicate family |
| **WBGGEMSDOE2 (this repo)** | [wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif](../downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif) | unscored | **blocked** (no labels.tif) | ✅ Yes — audited vs 58-raster registry |

**Best focus-site score: GEMSDOE32 `h33-h33-2-b2-...-zeros` at 0.2778 (owner-reported).** It is already submitted; re-submission spends a slot and adds no information.

---

## 3. Why did GEMSDOE32 `h33-h33-2-b2-...-zeros` (0.2778) score highest, and can we beat it?

**Hypothesis (not verified — no organizer receipt):** The `*-zeros` convention (NaN → 0 outside the footprint) keeps every cell finite and inside [0, 1], which passes the submission validator that produced the "Predicted values must be in range [0, 1]" error. The 0.2778 file is a dense dot field (37,654 dots per the GEMSDOE32 page) built on the h33/h38-family detection style. Because the DW-Tversky metric penalizes false negatives heavily (β = 0.8) and false positives lightly (α = 0.2), a broad, dense dot field over the survey area can recover many withheld fault pixels at modest FP cost. The name suffix `-zeros` and `-nan` twins across sites suggest format variants of the same raster, not independent methods.

**Can we beat 0.2778?** Not yet, and not by copying: the GEMSDOE32 lane's own newer unique file (H47, LLI-unique coupling) was projected *below* the champion (0.240–0.248) and lost on HOLDEOUT-DTI, so it was correctly held back. Beating 0.2778 requires a holdout-validated gain; our H1 generator is experiment 1 of 3 (protocol budget) and is currently **negative** because holdout scoring is blocked by the missing `labels.tif`.

**Unblocking path:** stage `training_features.tif`, `labels.tif`, `sample_submission.tif` (and `1m_DEM_links.csv`) into `data/` — see `scripts/download_competition_data.sh` (DrivenData login required; official page redirects to login). Then:
1. `python scripts/prepare_data.py --data-dir data`
2. `python scripts/evaluate_holdout.py --labels data/labels.tif --prediction downloads/....tif --features data/training_features.tif --report reports/holdout.json`
3. Promote to a submission slot only if holdout-DTI + 95% CI beats the same-evaluator repo best (protocol rule 6).

---

## 4. How to make a submission (step by step)

1. Create a DrivenData account and sign in at https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (data files require login).
2. Download `sample_submission.tif` — this is your format template (CRS EPSG:32611, 100 m, bounds, transform).
3. Generate predictions as a single-band GeoTIFF matching the sample's CRS/shape/geotransform exactly, float32, values in [0, 1], no NaN (use 0 outside the survey footprint).
4. Validate locally **before** uploading:
   ```
   python scripts/submission_writer.py --check your_file.tif --reference data/sample_submission.tif
   ```
   Every check must PASS (this is what caused the "Predicted values must be in range [0, 1]" error on a prior attempt).
5. On the submission page: choose File (single `.tif` or a `.zip` containing one `.tif`), enter a Note (≤ 140 chars, e.g. "clustering with k=25"), and submit.
6. Choose which single submission to score across both prize rounds before the deadline (round 1 = private test set; round 2 = expanded expert-verified label set).

---

## 5. Sources (official, verified)

- Competition problem & metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- About page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/
- Data page (login required): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Rules: https://www.drivendata.org/competitions/306/competition-doe-gems/rules/
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- GEMS_96647.pdf (submission procedure): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- GeoDAWN survey (USGS): https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- INGENIOUS (GBCGE): https://gbcge.org/current-projects/ingenious/
- EPSG:32611: https://epsg.io/32611
- GEMS data submission (GDR): https://gdr.openei.org/submissions/1391
- Tversky index: https://en.wikipedia.org/wiki/Tversky_index

---

## 6. Limitations

- No DrivenData credentials are available in this environment, so `training_features.tif`, `labels.tif`, and `sample_submission.tif` cannot be downloaded; HOLDEOUT-DTI and the leakage canary (AUC > 0.90 → leakage) cannot be run end-to-end yet.
- The leaderboard is public-test-set; round 1 scoring is on a private label set — public scores are only indicative.
- GPU is needed to train the reference U-Net; metric/loss/validation code is CPU-verified here.
- Weekly submission cap applies; promotion to a real slot is a separate selector step.
