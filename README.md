# WBGGEMSDOE2 — DOE GEMS Prize (`WBG2-HVGF` Verified Submission & Multi-Site Audit)

**Current status (2026-10-27 UTC):** Exactly **one** GeoTIFF in this repository is cleared as **`OK TO DOWNLOAD AND SUBMIT`**, validated end-to-end with zero human-inspector intervention across all 15 byte/grid/CRS/finite-`[0, 1]` checks and across `592` fleet reference rasters (`382` distinct decoded arrays). All legacy and peer files are explicitly quarantined as **`DO NOT SUBMIT`**.

---

## ✅ `OK TO DOWNLOAD AND SUBMIT` — Single Approved Submission (`WBG2-HVGF`)

| Field | Verified Value (`LOCAL-FORMAT-MEASUREMENT` / `HOLDOUT-DTI`) |
|---|---|
| **Submission Status** | **`OK TO DOWNLOAD AND SUBMIT`** (`verdict = "promote"`, `0` live competition slots consumed) |
| **Approved GeoTIFF (`.tif`)** | [`docs/downloads/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif`](docs/downloads/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif) (`136,232` bytes; exact mirror in `downloads/`) |
| **Approved Single-TIFF ZIP (`.zip`)** | [`docs/downloads/hvgf/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.zip`](docs/downloads/hvgf/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.zip) |
| **GeoTIFF SHA-256** | `2262aa7e543690c27a307efdd3a0bd15357cd917bac265da32b8a3cf792c4080` |
| **Single-TIFF ZIP SHA-256** | `dce3f3728c67ea23a780c312561bf998a2773596b9a0fbc66fe3fbabf54acc9e` |
| **DrivenData Note (`116 / 140` chars)** | `WBG2-HVGF E3: OOF hydrothermal vent back-proj + K/Th-demag + 1m/10m scarp/chi + 2-host relay submod (37654d, 0 NaN).` |
| **Format & `[0, 1]` Portal Safety** | 1-band `float32` · `EPSG:32611` · `3730 × 3292` (100 m) · **`0` NaN anywhere** · **`0` Inf anywhere** · **`0.0` outside footprint** · `nodata = None` · values strictly in `[0.0, 1.0]` · `37,654` non-touching `1.0` dots (`touching = 0`, `d_cat > 2.8 px`) |
| **Instrument A (`8 km` Spatial Quadrant Holdout)** | **`HOLDOUT-DTI = 0.1156`** (`95% CI [0.0982, 0.1332]`, `60,988` withheld positives, evaluator `gems57-pooled-hide-v2` — **`4.03×`** 19-band control `0.0287`, **`2.71×`** `MSPTCD E3` `0.0426`, and exceeding peer benchmark `GEMSDOE70` `0.1100`) |
| **Instrument B (Within-Network Component Hide)** | **`HOLDOUT-DTI = 0.0207`** (`95% CI [0.0127, 0.0303]`, `11,321` withheld positives — **`2.76×`** 19-band control `0.0075`) |
| **Instrument C (Blind SGMC Concealed Piedmont)** | **`HOLDOUT-DTI = 0.0528`** (`95% CI [0.0368, 0.0717]`, `3,292` independent USGS SGMC Cenozoic piedmont fault pixels — **`+29.7%`** over `DZ-16` `0.0407` and **`7.04×`** over `MSPTCD E3` `0.0075`) |
| **Single-Feature Leakage Canaries** | **`364 / 364` PASS** (`91` features × `4` folds; max two-sided ROC-AUC = **`0.6261 <= 0.90`** on `det_elev_lrm`) |
| **Uniqueness Across `592` Rasters** | `0` SHA-256 matches · pre-placement `|Spearman| <= 0.2149` · smoothed `|Pearson| <= 0.4212` · max discrete-peer 3-px overlap = **`45.10%`** (`<= 70%`) · 9 focus sites overlap = **`24.3%–29.8%`** (`<= 70%`) · **`0` enriched violations** |
| **JSON Run Card & Research Docs** | [`evidence/RUN_CARD_HVGF.json`](evidence/RUN_CARD_HVGF.json) · [`research/hvgf_hypotheses.md`](research/hvgf_hypotheses.md) · [`research/hvgf_findings.md`](research/hvgf_findings.md) |

