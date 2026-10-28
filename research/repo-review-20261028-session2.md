# Repository review — session 2 (2026-10-28)

## Decision

**Negative: do not submit any checked-in TIFF as a newly authorized candidate.** This pass did not generate a raster, run an experiment, spend a weekly slot, or claim a competition score. The task asks for a designated single method paragraph/lane, but none is assigned in the active project inputs; project policy (`AGENTS.md`) explicitly requires stopping rather than self-selecting. The executable readiness check reports **BLOCKED / DO NOT SUBMIT** because the required local competition inputs and feature cache are unavailable in this checkout. The current run card likewise records no new candidate experiment.

## Findings and corrections

1. **Critical user-facing decision conflict fixed.** `README.md` opened with a “cleared to submit” claim, `index.html` said WBG4-SSCC was cleared, and the first prominent banner of `docs/index.html` called a file “SAFE TO SUBMIT.” Those statements contradicted `evidence/session_run_card_20261028.json`, current checkout readiness, the incomplete-registry caveat, and the current literal duplicate gate. README, the root landing page and dashboard's top banner now state **DO NOT SUBMIT**; the dashboard no longer puts an old “OK TO DOWNLOAD” WBG2-DISTAL2 link in its highlighted card. Historical artifacts remain linked as archived/research evidence, not promoted downloads.
2. **Nine-site reference analysis already exists** in `research/focus-sites-review-20261028.md`, with named pinned file references, USER-REPORTED claims, estimates marked unavailable, and measured within-focus overlap. It reports GEMSDOE32's 0.2778 as the highest user-supplied value but does not claim organizer confirmation or causal attribution. Its measured peer overlaps exceed the protocol's 70% threshold; those archived files therefore are not unique under that comparison.
3. **B2 explanation remains hypothesis, not causal proof.** Existing pixel-array evidence links the B2 raster to pruning from the shared D2.8 mask, but there is no receipt connecting the stated leaderboard result to the exact bytes and no hidden-label contributions. The penalized false-positive/false-negative trade-off is a plausible explanation; the data do not identify that as why the reported score was reached. A leaderboard score estimate for a new raster is not defensible.
4. **Experiment gates are not satisfiable here.** Missing local `data/` inputs and cached features prevent use of the required cached stack / shared evaluator; complete registry coverage and interpretation of continuous-prior support are also unresolved. Surface pre-placement correlation cannot be recovered from the historical TIFF alone. No experiment is justified until lane assignment and these blockers are resolved.
5. **Potentially stale or inconsistent archived content remains.** Several deep-linked lane pages, release registers, JSON exports, and historical README sections retain promotion/estimate language. The corrected root README and home pages override that history for this checkout, but a full generated-site rebuild and cross-page stale-state audit is still necessary before publication. Do not treat artifacts in the release register as evidence that they satisfy the current prompt's stricter all-registry policy.

## Three review passes

- **Pass 1 — inspect:** read the working agreement, project charter, current run cards, release register/audits, nine-site review and the home-page content; checked source structure and local readiness.
- **Pass 2 — challenge:** identified the green “ready”/“safe” claims conflicting with the negative current run card and readiness result; confirmed the focus table differentiates user-reported scores from estimates and reports overlap; checked for absent data/cache.
- **Pass 3 — correct and verify:** changed the README and root/dashboard prominent decisions to negative, removed the highlighted downloadable link for the previously promoted scoped-only file, retained research links, and reran readiness. The latter exited 2 with BLOCKED / DO NOT SUBMIT. Test suite execution was unavailable because `pytest` is not installed (`pytest: command not found`; `python -m pytest`: `No module named pytest`). No source or cached data were changed by the readiness check; its generated diagnostics were restored before the final diff.

## Required next steps / limitations

- Assign a single method lane explicitly; do not infer one from this request's list of sites.
- Restore the official competition data and derived feature cache using an authenticated/authorized source; verify the pinned hashes and organizer provenance. This checkout does not contain them.
- Resolve what constitutes “dots” in the registered continuous prior, or formally change the exact duplicate rule; do not exempt it privately.
- Obtain a current comprehensive registry and run the pre-placement correlation and final-dot proximity gates on every registry raster.
- Only then run individual-feature leakage canaries and buffered whole-fault holdout under the pinned shared template, with evaluator version, withheld positives and confidence interval; compare matched folds to a baseline.
- Run repository tests in a Python environment with declared audit/test dependencies installed, rebuild all generated pages, and audit every prominent download/approval phrase before publication.
- A new submission may be offered only after all required gates pass. No score projection is a score; only a submission-page receipt is organizer-confirmed.

Official human-review links: [competition problem, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/), [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
