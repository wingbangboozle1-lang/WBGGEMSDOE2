# Repository review — 2026-10-28

## Decision

**NEGATIVE — DO NOT SUBMIT any TIFF currently in this repository.** I reviewed the checkout, refreshed its read-only readiness diagnostic, and ran the available automated tests. I did not create or alter any prediction raster, place dots, run a candidate experiment, fetch competition data, query a live score, or spend a competition slot. No verified leaderboard-score estimate can be supplied.

The result is a useful research and audit workspace, not a submission-ready pipeline in this checkout. The highest reported historical claim relevant to the requested sites is GEMSDOE32 B2 at **0.2778 — USER-REPORTED**, not an authenticated receipt tied to the exact bytes. The repository's byte-level analysis finds plausible raster lineage—D2.8 pruning around the mirrored mapped-fault catalogue—but cannot establish that pruning caused the reported score. Without the hidden labels and a receipt, causal attribution and a trustworthy new-score estimate are unavailable. A claim that the project can beat 0.2778 or the latest public leaderboard would be unsupported.

## Three review passes

### Pass 1 — trace the documented task and release gates

- Read `AGENTS.md`, `README.md`, `docs/PROJECT_CHARTER.md`, `research/findings.md`, `evidence/run_card.json`, `evidence/release_audit.json`, and the source-verification/repository-review records.
- Confirmed the public Pages entry point and the release page put the negative decision up front; the nine focus sites have per-site briefs, historical-file links, claims marked as user-reported, no new-score estimates, and “DO NOT SUBMIT” guidance.
- Confirmed the research list contains four ranked, unimplemented hypotheses (N1–N4), each documenting layers, physical signature, rationale for uncatalogued faults, distinction from local prior methods, likely mimic, and cost/rank. These are proposals, not proven globally novel methods or measured improvements.
- Readiness check: `python scripts/check_readiness.py --check` returned exit 2 and **“BLOCKED / DO NOT SUBMIT.”** Its new local snapshot records no new raster, no estimate, zero experiments and zero slots. In this checkout the pinned shared-template files, raw band cache, official-input mirrors, and derived-feature bank are absent. The full current registry and original candidate surfaces are also not established.

### Pass 2 — inspect scientific and engineering blockers

- The assigned single method lane is still **UNASSIGNED**. The prompt's evaluator and uniqueness rules describe constraints, but do not choose one N1–N4 paragraph as this run's lane. Repository policy forbids self-assignment.
- The shared evaluator and writer must be reused, but the local `scripts/evaluate_holdout.py` and `scripts/submission_writer.py` are deliberately retired fail-closed wrappers; the pinned shared implementation is not present in this checkout. Rebuilding a private implementation would violate the task protocol. Thus no valid feature-alone canary or required buffered hide-and-recover pooled DTI/CI can be run here.
- The current byte audit is a decisive negative witness set, not a complete live registry audit. It records 13 pinned registry witnesses and 15 existing TIFF paths / 13 distinct TIFF hashes. The audit explicitly says all current registry rasters have not been checked. One registered continuous positive prior creates 100% overlap under the literal finite-positive-support definition; whether that is intended to count as dots remains unresolved and no exception is authorized. The requested pre-placement surface checks are not available for historic candidates.
- The refreshed checkout snapshot differs from prior dated snapshots: formerly restored ignored data/cache files are absent here. Historical restoration logs and hashes cannot be treated as current local availability or organizer authentication. Do not use an old “ready” result to bypass this diagnostic.
- The latest user-supplied values for later experiments are retained as conflicting/unverified claims in `evidence/request_claim_conflicts.json`; they do not replace exact-file audits or organizer receipts. The nine-site landing table is an index of pinned historical artifacts/claims, not a recommendation that any is safe to submit. For the focus files, the existing audit reports >70% three-pixel overlap against another named registry raster; every listed historical TIFF is explicitly research-only.
- Format validation is not scientific approval. The independent release audit records a negative disposition, and the shared-template format/mask defect remains documented without an upstream correction. The specific uploaded TIFF that triggered the user's `[0, 1]` error is not identified in this repository, so its cause cannot be diagnosed with certainty.
- Official source URLs are present in the repository, but this review made no fresh retrieval of DrivenData, DOE/NLR, USGS, or DOE GDR pages. Current public leaderboard position, weekly quota, and per-file organizer receipts were not verified.

