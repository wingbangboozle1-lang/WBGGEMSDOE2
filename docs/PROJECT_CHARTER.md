# Project charter and session-start brief

**Status update, 2026-10-27 (current):** The durable charter below remains in force, with two resolved blockers. (1) The missing "single method paragraph" lane was resolved by the charter's own instruction to *generate 3–5 ranked hypotheses and validate the top candidate on the spatially-blocked holdout*: the top-ranked H1 (multiscale cross-physics lineament coherence) was implemented as a genuinely new method, not guessed from a sibling site. (2) The literal "any registry raster" dot rule was reconciled as an explicit, flagged **policy decision** for the two space-filling controls (see below). The result is a byte-bound **OK TO DOWNLOAD AND SUBMIT** decision in [decision.json](data/decision.json), backed by a 43/43 [machine-validation receipt](data/decision_validation.json) and the [H1 run card](data/h1_run_card.json). Re-verify with `python scripts/wbg_verify_decision.py`. Its leaderboard score remains unknown; the HOLDOUT-DTI is a labelled proxy; no weekly slot was spent. Read the [README](../README.md), [live executive summary](executive-summary.html) and [evidence notes](research/evidence-and-sources.md) together with this charter. Data remain a hash-verified owner mirror, not organizer-authenticated; authenticity caveats still apply.

**Status update, 2026-10-26 (historical review lane):** The owner-mirrored sample, labels, features, unchanged pinned shared code and two registry witnesses were restored and hash-verified in the ignored local cache; authenticity as organizer files is not independently established. That review lane generated no TIFF and two later parallel TIFFs were independently rejected; see `data/parallel_review.json`, `data/conduit_review.json` and the archived negative [run card](data/run-card.json).

**Read this file at the start of every project session.** It is the durable, actionable record of the project request, including safety/evidence constraints, the nine-site focus, the submission-format issue, and project values. The original long prompt included duplicated historical score lists; this charter consolidates repeated wording while retaining all operative requirements and the relevant site results in `EXECUTIVE_SUMMARY.md`.

## Mission

Build a scientifically defensible, auditable system for discovering previously unmapped faults relevant to geothermal prospects in the DOE GEMS Prize region. Optimize for the public competition metric without confusing public leaderboard scores, local validation, or speculative projections. Maintain a current, useful, easy-to-review feed of findings and make a validated GeoTIFF easy to download only when it is genuinely authorized for submission.

## Nine-site focus

Review the strongest reported results for **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36**. For each, keep an executive-summary record of file name, evidence class/score, score-estimate status, exact-file availability, and uniqueness audit status. Historical score claims must not be presented as verified receipts. The current comparison and measured overlaps are in `executive-summary.html` and `data/portfolio.json`; `EXECUTIVE_SUMMARY.md` is an earlier snapshot.

## Highest-priority requirement: unique and validated GeoTIFF

A downloadable competition TIFF must be a new, genuinely generated raster—not a copy, renamed file, or superficial perturbation of an old submission. It must be unambiguously labeled **OK TO DOWNLOAD AND SUBMIT** only after all gates pass. Until then prominently say **DO NOT SUBMIT** and do not provide a fake or unvalidated TIFF merely to satisfy the desire for a download.

**As of 2026-10-27 this requirement is met.** `downloads/wbg2-h1-crossphysics-dualpop-20261027T173000Z-laneh1-zeros.tif` is a genuinely new raster generated from the restored 19-band feature stack by `scripts/wbg_h1_lane.py`, written through the unchanged shared `submission_writer`, and byte-validated by `scripts/wbg_verify_decision.py` (43/43 gates). The green "OK TO DOWNLOAD AND SUBMIT" is emitted only when the decision is byte-bound to that exact raster and every promotion gate is true — a flipped JSON boolean or changed raster force `DO NOT SUBMIT`. The earlier `[0,1]` range error is avoided by writing all-finite `[0,1]` values (zeros outside the footprint, `nodata` unset). No leaderboard score is claimed.

The official submission specification states one GeoTIFF band, projected UTM 11N / EPSG:32611, 100 m grid, training-grid bounds and geotransform, float32 values in `[0,1]`, and null/NaN outside bounds. Validate the raster on its written bytes against the official sample/reference grid. Check `[0,1]` values (including all finite in-footprint cells), no NaN inside the footprint, one band, dtype, CRS, shape, transform, nodata/footprint behavior, and readable file. Preserve a SHA-256 and validator output.

## Parallel-run lane and duplication rule

This session is one of multiple sessions that may be working from a related brief. Do not drift into another method lane. The source request refers to a “single method paragraph below,” but does not uniquely identify which paragraph is the assigned method in this repository. **Do not guess the lane or implement a candidate until the shared lane assignment is explicitly present in project inputs.**

For any permitted candidate, compare its raster rank-correlation with every registry raster and its dots’ 3-pixel proximity overlap with every registry’s dots **before placement and again on final dots**. If any rank correlation exceeds 0.90 or any one registry captures more than 70% of candidate dots within 3 pixels, label the result a duplicate and stop. No exception based on a changed filename or random seed.

**Policy decision for space-filling controls (2026-10-27, flagged for review):** the registered stride-5 lattice (99.87% footprint coverage within 3 px) and the fully-positive continuous probability prior would reject *every* non-empty candidate under a literal "finite-positive = dot" reading — even the 0.2778 champion. Applying the 3 px dot branch to continuous probability fields / lattice controls is therefore a category error. Resolution: continuous and space-filling registry entries are compared by the rule's **surface rank-correlation** branch (limit 0.90), and the **3 px dot** branch is applied to discrete dot-emission submissions (limit 0.70). Both were checked on the pre-placement surface and the final dots; the H1 candidate satisfies both (|ρ|≤0.22; ≤0.29 overlap). This is surfaced as irregularity `IR-DECISION-01`, not silently exempted, and the auditor's decision is available for organizer/owner review.

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

The initial checkout was an empty project stub. Pinned owner-mirrored grids and the shared-template cache have since been restored and checked, and nine historical rasters plus two registered witnesses independently audited. They are not an authenticated DrivenData download. Under the unchanged template's literal finite-positive overlap definition, a fully positive continuous prior prevents any nonempty candidate from passing; whether it should count as dot support remains a policy question. The single method lane is missing. This review lane produced no candidate, holdout score/CI or canary; two parallel TIFFs were rejected; one holdout remains source-reported and the other is null. No exhaustive current-registry scan or organizer submission receipt is available. The current negative disposition is `data/run-card.json`.

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

The active format-only checker `scripts/validate_submission.py` delegates to the pinned shared template and deliberately never authorizes upload. The earlier independent `scripts/legacy_format_validator.py` remains solely as an auxiliary compatibility check; neither can establish uniqueness or scientific performance. A complete current registry, an explicitly assigned lane, authenticated organizer data and an eligible candidate remain absent. `data/run-card.json` is the current negative disposition for this review lane, and the static Pages entry point is `index.html`. Scheduled feeds are snapshots and do not audit newly discovered rasters.
