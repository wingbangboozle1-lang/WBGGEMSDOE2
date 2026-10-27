# WBGGEMSDOE2 — DOE GEMS Prize

**Read this current decision first at every session.** Then read [AGENTS.md](AGENTS.md), the [project charter](docs/PROJECT_CHARTER.md), [findings](research/findings.md), the [canonical run card](evidence/run_card.json), [release audit](evidence/release_audit.json), and [source-verification record](research/source-verification-release-20261027.md). The latest code/repository review and next-step priorities are in [repo-review-20261027.md](research/repo-review-20261027.md). The original prompt is preserved below; it is not a receipt or permission to bypass a failed gate.

## Current release: NEGATIVE — no file is approved. DO NOT SUBMIT.

**All existing TIFFs are research-only.** Former DZ-16 and H3-PACK approvals are revoked. Different lanes, filenames, packaging, projection fits, or density-normalized diagnostics do not override the requested literal all-registry stop.

- **[Download status: exact research TIFFs, hashes and read-back validation](docs/release.html)**
- **[Live dashboard](https://wingbangboozle1-lang.github.io/WBGGEMSDOE2/)** · [submission instructions](docs/executive-summary.html) · [nine-site executive table](docs/release.html#nine-sites)
- **[One current negative JSON run card](evidence/run_card.json)** · [independent byte audit](evidence/release_audit.json) · [official-source verification](research/source-verification-release-20261027.md)
- **[Ranked N1–N4 research proposals](research/hypotheses.md)** · [three-pass review record](research/release-reconciliation-review.md) · [current blocker register](research/release-blockers-20261027.md) · [this session’s repository review and run card](research/session-review-20261027.md) · [issue #23](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/issues/23)

No new candidate, dot placement, model experiment, competition upload, or weekly slot was used in this review. No eligible submission name/note or leaderboard estimate is fabricated. New-file fields remain `null`.

### What was independently measured

The audit reopened **10 existing TIFF paths / 8 distinct SHA-256 identities**, checked their **7 ZIPs**, and compared final positive support against **13 hash-pinned registry witnesses** (plus a full **467-raster multi-org fleet audit** in [`evidence/dphs_uniqueness_and_fleet_audit.json`](evidence/dphs_uniqueness_and_fleet_audit.json)). Every saved TIFF has a decisive literal duplicate witness (`DO NOT SUBMIT`).

| Existing research artifact | Lattice 3-pixel overlap | Inside/grid format | Extra all-finite check | Decision |
|---|---:|---|---|---|
| `wbg2-dphs-exp3-submod300m-20261027T194500Z-46a3a89a-zeros` *(New · HOLDOUT-DTI 0.1735)* | 99.836% | PASS | PASS | **DO NOT SUBMIT** |
| `wbg2-d19dotted-38000dots-20261027T191824Z-cb2f6ff4-zeros` | 99.147% | PASS | PASS | **DO NOT SUBMIT** |
| `wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros` | 99.923% | PASS | PASS | **DO NOT SUBMIT** |
| `wbg3-h3pack-34k-20261027T174337Z-zeros` | 99.862% | PASS | FAIL | **DO NOT SUBMIT** |
| `wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros` | 100.000% | PASS | PASS | **DO NOT SUBMIT** |
| `wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros` | 99.980% | PASS | PASS | **DO NOT SUBMIT** |
| `wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros` | 99.384% | FAIL | FAIL | **DO NOT SUBMIT** |
| `wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros` | 99.871% | PASS | PASS | **DO NOT SUBMIT** |

### WBG2-DPHS Campaign (`HOLDOUT-DTI = 0.1735`) & 467-Raster Fleet Empirical Synthesis

- **Pages Subsite:** [`docs/dphs/index.html`](docs/dphs/index.html) · **How to Submit (Contest Steps):** [`docs/dphs/how-to-submit.html`](docs/dphs/how-to-submit.html) · **Executive Forensic Brief:** [`docs/dphs/executive-summary.html`](docs/dphs/executive-summary.html) · **Full Report:** [`research/dphs_findings.md`](research/dphs_findings.md)
- **5 Preregistered Geological Hypotheses (`DPHS-H1..H5`, [`config/dphs_hypotheses.json`](config/dphs_hypotheses.json)):** Integrates 1 m USGS LiDAR residual scarps, 10 m 3DEP multi-scale DoG curvature & shoreline de-confounding, GeoDAWN aeromagnetic/radiometric lineaments, and Great Basin Play Fairway / GDR (`#1391`, `#1051`, `#1120`) hydrothermal + NBMG springs + Quaternary contacts + USGS ComCat seismicity (`60` zero-catalogue features; 61-feature leakage canary max symmetric ROC-AUC `0.61795 <= 0.90`).
- **3-Experiment Buffered Holdout (`gems57-pooled-hide-v2`, `alpha=0.2, beta=0.8`, 300 m triangular kernel, `60,988` withheld positives, [`evidence/wbg2_dphs_results.json`](evidence/wbg2_dphs_results.json)):**
  - **`EXP-3` (`DPHS-Submod300m`):** **`HOLDOUT-DTI = 0.1735` (`95% CI [0.1525, 0.1944]`)**, beating `ctrl_19b` (`0.0303`, paired `Δ = +0.1432`), `msptcd_31` (`0.0296`, paired `Δ = +0.1439`), `h3_blind_lattice` (`0.0720`, paired `Δ = +0.1015`), `EXP-1` (`0.0539`), and `EXP-2` (`0.0609`) across **4/4 folds**.
- **467-Raster Uniqueness & 95-Scored-Raster Fleet Model ([`evidence/dphs_uniqueness_and_fleet_audit.json`](evidence/dphs_uniqueness_and_fleet_audit.json), [`evidence/RUN_CARD_DPHS.json`](evidence/RUN_CARD_DPHS.json)):**
  - `WBG2-DPHS EXP-3` (`SHA-256 = 31f3d8e61d195dd5ac09f380815cd08ea072d8812e2f5021d2c41fa423e6ccd9`, `36,500` non-touching binary dots, `0` NaN anywhere) passes SHA-256 uniqueness (`0` matches), pre-placement surface Spearman (`0.8608 <= 0.90`), and 9-focus-site 3-px overlap (`42.68%–58.23% <= 70%`), **but stops fail-closed (`status = "negative"`, `DO NOT SUBMIT`, `0` slots spent)** on `>70%` 3-px overlap against `45` discrete fleet range-front scarp rasters (`95.87%` vs `GEMSDOE12`) + `48` blanket/lattice rasters (`99.84%` vs `13GEMSDOE` lattice).
  - Our **11-feature Physics + SGMC + Geometry Ridge empirical model** (`n = 95` scored rasters across `68` sites: grouped LOSO `R² = +0.4303`, `Spearman = +0.6488`; 9-focus rank `Spearman = +0.7554`) shows why `GEMSDOE32` (`0.2778 USER-REPORTED`, `34.0%` distal `>32 px`, `C_pied = 0.0888`) and `GEMSDOE70` (`0.3133 USER-REPORTED`, `36.8% >32 px`, `C_pied = 0.2136`) beat range-front-concentrated PU-HGBR runs (`DPHS-EXP3` `frac_gt_32px = 3.64%`, `EMPIRICAL-ESTIMATE = 0.0713`, `95% PI [0.0000, 0.1941]`).

A local format pass is not organizer acceptance, uniqueness, scientific validation or selector approval. The reference is an owner mirror, not an authenticated organizer sample. The actual bytes of the upload that produced “Predicted values must be in range [0, 1]” were not supplied; its cause remains unknown. H3's “zeros” TIFF has NaN outside the footprint; STEPXASYM marks 5,132,809 interior cells as NoData. These observations do not establish the cause of a different upload's error.

### Nine-site executive decision

These are the **strongest named historical claims supplied for each site**, not a claim to have found each site's current best file. Numbers are **USER-REPORTED**, with no organizer receipt binding a value to a hash. All nine latest repository HEADs have changed since their audited raster pins; a HEAD check is not a new-raster audit.

| Site summary | Exact historical research file | Historical claim / evidence | New-score estimate | Measured 3-pixel overlap | Submit? |
|---|---|---|---|---|---|
| [GEMSDOE32](docs/sites/GEMSDOE32.html) | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/45ee207185f72804497f7a7a392ad2c43e168f02/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif?raw=1) | 0.2778 USER-REPORTED | Unavailable | 100.00% near GEMSDOE24 | **DO NOT RESUBMIT** |
| [GEMSDOE36](docs/sites/GEMSDOE36.html) | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/b90418f852615aa0974cf9a53b92fa569ed133fc/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif?raw=1) | 0.2750 USER-REPORTED | Unavailable | 97.58% near GEMSDOE27 | **DO NOT RESUBMIT** |
| [GEMSDOE28](docs/sites/GEMSDOE28.html) | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/9c1be21e8f1be707347f737e42abf62ea669c819/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif?raw=1) | 0.2710 USER-REPORTED | Unavailable | 100.00% near GEMSDOE24 | **DO NOT RESUBMIT** |
| [GEMSDOE31](docs/sites/GEMSDOE31.html) | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/78f9bf3ae82e5c78ca348aa37c0660c339e72f0e/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif?raw=1) | 0.2708 USER-REPORTED | Unavailable | 100.00% near GEMSDOE24 | **DO NOT RESUBMIT** |
| [GEMSDOE33](docs/sites/GEMSDOE33.html) | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/a24fb7c5031ee08b12440af4593057858fecef8e/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif?raw=1) | 0.2632 USER-REPORTED | Unavailable | 99.71% near GEMSDOE27 | **DO NOT RESUBMIT** |
| [GEMSDOE25](docs/sites/GEMSDOE25.html) | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/606eef45e669a6da061ec24be4a3d870addadb0f/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif?raw=1) | 0.2600 USER-REPORTED | Unavailable | 100.00% near GEMSDOE24 | **DO NOT RESUBMIT** |
| [GEMSDOE30](docs/sites/GEMSDOE30.html) | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/35ce8911e2c3287eed973eacd12c252e8cb3f34c/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif?raw=1) | 0.2600 USER-REPORTED | Unavailable | 100.00% near GEMSDOE24 | **DO NOT RESUBMIT** |
| [GEMSDOE24](docs/sites/GEMSDOE24.html) | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/5cfab74597cd1d0a271e4640b4cc34511e56ca59/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif?raw=1) | 0.2477 USER-REPORTED | Unavailable | 100.00% near GEMSDOE25 | **DO NOT RESUBMIT** |
| [GEMSDOE27](docs/sites/GEMSDOE27.html) | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/f1e32af867d9cf0081af20866c8241ec8678a432/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif?raw=1) | 0.2449 USER-REPORTED | Unavailable | 98.02% near GEMSDOE24 | **DO NOT RESUBMIT** |

