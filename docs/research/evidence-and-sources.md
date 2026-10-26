# Evidence and limitations

## Competition facts from official sources

| Statement | Source |
|---|---|
| Predict faults indicative of geothermal resources, not geothermal production or vent locations directly. The public and private test sets are expert-identified faults omitted from the existing catalogue. | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| The target raster is single-band `float32`, EPSG:32611, 100 m resolution, with the training bounds and predictions in [0, 1]. The public description says outside bounds null/NaN. | [Submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) |
| DTI uses a 300 m triangular distance kernel, alpha 0.2 and beta 0.8. | [Performance metric and equations](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) |
| Existing USGS/INGENIOUS fault pixels are excluded from evaluation in both rounds; staff did not say that a two-pixel buffer is excluded. | [DrivenData staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) |
| The official reference notebook supports CPU and GPU; GPU is faster but not a formal requirement for every experiment. | [Organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) |
| External data need a license allowing use and sharing for verification. | [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| The challenge overview lists the deadline as December 3, 2026 at 23:59 UTC. Always verify for updates. | [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) |
| The [GDR INGENIOUS regional dataset](https://gdr.openei.org/submissions/1391) is CC BY 4.0 and lists the included sources and attribution. The USGS [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) is CC0. Verify the license of each supplementary source independently. | The official data-release pages linked at left |

## What we actually measured

The nine cited historical TIFFs, the owner-mirrored sample and label grids, and two registered witness files were downloaded from pinned GitHub commits and checked against their recorded SHA-256 digests. [Portfolio measurements](../data/portfolio.json) include decoded-content identity and directed Euclidean three-pixel overlap; they are not an exhaustive audit of all current or private submissions. Each of the nine historical site bests exceeds the requested overlap limit against at least one other priority-site historical raster. GEMSDOE25 and GEMSDOE30 have identical decoded in-footprint predictions, despite different bytes. The old project files are reference material only.

The B2 raster is exactly the user-reported GEMSDOE25 D2.8 raster minus its pixels at Euclidean catalogue distance **≤2 pixels**: 44,090 D2.8 dots, 6,436 removed, 37,654 retained. This is a statement about reopened owner-mirrored bytes, **not** proof that those bytes were actually submitted or that they caused the claimed result.

## Why might B2 have worked?

The official metric rewards credit near a withheld truth pixel but charges false-positive mass. Sparsifying a dense line can reduce redundant false-positive mass while preserving kernel coverage. The B2 catalogue-flank pruning could further remove low-value predicted pixels. The owner-supplied historical sequence is consistent with this interpretation; it does not reveal private truth, causal effects, or independent per-submission receipts. The exact score 0.2778 is **USER-REPORTED / NOT ORGANIZER-CONFIRMED**. The [official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is separate, time-varying, and not a receipt for B2.

For fixed truth count `N`, let `T=TP_w`, `F=FP_w`, and `S=T/[(1-beta)T+alpha F+beta N]`. For a finite change with positive denominators, improvement requires

`[1-(1-beta)S] * delta_T > alpha * S * delta_F`.

This is not a universal one-dot credit threshold. `T` is a sum over truth pixels; the self-credit of a dot is a different quantity. Coverage saturation and actual changes in both terms matter.

## Format and data provenance irregularities

* The user-reported portal error does not establish whether NaN, an out-of-range sentinel, a mask, or another cause was responsible. The local strict validator refuses non-finite or out-of-range values across the entire output as a conservative policy. The official text's outside-null wording and all-finite zero-outside files are **not proven equivalent**, and no portal acceptance is claimed.
* The owner-mirrored “sample” contains 60,988 positive cells, while the official page describes an absence-predicting sample. Its grid/footprint is useful for local checks, but its authenticity is not independently established.
* The public [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirects to login. This sandbox cannot directly reach the user-supplied Dropbox, GDR or USGS binary hosts. A hash-pinned public **owner mirror** was restored automatically; hashes confirm its internal integrity, not organizer provenance. Authenticated official files, private test labels, organizer receipts and the current weekly quota remain inaccessible.
* The repository was empty except for an initial README. Claims of a pre-existing full training pipeline or a GPU requirement were not valid descriptions of this checkout. A GPU is absent here; the reference solution also supports CPU.
* The requested method paragraph is not identifiable, and the literal registry rule conflicts with some sibling sites' density exemptions. The unmodified shared literal implementation treats every finite positive cell, including continuous probabilities, as support. One registered continuous probability raster has positive support over the entire footprint; under that implementation, every nonempty candidate fails overlap. Whether a continuous prior should count as “dots” is a policy ambiguity, not permission to silently exempt it. Even using only the binary lattice witness, a 37,654-dot field necessarily exceeds the threshold. The pigeonhole proof does **not** apply to every smaller field.
* In the upstream shared `metric.py` prose, `delta_T <= k` is stated, but `delta_T` may sum coverage gains over multiple truth pixels and exceed a dot's nearest-truth self-credit `k`. This is a **documentation issue**; the shared scorer and exact finite-change calculation are not changed or privately forked here. Do not use that inequality to justify candidate allocation. The owner must correct the shared upstream template; this session can only work in its assigned repository/branch.
