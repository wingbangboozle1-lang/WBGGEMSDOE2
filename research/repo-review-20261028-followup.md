# Repository review follow-up — 2026-10-28

## Decision

**NEGATIVE — DO NOT SUBMIT any TIFF in this checkout.** This follow-up resolves a material internal documentation conflict; it does not authorize generation, selection, or upload.

## Review passes

1. **Top-level decision and repository map:** inspected the current branch/status, README, project instructions, canonical and session run cards, release register/audit, project charter, release research, and landing-page banner. The landing page says no file is approved and the literal all-registry gate is not satisfied. `README.md` previously contradicted that by declaring a GEMSDOE candidate “ready to upload”; corrected its opening to the negative current decision and explicitly demoted older approvals to historical.
2. **Artifact and research claims:** existing files, registered candidates, focus-site reports, hypotheses and evidence were reviewed as records rather than presumed current validation. The specified sites' scores are user-reported, not organizer receipts. Prior score explanations infer relationships from raster lineage and DTI algebra, but hidden truth, exact authenticated submissions, and causation are not independently established. Projections are not scores. The existing candidate approvals conflict with the current fail-closed rules (incomplete registry, continuous-prior ambiguity, absent lane and unreproducible current cache); none can safely be endorsed.
3. **Execution and final checks:** `python scripts/check_readiness.py --check` completed with `BLOCKED / DO NOT SUBMIT` and updated its generated diagnostics. Attempted `PYTHONPATH=src .venv/bin/python -m pytest -q -rs`, but `.venv/bin/python` is absent; system `python -m pytest` also cannot run because pytest is not installed. Thus the older 350-pass report is historical and was not reproduced in this review. No raster was generated/modified, no holdout or canary was run, and no weekly slot was used.

## Current blockers / irregularities

- The project policy requires an explicitly assigned method lane; the protocol's duplicate/holdout constraints do not themselves select a method. Do not self-assign from the ranked proposal list.
- The live current registry is incomplete for the required literal uniqueness gate; the dense continuous prior support interpretation is unresolved. Historic pre-placement candidate surfaces are unavailable.
- Required competition data/cache and pinned shared tools are missing in this checkout. The shared evaluator/writer are fail-closed wrappers; private replacements would violate the reuse requirement.
- Several older README sections and lane pages still contain “ready”, “promote”, “OK to download”, and numeric projections. The current landing-page negative decision and this README opening supersede them for the current release. This follow-up specifically fixed the README’s highest-visibility contradiction; the older material should be reconciled before using it as an operational download site.
- Public leaderboard snapshot and submission quota are not refreshed here. There is no organizer receipt for the listed site scores and no defensible estimate for a newly generated submission.

## Next permitted steps

1. Obtain explicit lane assignment and settle continuous-prior duplicate interpretation.
2. Restore and authenticate organizer inputs, raw/cache data and exact pinned shared-template revision; resolve any shared validator defect upstream.
3. Refresh the complete registry and re-run the prescribed pre-placement/final uniqueness tests.
4. Only then run feature-alone canaries and matched buffered whole-segment holdout via the shared evaluator, within the 3-experiment / 2-hour budget.
5. A separate selector may consider promotion only after holdout improvement and all gates pass; no automated upload or slot use is authorized here.

## Run card (negative)

```json
{
  "hypothesis": "No candidate tested; method lane remains unassigned.",
  "mechanism": "No new surface or dots generated.",
  "named_non_fault_mimic": "Unfaulted intrusive or lithologic contact can mimic a geophysical edge.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "withheld_positives": null,
  "evaluator_version": null,
  "correlation_overlap_vs_registry": "No new candidate; prior registry evidence is incomplete and the continuous-prior interpretation unresolved.",
  "raster_sha256": null,
  "validator_output": "No candidate raster; fresh readiness BLOCKED / DO NOT SUBMIT.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
