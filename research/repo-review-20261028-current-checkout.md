# Repository review — current checkout (2026-10-28)

## Decision

**BLOCKED — DO NOT SUBMIT any TIFF from this checkout.** This review did not generate or modify any prediction raster, run an experiment, spend a competition slot, or claim a score. The current local readiness snapshot says `ok_to_submit: false`, `research_launch_authorized: false`, and `lane: blocked`.

This decision resolves conflicting repository messaging: older README sections and lane landing panels describe previously registered candidates as cleared, while `evidence/run_card.json` is negative, the current readiness report is blocked, the main dashboard has an authoritative negative release section, and project policy requires fail-closed behavior. I changed the README and homepage's first decision panel to show the current blocked status and label old promotion text as historical. Other legacy pages may still contain superseded claims and need reconciliation before a Pages deployment.

## Review passes

### Pass 1 — inspect project direction and artifacts

Read the working agreement, README, project charter, findings, run cards, release audit, release register, WBG4 lane configuration and current readiness diagnostics. The requested nine-site executive comparison exists, but it uses historical/user-supplied leaderboard claims, not authenticated per-file organizer receipts; completeness and latest site revisions are not established. No calibrated new-file leaderboard score estimate is supported. Existing TIFFs are not a valid substitute for an approved generated file.

### Pass 2 — reconcile safety and implementation conditions

`python scripts/check_readiness.py --check` refreshed the dated report. Its payload explicitly blocks research launch and submission because the lane is recorded unassigned; inputs and pinned shared code are absent from this checkout; the registry is incomplete and continuous-prior semantics unresolved; the documented shared format-mask issue is not shown corrected; scientific canaries/holdout are not run; and the separate selector/quota is unavailable. The script's `--check` is expected to return exit 2 when blocked; do not confuse that with a test failure or approval. The command invocation used alongside `git status` returned the latter command's exit code, so that shell status was not evidence about readiness exit status.

The repository contains a `config/release_register.json` with candidate records and historical promotion labels, but its existence is not a current authorization. It conflicts with the current readiness result and canonical negative run card. This requires a release-register reconciliation; do not alter its scientific historical evidence to manufacture approval. The README previously opened with an unconditional submit-ready claim, and `docs/index.html` showed a green “SAFE TO SUBMIT” lane immediately above a negative decision. Both were corrected to fail-closed wording. Older deep-linked pages remain an irregularity to audit before publication.

### Pass 3 — tests and final verification

- `python scripts/check_readiness.py --check` regenerated `evidence/checkout_readiness.json`, `docs/data/checkout-readiness.json`, and `docs/readiness.html`; output says **BLOCKED / DO NOT SUBMIT**.
- Created the ignored local `.venv`, installed the declared `requirements.txt`, then ran `.venv/bin/python -m pytest -q -rs`: **378 passed, 16 skipped, 32 warnings**. Skips are due to absent competition labels/sample or pinned shared template; this is not a full data-backed pipeline run.
- The first test run exposed one real defect: retired `scripts/run_wbg2_dphs.py --selftest` imported the absent shared `gems57` before emitting its STOP. Added an early self-test guard before optional imports/writes; the full test run above passed afterward.
- Inspected all five release-register paths; all referenced TIFF paths exist, but physical presence is not clearance and hashes were not revalidated in this review.
- `git diff --check` and static status consistency checks passed. Full browser/link build and live Pages deployment checks remain outstanding.

## Scientific and product findings

- The highest historical listed result, GEMSDOE32 B2 **0.2778**, is **USER-REPORTED** per the extant executive summary, not an organizer-confirmed receipt. The documented raster lineage/pruning is a plausible mechanism, not proof that it caused that score. We cannot infer the hidden-fault score of a new raster from it.
- The request's apparent current leaderboard figures conflict. The repository has a dated public observation, which is not a receipt for any local file and is not a stable current leaderboard check.
- The protocol's ranked ideas N1–N4 are proposals only; none can be asserted as globally novel or experimentally better without comparable holdouts. The requested one-lane assignment is not authoritatively resolved for this checkout. `config/wbg4_lane.json` names a previous method, but the readiness gate and canonical run card explicitly say unassigned; current policy says do not self-assign or bypass that gate.
- The repository's old “score estimates” are projections, not results. There is no defensible estimate for a new submission here.
- Downloadable valid GeoTIFF guidance and a format check do not make a file scientifically eligible or organizer-approved.

## Remaining work, ordered

1. Reconcile `config/release_register.json`, README, and every download page against the canonical current release authority. Make all superseded pages explicitly historical/research-only before publishing.
2. Obtain or restore the exact pinned official inputs and derived cache in this checkout; validate source provenance, hashes, grid, bands, and physical semantics. Resolve any shared template issue upstream, not in a private fork.
3. Obtain explicit lane authorization and a written interpretation of whether continuous positive priors count under the literal 3-pixel duplicate rule. Refresh the complete registry, not just pinned witnesses.
4. Use only shared cached features, pinned holdout evaluator, and writer. Run feature-alone leakage canaries and preregistered whole-segment buffered hide-and-recover tests; compare paired same-fold results and report HOLDOUT-DTI with evaluator, withheld positives, and 95% CI.
5. Independently check pre-placement surface and final dots against complete registry. Require format validation on the exact saved bytes. Only a separate selector may authorize a slot after checking weekly quota; capture an organizer receipt before calling any leaderboard score confirmed.
6. Install requirements and run the full test/build suite. Verify deployed GitHub Pages does not present any stale “safe to submit” CTA.

## Run card — this review

```json
{
  "hypothesis": "No candidate tested; no current lane authorized.",
  "mechanism": "No surface or dots generated. This is a repository/status review only.",
  "named_non_fault_mimic": "For the historical WBG4 structural-edge idea, an unfaulted lithologic/intrusive contact can create a geophysical edge.",
  "holdout_dti": null,
  "evaluator_version": null,
  "withheld_positives": null,
  "ci95": null,
  "correlation_overlap_vs_registry": "No new surface or dots; complete registry not verified.",
  "raster_sha256": null,
  "validator_output": "No new raster; none authorized. Existing readiness reports blocked; no format checks were rerun.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

## Sources for manual review

- Official competition overview, metric, and submission context: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Competition rules: https://www.drivendata.org/competitions/306/competition-doe-gems/
- Official public leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- DOE/USGS GeoDAWN data record: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DOE GEMS prize project context: https://gdr.openei.org/submissions/1391
