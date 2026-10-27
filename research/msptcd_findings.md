# Historical MSPTCD campaign: corrected findings

**Decision: NEGATIVE — DO NOT SUBMIT.** This is a retrospective analysis, not a new run. The prior MSPTCD campaign used its three experiments; its file failed the literal duplicate stop. [Read-back triage](../evidence/release_triage_20261027.json) independently measures 100% of its dots within three pixels of the pinned 13GEMSDOE lattice. Its pre-placement surface check was not performed in the required order. The artifact remains in the repository for reproducibility, not competition use.

## Mapped-fault proxy, not organizer performance

The former campaign used the pinned `gems57-pooled-hide-v2` pooled evaluator with α=0.2, β=0.8, and a 300 m triangular kernel, 60,988 withheld positives and four buffered spatial-component quadrants. Results below are **exploratory HOLDOUT-DTI on the owner-mirrored mapped-fault proxy**, not public/private leaderboard scores or independent model selection:

| Arm | HOLDOUT-DTI | 95% spatial-block CI |
|---|---:|---:|
| 19-band control | 0.023409 | [0.015356, 0.031895] |
| EXP3, selected on the same folds | 0.042554 | [0.032059, 0.054765] |
| EXP3 − control, paired | 0.019145 | [0.010977, 0.028755] |

These are recorded in [the historical run card](../evidence/RUN_CARD_MSPTCD.json); they do **not** prove that EXP3 beats an independently selected incumbent or the reported GEMSDOE32 B2. The labels used are identical to the mirrored mapped-fault catalogue, so the target is hide-and-recover mapped faults, not hidden organizer truth. The selected arm was chosen on the same folds used to report its result. Label-free derived features were prepared globally. The separate detached-splay diagnostic used a different split from the fitted quadrant models; it cannot establish that its diagnostic labels were excluded from training. Do not interpret that diagnostic as a clean held-out score.

Of 124 feature/fold canaries, the maximum recorded two-sided AUC was 0.6131, below the 0.90 flag threshold. **Passing canaries is not proof of no leakage**: it does not test every interaction, pipeline step, split, or acquisition artifact. Whole buffered components were used for the main proxy experiment, but this and the unmodified shared evaluator alone do not establish independent generalization. The original code performed dot placement before its registry check and wrote a research artifact despite duplicate witnesses; its historical executable is now retired.

## What is actually known about B2

Byte-level lineage shows GEMSDOE25 and 30 have identical predictions within the mirrored footprint; GEMSDOE32 B2 removes 6,436 of 44,090 dots at most two catalogue pixels away, leaving 37,654. GEMSDOE36 adds 1,200. The reported B2 value of **0.2778 is user-reported**, not tied to these bytes by a receipt. Reduced redundancy might improve the metric, but it could also remove useful proximity to unmapped truth. [Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) confirmed exclusion of known fault pixels, not a surrounding buffer. No truth or per-dot decomposition is available to establish a cause.

A prior claim that 6,436 removed binary dots produced `0.2 × ΔFP ≈ 12,074` was impossible and is withdrawn. If the false-positive term changes by no more than the 6,436 removed unit-valued predictions, the weighted change is at most 1,287.2; the actual change is not measured here. No substitute causal calculation is claimed.

## Band 6 identity remains unresolved

The pinned owner mirror describes band 6 as tilt angle or total curvature. [Local read-back](../evidence/input_metadata_20261027.json) reports **3,073 masked NoData sentinel cells** inside the sample footprint, and 5,164,300 valid cells with no negative valid values; valid q01/median/q99 are approximately 7.7223/18.4817/29.1005. The official page's radiometric illustration and these numbers do not independently authenticate the band, establish its units, or prove it cannot be a derivative. In particular, a tilt-angle distribution need not have an assumed 50% negative values. The campaign's internal `tc_radiometric` name is a historical label, not verified physical identity. The mirrored stack and sample are not confirmed equal to the login-protected organizer files.

## No clearance

Local checks against a mirror are diagnostics, not organizer acceptance. All five examined historical files fail the lattice duplicate stop. New hypotheses and data-access caveats are in [the current shortlist](hypotheses.md); sources are in [the access register](msptcd_sources.md). No new GeoTIFF or competition submission was produced in this review.
