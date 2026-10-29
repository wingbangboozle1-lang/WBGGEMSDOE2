# Repository review — 2026-10-29

## Decision

**BLOCKED / DO NOT SUBMIT. No new TIFF was generated and no competition slot was used.** This review is an audit and safety correction, not a scientific experiment. It cannot claim a leaderboard score or that any candidate beats 0.2778. The best historical value in the supplied nine-site list remains the **USER-REPORTED** GEMSDOE32 B2 value, 0.2778; there is no organizer receipt tying that score to the audited bytes. The request's other leaderboard figures (0.3195, 0.4413) are not interchangeable evidence of a score for any of these files.

## What I inspected and verified in this checkout

- Repository state began clean at `74b7e44` on `arena/0ce1f939-wbggemsdoe2`; no PR already exists for this branch. The README, project charter, current findings, run card, release audit, readiness diagnostic, nine-site summary, review ledger, hypothesis shortlist, release/uniqueness code, tests and output pages were inspected.
- `python scripts/check_readiness.py --check` returned **exit 2** and `BLOCKED / DO NOT SUBMIT`. It refreshed the dated readiness snapshot. At this checkout, organizer input rasters and cached features are absent; the method lane is unassigned; complete-registry checks, shared-code format issue, scientific validation and separate selector are blocked or not run.
- The readiness snapshot identifies a literal overlap contradiction: at 37,654 dots, its binary-lattice lower bound is 82.34% within three pixels (above the specified 70% stop); under the current finite-positive-support interpretation a continuous positive prior gives 100% overlap. The latter rule's intended treatment remains unresolved. These are recorded calculations/audits, not new candidate measurements.
- `python -m pytest -q -rs`: initially unavailable because pytest was not installed in the base interpreter. I created the ignored `.venv/`, installed the declared `requirements.txt`, then ran `.venv/bin/python -m pytest -q -rs`: **378 passed, 18 skipped, 32 warnings**. Skips explicitly require missing official rasters/labels, the pinned shared template, or the feature grid. The warnings are Rasterio pending-deprecation warnings. No tracked dependency changes were made.
- `git diff --check` passed after the README safety edit.
- GitHub PR query for this branch returned none. No PR is open or merged by this review.

## Nine-site executive decision

The detailed audited table remains at [`docs/executive-summary.html`](../docs/executive-summary.html) and the reviewed historical evidence at [`docs/EXECUTIVE_SUMMARY_NINE_SITES_20261028.md`](../docs/EXECUTIVE_SUMMARY_NINE_SITES_20261028.md). The safe selection status for every requested site is **none / DO NOT SUBMIT**. The historical site-owner figures supplied by the requester are claims, not confirmed receipts. A new leaderboard-score estimate is **unavailable**, not zero and not a projection.

| Site | Best reported historical file | Reported score | Current decision |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Research-only; duplicate-family concerns; do not submit |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Research-only; shared family; do not submit |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Research-only; do not submit |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Research-only; related to GEMSDOE31; do not submit |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Research-only; same decoded family as GEMSDOE25 in audit; do not submit |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Research-only; related/identical decoded dots to GEMSDOE28 in audit; do not submit |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Highest supplied claim; research-only; not proven causal or unique; do not submit |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Research-only; do not submit |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Research-only; related B2 family in audit; do not submit |

Score values in this table are copied from the user-supplied list and are **USER-REPORTED**, not HOLDOUT-DTI and not ORGANIZER-CONFIRMED. The repository's separate fixed-raster holdout is not comparable to the reported competition scores: it holds out mapped faults while official scoring masks known mapped faults. Do not use that result as a predictor of leaderboard performance.

### B2 interpretation

The byte lineage offers a plausible mechanism: removing catalogue-adjacent locations from a dense related map could reduce false-positive mass while retaining some 300 m kernel coverage. This is a hypothesis, not a demonstrated cause of 0.2778. The hidden evaluation truth and exact organizer receipt are absent, so neither the gain attributable to pruning nor an expected score for a new raster can be calculated defensibly. Pruning a raster family also does not make the method scientifically unique under the requested registry-overlap rule.

## Pre-implementation hypotheses (reviewed, not authorized)

These are the existing ranked N1–N4 proposals in [`research/hypotheses.md`](hypotheses.md), not newly validated ideas. The missing assigned lane blocks implementation; do not select a method unilaterally.

