# Historical MSPTCD findings with independent-review corrections

**Verdict: NEGATIVE / DO NOT SUBMIT.** No new candidate experiment, placement, scientific holdout or competition slot was used in the current review. Original prose is archived in [`evidence/reconciliation_archive/msptcd_findings.md`](../evidence/reconciliation_archive/msptcd_findings.md).

## Independently measured in this review

- All five local TIFF identities fail a literal registry overlap witness. The saved MSPTCD TIFF has SHA-256 `fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614`, 25,594 dots and 100% overlap within inclusive Euclidean 3 px of the pinned lattice. Its local format pass is not organizer acceptance. [Exact forensic audit](../evidence/release_audit.json).
- GEMSDOE25/30 decode identically. B2 is their 44,090-dot mask after removing exactly 6,436 dots within 2 px of the mirrored catalogue. GEMSDOE36 adds 1,200 dots to B2 and removes none. This establishes lineage, not a cause for any **USER-REPORTED** value. [Registry recheck](../evidence/registry_recheck_20261027.json).
- The full raw stack was restored: 418,912,844 bytes, SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, 19 raw caches. It is still an owner mirror, not organizer-authenticated. [Restoration receipt](../evidence/data_preparation.json).
- B6 has 5,164,300 finite / 3,073 missing cells inside the mirrored footprint, q01 7.7223, median 18.4817 and q99 29.1005. Earlier quantiles/counts differ. The range excludes an unscaled tilt in radians; positivity alone does not prove radiometric identity or units. [Raw diagnostic](../evidence/feature_semantics_review.json).

## Historical SOURCE-REPORTED HOLDOUT-DTI — not reproduced here

These are preserved campaign receipts, not current v2 results and not leaderboard estimates. Evaluator: `gems57-pooled-hide-v2`; four label-blind quadrant folds with whole intersecting components hidden and an 80 px / 8 km buffer; 60,988 pooled withheld positives. Intervals are conditional paired spatial-cluster bootstrap intervals (1,000 draws, 20 km clusters).

| Historical arm | SOURCE-REPORTED HOLDOUT-DTI | 95% CI |
|---|---:|---|
| CTRL-19B | 0.023409 | [0.015356, 0.031895] |
| EXP-1 core | 0.034975 | [0.025587, 0.045475] |
| EXP-2 strain/PU | 0.028575 | [0.020416, 0.038058] |
| EXP-3 greedy ensemble | 0.042554 | [0.032059, 0.054765] |

The historical paired EXP-3 minus control delta was 0.019145, 95% CI [0.010977, 0.028755]. Do not extrapolate its relative gain to the leaderboard or compare it numerically to an experiment on different folds. The exact full-precision source measurements are in [`wbg2_msptcd_results.json`](../evidence/wbg2_msptcd_results.json).

## Why the current implementation needs a fresh incumbent

1. The v1 orientation formula `abs(cos(2*delta))` treated perpendicular edge normals as coherent. Corrected v2 uses squared axial cosine; only synthetic tests were run. Historical v1 results do **not** validate the correction.
2. Old caches reused files based on existence alone. The current cache binds feature version, implementation, all required raw-band bytes, footprint and output digests, installing its manifest last.
3. The former web renderer listed nonexistent/misindexed bands and overstated physical meanings. The corrected renderer reads the actual band receipt/source constants. [Accurate feature interpretation](msptcd_hypotheses.md).
4. All 124 source-reported canary checks passing is not proof that leakage is absent. The detached-mask diagnostic reuses OOF predictions without refitting and is not independent validation. Source input hashes and full prediction surfaces are insufficiently bound to reproduce the old scientific campaign here.
5. The old runner placed dots before registry checks and wrote a TIFF after a failed gate. It is now stopped at the beginning of `main()` until a reviewed, authorized launcher exists; no historical evidence is overwritten.

## What cannot be concluded

A whole-quadrant source-reported local metric and an owner-reported public value measure different tasks; their discrepancy does not quantify “hidden-fault novelty” or establish a score mapping. The official target is fault traces, not vent detections. Potential-field edges, conductivity or a structural junction do not prove a geothermal system.

No saved TIFF is cleared; no current best corrected-code holdout is established. An incomplete registry disproves uniqueness when it supplies a witness but cannot certify a pass. The [current negative run card](../evidence/run_card.json), [download decision](../docs/release.html), [revised proposal shortlist](hypotheses.md), and [source verification](source-verification-release-20261027.md) govern next steps.
