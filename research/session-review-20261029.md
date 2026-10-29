# Session review — 29 October 2026

## Decision

**NEGATIVE — DO NOT DOWNLOAD OR SUBMIT any TIFF in this checkout.** No new raster was generated, no holdout experiment or leakage canary was run, no weekly slot was used, and no submission score is estimated. This is not a scientific conclusion that every possible method fails; it is the consequence of protocol and data gates failing closed.

The user-supplied parallel-run protocol does not identify a single method paragraph/lane (the thresholds are placeholders and the assigned method text is absent). `AGENTS.md`, `config/research_hypotheses.json`, and current readiness all prohibit self-assigning a lane. The pinned competition input rasters, derived feature stack, and shared evaluator/writer are also missing in this checkout; the registry is explicitly incomplete and the continuous-prior overlap interpretation is unresolved. No valid way remains to produce the requested new TIF without violating the stated protocol.

## Passes and verification

### Pass 1 — review the repository and carry forward the prior session

Read `AGENTS.md`, the session-start README section, project charter, findings, canonical run card, release audit, nine-site comparison, focus-site audit, release register/readiness, and previous session review. The nine historical site claims and file lineage are present. The repo contains four ranked *desk hypotheses* in `config/research_hypotheses.json` (`N1`–`N4`); these are proposals, not results. The request's current-leaderboard numbers (0.3195, 0.4413) are not reconciled by a contemporaneous authenticated receipt; the latest checked-in official-public observation is dated 2026-10-28 and is not a receipt for any local file.

### Pass 2 — re-run current gates and inspect contradictions

- Ran `python scripts/check_readiness.py --check`: it printed **BLOCKED / DO NOT SUBMIT** and returned exit code 2 as designed. It refreshed the dated readiness outputs. Its blockers include unassigned lane, missing official input files and cached features, missing pinned shared code, incomplete registry, unresolved continuous-prior rule, unresolved shared format issue, no scientific validation, and no separate selector/quota receipt.
- The exact saved readiness snapshot is `evidence/checkout_readiness.json`; the report distinguishes owner-mirror pins from authenticated organizer inputs.
- Found stale, directly conflicting positive wording lower in `README.md` that called the historical distal2 and EDTI artifacts “OK TO DOWNLOAD” or “safe to submit,” despite the current negative run card and the literal overlap stop. This is a release-communication defect. Historical measurement text must not be read as present upload authorization. The README has been amended to label these as withdrawn archive records and to remove live download CTAs from those statements.
- Current checked-in nine-site audit has exact-byte SHA-256 pins and pairwise 3-pixel overlaps. It is a pinned historical snapshot, not proof of uniqueness against today's entire online registry or all newer HEADs.

### Pass 3 — test and re-check

Created the ignored virtual environment from `requirements.txt` and ran `.venv/bin/python -m pytest -q -rs`: **379 passed, 18 skipped, 0 failed**, 32 Rasterio affine-operation pending-deprecation warnings. Skips require absent sample/competition labels or absent pinned shared template. These passing tests validate local code and fixtures only; they do not clear scientific, registry, format, or organizer gates. `git diff --check` is run before delivery.

## Requested nine-site executive comparison

The score column below reproduces the requester-supplied historical claims, all **USER-REPORTED**, not organizer-confirmed receipts. The estimated new leaderboard score is **unavailable for every row**: there is no calibrated predictive estimate that is valid for the competition's unseen unmapped-fault target. The single best historical claim in this supplied set is GEMSDOE32's 0.2778, but that value is not evidence that a new file will score similarly.

| Site | Historical file (research reference only; not an upload recommendation) | Reported score / evidence | Estimate for a new submission | Unique vs other eight? | Decision |
|---|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 USER-REPORTED | Unavailable | No — up to 100.00% 3-px overlap (GEMSDOE25/27/30) | DO NOT SUBMIT |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 USER-REPORTED | Unavailable | No — up to 100.00% (GEMSDOE24/27/30) | DO NOT SUBMIT |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 USER-REPORTED | Unavailable | No — up to 98.02% (GEMSDOE24) | DO NOT SUBMIT |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 USER-REPORTED | Unavailable | No — up to 100.00% (GEMSDOE30) | DO NOT SUBMIT |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 USER-REPORTED | Unavailable | No — up to 100.00% (GEMSDOE24/25/27/28/31) | DO NOT SUBMIT |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 USER-REPORTED | Unavailable | No — up to 100.00% (GEMSDOE30) | DO NOT SUBMIT |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | **0.2778 USER-REPORTED** | Unavailable | No — up to 100.00% (GEMSDOE36) | DO NOT SUBMIT / historical leader only |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 USER-REPORTED | Unavailable | No — up to 99.71% (GEMSDOE27) | DO NOT SUBMIT |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 USER-REPORTED | Unavailable | No — up to 97.58% (GEMSDOE27) | DO NOT SUBMIT |

**Exact downloadable submission for this checkout: none.** The historical file names and pinned overlap figures are recorded for research and audit only. “Unique” in this table means not unique relative to the other eight under the inclusive 3-pixel dot-overlap comparison; it does not claim global registry coverage. The exact pairwise matrix and hashes are in `evidence/nine_site_recheck_20261028.json`; the source pins are in `registry/focus_sites.json`.

## Why GEMSDOE32's reported 0.2778 may exceed the other listed values

A plausible, byte-audited lineage in this repository is that GEMSDOE25 and GEMSDOE30 are the same 44,090-dot in-footprint array, while GEMSDOE32 B2 is the related array after removing dots near the mapped catalogue. Under the competition's asymmetric distance-weighted Tversky metric, pruning can improve a score if the reduction in weighted false positives exceeds the lost weighted true-positive coverage. That is a conditional mechanism, not a causal finding. The hidden evaluation truth, an organizer receipt binding 0.2778 to the exact pinned bytes, and a matched experiment are not available here; we therefore cannot say that pruning caused the reported score or predict a higher score.

