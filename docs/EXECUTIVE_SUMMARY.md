# Current executive summary

This is a repository copy of the current decision; the [interactive dashboard](executive-summary.html) contains the nine briefs and submission checklist.

## Submission decision: DO NOT SUBMIT — no file is cleared

| Item | Current evidence |
|---|---|
| Download to submit | **None.** The existing TIFFs are research artifacts, not approved submissions. [Open the executive summary](executive-summary.html). |
| Estimated organizer score | **Unavailable.** A mapped-fault holdout is not the organizer's hidden new-fault score; no calibrated transfer has been established. |
| Unique against the registry? | **No prior candidate passed the requested literal rule.** The current registry inventory is incomplete, and the continuous-prior interpretation is unresolved. [Reopened-byte audit](../evidence/local_artifact_audit_20261027.json). |
| What changed | Previous DZ-16 and H3-PACK approval claims have been **revoked**: both exceed 70% proximity to a registered binary lattice. An enrichment-based exception was not authorized. |
| This lane's run | **Negative:** no explicitly assigned method, no new prediction, no new HOLDOUT-DTI, and no competition slot used. [Run card](../evidence/run_card.json). |

### Existing research artifacts — never submit them

All tests below use a hash-pinned **third-party mirror** of the grid, not an authenticated organizer sample. The within-3-pixel overlap is the fraction of the candidate's positive footprint pixels near the binary lattice. A continuous prior adds a separate ambiguity, because the shared tool treats all positive prior pixels as support; whether that is the intended meaning of “dots” has not been resolved.

| Archived file | Lattice overlap | Local format diagnostic | Decision |
|---|---:|---|---|
| DZ-16 `wbg2-dz16-n34500-…-zeros.tif` | 99.98% | Finite, in range and grid-matched to mirror | **DO NOT SUBMIT** |
| H3-PACK `wbg3-h3pack-34k-…-zeros.tif` | 99.86% | In-footprint valid; NaN outside; strict all-finite check fails | **DO NOT SUBMIT** |
| MSPTCD `wbg2-msptcd-e3-25594dots-…-zeros.tif` | 100.00% | Finite, in range and grid-matched to mirror | **DO NOT SUBMIT** |
| STEPXASYM `wbg2-h1-stepxasym-…-zeros.tif` | 99.38% | Finite raw values, but 5,132,809 interior cells masked as NoData | **DO NOT SUBMIT** |
| CONDUIT `wbg-h1-blind-conduit-breach-…-zeros.tif` | 99.87% | Finite, in range and grid-matched to mirror | **DO NOT SUBMIT** |

A format check cannot establish a geological discovery, novelty, portal acceptance, or a leaderboard win. The exact file previously rejected by the portal was not provided; its `[0,1]` error cannot be diagnosed from another file. The official page requires null/NaN outside bounds; the portal's treatment of zeros outside the footprint and of NaN must be confirmed using authenticated organizer data, not assumed.

## Historical focus-site executive summary

The file names and values below are **USER-REPORTED historical claims**, not organizer-confirmed submission receipts or score estimates. The downloaded, hash-checked historical arrays were assessed against other listed focus files; none is a new submission and all exceed the literal 70% overlap threshold with at least one peer. Site HEADs have moved since the pinned audits; newer rasters have not been reviewed. [Site-by-site evidence](executive-summary.html#priority-sites) · [freshness](data/focus-freshness.json).

| Site | Historical file (research only) | USER-REPORTED | Estimated organizer score | Unique under literal peer rule? |
|---|---|---:|---|---|
| [GEMSDOE24](sites/GEMSDOE24.html) | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 | Unavailable | No; 100.0% near GEMSDOE25 |
| [GEMSDOE25](sites/GEMSDOE25.html) | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 | Unavailable | No; 100.0% near GEMSDOE24 |
| [GEMSDOE27](sites/GEMSDOE27.html) | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 | Unavailable | No; 98.0% near GEMSDOE24 |
| [GEMSDOE28](sites/GEMSDOE28.html) | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 | Unavailable | No; 100.0% near GEMSDOE24 |
| [GEMSDOE30](sites/GEMSDOE30.html) | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 | Unavailable | No; 100.0% near GEMSDOE24 |
| [GEMSDOE31](sites/GEMSDOE31.html) | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 | Unavailable | No; 100.0% near GEMSDOE24 |
| [GEMSDOE32](sites/GEMSDOE32.html) | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 | Unavailable | No; 100.0% near GEMSDOE24 |
| [GEMSDOE33](sites/GEMSDOE33.html) | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 | Unavailable | No; 99.7% near GEMSDOE27 |
| [GEMSDOE36](sites/GEMSDOE36.html) | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 | Unavailable | No; 97.6% near GEMSDOE27 |

**Why GEMSDOE32 B2 might have done well:** in the reopened mirrors its mask equals the GEMSDOE25/30 D2.8 mask after removing all points at distance ≤2 pixels from the mirrored known-fault catalogue. The 300 m metric can reward coverage while penalizing redundant predicted mass, so pruning *may* help, but hidden truth and a receipt tying the reported 0.2778 to the exact bytes are unavailable. Causation and performance of a new file remain unknown. [Detailed proof and sources](research/why-b2-scored-2778.html).

**Important organizer clarification:** [DrivenData staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) explicitly say the known-fault mask is pixel-exact; a new-fault label can be within 300 m of a known trace. Thus a 2-pixel exclusion is **not** a mandated or cost-free buffer.

The official [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed **0.4544** at rank one when viewed on 2026-10-27 around 19:05 UTC. This is an **ORGANIZER-PUBLISHED public observation**, not an ORGANIZER-CONFIRMED receipt for a project file. It can change; the automated feed shows a clearly dated stale snapshot if refresh fails.

## Research and historical holdout

Four distinct [ranked desk proposals](../research/hypotheses.md) identify the layers, physical signal, competing non-fault explanations, scope of novelty and data costs. The highest-ranked upward-continuation proposal is **not an assigned lane** and has not been tested here. A pinned [nine-site README-only recheck](../research/focus-head-readme-review-20261027.md) found related earlier work, so novelty is not asserted fleet-wide. The earlier depth-offset and conductive-flank proposals are already implemented in `src/wbggems/msptcd.py` and are no longer advertised as new.

A prior lane **reported** HOLDOUT-DTI **0.042554** (95% spatial-block CI **[0.032059, 0.054765]**, `gems57-pooled-hide-v2`, **60,988 withheld positives**) versus its reported control **0.023409** (95% CI **[0.015356, 0.031895]**). These values are not organizer scores and have **not** been independently replayed in this review. The interval is conditional on the fixed folds/fits, and the winner was selected from multiple arms; its CI is not a selection-adjusted leaderboard forecast. Passing individual AUC canaries does not prove absence of leakage. The saved MSPTCD raster fails the literal duplicate stop. [Archived campaign](msptcd/) · [raw result](../evidence/wbg2_msptcd_results.json).


For next steps and the preserved original prompt, see the [repository README](../README.md).
