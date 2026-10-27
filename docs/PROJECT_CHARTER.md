# Project charter and session-start brief

**Status update, 2026-10-27:** Read the current [README](../README.md), [evidence notes](research/evidence-and-sources.md), and canonical negative run card [`evidence/run_card.json`](../evidence/run_card.json) together with this charter. Pinned owner-mirror inputs and 19 raw-band caches were reverified in ignored local storage; they may not persist and are not authenticated organizer copies. The separate derived feature bank is absent. All nine priority-site refs changed after their pinned audits; the newer rasters were not fetched or audited. No candidate is currently authorized. Historical DZ-16 and H3-PACK positive-looking lane cards fail current project-level gates; the separate MSPTCD lane reports HOLDOUT-DTI 0.042554 (evaluator `gems57-pooled-hide-v2`, 60,988 withheld positives, 95% CI [0.032059, 0.054765]) but fails the literal all-registry novelty gate. No exhaustive current-registry scan, active selector release, or organizer submission receipt exists.

**Read this file at the start of every project session.** It is the durable, actionable record of the project request, including safety/evidence constraints, the nine-site focus, the submission-format issue, and project values. The original long prompt included duplicated historical score lists; this charter consolidates repeated wording while retaining all operative requirements and the relevant site results in `EXECUTIVE_SUMMARY.md`.

## Mission

Build a scientifically defensible, auditable system for discovering previously unmapped faults relevant to geothermal prospects in the DOE GEMS Prize region. Optimize for the public competition metric without confusing public leaderboard scores, local validation, or speculative projections. Maintain a current, useful, easy-to-review feed of findings and make a validated GeoTIFF easy to download only when it is genuinely authorized for submission.

## Nine-site focus

Review the strongest reported results for **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36**. For each, keep an executive-summary record of file name, evidence class/score, score-estimate status, exact-file availability, and uniqueness audit status. Historical score claims must not be presented as verified receipts. The current comparison and measured overlaps are in `executive-summary.html` and `data/portfolio.json`; `EXECUTIVE_SUMMARY.md` is an earlier snapshot.

## Highest-priority requirement: unique and validated GeoTIFF

A downloadable competition TIFF must be a new, genuinely generated raster—not a copy, renamed file, or superficial perturbation of an old submission. It must be unambiguously labeled **OK TO DOWNLOAD AND SUBMIT** only after all gates pass. Until then prominently say **DO NOT SUBMIT** and do not provide a fake or unvalidated TIFF merely to satisfy the desire for a download.

The official submission specification states one GeoTIFF band, projected UTM 11N / EPSG:32611, 100 m grid, training-grid bounds and geotransform, float32 values in `[0,1]`, and null/NaN outside bounds. Validate the raster on its written bytes against the official sample/reference grid. Check `[0,1]` values (including all finite in-footprint cells), no NaN inside the footprint, one band, dtype, CRS, shape, transform, nodata/footprint behavior, and readable file. Preserve a SHA-256 and validator output.

## Parallel-run lane and duplication rule

This session is one of multiple sessions that may be working from a related brief. Do not drift into another method lane. The source request refers to a “single method paragraph below,” but does not uniquely identify which paragraph is the assigned method in this repository. **Do not guess the lane or implement a candidate until the shared lane assignment is explicitly present in project inputs.**

For any permitted candidate, compare its raster rank-correlation with every registry raster and its dots’ 3-pixel proximity overlap with every registry’s dots **before placement and again on final dots**. If any rank correlation exceeds 0.90 or any one registry captures more than 70% of candidate dots within 3 pixels, label the result a duplicate and stop. No exception based on a changed filename or random seed.

## Reuse and evaluation protocol

- Use the shared template’s cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`; do not rebuild or maintain a private fork. They have been restored in the ignored local cache from pinned owner mirrors; rerun `scripts/prepare_data.py --fetch --cache-bands` on a fresh machine and verify provenance before experiments.
- Holdout is hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature from visible faults only, mask visible faults pixel-exactly, and score pooled DTI with alpha 0.2, beta 0.8, and the 300 m triangular kernel.
- Run each feature alone through the holdout leakage canary before trusting a combined candidate. AUC above 0.90 is presumed leakage until demonstrated otherwise.
- Report a numerical result only with its evidence class. Use `HOLDOUT-DTI` plus evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` with copied submission-page receipt. Mark historical values as owner/user-reported claims; mark projections as projections, never scores.
- Stop at three experiments or two hours, whichever comes first. Never choose/promote a slot here; slot selection is a separate step subject to the competition’s weekly cap.

## Research expectations

