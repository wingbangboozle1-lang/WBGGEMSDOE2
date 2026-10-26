# Project charter and session-start brief

**Read this file at the start of every project session.** It is the durable, actionable record of the project request, including safety/evidence constraints, the nine-site focus, the submission-format issue, and project values. The original long prompt included duplicated historical score lists; this charter consolidates repeated wording while retaining all operative requirements and the relevant site results in `EXECUTIVE_SUMMARY.md`.

## Mission

Build a scientifically defensible, auditable system for discovering previously unmapped faults relevant to geothermal prospects in the DOE GEMS Prize region. Optimize for the public competition metric without confusing public leaderboard scores, local validation, or speculative projections. Maintain a current, useful, easy-to-review feed of findings and make a validated GeoTIFF easy to download only when it is genuinely authorized for submission.

## Nine-site focus

Review the strongest reported results for **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36**. For each, keep an executive-summary record of file name, evidence class/score, score-estimate status, exact-file availability, and uniqueness audit status. Historical score claims must not be presented as verified receipts. The current comparison is in `EXECUTIVE_SUMMARY.md`.

## Highest-priority requirement: unique and validated GeoTIFF

A downloadable competition TIFF must be a new, genuinely generated raster—not a copy, renamed file, or superficial perturbation of an old submission. It must be unambiguously labeled **OK TO DOWNLOAD AND SUBMIT** only after all gates pass. Until then prominently say **DO NOT SUBMIT** and do not provide a fake or unvalidated TIFF merely to satisfy the desire for a download.

The official submission specification states one GeoTIFF band, projected UTM 11N / EPSG:32611, 100 m grid, training-grid bounds and geotransform, float32 values in `[0,1]`, and null/NaN outside bounds. Validate the raster on its written bytes against the official sample/reference grid. Check `[0,1]` values (including all finite in-footprint cells), no NaN inside the footprint, one band, dtype, CRS, shape, transform, nodata/footprint behavior, and readable file. Preserve a SHA-256 and validator output.

## Parallel-run lane and duplication rule

This session is one of multiple sessions that may be working from a related brief. Do not drift into another method lane. The source request refers to a “single method paragraph below,” but does not uniquely identify which paragraph is the assigned method in this repository. **Do not guess the lane or implement a candidate until the shared lane assignment is explicitly present in project inputs.**

For any permitted candidate, compare its raster rank-correlation with every registry raster and its dots’ 3-pixel proximity overlap with every registry’s dots **before placement and again on final dots**. If any absolute rank correlation exceeds 0.90 or any one registry captures more than 70% of candidate dots within 3 pixels, label the result a duplicate and stop. No exception based on a changed filename or random seed.

## Reuse and evaluation protocol

- Use the shared template’s cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; do not rebuild or maintain a private fork. The repository currently does not contain these assets, so their provenance/revision must be established before experiments.
- Holdout is hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature from visible faults only, mask visible faults pixel-exactly, and score pooled DTI with alpha 0.2, beta 0.8, and the 300 m triangular kernel.
- Run each feature alone through the holdout leakage canary before trusting a combined candidate. AUC above 0.90 is presumed leakage until demonstrated otherwise.
- Report a numerical result only with its evidence class. Use `HOLDOUT-DTI` plus evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` with copied submission-page receipt. Mark historical values as owner/user-reported claims; mark projections as projections, never scores.
- Stop at three experiments or two hours, whichever comes first. Never choose/promote a slot here; slot selection is a separate step subject to the competition’s weekly cap.

## Research expectations

Before implementation, state 3–5 candidate geological hypotheses. Each must specify the exact available layer(s), physical signature, reason it may find an uncatalogued fault (rather than re-identify training faults), distinction from methods in this repository/site evidence, likely non-fault mimic, expected ranking and cost. Prefer provided features. If new data are essential, identify a free official source and verify that it is obtainable and permitted before calling the idea viable.

Check claims against official competition/sponsor/scientific sources and include direct source links. Distinguish official evidence from site-owner claims and unverified historical submissions. Flag missing data, stale leaderboard snapshots, inaccessible pages, and any mismatch between requested and available inputs. Do not claim independent replication unless the actual artifact and code were run.

## Current project reality / limitations

At the start of this session, the tracked repository contained only a 13-byte README. It had no model, pipeline, cached feature stack, holdout evaluator, submission writer, competition data, registry rasters, or TIFF artifacts. Python packages `rasterio`, `numpy`, `scipy`, `scikit-learn`, and `pytest` were not installed. The competition data download page is user-authenticated. Therefore this checkout cannot produce or validate a competition TIFF, measure a holdout score/CI, run leakage canaries, or assess raster novelty. An honest negative run card is recorded in `RUN_CARD.json`.

## User-requested review passes

Every delivery must include at least three passes:

1. Implement the requested documentation/workflow and verify it against source materials.
2. Review for missing requirements, unsupported assumptions, defects, and edge cases; fix them.
3. Re-check against the complete charter, test the final outputs, and state unresolved blockers. Do not end after pass one.

## Core values

- **Maximize P(Win)** — decision framework: assess evidence, risk, and opportunity cost; prioritize experiments that can improve the probability of winning. The objective is measured scientific performance, not more artifacts or more submissions.
- **Own the Outcome** — own the end-to-end result. Report failures and negative outcomes, repair shared tools at their source, and turn evidence into better future decisions.

## Competition sources and context

Official source links are kept in `EXECUTIVE_SUMMARY.md`. The DrivenData competition specifies faults as the prediction target, provides a training feature GeoTIFF and known-fault labels, and describes public and private test sets of new expert-labeled faults. External data are permitted when the license allows challenge use and sharing with the sponsor. The official rules and organizer advice take precedence over this charter if they conflict. The September 2026 rules also require disclosure of generative-AI use in the submission narrative, allow up to three weekly prediction submissions, and require one final selection across both prize rounds; verify the current rules at decision time.

## Current implementation boundary

A format-only checker now exists at `scripts/validate_submission.py` with unit tests. It checks an actual candidate against an actual reference TIFF and deliberately never authorizes upload. The repository still lacks the competition data, the shared evaluator/writer, a complete raster registry, and an explicitly assigned lane. `docs/RUN_CARD.json` is the current machine-readable no-experiment disposition. The static Pages entry point is `docs/index.html`; it is a snapshot, not a live leaderboard feed.
