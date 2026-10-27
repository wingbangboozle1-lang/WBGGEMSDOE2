# Repository review and next-step decision — 2026-10-27

## Executive decision

**Negative / DO NOT SUBMIT.** The project has a substantial evidence-first static site, per-site historical summaries for the requested nine GEMSDOE sites, a canonical run card, an independent byte-bound release audit, and broad test coverage. It does **not** currently contain an eligible submission. Do not download any repository TIFF for a competition slot.

This review was limited to the checked-out repository, its saved evidence, local build scripts, and tests. I did not create or modify a prediction raster, launch a model experiment, use a competition slot, fetch new competition data, or authenticate an organizer score receipt. The user-requested method lane is still explicitly unassigned; the project charter and shared-lane rules prohibit assigning one by inference.

## Three review passes

### Pass 1 — trace the current decision and pipeline

- Read `AGENTS.md`, the current charter, findings, run card, release audit, and source-verification report, as required by the repository's working agreement.
- Confirmed that the README preserves the original project prompt and prominently labels the release **NEGATIVE / DO NOT SUBMIT**.
- Confirmed that `docs/release.html` presents the nine-site comparison and the download gate; historical numbers are marked user-reported, new-score estimates are unavailable, and every historical file is research-only.
- Confirmed the run-card contract has no new candidate name, raster hash, holdout score, confidence interval, or approval.

### Pass 2 — check implementation, contradictions, and edge cases

- Reopened the canonical `evidence/release_audit.json` summary: **10 TIFF paths, 8 distinct TIFF SHA-256 identities, 7 ZIPs, 13 pinned registry witnesses**. It says the current registry is not fully covered. The 8 unique audited identities each have a literal duplicate witness; a local format PASS does not authorize upload.
- Found a material stale-count defect: the current run card said **6 ZIPs**, and the project charter/blocker summary said **9 paths / 7 identities / 6 ZIPs**, even though the byte-bound audit and README said **10 / 8 / 7**. The run-card builder verified TIFF path/hash totals but did not derive the ZIP and witness counts. Updated it to derive those counts from the canonical audit, corrected the current summaries, and added a regression test.
- Kept historical count snapshots in explicitly dated archival/reconciliation records unchanged; those describe the evidence available at their recorded point, not the current inventory.
- Verified the relevant safety mechanisms in `src/wbggems/release.py`: missing/changed artifacts and ZIP members fail closed, witnesses bind to pinned hashes and thresholds, and publication refuses a current card that claims approval.
- Reviewed the nine-site status: the strongest historical claim listed for GEMSDOE32 is **0.2778 USER-REPORTED**, not a receipt bound to the downloaded bytes. Repository evidence describes B2 as the GEMSDOE25/30 D2.8 mask after removing predictions within two pixels of the mirrored known-fault catalogue. This is a measured lineage relationship; the reason for the reported leaderboard value is not causally proven without hidden truth and an authenticated receipt. Pruning can plausibly improve the stated precision/recall tradeoff, but it can also delete predictions that would earn distance-kernel credit.
- The saved source record reports a public leaderboard observation of **0.4544 on 2026-10-27**. This is an organizer-published public-page observation, not a receipt for this project's file and not a stable private-leaderboard target. It conflicts with earlier user-supplied values such as 0.3195/0.4413; do not treat those as current verified leaders.

### Pass 3 — rebuild and run tests

- Created an ignored virtual environment and installed the versions allowed by `requirements.txt`.
- Ran the same static-site/evidence build sequence used by CI: `build_hypotheses.py`, `build_run_card.py`, `build_site.py`, `build_site_data.py`, `build_msptcd_site.py`, `build_release.py`, and `build_release_review.py`. All completed successfully; the site builders kept the negative disposition.
- Ran `.venv/bin/python -m pytest -q`: **295 passed, 12 skipped, 32 warnings**. Skips are explicit: the ignored pinned sample/shared-template data are not present in this checkout. Warnings are Rasterio affine-operation pending deprecations, not test failures.
- Ran `git diff --check`; it passed. No experiment, TIFF generation, or slot use occurred.