**GitHub Pages Portal:** <https://wingbangboozle1-lang.github.io/WBGGEMSDOE2/>  
Direct pages: [Submission & Download (`docs/submission/index.html`)](docs/submission/index.html) · [Executive Summary & Multi-Site Table (`docs/submission/executive-summary.html`)](docs/submission/executive-summary.html) · [How to Submit to DrivenData (`docs/submission/how-to-submit.html`)](docs/submission/how-to-submit.html) · [PhD Method & Metric (`docs/submission/methodology.html`)](docs/submission/methodology.html) · [Official Sources (`docs/submission/sources.html`)](docs/submission/sources.html).

---

## ⛔ `DO NOT SUBMIT` — Quarantined Legacy & Historical Rasters

| File | Gate Status | Exact Technical Reason |
|---|---|---|
| `docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif` | **`DO NOT SUBMIT`** | **Root cause of DrivenData `"Predicted values must be in range [0, 1]"` error:** legacy `scripts/write_h3_submission.py:57` wrote `7,111,787` `NaN` pixels outside footprint (`nodata=nan`). DrivenData checks `((pred >= 0) & (pred <= 1)).all()` where `NaN >= 0` is `False`. Upstream writer & `src/wbg3/validate.py` are now fixed and regression-tested in `tests/test_wbg3_validate.py`. |
| `docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif` | **`DO NOT SUBMIT`** | Superseded catalogue-only geometric baseline (outscored on blind SGMC piedmont faults `0.0407 -> 0.0528` by `WBG2-HVGF`). |
| `docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif` | **`DO NOT SUBMIT`** | Superseded 19-band MSPTCD research raster (outscored `0.0426 -> 0.1156` on 8 km quadrant holdout and `0.0075 -> 0.0528` on blind SGMC piedmont faults by `WBG2-HVGF`). |
| `docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif` | **`DO NOT SUBMIT`** | Contains `5,132,809` `-9999.0` sentinel pixels inside footprint + `99.4%` lattice overlap. |
| All 9 historical priority-site files (`GEMSDOE24..36`) & peer fleet rasters | **`DO NOT SUBMIT`** | Historical peer submissions (`83%–100%` mutual 3-px overlap on shared `H19-5` surface; several contain `-nan` outside footprint). Never copy or re-upload previous submissions. |

---

## Executive Auditable Table — Promoted `WBG2-HVGF` vs. Nine Priority Sites

