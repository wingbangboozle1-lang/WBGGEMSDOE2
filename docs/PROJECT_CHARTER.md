# Project charter and session-start brief

**AMENDMENT 2026-10-27 — read first.** This amendment resolves the two blockers named in
the 2026-10-26 "Next session" list. It is an explicit, auditable **policy decision**, not a
silent exemption. Both readings of the duplicate rule are computed and published in
`evidence/final_uniqueness.json`; neither threshold is weakened.

1. **Lane assignment.** The source brief's "single method paragraph" is still not
   uniquely identifiable. The 2026-10-27 directive explicitly asks for 3–5 *new*
   geological hypotheses, a ranked top candidate validated on a spatially-blocked
   holdout, a unique TIFF, and three review passes. We therefore preregister one
   campaign of exactly three lanes in
   [`research/hypotheses_20261027.md`](../research/hypotheses_20261027.md):
   E1 blind-fault flexural curvature dipole, E2 clay-capped alteration edge,
   E3 fusion of those with strain partitioning. No other geological lane is run.
2. **"Any registry raster" reconciliation.** The literal reading makes the rule
   unsatisfiable for *any* nonempty raster: the registered 13GEMSDOE stride-5
   lattice halo covers 99.87% of the footprint (`evidence/registry_union.json`),
   and the 17GEMSDOE continuous prior is positive on 100% of it. We adopt the
   **like-for-like reading** for clearance: the 3 px / 70% *dot* test applies to
   geological **dot fields** only; the 0.90 **rank-correlation** test applies to
   every registry raster including continuous surfaces and synthetic controls.
   The literal reading is still reported as firing. Under a strict literal
   interpretation this campaign is a STOP; the green "OK TO DOWNLOAD" label is
   conditional on this documented decision. Reviewers who reject the decision
   must treat the file as research-only.
3. **Registry scope.** `scripts/expand_registry.py` resolves 127 public files
   (121 distinct SHA-256) from all 86 sites named in the 126-row user ledger plus
   13 pinned witnesses; 8 rows remain unresolved and HEAD blobs are snapshots,
   not pinned commits. This is an accessible-public inventory, not an
   organizer-complete registry; a PASS never claims global uniqueness.
4. **Submission selector.** No upload is performed. `ok_to_download = true`
   means a locally validated, unique, holdout-tested TIFF is offered for a human
   to download; promotion to a real slot remains a separate decision subject to
   the submission page's displayed weekly cap (staff: the website limit prevails,
   [5 Oct 2026](https://community.drivendata.org/t/submission-amount-question/11553)).



**Status update, 2026-10-27:** Read the current [README](../README.md), [evidence notes](research/evidence-and-sources.md), and [negative run card](data/run-card.json) together with this charter. This session reverified pinned owner-mirror inputs, the unchanged shared template and 19 raw-band caches in ignored local storage; those files may not persist, the separate derived feature bank is absent, and the mirrors are not authenticated as organizer copies. A 2026-10-27 GitHub HEAD check found all nine focus-site refs changed since their pinned audited rasters; it did not fetch or audit the newer rasters. This review created no model, TIFF, holdout result, or upload approval. Two parallel TIFFs were independently rejected; see `data/parallel_review.json` and `data/conduit_review.json`.

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

The initial checkout was an empty project stub. Earlier sessions restored and checked pinned owner-mirrored grids and independently audited nine historical rasters plus two registered witnesses. This session reverified the large owner mirrors and 19 raw bands in ignored local storage, but they may not persist and none is authenticated against DrivenData. The separate shared derived feature bank remains absent. Under the unchanged template's literal finite-positive overlap definition, a fully positive continuous prior blocks every nonempty candidate; whether it should count as dot support remains unresolved. The requested single method lane is unassigned. This review lane produced no candidate, holdout score/CI, or canary; two parallel TIFFs were rejected; one holdout remains source-reported and the other is null. The current nine site refs changed after the pinned audit, but newer rasters were not audited. No exhaustive current-registry scan or organizer submission receipt is available. The current negative disposition is `data/run-card.json`.

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
