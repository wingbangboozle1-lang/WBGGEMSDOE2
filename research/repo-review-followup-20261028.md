# Repository review follow-up — 2026-10-28

## Executive outcome

**Negative / stop: no new TIFF is cleared to download for submission. No experiment was run and no weekly slot was used.** The active publication policy in `src/wbggems/release.py` is deliberately fail-closed: its module text says there is no authorized lane or complete registry; `require_experiment_lane()` rejects a campaign without an assignment and then still requires a complete registry and reviewed pre-placement launcher. The canonical `evidence/run_card.json` likewise records lane `UNASSIGNED`, null holdout/novelty values, no new candidate, and `ok_to_submit: false`. The README's earlier assertion that a WBG4 file is “ready to upload” conflicts with those governing records and must not be relied on.

No TIFF was opened in this review because `rasterio` is not installed in this environment. Existing TIFF measurements below are repository-recorded claims, not fresh byte-level reproduction. We did not alter submission artifacts, override the duplicate rule, infer a score, or choose a submission.

## Audit findings and irregularities

1. **Release authority conflict (critical).** `README.md` previously began by declaring a TIFF ready to upload, while `src/wbggems/release.py`, `evidence/run_card.json`, and `evidence/release_audit.json` encode a negative decision. Several archived cards and `config/release_register.json` have positive `PROMOTE`/`PUBLISH` language. The same register describes the distal candidate as `ok_to_submit: false` while also calling it `PROMOTE-TO-SELECTOR`. Positive historical rows are not current selector authorization. A single current authoritative decision must govern every download CTA.
2. **No authorized experiment lane.** `config/research_hypotheses.json` and the canonical card are the governing configuration referenced by the release gate; a separate `config/wbg4_lane.json` and WBG4 evidence are legacy records and cannot override that gate. The request's protocol says to stop when no method paragraph is assigned. No new hypothesis was run or ranked as an assigned experiment here.
3. **Literal uniqueness rule blocks candidates on recorded evidence.** The latest canonical card reports a binary-lattice lower-bound overlap of 82.34% for a 37,654-dot budget and a continuous prior with full-footprint positive support. Those exceed the stated 70% stop. The interpretation of continuous probability support is unresolved, but the binary lattice witness alone blocks that budget. No exemption was invented.
4. **Score claims are not receipts.** The reported 0.2778 for the GEMSDOE32 B2 artifact and listed scores from the GEMSDOE sites are user/site-reported claims unless tied to an organizer submission receipt. No such receipt was verified in this review. Historical score values cannot justify a projection for a new artifact. Existing writeups contain conditional arithmetic, not measured new-submission leaderboard scores.
5. **Data / runtime gap.** `data/` has zero files in this checkout. `pytest` is not installed as a command and importing `rasterio` fails. Consequently the shared-template holdout, feature-only leakage canaries, raster byte validation, uniqueness reruns, site build tests and line-by-line data provenance checks could not execute. We did not try the competition downloader: prior repository records state it requires DrivenData authentication and the sandbox only permits outbound access to a limited host allowlist.
6. **Protocol budget.** Existing evidence records earlier experiments in other lanes; this review performed 0 experiments. The prescribed ceiling is 3 experiments or 2 hours; spending experiments under an unassigned lane or using a private fork would violate the protocol. `scripts/evaluate_holdout.py` and `scripts/submission_writer.py` exist, but their presence is not proof of a compliant current run or of cache availability.

## Requested site comparison / B2 explanation

The repository contains archived site comparisons and lineage analysis, but this review does not independently fetch the nine sites or authenticate score receipts. The recorded hypothesis is that B2's higher claimed score than related patterns may reflect retaining spatial proximity to hidden faults while pruning dots near known faults; the archive records a relation between GEMSDOE25/30 masks and B2 after removing dots near the mirrored catalogue. That is a plausible mechanism under the stated proximity-weighted metric, **not a verified causal explanation**: hidden truth and organizer receipts are unavailable, and the repo's own documented held-out-catalogue ranking does not calibrate leaderboard scores. Therefore no defensible point estimate can be supplied for a new submission and there is no basis to claim it beats 0.2778 or the reported current leader.

## Next actionable work

1. Reconcile README, executive summary, release register, site CTA, and canonical run cards to one byte-bound negative status; archived positive cards must be visibly labeled historical.
2. Restore supported Python dependencies and official competition inputs only through the authorized route; record source URL, retrieval time, grid metadata, and SHA-256. Do not treat owner mirrors as organizer-authenticated data.
3. Resolve the continuous-prior support interpretation from an official competition source, while retaining the binary-lattice blocker. The outbound network allowlist prevents this environment from reaching DrivenData; official USGS and reference-solution links can be retained for later review.
4. Only after explicit lane assignment and compliant shared-template/cache verification, run the specified buffered whole-segment pooled DTI evaluation, all single-feature leakage canaries, and pre-placement + final registry comparison. Stop immediately at either literal duplicate threshold.
5. Run tests and a Pages build in an environment with the declared dependencies. Keep the slot selector separate. Do not publish any TIF as “OK to submit” absent all gates and selector authorization.

## Checks performed

- Inspected branch and clean starting worktree: `arena/c561cbbd-wbggemsdoe2`; no pre-existing changes observed.
- Read `AGENTS.md`, the README opening and historical brief, current lane config, canonical run card, release policy, release register, and WBG4 lane evidence.
- `find data -type f`: 0 files.
- `pytest -q`: unavailable (`pytest: command not found`).
- Python import check: `rasterio` unavailable (`ModuleNotFoundError`).
- `python -m compileall -q src scripts`: passed.
- JSON parse of canonical run card, release audit, research hypotheses, and release register: passed.
- `git diff --check`: passed.
- No experiment, candidate generation, submission upload, or slot selection was performed. The repository changes in this pass are documentation-only; PR/merge status is reported separately after attempting the requested GitHub workflow.

## Sources for later manual review

- DrivenData problem description and metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Competition rules: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Competition data (login gated): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Organizer reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Official USGS GeoDAWN data: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Official EPSG:32611 reference: https://epsg.io/32611