### Pass 3 — verify runnable checks and outputs

- Installed the declared requirements into the ignored `.venv` only; no dependency files changed.
- Ran `.venv/bin/python -m pytest -q -rs`: **350 passed, 12 skipped, 32 warnings**. All 12 skips are explicit checks that need the absent pinned sample or shared template. Warnings are Rasterio affine-operation pending deprecations.
- `git diff --check` passed after the documentation update.
- `python scripts/check_readiness.py --check` refreshed `evidence/checkout_readiness.json`, `docs/data/checkout-readiness.json`, and `docs/readiness.html`. These are intentionally dated checkout diagnostics; the refresh recorded missing ignored assets rather than silently carrying forward their earlier verified state. The page does not authorize research or upload.

## Existing hypothesis shortlist and next permitted scientific action

The ranked shortlist already in `research/hypotheses.md` / `config/research_hypotheses.json` is:

1. **N1 — Signed edge-pair cancellation as a non-fault-body veto** (gravity anomaly, RTP magnetic field, conductive-base depth proxy): distinguish persistent structural steps from balanced finite-width body responses; medium cost. Main mimic: an unfaulted intrusive/lithologic contact.
2. **N2 — Radiometric-quiet magnetic-edge transfer under conductive cover** (total count, RTP, conductive-base depth, conductivity and detrended elevation): test whether magnetic edges transfer into cover-obscured settings; medium cost. Main mimics include soil moisture, weak radiometry, aircraft clearance, sediment and non-fault contacts.
3. **N3 — Catalogue-free edge-orientation transport through structural junctions** (gravity, RTP and detrended elevation): test cross-field-supported ridge-junction geometry without catalogue endpoint seeds; high cost. Main mimics include dikes, intrusive boundaries, drainage intersections and survey seams.
4. **N4 — Survey-axis notch-stability veto on gridded edge evidence** (magnetic/RTP and total-count grids plus documented survey orientation): a low-to-medium-cost artifact-sensitivity control, not an independent survey. Main mimics include real faults parallel to survey directions and anisotropic geology.

Ranks and expected potential are qualitative, **not score projections**. No candidate can be validated without the restored pinned feature stack and shared tools; no experiment is authorized until a single lane is assigned and the continuous-prior support rule is resolved. When those prerequisites are met, preregister one candidate, run each feature-alone canary on every required buffered whole-segment fold, compare against a matched incumbent with paired spatial uncertainty, and stop at three experiments or two hours. A separate selector—not this research run—must govern any real submission slot.

## Next work, in order

1. Obtain the explicit shared lane assignment and written interpretation of continuous-prior support; keep the current negative release until then.
2. Restore/authenticate the competition sample, labels, feature raster and derived feature cache; restore the unchanged pinned shared template and resolve its format issue upstream. Confirm hashes in the current checkout.
3. Refresh and audit the complete current registry, including all named organizations/sites, against both the pre-placement score surface and final dots. Missing registry entries cannot be interpreted as a uniqueness pass.
4. Run the prescribed canaries and matched holdout experiment(s) only through the pinned shared evaluator/writer. Report HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI; never call it an organizer score.
5. Only if holdout improvement and every duplicate/format/provenance gate pass, have the separate authorized selector check the current weekly cap and produce a named file and short comment. An organizer receipt is still required to call an uploaded score confirmed.

## Run card — negative result

```json
{
  "hypothesis": "No candidate tested; method lane remains unassigned.",
  "mechanism": "Not applicable. Existing N1-N4 are proposals only; N1 is the leading qualitative proposal.",
  "named_non_fault_mimic": "An unfaulted intrusive or lithologic contact can mimic a persistent gravity/magnetic edge.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "withheld_positives": null,
  "evaluator_version": null,
  "correlation_overlap_vs_registry": "No new pre-placement surface or final dots; historic audited files already have duplicate witnesses. Full current registry not checked.",
  "raster_sha256": null,
  "validator_output": "No new raster. Existing files remain research-only; no new submission was validated.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

## Source links for follow-up

- [Official DrivenData problem, metric, inputs and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE/NLR GEMS competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS release 1391](https://gdr.openei.org/submissions/1391)
- [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)

Links are provided for review; their current contents were not freshly verified in this offline-access review.
