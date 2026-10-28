# Repository review — 27 October 2026

**Decision: NEGATIVE. No new candidate was constructed or scored. DO NOT SUBMIT any current research TIFF.** This report supersedes the checkout counts in the earlier [release reconciliation](release-reconciliation-review.md); the earlier report remains as historical context.

## Executive decision and evidence labels

| Question | Result | Evidence class |
|---|---|---|
| What does the strongest named historical GEMSDOE claim show? | GEMSDOE32 B2 is reported at **0.2778**; no authenticated organizer receipt ties that value to the exact bytes. | **USER-REPORTED**, not organizer-confirmed |
| Why might B2 differ from its catalogue-neighbour lineage? | B2 removes 6,436 dots within two pixels of the owner-mirrored mapped-fault catalogue from a 44,090-dot mask, leaving 37,654. Fewer redundant predictions could lower false-positive cost while keeping nearby kernel coverage, but lost true coverage is also possible. | **MEASURED local-byte lineage; causal explanation unverified** |
| Was the reported improvement proved? | No. The 0.2778 versus 0.2600 difference is between user-reported claims. Hidden-label contributions and a per-file organizer receipt are unavailable. | **USER-REPORTED comparison; no causal attribution** |
| Is there a defensible estimate for a new file? | No estimate; no new file exists. | **No estimate / no candidate** |
| Which downloadable file is safe to submit? | None. Existing links are explicitly research references; every saved identity fails the literal duplicate gate. | **Local byte and registry audit; incomplete registry** |
| Was the requested top hypothesis validated on the prescribed holdout? | No. No method lane was assigned, the complete current input/cache stack is absent, and no candidate passed pre-placement novelty. | **HOLDOUT-DTI: NOT RUN** |

The repository's prior official-public snapshot displayed **0.4544** for xiaofanhu at `2026-10-27T19:09:35.302551Z`. That is an **ORGANIZER-PUBLISHED PUBLIC LEADERBOARD OBSERVATION**, not a receipt for B2 or any project file; this review did not obtain a newer snapshot. The prompt's 0.3195 and 0.4413 claims remain user-supplied. No score projection is made. See the [dated observation](../evidence/public_leaderboard_recheck_20261027.json) and the detailed [B2 analysis](../docs/research/why-b2-scored-2778.md).

## Nine-site executive table and download safety