### What B2 explains — and does not

**MEASURED:** GEMSDOE25/30 decode to the same 44,090 dots. B2 removes exactly the 6,436 within 2 px of the mirrored catalogue, leaving 37,654. GEMSDOE36 adds 1,200 dots to B2 and removes none. **DERIVED:** FN = N − TP, so the official metric is `TP / (0.2 TP + 0.2 FP + 0.8 N + epsilon)` and TP ≤ N. Deleting dots helps only if reduced FP outweighs lost truth credit. That is a plausible mechanism for the USER-REPORTED 0.2778, not proof of its cause. Staff confirmed exact known-pixel exclusion, not a two-pixel collar. [Detailed analysis](docs/research/why-b2-scored-2778.html).

The official public leaderboard displayed **0.4544** for xiaofanhu on 2026-10-27 ([dated observation](evidence/public_leaderboard_recheck_20261027.json), [official page](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)). This is **ORGANIZER-PUBLISHED PUBLIC OBSERVATION**, not an ORGANIZER-CONFIRMED receipt for a project file, HOLDOUT-DTI, or proof we can beat it. The 0.3195/0.4413 values in the prompt remain unverified user claims.

### Historical campaign and scientific correction

Prior MSPTCD **SOURCE-REPORTED HOLDOUT-DTI**: 0.042554, 95% spatial-bootstrap CI [0.032059, 0.054765], 60,988 withheld positives, evaluator `gems57-pooled-hide-v2`; historical control 0.023409. This review **did not reproduce it**. A v1 orientation defect treated perpendicular edges as coherent. Corrected `msptcd-v2-axial-cos-squared` has synthetic tests and **no measured holdout result**. Content-bound/versioned caches replace existence-only reuse. Passing AUC canaries does not prove no leakage. The former web table also invented nonexistent/misindexed bands; its replacement uses the actual source schema. [Corrected historical report](docs/msptcd/index.html) · [historical card with corrections](evidence/RUN_CARD_MSPTCD.json).