| Qualitative rank / cost | Layers and target signature | Why possibly uncatalogued | Main non-fault mimic | Difference / status |
|---|---|---|---|---|
| 1. N1 / medium | RTP magnetics + isostatic gravity + conductive-base depth proxy; signed cross-normal edge profiles that distinguish persistent steps from balanced paired lobes | Tests concealed density steps without catalogue seeding | Unfaulted intrusive/lithologic contact | Signed profile return-to-background/body veto differs from the repo's unsigned gradients; proposal only |
| 2. N2 / medium | Total-count radiometric, RTP, conductive-base depth, conductivity, detrended elevation; scale-persistent magnetic edge with radiometric edge loss under cover | Tests a possible surface-mapping omission regime | Moisture, sediment, aircraft clearance, weak signal, non-fault contact | Cross-modal cover-conditioned transfer, not positive radiometric-edge fusion; proposal only |
| 3. N3 / high | Gravity, RTP and detrended elevation; catalogue-free orientation transport and cross-field-supported ridge junctions | Searches geometry not seeded by known fault endpoints | Dikes, intrusive contacts, drainage crossings, acquisition seams | Edge-graph transport/junction test beyond local Hessian alignment; proposal only |
| 4. N4 / low-medium | Magnetic/RTP and total-count grids; stability under survey-axis directional notch control | Helps distinguish acquisition striping from geologic lineaments | Real faults parallel to survey direction; anisotropic geology | Artifact-sensitivity control, not independent geology; proposal only |

No new external dataset is required by those proposals as written, but the layers are currently owner-mirror claims rather than authenticated competition inputs. No claim is made that these ideas are novel across all competitors. Required shared cache/evaluator and authenticated input files are missing. Thus **none is viable for a scored test in this checkout**.

## Irregularities and risks

1. Older README text contained an archived WBG4 download link and “read this first” wording that conflicted with the current negative decision. This review removed the live-download framing and explicitly labels that file historical research-only. Other archived pages remain subject to the release audit's download-link scan; do not infer authorization from an old page or TIFF link.
2. The user asks for literal verbatim prompt storage. README already contains a consolidated operating brief and references the charter; it does not reproduce the exceptionally long, repeated original request verbatim. Repeating every duplicated paragraph would worsen maintainability. Preserve the operative protocol and link the source request if provided as a durable source file; do not silently treat the paraphrase as verbatim.
3. The single-lane paragraph is not assigned in governing project records. The strict overlap rule is also in conflict with the dense lattice/prior evidence. Both need explicit policy resolution, not code workarounds.
4. The site's reported scores and current leaderboard claims have no per-submission receipts in this checkout. The official pages below are canonical manual-review references but were not freshly fetched in this pass.
5. The shared template format/mask defect is still documented as unresolved upstream. A validator against an owner mirror is not organizer acceptance.
6. `scripts/download_competition_data.sh` requires DrivenData authentication. No credentials are present or requested; logged-in data download cannot be completed autonomously from this environment. Do not use public mirrors as authenticated organizer data.

## Next work in strict order

1. Resolve the literal duplicate rule's treatment of dense continuous priors and provide one explicit method-lane assignment.
2. Restore and authenticate official competition training labels, sample grid and feature inputs; restore the unchanged pinned shared template and fix its defect upstream. Re-run readiness and verify hashes.
3. Refresh the complete registry, verify original pre-placement surfaces and final dots, and stop if either threshold is exceeded.
4. Only then preregister one allowed method, run each feature-alone leakage canary, and execute a buffered whole-segment hide-and-recover test with the pinned shared evaluator/writer; report evaluator version, withheld positives, pooled DTI and spatial 95% CI. Limit to three experiments or two hours.
5. Require improvement against a comparable holdout incumbent plus all format, provenance, uniqueness and freshness gates. A separate authorized selector must check weekly cap and decide any slot; the research runner must not promote.

## Official links for review

- [DrivenData problem, metric, features and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData data tab (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [DOE/NLR competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [EPSG:32611](https://epsg.io/32611)

These links are supplied for checking and were not freshly retrieved in this review. The local report deliberately does not claim they were independently verified today.

## Run card — negative review

```json
{
  "hypothesis": "No new hypothesis tested; N1 is the leading qualitative proposal only; no method lane is assigned.",
  "mechanism": "No candidate mechanism tested. N1 proposes distinguishing persistent signed geophysical steps from finite-width paired-lobe responses.",
  "named_non_fault_process_that_could_mimic_it": "An unfaulted intrusive or lithologic contact can create a persistent gravity/magnetic edge.",
  "holdout_dti": null,
  "holdout_ci_95": null,
  "holdout_label": "NOT RUN; no evaluator version or withheld-positive count applies.",
  "correlation_overlap_vs_registry": "No new surface or dots. Existing audits show a binary-lattice lower-bound overlap of 82.34% at 37,654 dots; continuous-prior semantics unresolved; registry not complete.",
  "raster_sha256": null,
  "validator_output": "No new raster; nothing to validate. Existing research assets are not approved for submission.",
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative"
}
```