Full 144-row broader ledger: [`docs/data/user-reported-ledger-20261027.csv`](docs/data/user-reported-ledger-20261027.csv) (live public leaderboard #1: `xiaofanhu` `0.4544` `ORGANIZER-PUBLISHED`; highest `USER-REPORTED` broader fleet entry: `GEMSDOE100` `0.3195`).

| Site / Lane | File & Verified SHA-256 Prefix | Score / Holdout Metric (Strictly Labeled) | Geometry Model Estimate (`±0.18`) | Dots (`d_cat` median) | Unique Across GEMSDOE Sites? | Action |
|---|---|---|---|---:|---|---|
| **`WBGGEMSDOE2` (`WBG2-HVGF E3`)** | [`wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif`](docs/downloads/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif) (`2262aa7e543690c2…`) | **`0.1156` `HOLDOUT-DTI`** (8 km quad) · **`0.0528` `HOLDOUT-DTI`** (SGMC piedmont) · **`0.0207` `HOLDOUT-DTI`** (network) | `0.068` geom-only (`0.271–0.311` mass-balance band at N=20k) | `37,654` (`27.9 px`) | **YES** (`24.3%–29.8%` vs 9 focus; `<=45.1%` vs all discrete peers) | **`OK TO DOWNLOAD AND SUBMIT`** |
| `GEMSDOE32` | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (`087fb3f601d83804…`) | `0.2778` (`USER-REPORTED`) | `0.253` (`EMPIRICAL-ESTIMATE`) | `37,654` (`18.0 px`) | NO (`100.0%` vs `GEMSDOE25/30`) | `DO NOT SUBMIT` |
| `GEMSDOE36` | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (`698ca8277009128d…`) | `0.2750` (`USER-REPORTED`) | `0.273` (`EMPIRICAL-ESTIMATE`) | `38,854` (`17.5 px`) | NO (`98.0%` vs `GEMSDOE32`) | `DO NOT SUBMIT` |
| `GEMSDOE28` | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (`48009bd74011907a…`) | `0.2710` (`USER-REPORTED`) | `0.266` (`EMPIRICAL-ESTIMATE`) | `37,660` (`18.0 px`) | NO (`100.0%` vs `GEMSDOE25`) | `DO NOT SUBMIT` |
| `GEMSDOE31` | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` (`e15bd24384115709…`) | `0.2708` (`USER-REPORTED`) | `0.258` (`EMPIRICAL-ESTIMATE`) | `40,199` (`17.2 px`) | NO (`100.0%` vs `GEMSDOE25`) | `DO NOT SUBMIT` |
| `GEMSDOE33` | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` (`cb490425926ef250…`) | `0.2632` (`USER-REPORTED`) | `0.254` (`EMPIRICAL-ESTIMATE`) | `41,865` (`17.1 px`) | NO (`100.0%` vs `GEMSDOE25`) | `DO NOT SUBMIT` |
| `GEMSDOE25` | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`638a1241c0d1f775…`) | `0.2600` (`USER-REPORTED`) | `0.254` (`EMPIRICAL-ESTIMATE`) | `44,090` (`16.1 px`) | NO (`100.0%` pixel twin of `30`) | `DO NOT SUBMIT` |
| `GEMSDOE30` | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (`91eae1ca60792154…`) | `0.2600` (`USER-REPORTED`) | `0.254` (`EMPIRICAL-ESTIMATE`) | `44,090` (`16.1 px`) | NO (`100.0%` pixel twin of `25`) | `DO NOT SUBMIT` |
| `GEMSDOE24` | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` (`a1db8443f7123770…`) | `0.2477` (`USER-REPORTED`) | `0.242` (`EMPIRICAL-ESTIMATE`) | `60,069` (`15.2 px`) | NO (`100.0%` superset of `25`) | `DO NOT SUBMIT` |
| `GEMSDOE27` | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`81bbef0b79d4b4ab…`) | `0.2449` (`USER-REPORTED`) | `0.243` (`EMPIRICAL-ESTIMATE`) | `61,328` (`15.0 px`) | NO (`98.0%` vs `GEMSDOE24`) | `DO NOT SUBMIT` |

---

## PhD Key Findings & Reproducible Pipeline

Full derivations and citations: [`research/hvgf_findings.md`](research/hvgf_findings.md) & [`research/hvgf_hypotheses.md`](research/hvgf_hypotheses.md).

1. **Exact Proof of Why `GEMSDOE32` (`0.2778`) Beat Its Eight Siblings:** Because $\mathrm{TP}_w(p) + \mathrm{FN}_w(p) \equiv |G|$, official `DW-Tversky(0.2, 0.8)` equals $\mathrm{TP}_w / (0.8|G| + 0.2\mathrm{TP}_w + 0.2\mathrm{FP}_w)$, setting a marginal precision bar of $\Delta\mathrm{TP}_w/\Delta n > 0.2s/(1-0.2s) \approx 5.9\%\text{--}6.7\%$. Byte comparison proves `GEMSDOE32` (`37,654` dots) equals `GEMSDOE25/30` (`44,090` dots, `0.2600`) **minus the exact `6,436` dots within `d_cat <= 200 m` of known USGS/INGENIOUS faults**, removing `1,287.2` dead-weight FP denominator units at zero TP loss (`|G_hidden| ≈ 13.5k–16k` px).
2. **How `WBG2-HVGF` Surpasses the 19-Band Ceiling:** Restoring the SHA-256-verified 19-band `training_features.tif` plus 11 public-domain/CC-BY-4.0 external geothermal/radiometric/LiDAR/10m-$\chi$ layers (`scripts/restore_external_geothermal_data.py`) and introducing **anisotropic up-gradient hydrothermal plume back-projection (`H-HVGF-1`)**, **GeoDAWN K/Th-demagnetization alteration (`H-HVGF-2`)**, **1m LiDAR + 10m $\chi$-gradient + pluvial shoreline veto (`H-HVGF-3`)**, **Mohr-Coulomb strain + concealed piedmont Worm ridges (`H-HVGF-4`)**, and **fold-visible `C1 != C2` relay anatomy with lateral scarp-shoulder suppression (`H-HVGF-5`)** lifts 8 km quadrant `HOLDOUT-DTI` to **`0.1156` (`4.03×` control)** and blind SGMC piedmont `HOLDOUT-DTI` to **`0.0528` (`+29.7%` vs `DZ-16`)**.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash scripts/download_competition_data.sh
python scripts/restore_external_geothermal_data.py
python scripts/fetch_shared_template.py
python scripts/build_feature_bank.py
python scripts/run_wbg2_hvgf.py        # runs 91x4 canaries, 3-instrument holdout, uniqueness & emits GeoTIFF
python scripts/final_audit.py          # 585-raster uniqueness & byte audit
python scripts/candidate_estimate.py
python scripts/build_site_v2.py && python scripts/build_submit_page.py && python scripts/build_site.py
pytest -q
```

