# WBGGEMSDOE2 — evidence-gated GEMS Prize research

> **Current decision: NO TIFF is cleared for download-and-submit.** The initial checkout contained only a stub README; this repository now contains project documentation but still has no competition rasters, model, cached feature stack, holdout evaluator, or submission writer. Generating a plausible-looking GeoTIFF without those inputs would be unvalidated and could repeat the reported `[0, 1]` submission error. No TIFF is being fabricated or represented as submit-ready.

## Start here on every project session

Read [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md) first. It preserves the user’s goals, hard evidence and lane gates, three-pass review requirement, core values, and the constraints this repository must honor. Then read [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) for the current nine-site comparison, candidate hypotheses, official-source links, and blockers. The machine-readable negative run card is [`docs/RUN_CARD.json`](docs/RUN_CARD.json).

## Executive decision

- **Best of the nine historical results as supplied by the user:** GEMSDOE32’s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, reported as **0.2778**. This is an **owner/user-reported historical claim**, not a HOLDOUT-DTI measurement or an organizer receipt in this checkout. The method’s causal explanation and score cannot be reproduced from the present repository.
- **Current official public leaderboard snapshot:** the DrivenData leaderboard page showed **0.4437** at the top when reviewed on 2026-10-26. This is a live, organizer-hosted public leaderboard value, not a local holdout result and not a prediction for our model. See the official leaderboard link in the executive summary.
- **Submission to download:** **none**. There is no validated unique TIFF here. Do not submit any historical file or a renamed/perturbed copy.
- **Score estimate for a new candidate:** **not estimable** until the competition rasters, same-evaluator spatial holdout results, and score calibration data are accessible. Do not treat a projection or a past site claim as a score.

## Non-negotiable workflow

1. Reuse the established template’s cached features, `evaluate_holdout.py`, and `submission_writer.py`; do not create a private competing implementation. They are absent from this checkout, so first recover/use the shared template and record its immutable revision.
2. Run whole-segment spatial hide-and-recover with buffers and fold-local catalogue-derived features; mask visible positives pixel-exactly. Score pooled DTI with alpha 0.2, beta 0.8, and the 300 m triangular kernel.
3. Report every measured result as `HOLDOUT-DTI (evaluator/version, withheld-positive count, 95% CI)` or `ORGANIZER-CONFIRMED (submission-page receipt)`. Label all other numbers explicitly as owner-reported claims or projections, never as scores.
4. Run each feature alone through the holdout leakage canary. Any AUC > 0.90 is presumed leakage until independently resolved.
5. Check rank correlation and 3-pixel dot overlap against every registry raster both before placement and on final dots. Abort if correlation > 0.90 or >70% overlap with any registry raster.
6. Verify saved TIFF bytes against the official submission grid and single-band float32 `[0,1]` requirements, with no NaN inside the footprint. Only after all scientific, uniqueness, and format gates pass can it be marked **OK TO SUBMIT**.
7. Maximum research budget: three experiments or two hours. Do not use a weekly submission slot as an experiment. Promotion/selection is separate.

## Work remaining

The immediate blocker is not GPU compute: it is missing data and missing shared pipeline code. The DrivenData competition data page requires an enrolled/account-authenticated session; this environment has no competition login. Put the authorized competition files in the expected `data/` location on an unrestricted, authorized machine, then reconnect them to the shared template and run its documented preparation pipeline. Do not commit licensed/large data. See the executive summary for source links, a ranked untested hypothesis shortlist, and the exact evidence required to resume.

## Core values

- **Maximize P(Win)** — spend effort only on falsifiable experiments that outperform the current same-evaluator holdout champion and pass duplicate/leakage/format gates; never spend a slot on an untested hunch.
- **Own the Outcome:** report negative results, missing evidence, blockers, and defects clearly; repair shared tools at their source and preserve reproducibility.
