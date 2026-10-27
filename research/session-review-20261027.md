# Repository review and next-step decision — 27 October 2026

## Executive decision

**No new TIFF is approved or generated. DO NOT SUBMIT any existing local TIFF.** This review used zero candidate experiments and zero competition submission slots. It does not estimate a new leaderboard score. The requested per-site comparison and four ranked hypotheses already exist in the current dashboard and [`research/hypotheses.md`](hypotheses.md); this review checked their status instead of repeating or silently promoting their historical claims.

The blocker is not lack of an interesting hypothesis. The governing project agreement says to stop when the method lane is unassigned, and this request does not identify one specific N1–N4 method paragraph as the authorized lane. A ranked proposal is not authorization. Separately, the current-data and registry/uniqueness gates are not met. Generating a new file despite those gates would violate the requested parallel-run protocol and could create a misleading upload artifact.

## What I checked

- Read the project working agreement, README and preserved original prompt, current executive summary, project charter, research findings, canonical run card, release audit, source recheck and current ranked hypothesis register.
- Confirmed the canonical run card and its public aliases are negative: no HOLDOUT-DTI result for a new candidate, no estimate, no new raster hash, no submission name or note, and `ok_to_submit=false`.
- Restored only the pinned shared-template code into ignored local storage. No private copy or fork of the evaluator/writer was made. The separate shared-derived feature bank and competition `data/` inputs are not present in this checkout. No experiment was run.
- Ran the repository suite after restoring the template: **306 passed, 1 skipped**. The skipped case requires the pinned competition sample raster, which is absent. There were 37 Rasterio pending-deprecation warnings; no test failures.
- Ran the template's standalone holdout-evaluator tests from the already-present `data/shared_template/tests/test_evaluate_holdout.py`: **8 passed**. These are small synthetic/unit checks; they are not a geological holdout result.
- The first local test attempt found `pytest` missing from the base interpreter and the system package manager correctly refused a system install. I created an ignored `.venv` and installed the pinned project requirements there. No dependency or data artifacts were added to Git.
- Verified official pages during this review: the DrivenData problem statement, organizer reference-solution repository, USGS GeoDAWN data-release page and public leaderboard. Links are in [Sources checked](#sources-checked). The fetched leaderboard rendered a public score of `0.4544` for its leader; this is an **ORGANIZER-PUBLISHED PUBLIC LEADERBOARD OBSERVATION**, not a project submission receipt, hidden/private score, final-round score or basis for predicting a new file.

## Historical nine-site result: what can and cannot be inferred

The supplied GEMSDOE24/25/27/28/30/31/32/33/36 values are historical user-reported claims, not authenticated submission-page receipts. The existing [nine-site executive summary](../docs/CURRENT_EXECUTIVE_SUMMARY.md) links each listed raster and correctly labels the result claims and uniqueness limitations. Its strongest supplied historical claim is GEMSDOE32's `0.2778` (**USER-REPORTED**, not organizer-confirmed).

The saved mirror audit supports a measured lineage: the GEMSDOE25 and GEMSDOE30 d2.8 masks are identical inside the mirrored footprint; the GEMSDOE32 B2 mask equals that mask after deleting 6,436 catalogue-near dots (44,090 → 37,654); GEMSDOE36 adds 1,200 dots to B2. This is a byte-level relationship, **not** proof that pruning caused a score improvement. The official distance-weighted Tversky metric rewards probability-weighted proximity to withheld faults while penalizing false-positive mass. A plausible explanation for a sparse B2 score is that pruning reduced false-positive cost while retaining enough proximity credit—but the private labels, per-cell score contributions and authenticated receipt needed to establish causation are unavailable. Therefore the repo cannot defensibly claim that a new submission would beat `0.2778` or the public leaderboard.

## Ranked geological proposals already recorded

These are the existing qualitative ranks, **not measured DTI forecasts**, and were not re-run or promoted in this review:

| Qualitative order | Hypothesis | Layers/signature | Key caveat and data status |
|---:|---|---|---|
| 1 | N1 — signed edge-pair cancellation / non-fault-body veto | Cached RTP, isostatic gravity and conductive-base depth bands; test signed cross-normal profiles for persistent steps versus finite-width balanced lobes. | Intrusive or lithologic margins can mimic a step; a fault-bounded block can be wrongly vetoed. No new binary is proposed, but organizer-authenticated feature input/cache and explicit lane authority are missing. |
| 2 | N2 — radiometric-quiet magnetic-edge transfer under conductive cover | Total-count, RTP, conductive-base depth, conductivity and detrended-slope bands; test whether magnetic edges persist where surface radiometric contrast weakens, with within-fold strata and negative controls. | Soil moisture, sediment, clearance, weak radiometry and buried non-fault contacts mimic the pattern. Band interpretation/units require provenance; no new external binary is proposed. |
| 3 | N3 — catalogue-free edge-orientation transport | Isostatic gravity, RTP and detrended elevation; build a label-free edge graph and test multi-field junction continuity without catalogue-endpoint seeding. | Dikes, intrusions, drainage intersections and survey seams mimic junctions. Requires a new graph operator, but no new external binary is proposed. |
| 4 | N4 — survey-axis notch-stability veto | Magnetic and total-count grids plus official GeoDAWN survey-orientation metadata; compare local axis-selective attenuation against rotated-axis controls. | Can suppress real axis-parallel faults; a gridded sensitivity test does not independently validate flight-line artefacts. Official USGS metadata is accessible, but the raw input and lane gates still block evaluation. |

The detailed paragraphs, claims of difference from locally reviewed methods, confounders and source links are in [`research/hypotheses.md`](hypotheses.md) and [`config/research_hypotheses.json`](../config/research_hypotheses.json). The official USGS source documents distinct survey areas, different flight/tie-line spacing, aircraft and variable terrain clearance; that supports careful local artefact controls, not a global notch or a fault label. These proposals are not globally novel claims.

## Three-pass review

### Pass 1 — implementation and current state

- The requested prompt is already preserved in README and the README instructs future sessions to read it along with the working agreement and current decision documents.
- The site already places the negative submission decision prominently and includes the nine-site table, download-status page, submission instructions, official sources and current evidence links.
- A `.tif` exists in the repository, but the current audit explicitly treats it as research-only and `DO NOT SUBMIT`; it is not a valid new/approved deliverable. The most recent release audit reports every audited TIFF identity has a decisive literal overlap witness.
- No experiment was authorized because the lane is unassigned. Restoring evaluator code and unit-testing it does not constitute a holdout or candidate evaluation.

### Pass 2 — bug, assumption and edge-case review

- **Completeness of novelty inventory:** current witness set is not a complete, fresh registry. A passing comparison to nine focus-site files would not establish uniqueness. The existing audit says all current registry rasters have not been checked.
- **Literal novelty policy:** the pinned 13GEMSDOE stride-5 lattice is a binary duplicate witness; at a 37,654-dot budget, the saved mathematical bound forces more than 70% of any in-footprint set within three pixels of it. A separate continuous positive prior covers the full footprint under the literal finite-positive support rule. Whether a continuous probability prior should count as “dots” remains an unresolved policy interpretation; do not silently exempt it or work around the lattice with edge-biased points.
- **Pre-placement check:** old candidate surfaces were unavailable for replay. Final-raster overlap alone cannot retroactively certify their pre-placement surface tests.
- **Inputs and provenance:** no authenticated organizer data, labels or sample raster is present. The public owner mirror is not equivalent to a DrivenData-authenticated download. The new-score estimate remains null; do not present the public leaderboard or user-reported site results as an estimate.
- **Validation vs acceptance:** synthetic tests establish code behavior only. The missing competition sample means one input-dependent test is skipped. A local format check cannot establish organizer acceptance or resolve the cause of the user's past range error.
- **Holdout leakage:** there is no newly measured spatially blocked HOLDOUT-DTI and no all-fold single-feature canary result for N1–N4. Historical or parallel source-reported values are not evidence for a corrected/new method.

### Pass 3 — request and next-step reconciliation

- The user asks for a unique TIF and a current estimate, but the higher-priority in-repo fail-closed rules require explicit lane assignment and a clear uniqueness path first. We must not manufacture a file or guess an estimated score.
- No weekly slot is selected or used. Slot selection is a separate selector step, not implied by a passing test or a file appearing for download.
- Before any experiment: assign exactly one method paragraph; restore inputs into the prescribed shared-template cache with provenance; resolve the continuous-prior rule; refresh and audit the complete registry; confirm the current submission format and quota through official account access. Then run the specified buffered whole-segment hide-and-recover protocol, derive catalogue features only from visible faults, run each-feature canaries across folds, compare to a matched incumbent, and stop after three experiments or two hours. Only then can a separate selector consider a submission.
- Before generating any new TIFF, fix/report the known shared validator's interior-mask behavior upstream (or use the permitted shared template's supplemental gate without forking), and require strict read-back: single-band format, values in `[0,1]`, no NaN inside footprint, exact CRS/shape/transform, output hash, and recorded validator output. No such release gate has been cleared here.