The **full pinned 19-band raw stack and caches were restored**: 418,912,844 source bytes, SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`. Organizer provenance, band-unit semantics and the separate shared derived bank remain unresolved. Do not claim the raw stack is absent or that lack of GPU prevents this audit. [Input receipt](evidence/data_preparation.json) · [raw feature diagnostic](evidence/feature_semantics_review.json).

## Reproduce safely

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/build_hypotheses.py
.venv/bin/python scripts/build_run_card.py
.venv/bin/python scripts/build_site_data.py
.venv/bin/python scripts/sync_msptcd_evidence.py
.venv/bin/python scripts/build_msptcd_site.py
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/build_release.py
```

The release builder checks TIFF/ZIP inventories, byte hashes, ZIP-member bytes, policy and pinned-witness consistency before writing. It cannot approve a file. Five original private generators/approval gates and seven newly encountered campaign/refinement/projection entrypoints now stop. Historical campaigns stop before feature/model/output work. All nine current-card aliases mirror the one canonical negative card. Contradictory original receipts/sources remain in [`evidence/reconciliation_archive/`](evidence/reconciliation_archive/) as **historical, non-authorizing** material.

Optional forensic rerun (not a candidate experiment; requires ignored reference/registry bytes):

```bash
.venv/bin/python scripts/fetch_shared_template.py
.venv/bin/python scripts/audit_registry.py --fetch --output evidence/registry_recheck_20261027.json
.venv/bin/python scripts/prepare_data.py --fetch --cache-bands
.venv/bin/python scripts/audit_release.py
```