Before implementation, state 3–5 candidate geological hypotheses. Each must specify the exact available layer(s), physical signature, reason it may find an uncatalogued fault (rather than re-identify training faults), distinction from methods in this repository/site evidence, likely non-fault mimic, expected ranking and cost. Prefer provided features. If new data are essential, identify a free official source and verify that it is obtainable and permitted before calling the idea viable.

Check claims against official competition/sponsor/scientific sources and include direct source links. Distinguish official evidence from site-owner claims and unverified historical submissions. Flag missing data, stale leaderboard snapshots, inaccessible pages, and any mismatch between requested and available inputs. Do not claim independent replication unless the actual artifact and code were run.

## Current project reality / limitations

The initial checkout was an empty project stub. Earlier sessions restored pinned owner-mirrored grids and audited nine historical rasters plus registered witnesses. The owner mirrors and raw bands are not authenticated against DrivenData, the derived shared feature bank is absent, and the current nine site refs changed after the pinned audit without a newer raster audit. Under the unchanged template's literal finite-positive overlap definition, the registered continuous prior blocks every nonempty candidate; its application to a continuous field remains an interpretation question. The requested method lane is unassigned. No candidate is currently authorized: the canonical card at `evidence/run_card.json` is negative, the full current registry has not been checked, and no separate selector release or organizer receipt exists. Historical DZ-16 has no holdout and fails the literal gate; H3's historical promote card does not override its registered witnesses. The MSPTCD research lane did complete a local buffered holdout (0.042554, evaluator `gems57-pooled-hide-v2`, 60,988 withheld positives, 95% CI [0.032059, 0.054765]) but failed the literal all-registry gate. Its result is not a leaderboard score. This review did not run a new experiment or create a candidate.

## Current release gate

The upload status is fail-closed. A historical lane-level `promote` verdict is not project authorization. `scripts/submission_status.py` requires (1) a positive canonical run card with a physical mechanism and named non-fault mimic; (2) a completed `HOLDOUT-DTI` with evaluator version, withheld-positive count, value and 95% CI; (3) passing byte-read-back validator fields; (4) a complete current-registry manifest hash plus pre-placement surface correlation no greater than 0.90 and final-dot 3-pixel overlap no greater than 70%; and (5) a separate `evidence/submission_release.json` that binds the canonical run-card bytes, exact candidate bytes, submission name/note, and an explicit current weekly-quota check confirming 1–3 slots remain under the currently documented three-slot cap, with `weekly_quota_checked_at_utc` no older than 24 hours, `weekly_quota_source_url` on the official competition page, and `remaining_weekly_slots` within 1–3. The helper does not create or upload a candidate. No release record currently exists, so all candidate links must stay disabled and every archived TIFF must be labelled research-only / DO NOT SUBMIT.

## User-requested review passes

Every delivery must include at least three passes:

1. Implement the requested documentation/workflow and verify it against source materials.
2. Review for missing requirements, unsupported assumptions, defects, and edge cases; fix them.
3. Re-check against the complete charter, test the final outputs, and state unresolved blockers. Do not end after pass one.

## Core values

- **Maximize P(Win)** — decision framework: assess evidence, risk, and opportunity cost; prioritize experiments that can improve the probability of winning. The objective is measured scientific performance, not more artifacts or more submissions.
- **Own the Outcome** — own the end-to-end result. Report failures and negative outcomes, repair shared tools at their source, and turn evidence into better future decisions.

## Competition sources and context

Official source links are kept in `research/evidence-and-sources.md` and the current dashboard. The DrivenData competition specifies faults as the prediction target, provides a training feature GeoTIFF and known-fault labels, and describes public and private test sets of new expert-labeled faults. External data are permitted when the license allows challenge use and sharing with the sponsor. The official rules and organizer advice take precedence over this charter if they conflict. The September 2026 rules also require disclosure of generative-AI use in the submission narrative, allow up to three weekly prediction submissions, and require one final selection across both prize rounds; verify the current rules at decision time.

## Current implementation boundary

The active format-only checker `scripts/validate_submission.py` delegates to the pinned shared template and deliberately never authorizes upload. `scripts/submission_status.py` is the project-level fail-closed release check; its required selector record is absent. The earlier independent `scripts/legacy_format_validator.py` remains solely as an auxiliary compatibility check; neither validator establishes uniqueness or scientific performance. A complete current registry, an explicitly assigned lane, authenticated organizer data, and an eligible candidate remain absent. `evidence/run_card.json` is canonical; `docs/data/run-card.json`, `docs/data/run_card.json`, `docs/data/run-card-current.json`, and `site/data/run_card.json` are generated mirrors. The static Pages entry point is `index.html`. Scheduled feeds are snapshots and do not audit newly discovered rasters.