The generated [nine-site executive comparison](../docs/release.html#nine-sites) remains the canonical table. It lists the historical file reference, reported value and evidence class, new-score estimate status, measured local near-neighbour overlap, and submit decision for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. New-score estimates are unavailable for all nine; each is marked **DO NOT RESUBMIT**. The links are research references, not submission downloads.

Current local release-audit measurements: **10 TIFF paths, 8 distinct TIFF SHA-256 identities, 7 ZIP archives, and 13 pinned registry witnesses**. Each of the eight identities independently exceeds the strict 70% three-pixel overlap stop against the registered binary lattice. The registry is incomplete, so this is not a claim of exhaustive global uniqueness. The current byte counts and reasons are in [`evidence/release_audit.json`](../evidence/release_audit.json); historical artifacts are not renamed or presented as novel.

## Ranked geological hypotheses — proposals only

The ranked list is qualitative, not a performance ranking. It is not a new score estimate, measured delta, or claim of global method novelty. Full signatures, source links, limitations, and named mimics are in [research/hypotheses.md](hypotheses.md).

| Rank | Hypothesis | Geological test and distinction from reviewed methods | Named non-fault mimic | Cost / status |
|---:|---|---|---|---|
| 1 | **N1 — Signed edge-pair cancellation / finite-body veto** | Test whether multi-scale gravity/magnetic cross-normal profiles show a persistent one-sided step or instead balanced opposite-polarity lobes returning to background. This tests signed profile geometry and a finite-body veto, unlike the reviewed unsigned shifted-gradient/orientation products. | Unfaulted intrusive or lithologic contact; a real narrow fault-bounded block could also be wrongly vetoed. | Medium; unimplemented |
| 2 | **N2 — Radiometric-quiet magnetic-edge transfer under conductive cover** | Test whether magnetic ridges persist while co-located, provisionally interpreted band-6 total-count/radiometric edges disappear in low-relief/deeper-conductive-base strata, with fold-local conductivity-rank controls. This tests cover-conditioned cross-modal edge disappearance rather than treating total-count edges as another positive feature. | Moist soil, uniform sediment, variable aircraft clearance, weak radiometric signal, or a buried non-faulted contact. | Medium; unimplemented |
| 3 | **N3 — Catalogue-free orientation transport at structural junctions** | Build a label-free gravity/magnetic edge graph; transport axial normals along ridges, then test cross-field-supported junction continuity without catalogue endpoints. This is an along-edge graph test, unlike local Hessian/alignment features. | Intersecting dikes, unfaulted intrusive boundaries, drainage junctions, or acquisition seams. | High; exploratory and unimplemented |
| 4 | **N4 — Survey-axis notch-stability veto** | Perturb gridded magnetic/radiometric evidence around documented survey-axis directions with rotated-axis controls; test local stability, not geological truth. Independent flight-line confirmation would require line-level observations not present here. | Real faults aligned with survey axes may be attenuated; gridding, dikes, anisotropic lithology, and acquisition seams can also be directional. | Low–medium; unimplemented |

The data layer names and units are not authenticated against organizer binaries. N1–N3 would use named provided-stack layers, but the current feature stack and raw-band caches are absent. N4's official context is the [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and); line-level files were not restored or independently checked. No new external binary is represented as obtained. The dated source-by-source review is [here](source-verification-release-20261027.md).

## Current inputs and why validation stopped

The refreshed run card measures current local presence at generation time:

- **0/4** pinned `data/official/` owner-mirror inputs verified; the full feature TIFF (418,912,844 bytes in the prior restore receipt) is absent.
- **0/19** receipt-pinned raw-band caches present and hash-verified; shared `evaluate_holdout.py` and `submission_writer.py` are not verified at either pinned cache root; the derived feature bank is absent.
- **2/2** small audit mirrors verified. Those bytes are owner-mirror evidence, not authenticated organizer data.

The input snapshot is in [`evidence/run_card.json`](../evidence/run_card.json). Prior restore receipts are historical and do not establish present availability. The [official data endpoint](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) requires login; no credentials were requested or stored.

A candidate cannot pass the user's literal pre-placement gate against the pinned binary lattice at the standard 37,654-dot budget: the minimum-overlap counting bound is **82.3418%**, above the strict **70%** stop. Every already-saved TIFF also fails the measured lattice comparison. The separately registered continuous prior is an additional witness under the finite-positive-support interpretation; its status as “dots” remains ambiguous, so no exception was invented. The registry is not exhaustive. No new candidate surface or final dots were made, so there is no candidate-specific rank correlation, overlap, or surface-before-placement result.

No HOLDOUT-DTI, leakage canary, matched incumbent comparison, or spatial confidence interval was run for N1–N4. This is intentional fail-closed behavior, not a negative scientific result. If a lane is later assigned, the existing protocol still requires whole fault segments plus a buffer, features derived only from visible faults, exact visible-fault pixel masking, a feature-alone AUC leakage canary (AUC > 0.90 is leakage until resolved), the unchanged shared evaluator/writer, pooled DTI with alpha 0.2, beta 0.8 and a 300 m triangular kernel, and the prespecified limit of **at most three experiments or two hours**. A projection cannot substitute for HOLDOUT-DTI.

## Three review passes completed

1. **Evidence and scope pass:** Re-read the current README, charter, findings, prompt-preservation section, nine-site table, B2 lineage, public-leaderboard record, and dated official-source review. Kept USER-REPORTED scores separate from organizer-published public observations and HOLDOUT-DTI; confirmed no new score estimate or submission download is justified.
2. **Science, code, and data pass:** Inspected the hypothesis configuration/builders, run-card generation, pinned source/cache locations, release and registry audits, candidate/format gates, and tests. Updated the run card to derive release counts from the audit and derive file availability from the actual pinned paths/hashes; added regressions for counts, local availability, template files, and audit mirrors. Corrected historical restore language and retained the binary-lattice witness as the unambiguous stop.
3. **Generated-output and safety pass:** Regenerated the run card and public research/release pages; checked that release counts agree across audit, card, README, and charter; checked current local-input status in rendered pages; retained historical counts only in explicitly dated reports; and confirmed every current download is marked research-only. The full test result is recorded after the final rerun below.

These choices apply **Maximize P(Win)** by rejecting an unauthenticated, ineligible copy and **Own the Outcome** by publishing the missing-input state and negative decision instead of manufacturing a forecast. No experiment or competition slot was consumed, and no candidate GeoTIFF or submission name/note was created.

## Official references

- [DrivenData competition target, feature inventory and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [USGS GeoDAWN survey release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS Argenta Rise multi-physics study](https://pubs.usgs.gov/publication/70271418)
- [USGS Great Basin blind-geothermal synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and)
- [DOE Geothermal Data Repository release 1391](https://gdr.openei.org/submissions/1391)

No authenticated competition download was available. Source-page support and access limits are documented in the [dated official-source review](source-verification-release-20261027.md).

## Validation record

**Full test suite: 297 passed, 12 skipped, 32 warnings.** The warnings are Rasterio `PendingDeprecationWarning`s about affine multiplication; no test failed. The first rerun exposed a test-fixture omission (`registry/template_pins.json`) and a not-yet-created report link; both were fixed before the passing rerun. All seven builders completed successfully. No experiment, candidate TIFF, portal validation, or weekly slot occurred. A pull request/merge is not claimed here until GitHub records it.