## Sources checked

- [DrivenData GEMS problem description, datasets, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Confirms the task is predicting faults indicative of geothermal resources—not direct vent detection—and that experts label previously unmapped faults for scoring; the final round expands labels after expert review.
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). Public-page observation only; not a receipt for any project file and does not identify a hidden/final score.
- [Organizer reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution). Public repository page; its existence does not validate this project's model or data.
- [USGS GeoDAWN official data-release page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Describes airborne magnetic/radiometric products, distinct acquisition areas and specifications, variable clearance, product formats, DOI `10.5066/P93LGLVQ` and CC0 marking.
- [Project source verification record](source-verification-release-20261027.md) and [current blocker register](release-blockers-20261027.md) preserve deeper source-by-source checks and access limitations.

## Final run card

```json
{
  "hypothesis": "No new candidate. N1 is the highest-ranked qualitative proposal in research/hypotheses.md; not authorized because the method lane is unassigned.",
  "mechanism": "No surface or dots were constructed. Proposed N1 tests signed gravity/magnetic cross-normal edge profiles to discriminate persistent steps from finite-width body signatures.",
  "named_non_fault_mimic": "Unfaulted intrusive or lithologic body margins; a fault-bounded narrow block can also resemble a finite-width body.",
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "status": "NOT RUN",
    "evaluator_version": "gems57-pooled-hide-v2 (pinned shared-template code; unit-tested only)",
    "withheld_positive_pixels": null,
    "ci95": null
  },
  "correlation_overlap_vs_registry": {
    "preplacement_surface_rank_correlation": null,
    "final_dot_overlap": null,
    "status": "No candidate surface/dots; exhaustive current registry absent; existing candidate artifacts have rejection witnesses."
  },
  "raster_sha256": null,
  "validator_output": {
    "status": "No new raster to validate; no NaN/range/CRS/shape/transform result for a new candidate.",
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null
  },
  "submission_name": null,
  "note": null,
  "verdict": "negative"
}
```