## Highest-priority blockers

1. **No submission currently qualifies.** The literal duplicate rule rejects every existing audited TIFF. The binary-lattice witness creates a high-overlap lower bound at the standard dot budget. A fully positive continuous prior yields 100% overlap under the pinned finite-positive support definition; whether that raster is intended to count as “dots” is unresolved. Do not invent an exemption or move points to footprint edges to game the gate.
2. **The method lane is unassigned.** `research/hypotheses.md` ranks N1–N4 proposals, but expressly does not authorize any of them. Per the parallel-run protocol, no experiment should start until an explicit single lane is assigned and the continuous-support rule is clarified.
3. **The freshness and provenance gates remain open.** Thirteen pinned witnesses are a decisive duplicate-detection set, not an exhaustive current registry. Historical site repository HEAD changes do not prove current raster content or uniqueness. The feature/reference assets are owner mirrors and not authenticated organizer downloads; the shared derived feature bank is absent here.
4. **The corrected model has no matched holdout evidence.** Historical scores are user claims or source-reported experiment results. They do not establish that a new method beats 0.2778, the public leaderboard, or the private test set. No corrected-v2 HOLDOUT-DTI, withheld-positive count, paired CI, or all-fold canary was measured in this review.
5. **The reported upload error is unresolved.** The exact TIFF that triggered “Predicted values must be in range [0, 1]” is not in the repository. Existing examples show distinct encoding issues (outside-footprint NaN and masked in-footprint cells), but neither identifies the cause of that different upload. Do not silently clip or rewrite a candidate.
6. **Shared-template format behavior needs upstream resolution.** The committed report reproduces an in-footprint mask/NoData issue in the pinned shared tool. Keep the tool pinned and do not create a private fork; an upstream fix and exact organizer-compatible reference remain outstanding.

## Research proposals already recorded (not results)

`research/hypotheses.md` contains four unimplemented, locally testable proposals with layers, targeted signatures, competing explanations, differences from existing code, and cost/rank judgments. It does not establish novelty across all other projects or score improvement. The sensible next scientific step—only after the lane and policy gates are settled—is to preregister one proposal, use the shared feature stack/evaluator/writer, calculate each feature-alone canary on every buffered whole-segment fold, then compare it to a matched corrected incumbent. The experiment budget remains at most three experiments or two hours.

## Recommended work order

1. Resolve the lane and the continuous-prior support interpretation in the shared project controls; retain a negative release meanwhile.
2. Refresh and hash-pin a complete current registry, including parallel submissions, and authenticate the exact competition sample/features through an authorized organizer download. Re-run input provenance checks; do not use a changed site HEAD as a substitute for raster audit.
3. Fix the shared validator issue upstream and preserve a strict independent readback for range, mask, footprint, CRS, shape, transform, and written-file integrity.
4. Build/reuse the pinned derived feature cache and run one preregistered candidate plus a matched baseline on identical buffered spatial folds. Record evaluator version, withheld-positive count, pooled DTI, paired spatial 95% CI, and every feature-alone canary.
5. Recheck candidate surface correlation before placement and final-dot overlap against every registry raster. Only after every gate passes should a separate authorized selector inspect the current weekly quota and create a named file/note; no automatic upload is appropriate.

## Official reference links for the next research pass

These are traceable sources already recorded in the repository; this review did not independently fetch them anew:

- [DrivenData GEMS problem, metric, feature inventory and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE/NLR GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS Argenta Rise multi-physics study](https://pubs.usgs.gov/publication/70271418)
- [DOE GDR INGENIOUS data release 1391](https://gdr.openei.org/submissions/1391)
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)

No external scientific claim above is represented as newly verified in this repository review. See `research/source-verification-release-20261027.md` for the dated provenance and access limitations.
