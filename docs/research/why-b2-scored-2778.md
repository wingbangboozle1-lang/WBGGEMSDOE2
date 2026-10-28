# Why GEMSDOE32 B2 may have reached 0.2778

**The 0.2778 value is a USER-REPORTED historical claim, not tied to these bytes by an authenticated organizer receipt. Its cause is unknown.** The public leaderboard is not a per-file receipt. No defensible score estimate is available for a new method; this explanation is not proof that it will score higher.

## What is reproducible

Using the hash-pinned historical files and an **owner-mirrored**, not authenticated organizer, catalogue:

- GEMSDOE25 and GEMSDOE30 have identical in-footprint prediction arrays despite different TIFF bytes.
- GEMSDOE32 B2 is that 44,090-dot array after removing **6,436** dots within two pixels of the mirrored catalogue, leaving **37,654**. GEMSDOE36 adds **1,200** dots to B2 and removes none. See [the portfolio audit](data/portfolio.json).
- The pinned binary lattice covers 5,160,724 of 5,167,373 footprint cells within three pixels. At 37,654 distinct dots, at least **82.34%** must be within that lattice halo; the required threshold is 70%, so this budget cannot pass that witness. The same arithmetic does not prove all smaller budgets fail. The separate continuous-prior witness would block every nonempty map if its finite-positive support is treated as dots; that interpretation is unresolved and no exemption is assumed.

## What could explain the reported difference

The [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) uses a 300 m triangular kernel with α=0.2 and β=0.8. Removing redundant predictions **might** reduce false-positive mass while retaining coverage near hidden fault truth; it could also remove useful true-positive coverage. [Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) say known fault pixels are masked; 1–2 pixels away are **not** known to be masked, so nearby withheld truth may matter. Without hidden labels, per-dot contributions and receipts, there is no verified causal decomposition or reliable score estimate. Repeated leaderboard probing can overfit a public set.

For a fixed truth set, write weighted true positives as `T`, weighted false positives as `F`, its positive count as `N`, and `FN = N−T`. Then `DTI = T / [(1−β)T + αF + βN + ε]`. For an old score `s` and finite changes ΔT and ΔF, the new value improves exactly when `[1−(1−β)s] ΔT > αs ΔF`, assuming the denominator stays positive. Both lost truth coverage and removed false positives matter; these terms were not measured for B2. This identity is not a score estimate.

An older claim that the removal of 6,436 binary dots yielded `0.2 × ΔFP ≈ 12,074` is withdrawn as mathematically impossible. Even under the upper bound of one unit of false-positive mass per removed dot, the weighted reduction could not exceed 1,287.2. The actual contribution is unmeasured.


## Comparison with the other eight named historical files

These are measured dot counts paired with user-supplied historical claims, **not per-file organizer receipts or current best-file rankings**. GEMSDOE25 and GEMSDOE30 decode to identical binary predictions on the mirrored footprint even though their GeoTIFF packaging differs. B2 is not a genuinely new method relative to that lineage.

| Historical reference | Positive dots | USER-REPORTED claim |
|---|---:|---:|
| [GEMSDOE32](sites/GEMSDOE32.html) | 37,654 | 0.2778 |
| [GEMSDOE36](sites/GEMSDOE36.html) | 38,854 | 0.2750 |
| [GEMSDOE28](sites/GEMSDOE28.html) | 37,660 | 0.2710 |
| [GEMSDOE31](sites/GEMSDOE31.html) | 40,199 | 0.2708 |
| [GEMSDOE33](sites/GEMSDOE33.html) | 41,865 | 0.2632 |
| [GEMSDOE25](sites/GEMSDOE25.html) | 44,090 | 0.2600 |
| [GEMSDOE30](sites/GEMSDOE30.html) | 44,090 | 0.2600 |
| [GEMSDOE24](sites/GEMSDOE24.html) | 60,069 | 0.2477 |
| [GEMSDOE27](sites/GEMSDOE27.html) | 61,328 | 0.2449 |

B2's reported 0.2778 versus 0.2600 for the identical D2.8 masks is an arithmetic difference of 0.0178 between unverified claims. GEMSDOE36 adds 1,200 dots to B2 but has a lower user-reported 0.2750. This is consistent with, but does not prove, a false-positive-cost explanation; different receipts, hidden truth, thresholds and public-set overfitting remain possible. Exact historical download names and immutable source pins are available in the site briefs and [nine-site decision](release.html#nine-sites).

## The public leader is a separate observation

The official public leaderboard displayed **0.4544 for xiaofanhu on 27 October 2026**, captured in the [dated observation](data/public_leaderboard_recheck_20261027.json) and linked to the [official page](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). This is an ORGANIZER-PUBLISHED PUBLIC OBSERVATION, not an organizer receipt for B2 or a project prediction. The prompt's 0.3195 and 0.4413 values remain USER-SUPPLIED, not authenticated receipts. Subtracting 0.2778 from 0.4544 gives 0.1766; that arithmetic is **not** a validated target gap or a forecast of attainable improvement.

## Literal novelty cannot be replaced by score fitting

On the pinned owner-mirrored footprint, the 13GEMSDOE stride-5 binary lattice covers **5,160,724 of 5,167,373 pixels within inclusive Euclidean 3 px: 99.8713273%**, not 99.96%. Only 6,649 pixels are uncovered. A 37,654-distinct-dot map therefore has at least `(37,654 − 6,649) / 37,654 = 82.3418495%` overlap, already above the strict 70% stop. The count-only maximum budget that could possibly meet that limit is 22,163; this is an upper bound, not a constructive placement recipe or permission to exploit footprint edges.

