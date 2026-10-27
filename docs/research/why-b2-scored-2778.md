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

## Can a new method beat it?

**Unknown.** A prior three-experiment MSPTCD campaign produced an exploratory mapped-fault proxy result, not organizer performance: selected EXP3 **HOLDOUT-DTI 0.042554**, 95% CI [0.032059, 0.054765], shared evaluator `gems57-pooled-hide-v2`, 60,988 withheld positive pixels. It was selected on the same folds, uses mirrored labels equal to the mapped catalogue, has globally prepared label-free features and an invalidated separate detached-splay interpretation. The 124 canaries below the alarm threshold do not prove the absence of leakage. Its saved TIFF fails the literal lattice stop. See [corrected findings](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/msptcd_findings.md).

The method lane remains **UNASSIGNED**; no proposal is authorized to run. The [ranked proposal shortlist](research.html) includes repeated cross-drainage patterns, multi-depth conductance, flight-line repeatability and multi-epoch deformation. They are plausible mechanisms with named non-fault mimics, **not tested results**, and their relevant external binary coverage has not been verified. Earlier depth-shift and conductivity-flank proposals are not described as untried: MSPTCD implemented closely related features.

## Decision

**No file is approved for submission. DO NOT SUBMIT.** No new TIFF, filename or submission note was created in this review. Five historical local TIFFs fail the lattice duplicate stop, regardless of whether a format test against the mirror passes. See the [release triage receipt](data/release_triage_20261027.json) and [negative run card](data/RUN_CARD_FINAL.json).

The user's earlier upload error, “Predicted values must be in range [0, 1],” cannot be diagnosed without the exact rejected file. Check actual values, non-finite values, masks, grid and metadata without clipping; a local pass is not portal acceptance. Future work additionally requires an assigned lane, a complete fresh registry, authenticated input data, and the prescribed matched buffered-holdout, pre-placement, final-dot and shared-writer gates. A separate quota-aware selector decides any real submission.