## Remaining Limitations & Suggested Next Steps

1. **Obtain a live `ORGANIZER-CONFIRMED` score (`0` weekly slots spent here):** Upload `wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif` via DrivenData with the 116-character note above and record the organizer receipt.
2. **2D Spatial U-Net / ConvNeXt Ensemble on the 88-Channel HVGF Stack:** Train a fold-safe 2D U-Net/ConvNeXt using differentiable `DW-Tversky(alpha=0.2, beta=0.8)` loss on our cached 88-channel HVGF feature stack and blend OOF probabilities with `WBG2-HVGF` prior to greedy 300 m submodular dot allocation.
3. **InSAR & Station-Level Magnetotelluric Phase Tensors:** Add open Sentinel-1/ARIA interseismic velocity gradients and raw GBCGE/USArray MT station tensors to sharpen blind intrabasin faults beneath actively resurfaced playas where 1m LiDAR scarps are muted.

## Original project prompt

The following preserves the project request as a historical starting point; numeric claims and links in it are **not independently verified** merely by appearing here. Read the current evidence above before acting.

<details><summary>Expand the original project prompt</summary>

Review the repo.

I want to focus on  the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.  I want an executive summary on every site that is clear and obvious which is the best submission to submit to obtain a high score on the leaderboard.  It should also be unique and not an exact duplicate of any previous submission that is the same as below.  Keep iterating and testing until we have the highest scoring submission to download and submit.

We should be able to estimate the score for a submission.  I want a table in the executive summary that clearly lists what file to download, what the estimate score is, and whether it is a unique submission unlike any of the other GEMDOE sites listed below.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871: 0.1047

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

h97b-candidate: 0.0856

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449

....

[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)

tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290

....

[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)

h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658

....

[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)

h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

....

[https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html)

ml-binary-ridge-20261012T000000Z: 0.0180

....

[https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html)

h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499

....

[https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html)

h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351

....

[https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html)

h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009

h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751

....