A registered continuous prior is positive across the whole footprint. Under the stated finite-positive support rule every nonempty candidate overlaps it by 100%; whether those cells should be interpreted as dots is unresolved, so **no exemption is assumed**. A weaker density-normalized/discrete-peer result cannot override the requested rule. Source [registry measurements](../site/data/registry_audit.json) are pinned rejection witnesses, not an exhaustive current registry. All nine focus HEADs have newer unaudited refs.

The concurrently merged D19-DOTTED and E3-soft88 bytes were independently reopened in this review. Their binary-lattice overlaps are 99.147% and 99.923%, respectively; both pass conservative local format checks but remain **DO NOT SUBMIT**. Their source-reported scientific experiments were not replayed, and their original pre-placement surfaces were not independently available. [Latest eight-identity audit (10 TIFF paths, 7 ZIPs)](data/release_audit.json).

## Geological meaning needs more than plausible band names

The official layer description identifies depth to the **conductive base**, not an authenticated basement-depth surface. Page illustrations and a third-party 19-band schema do not prove that a mirrored binary band is the same product with known units, acquisition properties or coverage. A prior hash-pinned owner-mirror restore receipt exists, but the full stack and per-band caches are absent from this checkout; current availability is in the run card. The mirror is not authenticated against organizer data. B6's observed values differ from some prior prose; B15 also has negative samples. Those facts flag unresolved provenance/semantics, not proof of a geothermal structure.

Signed cross-profile geometry, radiometric controls, orientation transport and survey-axis vetoes have named non-fault mimics: unfaulted lithologic or intrusive contacts, alluvial edges, drainage, survey leveling and acquisition striping. They are qualitative research proposals, not new discoveries or numerical performance claims. A visible-fault association can reward an already mapped structure rather than an uncatalogued target. Any future model must use only fold-visible faults for catalogue features, mask their exact pixels in scoring, hide whole segments plus a buffer, and run a feature-alone leakage canary for every feature. AUC above 0.90 is a presumed-leakage alarm, not a tunable exception.

## The range rejection must be diagnosed on actual saved bytes

The filename suffix `zeros` is not a validation result. H3-PACK contains **7,111,787 NaNs outside** the mirrored footprint; STEPXASYM marks **5,132,809 interior cells as NoData**. The former can pass an inside/grid-only check while failing an extra whole-array-finite check; the latter fails the masked-footprint check. Neither fact establishes what caused the user's different, unavailable rejected upload.

The official format permits outside null/NaN according to its published text; the portal implementation and authenticated submission form were not inspected. The supplemental strict-finite check is a conservative diagnostic, **not a verified portal requirement or acceptance receipt**. Reopen the exact single-band float32 file and report below-zero, above-one, NaN, infinity and masked-cell counts separately inside/outside, plus EPSG:32611, 100 m resolution, shape and transform. Never silently clip or rename an old map as a new submission. The pinned shared gate's interior-mask gap has an upstream report/reproducer but no claimed upstream fix. [Issue #23](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/issues/23) tracks the blocker.

## Can a new method beat it?

**Unknown.** A prior three-experiment MSPTCD campaign produced an exploratory mapped-fault proxy result, not organizer performance: selected EXP3 **HOLDOUT-DTI 0.042554**, 95% CI [0.032059, 0.054765], shared evaluator `gems57-pooled-hide-v2`, 60,988 withheld positive pixels. It was selected on the same folds, uses mirrored labels equal to the mapped catalogue, has globally prepared label-free features and an invalidated separate detached-splay interpretation. These are archived v1 results, not results for the corrected v2 alignment feature. The 124 canaries below the alarm threshold do not prove the absence of leakage. Its saved TIFF fails the literal lattice stop. See [corrected findings](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/msptcd_findings.md).

The method lane remains unassigned (UNASSIGNED); no proposal is authorized to run. H1 is not nominated or authorized to rerun; N1–N4 remain unimplemented desk proposals. The [ranked proposal shortlist](research.html) includes signed multi-physics edge pairs with a body veto, radiometrically quiet magnetic transfer, catalogue-free orientation transport, and survey-axis notch stability. They are plausible mechanisms with named non-fault mimics, **not tested results**, and their relevant external binary coverage has not been verified. Earlier depth-shift and conductivity-flank proposals are not described as untried: MSPTCD implemented closely related features.

## Decision

**No file is approved for submission. DO NOT SUBMIT.** No new TIFF, filename or submission note was created in this review. The latest independent byte audit covers 10 existing TIFF paths / 8 distinct identities / 7 ZIPs; all eight TIFF identities fail the literal lattice duplicate stop, regardless of whether a format test against the mirror passes. See the [current byte-audit receipt](data/release_audit.json) and [canonical negative run card](data/run-card.json).

The user's earlier upload error, “Predicted values must be in range [0, 1],” cannot be diagnosed without the exact rejected file. Check actual values, non-finite values, masks, grid and metadata without clipping; a local pass is not portal acceptance. Future work additionally requires an assigned lane, a complete fresh registry, authenticated input data, and the prescribed matched buffered-holdout, pre-placement, final-dot and shared-writer gates. A separate quota-aware selector decides any real submission.