A caution against using the local proxy as a leaderboard forecast: `evidence/fixed_raster_holdout_20261028.json` reports **HOLDOUT-DTI 0.006697, 95% CI [0.005990, 0.007368], 60,988 withheld positives, evaluator `gems57-pooled-hide-v2`** for the fixed GEMSDOE32 raster. This holdout scores withheld catalogue faults and reuses a fixed raster rather than regenerating from fold-visible features. The competition's target is new expert-mapped faults, so this is not a valid estimate of the 0.2778 leaderboard claim and is not a ranking of submission quality. For that reason no numeric projection is shown.

## Ranked candidate hypotheses — desk proposals only

These are the four pre-existing, unimplemented hypotheses already recorded in `config/research_hypotheses.json`, not newly asserted discoveries. “Expected improvement” is only a qualitative prioritization; no numerical DTI uplift is supported. No new data are proposed because the immediate blocker is unavailable/pinned project inputs and lane authorization, not lack of another public dataset.

| Rank | Hypothesis / exact layers | Physical signature and uncatalogued-fault rationale | Main non-fault mimic | Difference from methods already in repo | Expected DTI potential / cost |
|---:|---|---|---|---|---|
| 1 (N1) | Signed edge-pair cancellation: RTP (band 2), isostatic gravity anomaly (band 13), depth-to-basement surface (band 15) | Across gravity-edge normals, test signed profiles at 200/400/800 m scales for persistent one-sided steps versus paired opposite-polarity lobes returning to baseline; use along-strike continuity. A buried density step might persist beneath cover with no mapped surface trace. | Intrusive/lithologic contact; real horst or narrow fault block could be falsely vetoed. | Existing MSPTCD uses unsigned shifted gradient amplitudes/orientation, not profile polarity/return-to-background. | Highest qualitative priority; medium cost. |
| 2 (N2) | Radiometric-quiet magnetic-edge transfer: total count (band 6), RTP (2), basement depth (15), conductivity surface (17), detrended slope (19) | Find magnetic edges persisting across scales while co-located total-count edge disappears in low-relief/deeper-conductive strata; compare with matched controls. Concealed structures may lack surface expression. | Moisture, sediment composition, aircraft clearance, weak signal, buried nonfault contact. | Tests cross-modal *edge disappearance* as a cover regime, rather than treating radiometric edges as positive evidence; not another depth-shift or conductivity-flank weighting. | Moderate qualitative priority; medium cost. |
| 3 (N3) | Catalogue-free edge-orientation transport: isostatic gravity (13), RTP (2), detrended elevation (12) | Build label-free edge graphs and evaluate axial-normal continuity/curvature at independent cross-field junctions, without catalogue endpoints; may expose blind structures. | Intersecting dikes, intrusive margins, drainage junctions, survey seams. | Repository has local Hessian ridges/alignment/greedy coverage but no along-ridge orientation transport graph; not proof of globally novel method. | Exploratory; high cost. |
| 4 (N4) | Survey-axis notch-stability veto: magnetic anomaly (band 1), RTP (band 2), total count (band 6), plus official USGS flight-line geometry metadata | In matched tapered windows, attenuate spectral energy around documented survey-axis directions; compare with rotated-axis controls and retain only cross-field edges that stay stable. This is an artefact-sensitivity test, not positive fault evidence. Could reduce acquisition-line false positives and free prediction mass for geological signals. | Real faults parallel to the survey axes may also be attenuated; gridding, dike swarms and anisotropic lithology can mimic directional persistence. | No local MSPTCD survey-axis notch perturbation test exists. It differs from a cross-flight-line independent confirmation test; that would require additional external observations. The cited metadata layer has not been obtained/proven obtainable in this checkout, so N4 is not viable until its official availability/provenance is checked. | Lowest direct discovery potential; low-to-medium cost. |

**No candidate is currently viable to implement.** The parallel-run protocol's named lane is missing, so these do not authorize a self-assigned run. Before any future experiment: restore and hash-check inputs and the unchanged shared evaluator/writer, resolve the complete registry and dense-prior rule, obtain lane assignment, then run feature-alone leakage canaries before a buffered whole-segment hide-and-recover experiment. The three-experiment/two-hour cap applies. Slot selection is separate and was not performed.

## Requested download, portal error, and limits

- No new unique TIFF was produced. This is intentional: generating a new file would violate the protocol stop condition and give false confidence.
- The submitted file that produced “Predicted values must be in range [0, 1]” was not supplied, so its cause cannot be diagnosed from this checkout. A future writer must validate the exact saved bytes, all values the portal may read, band count, CRS, shape, transform, and footprint handling; local format validation is not organizer acceptance.
- The official competition-data page requires login. This environment has no authenticated DrivenData data access. The restored historical/mirror references are not authenticated organizer inputs; the current ignored `.cache` input, features and shared-template paths are missing.
- No account-specific remaining weekly quota, selector receipt, or submission-page receipt is available. No leaderboard estimate is supportable.

## Sources for manual review

- [DrivenData problem statement, metric and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Competition data page (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — changing public observation, not a per-file receipt
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN survey data record](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GEMS project record, GDR #1391](https://gdr.openei.org/submissions/1391)
- [GEMS prize reference document](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official EPSG:32611 registry](https://epsg.io/32611)

## Run card

See `evidence/session_run_card_20261029.json`. The verdict is `negative`; no candidate or raster hash exists, validator was not run on a new TIFF, and no score is projected.