The shared evaluator/writer remain pinned and unchanged. A shared NoData-mask defect is reproduced by regression tests; [upstream report](research/shared-template-format-report.md) creation is permission-denied. No private evaluator/writer fork substitutes for the unresolved upstream fix.

### Before another experiment

1. Record a single explicit method-lane assignment and complete fresh immutable registry. No silent lattice/continuous-prior exemptions or footprint-edge gaming.
2. Authenticate organizer input/reference bytes; resolve the shared format gate upstream.
3. Run every feature-alone canary on buffered whole-segment spatial holdouts; use only visible faults for catalogue features and mask visible pixels exactly.
4. Establish a matched corrected-code incumbent on identical folds with the shared pooled DTI evaluator, 300 m triangular kernel, alpha 0.2/beta 0.8, and paired spatial 95% CI. Historical v1 metrics are not that incumbent.
5. Check original surfaces before placement and final dots against **every** registry raster: absolute rank correlation >0.90 **or** inclusive Euclidean 3 px overlap >70% means duplicate and STOP. Stop at 3 experiments or 2 hours.
6. A separate authorized selector checks actual remaining quota (official rules: up to 3 submissions/week), assigns a unique meaningful filename and ≤140-character note, and archives the exact organizer receipt. No slot is selected in this review.

### Current-request claim amendments

The original brief below and later 144-row ledger are historical unverified snapshots. The current request supplies different S21/S33/KPL36 values and leaves some formerly populated claims blank. The [conflict register](evidence/request_claim_conflicts.json) retains both; blank is never zero. Newly named ATRG, conditional-continuation and spectral-tilt files are references only; filenames do not prove novelty or approval. None is used to fit a release forecast.

#### Current request values that differ from the prior snapshot (all USER-REPORTED)

| Reference | Current supplied value | Prior snapshot value | Treatment |
|---|---:|---:|---|
| GEMSDOE27 H31 DRCG | 0.2250 | blank | No organizer receipt |
| GEMSDOE28 S21 PUHGB | 0.0206 | 0.1628 | Conflict, neither authenticated |
| GEMSDOE33 S33 strain/seismicity | 0.0963 | 0.0363 | Conflict, neither authenticated |
| GEMSDOE36 KPL36 exp3 | 0.1647 | 0.2314 | Conflict, neither authenticated |
| GEMSDOE91 S22 spectral tilt | 0.0298 | absent | New claim, not a receipt |
| GEMSDOE91 S18, KANLER3, EUG1–3, WBG1 and several GINNY/WBG3 references | blank | values previously populated | Current blank is not zero or a verified result |

Additional currently unscored names: `wbg2-atrg-28500dots-20261027T002046Z-105e98d5-zeros`; `wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros`; `wbg1-r64c-anderson-conditional-continuation-37654-20261027T015745Z-36d985e6-zeros`. Their mention does not create a candidate, score or approval.

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

---

### 2026-10-27 Parallel-Run Protocol & Updated Ledger Addendum

- Current top public leaderboard score reported in prompt: `0.4413` (`ORGANIZER-PUBLISHED` snapshot on 2026-10-27: `0.4544`, `xiaofanhu`).
- Verified 144-row (`128` scored, `16` blank/duplicate) prompt ledger archived in [`docs/data/user-reported-ledger-20261027.csv`](docs/data/user-reported-ledger-20261027.csv) and [`evidence/prompt_ledger_audit_20261027.json`](evidence/prompt_ledger_audit_20261027.json).
- Hypothesis preregistration (`3–5` novel geological hypotheses naming specific layers, physical signature, why missing from USGS/INGENIOUS catalogue, non-fault mimic, repo differentiation, ranked by expected DTI gain and cost): [`config/dphs_hypotheses.json`](config/dphs_hypotheses.json) and [`research/dphs_hypotheses.md`](research/dphs_hypotheses.md).
- Parallel-Run Protocol (`gems57-pooled-hide-v2` hide-and-recover buffered holdout, `alpha=0.2, beta=0.8`, 300 m kernel, single-feature leakage canary `AUC > 0.90`, pre-placement surface rank-corr `> 0.90` + final-dot 3-px overlap `> 70%`, max 3 experiments, shared `evaluate_holdout.py` + `submission_writer.py`, 1 JSON Run Card): [`evidence/RUN_CARD_DPHS.json`](evidence/RUN_CARD_DPHS.json).

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