[https://buffedlizard55-lab.github.io/62GEMSDOE/](https://buffedlizard55-lab.github.io/62GEMSDOE/)

datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000

....

[https://buffedlizard55-lab.github.io/GEMSDOE63/](https://buffedlizard55-lab.github.io/GEMSDOE63/)

cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303

....

[https://buffedlizard55-lab.github.io/GEMSDOE64/](https://buffedlizard55-lab.github.io/GEMSDOE64/)

h64-lidar-scarp-cv-20261011T220000Z:0.0383

....

[https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html)

sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431

....

[https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html)

gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE67/](https://buffedlizard55-lab.github.io/GEMSDOE67/)

h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356

ovtr-ml-cover-tau3p0-20261012-nan:0.1426

....

[https://buffedlizard55-lab.github.io/GEMSDOE68/](https://buffedlizard55-lab.github.io/GEMSDOE68/)

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan:0.0437

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-zeros: 0.0437

....

[https://buffedlizard55-lab.github.io/GEMSDOE69/](https://buffedlizard55-lab.github.io/GEMSDOE69/)

gems69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053

....

[https://buffedlizard55-lab.github.io/GEMSDOE70/](https://buffedlizard55-lab.github.io/GEMSDOE70/)

gems70-p5-dual-submod300-oof38k-20261020:0.2478

....

[https://buffedlizard55-lab.github.io/GEMSDOE71/](https://buffedlizard55-lab.github.io/GEMSDOE71/)

gems71-hydro-conduit-38800-20261020T120000Z-zeros: 0.0558

....

[https://buffedlizard55-lab.github.io/GEMSDOE72/](https://buffedlizard55-lab.github.io/GEMSDOE72/)

gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros: 0.0492

....

[https://buffedlizard55-lab.github.io/GEMSDOE73/](https://buffedlizard55-lab.github.io/GEMSDOE73/)

gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros: 0.1917

....

[https://buffedlizard55-lab.github.io/GEMSDOE74/](https://buffedlizard55-lab.github.io/GEMSDOE74/)

gemsdoe74-triregime-radon-piedmont-37654-20261021T051000Z-zeros:0.0669

....

[https://buffedlizard55-lab.github.io/GEMSDOE75/](https://buffedlizard55-lab.github.io/GEMSDOE75/)

gems75-trlt-radon-loco-ridge-20261021-zeros:0.1627

....

[https://buffedlizard55-lab.github.io/GEMSDOE76/](https://buffedlizard55-lab.github.io/GEMSDOE76/)

gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros:0.1555

gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros:0.2343

....

[https://buffedlizard55-lab.github.io/GEMSDOE77/](https://buffedlizard55-lab.github.io/GEMSDOE77/)

gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros:0.0964

....

[https://buffedlizard55-lab.github.io/GEMSDOE78/](https://buffedlizard55-lab.github.io/GEMSDOE78/)

gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros:0.1564

....

[https://buffedlizard55-lab.github.io/GEMSDOE79/](https://buffedlizard55-lab.github.io/GEMSDOE79/)

gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros:0.0005

....

[https://buffedlizard55-lab.github.io/GEMSDOE80/](https://buffedlizard55-lab.github.io/GEMSDOE80/)

gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros:0.0943

....

[https://buffedlizard55-lab.github.io/GEMSDOE81/](https://buffedlizard55-lab.github.io/GEMSDOE81/)

gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros:0.0041

....

[https://buffedlizard55-lab.github.io/GEMSDOE82/](https://buffedlizard55-lab.github.io/GEMSDOE82/)

gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros:0.1886

....

[https://buffedlizard55-lab.github.io/GEMSDOE83/](https://buffedlizard55-lab.github.io/GEMSDOE83/)

gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros:0.0573

....

[https://buffedlizard55-lab.github.io/GEMSDOE84/](https://buffedlizard55-lab.github.io/GEMSDOE84/)

gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros:0.0132

....

[https://buffedlizard55-lab.github.io/GEMSDOE85/](https://buffedlizard55-lab.github.io/GEMSDOE85/)

gemsdoe85-hjcd-ventbridge-submod-zeros: 0.1110

....

[https://buffedlizard55-lab.github.io/GEMSDOE86/](https://buffedlizard55-lab.github.io/GEMSDOE86/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE87/](https://buffedlizard55-lab.github.io/GEMSDOE87/)

h87-h87-cmgep-20261022T060000Z-8f394f43:0.0500

....

[https://buffedlizard55-lab.github.io/GEMSDOE88/](https://buffedlizard55-lab.github.io/GEMSDOE88/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE89/](https://buffedlizard55-lab.github.io/GEMSDOE89/)

gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:0.0301

....

[https://buffedlizard55-lab.github.io/GEMSDOE90/](https://buffedlizard55-lab.github.io/GEMSDOE90/)

gems90-cnc-35000dots-20261024T084324Z:0.0749

....

[https://buffedlizard55-lab.github.io/GEMSDOE91/](https://buffedlizard55-lab.github.io/GEMSDOE91/)

gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros:0.1367

gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros:0.1823

gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405:

....

[https://buffedlizard55-lab.github.io/GEMSDOE92/](https://buffedlizard55-lab.github.io/GEMSDOE92/)

gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros:0.0255

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros:0.0859

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros:0.0742

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite:0.2190

gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite:

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

gems28-s18-mxtp-20261025-3e95505c011a-allfinite:0.0217

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

gems30-MSDB1-edge44090-20261025-e7856ec3f14a:0.1462

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>

---

## Parallel-session recheck — REJECTED / DO NOT SUBMIT

A concurrent session produced `wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif` (SHA-256 `592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33`). Its nine-file novelty check was incomplete. An independent byte-level recheck found **99.3838%** of its 34,564 dots within 3 px of the registered binary lattice and 5,132,809 footprint cells marked NoData. The continuous prior gives 100% overlap under the shared finite-positive support definition, subject to the interpretation caveat above. The pre-placement surface was not replayed. This file is **research only, not a submission**.

The parallel source reported **HOLDOUT-DTI 0.1321**, evaluator `WBGGEMSDOE2-HIDE-RECOVER-v2.0`, 58,016 withheld positives, reported 95% CI [0.1290, 0.1349] (and when subsequently uploaded on 2026-10-26, its `USER-REPORTED` public DTI in the 2026-10-27 prompt ledger was **`0.0725`**). That result has **not** been independently reproduced, used a private rather than the required shared evaluator, and reports canaries only for one fold, did not exclude evaluation cells from its training zone, and the committed lane script does not reproduce the reported interval. It is not a leaderboard score or proof of beating the matched incumbent. Its speculative live-score projection is not accepted. Three experiments were source-reported in that parallel lane; this review lane ran none, and no organizer receipt is available.

See the [rechecked parallel brief](docs/executive-summary/index.html), [independent evidence](evidence/parallel_review.json), [preserved original records](evidence/parallel_archive/), and the single [canonical negative run card](evidence/run_card.json). The incomplete parallel generator, partial uniqueness audit and zero-NoData private writer are disabled rather than silently reused.


## Second parallel conduit record — STOP

A concurrent session generated `downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif` (SHA-256 `95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad`). Its 58-file uniqueness PASS omitted the registered binary lattice. At its own ≥0.5 threshold, 5,087,882 of 5,094,374 cells (99.8726%) lie within three pixels of that lattice: **STOP; research only; do not submit**. The continuous-prior overlap is 100% under finite-positive support, subject to the policy caveat above. The local format check passes against the mirrored reference, not authenticated organizer bytes; no holdout or organizer receipt is available.

The archived generator uses synthetic geometric trends and smooth noise, not the named geophysical feature arrays; a calculated decay term is unused. Its private evaluator does not apply the specified buffer, pixel-exact visible-fault masking, or pooled metric. The original material is preserved in [the archive](evidence/conduit_archive/), both private tools are disabled, and the [byte-bound recheck](evidence/conduit_review.json) supersedes the original uniqueness claim. This second session reported one experiment. No additional experiments or slot use were performed in this review lane.

## Arena Core Values & Operating Discipline

* **Maximize P(Win):** Concentrate every experiment on true subsurface physical signals, zero-leakage buffered whole-segment holdout evaluation (`gems57-pooled-hide-v2`), and exact 300 m submodular DTI kernel economics — never spending competition slots on duplicate or leaky artifacts.
* **Own the Outcome:** Verify every claim from raw GeoTIFF bytes and official competition/USGS/DOE sources, label every metric strictly (`HOLDOUT-DTI`, `ORGANIZER-CONFIRMED`, `ORGANIZER-PUBLISHED`, `USER-REPORTED`, `MEASURED`), and preserve all four repository lanes (`docs/`, `docs/submission/`, `docs/submit/`, `docs/msptcd/`) transparently without overwriting prior audit records.
