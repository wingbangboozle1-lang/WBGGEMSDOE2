# Checkout review and run card — 2026-10-28

## Decision

**NEGATIVE / DO NOT SUBMIT.** No new TIFF or leaderboard estimate was produced. This is a fresh checkout-level decision, not an organizer score and not a claim that all historic files were byte-rechecked in this review.

## Evidence reviewed

- Read the repository working agreement, README, project charter, current run cards, release register, WBG4 lane configuration and its archived method/hypothesis notes.
- Ran `python scripts/check_readiness.py --check`: exit code **2**, output `BLOCKED / DO NOT SUBMIT`; readiness snapshot says `ok_to_submit: false`, with organizer mirrors and cached feature bands missing. `data/` is absent.
- The repository contains wrapper paths named `scripts/evaluate_holdout.py` and `scripts/submission_writer.py`; charter/review state says these are retired fail-closed wrappers. There is no available pinned shared evaluator/writer implementation to reuse, and no local derived feature bank. Thus no valid experiment can be executed under the prescribed reuse protocol.
- The current release audit says only 13 pinned registry witnesses were checked and `all_current_registry_rasters_checked: false`. A full uniqueness assertion is unavailable. No candidate surface existed to test pre-placement.
- No competition login, upload, organizer receipt, or account quota was checked. Historical score claims remain claims, not current receipts.

## Ranked candidate hypotheses (proposal ranking, not score projections)

The `WBG4-SCORR` method paragraph in `config/wbg4_lane.json` is the only recorded lane for this checkout. These ideas below are scoped alternatives for future selector/lane governance; they are not authorization to run outside that lane. They use layers named in the repository's WBG4 hypotheses, but current byte availability and provenance must be re-established first.

| Rank | Candidate | Layers and signature | Why it might find a missing fault | Difference from recorded methods | Cost / blocker |
|---:|---|---|---|---|---|
| 1 | Radiometric K–Th disequilibrium alteration corridor | GeoDAWN K, Th, Th/K and UK; seek persistent along-strike ratio anomaly/edges | Alteration may extend past a mapped trace or be preserved where a scarp is buried | A ratio-focused alteration indicator rather than a general multi-layer scarp classifier or simple radiometric edge fusion | Low–medium; use cached bands, but cache is absent; mimic: evaporites/clays/ash |
| 2 | Magnetic lineament continuity under cover | GeoDAWN upward-continued TMI and, if available, full magnetic feature bands; scale-space gradient ridges | Buried basement faults can lack surface relief and catalogue exposure | Deep magnetic geometry as primary signal rather than lidar morphology | Medium; full official feature raster absent; mimic: lithologic contacts/intrusions |
| 3 | Geothermal-discharge structural linkage | Official GDR springs/well geochemistry plus fault-independent lineament orientation | Discharge may pin a permeable structure whose mapped trace is incomplete | Pairwise relay/continuation geometry rather than simple thermal point density | Low–medium; current point file not present in checkout; mimic: non-tectonic brine discharge/wells |
| 4 | Multi-scale lidar relief-texture entropy | USGS lidar relief and curvature channels; local scale-normalized entropy/variance | Could identify subtle buried/eroded structures not represented by single-scale edge maxima | Texture statistic rather than existing scarp curvature and classifier features | Low; lidar stack absent; mimic: drainage/landslides |
| 5 | Strike-conditioned structural corridor (recorded WBG4-SCORR lane) | Lidar scarp, GeoDAWN radiometrics/extensions, SGMC geometry and visible faults; coherent multi-scale corridor | Withhold whole components and train blind to catalogue proximity, targeting geophysical analogues | Existing archived campaign describes an earlier supervised multi-layer corridor model | Medium; historical result is not reproducible here; do not rerun until shared code and cache are restored |

This rank orders qualitative expected value per implementation cost, not measured DTI improvement. AUC/DTI canaries must precede trust in any feature/model. The first four ideas are not to be run unless a separate governance decision assigns the method lane; do not exceed the three-experiment/two-hour cap.

## Focus-site historical leaderboard claims

The user-provided list identifies GEMSDOE32 B2 as 0.2778, GEMSDOE36 as 0.2750, GEMSDOE28 as 0.2710, GEMSDOE31 as 0.2708, GEMSDOE33 as 0.2632, GEMSDOE25 and GEMSDOE30 as 0.2600, GEMSDOE24 as 0.2477, and GEMSDOE27 as 0.2449. **All are USER-REPORTED / site-ledger claims in this review, not ORGANIZER-CONFIRMED receipts.** The highest listed is GEMSDOE32 B2, but its exact causal reason for score cannot be established from public/mirrored artifacts; existing repository analysis suggests a pruned catalogue-collar lineage, which is a hypothesis. See the linked site briefs at `docs/sites/` and official competition context at <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>.

No score estimate is offered for a new file. A holdout on catalogue faults is not automatically predictive of performance on expert-labelled faults missing from the catalogue; archived repository calibration also warns against converting holdout into leaderboard score.

## Three passes

1. **Pass 1 — implementation/review:** inspected the active documents and runtime gates; fixed top-level README and AGENTS.md to stop surfacing a stale “ready to upload” approval above the current negative readiness status.
2. **Pass 2 — consistency and risk review:** noted historical artifact claims conflict with current missing data/cache and incomplete registry. Explicitly retained historical B2 reasoning as a hypothesis, not fact. Did not create a raster to satisfy the request at the expense of the lane, leakage, or duplicate gates.
3. **Pass 3 — verification:** re-ran readiness; exit 2 as above. The first unit-suite run exposed one defect: the retired DPHS launcher imported the absent pinned `gems57` package before its self-test could fail closed. Added an early `--selftest` stop before optional imports; this does not enable experiment execution or change the shared template. Re-ran `.venv/bin/python -m pytest -q -rs`: **378 passed, 16 skipped, 32 warnings**. Skips concern absent sample/labels/shared template. `git diff --check` passed. No score or uniqueness result is promoted by this documentation/code correction.

## Run card (JSON)

```json
{
  "hypothesis": "No candidate was tested. Leading future proposal: radiometric K-Th disequilibrium corridor; no lane authorization beyond the recorded WBG4-SCORR paragraph.",
  "mechanism": "Potential persistent along-strike alteration ratio contrast from GeoDAWN K/Th and derived ratios; not evaluated in this checkout.",
  "named_non_fault_process": "Evaporite or lacustrine clay can produce a K-Th radiometric contrast without a fault.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "withheld_positive_count": null,
  "evaluator_version": null,
  "correlation_overlap_vs_registry": "Not measured; no new candidate surface/dots. Current audit is incomplete (13 pinned witnesses only).",
  "raster_sha256": null,
  "validator_output": "No new raster. Readiness exit 2; existing artifacts are not authorized by this review.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```

## Next blockers

1. Restore authenticated competition inputs and cached feature stack; record hashes and provenance.
2. Restore the unchanged pinned shared evaluator and writer; repair any defect upstream only.
3. Refresh all registry rasters, including each focus site's current best; resolve the continuous-prior/dot-overlap interpretation rather than silently exempting it.
4. Only after those checks, preregister the assigned hypothesis, run per-feature leakage canaries and buffered whole-component holdout, report HOLDOUT-DTI with evaluator/count/95% CI, then run surface and final-dot duplicate checks.
5. Keep slot choice separate. Verify current quota and obtain an organizer receipt before claiming a public score.
