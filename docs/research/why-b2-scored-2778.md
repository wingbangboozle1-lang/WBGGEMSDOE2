# Why GEMSDOE32 B2 may have scored well — and whether we can beat it

**Evidence class: HISTORICAL-MIRROR-MEASUREMENT + USER-REPORTED CLAIM — NOT ORGANIZER-CONFIRMED**

This note answers the user's direct question: *Why and how did `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` get the highest score among the nine focus sites, and can we generate a submission that scores higher than 0.2778?*

All numeric claims below are labeled per the parallel-run protocol. No ORGANIZER-CONFIRMED receipt linking a specific raster SHA-256 to its score is present in any of the nine repositories at their audited commits. The 0.2778 figure is therefore treated as a **USER-REPORTED historical claim**, not a verified organizer score.

## 1. What the bytes prove (and what they do not)

We reopened the nine pinned historical TIFFs at their exact pinned file SHA-256 and compared them against the hash-pinned owner mirror of the competition grid (footprint = 5,167,373 cells, EPSG:32611, 100 m). All nine match the mirror's CRS/shape/transform.

Measured lineage:

- **GEMSDOE25** (`dotted-h19-5-d2-8`, 44,090 dots) and **GEMSDOE30** (`d28-poisson300m-offcat-44090`, 44,090 dots) have **byte-identical decoded in-footprint prediction masks** (`decoded_prediction_sha256 = c1390c...`), despite different file bytes, nodata tags (`nan` vs `zeros`), and compression. They are not independent submissions in prediction content.
- **GEMSDOE32 B2** (`h33-h33-2-b2`, 37,654 dots, `c55bafc4...`, 0.2778 claim) is **exactly** the GEMSDOE25/D2.8 mask with every dot at Euclidean distance ≤2 pixels from the mirrored existing-fault catalogue removed: 44,090 → 37,654 (6,436 removed, 0.2778 claim). This is reproducible with `python scripts/audit_registry.py --fetch` — see `evidence/registry_audit.json` lineage field.
- **GEMSDOE36** (`anderson-geothermal-pinn`, 38,854 dots, 0.2750 claim) is exactly B2 plus 1,200 added dots, 0 removed.

This lineage is a **measurement of archived bytes**, not proof that those bytes were actually uploaded to DrivenData, that they produced the claimed score, or that the pruning *caused* the score.

## 2. Why the claimed 0.2778 is scientifically plausible

The official metric is the distance-weighted Tversky index (DTI) with a 300 m triangular kernel, α=0.2, β=0.8 ([DrivenData metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric), [Tversky index](https://en.wikipedia.org/wiki/Tversky_index)):

For pooled true-positive mass T, false-positive mass F, and truth count N, with S = T / [(1−β)T + αF + βN + ε], improvement requires `[1-(1-β)S]·ΔT > α·S·ΔF` for finite changes with positive denominators. This is an exact rewriting of the pooled metric; it is **not** a per-dot threshold, because ΔT sums kernel-weighted contributions over many truth pixels and can exceed a single dot's self-credit.

Key implications:

1. **Coverage vs. mass trade-off.** Dense, correlated ridges (e.g., GEMSDOE24's 60,069 dots) can saturate coverage while accumulating false-positive mass. Sparsifying from 44,090 to 37,654 could retain substantial truth credit while reducing αF; the hidden labels are unavailable, so that is a mechanism compatible with the user-reported claims, not a measured improvement.
2. **Catalogue-proximity pruning.** [DrivenData staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) explicitly state that known USGS/INGENIOUS fault pixels are masked pixel-exactly, with **no surrounding buffer**, and new expert truth can be within 300 m of a known fault. Dots 1–2 pixels away are not excluded merely for that proximity: they may earn truth credit if near an unmapped fault, or add false-positive mass if far from one. Removing them might improve or worsen T and F. The user-reported figures differ by 0.0178 (0.2778 − 0.2600), but neither the difference nor this mechanism is confirmed by a receipt or private-truth analysis.
3. **Not proof of optimality.** Without private truth, per-dot T/F decomposition, or authenticated receipts, we cannot prove this causal story, rule out that a denser or differently placed set would score higher, or guarantee generalization to the private set. The 0.2778 claim is **not** evidence that B2 is globally optimal.

## 3. Could we score higher than 0.2778?

Honest answer: **unknown. No defensible score estimate or calibrated forecast is available.**

- We did not compute HOLDOUT-DTI for any of the nine historical files under the required shared evaluator (`gems57-pooled-hide-v2`, whole-segment buffered holdouts, visible-faults-only catalogue features, pooled α=0.2 β=0.8). A separate prior MSPTCD lane reported using the shared evaluator on its own arms; those results were not independently replayed here and do not measure the nine historical files. Another parallel lane used a private, non-compliant evaluator.
- No submission-page receipt links any historical SHA-256 to a live leaderboard value. The public leaderboard was manually rechecked at 0.4544 on 27 October 2026 at approximately 19:05 UTC; an earlier automatic refresh failed, and the dashboard marks expired or failed-refresh snapshots stale; the aggregate leaderboard is not a per-file receipt, and public performance does not guarantee private-round performance.
- A valid test would require: (a) resolving the literal registry policy (see §4), (b) using the shared cached feature stack and evaluator, (c) comparing the new candidate and the same-fold incumbent with paired 95% spatial-block CIs, and (d) obtaining organizer confirmation. A paired interval should accompany the comparison, with multiple-arm selection disclosed; a proxy is not a leaderboard score.

## 4. Why we are blocked from generating a new unique TIF today

The novelty stop is independent of format. Under the shared literal interpretation of support, the requested duplicate rule produces an effective **policy-logic contradiction**:

- **Binary lattice witness:** The registered [13GEMSDOE stride-5 lattice](https://github.com/buffedlizard55-lab/13GEMSDOE/blob/92ee6f074323f161eed837b80ec3ee5b662e26f5/docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif?raw=1) (SHA-256 `b4570b406e...`) covers 5,160,724 of 5,167,373 footprint cells within 3 px. At the standard 37,654-dot budget, any 37,654 distinct in-footprint dots must overlap it by at least (37,654−6,649)/37,654 = **82.34% > 70% STOP**. This is a pigeonhole bound, not an experiment.

- **Continuous prior witness:** The registered [17GEMSDOE continuous probability prior](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) (SHA-256 `ab0a0a62...`) is **positive in all 5,167,373 footprint cells**. The unchanged shared uniqueness tool defines support as every finite value >0. If that literal definition applies to continuous rasters, **every nonempty candidate has 100% overlap**. Whether a probability field should count as "dots" requires an explicit policy clarification; we do not silently exempt it.

Both witnesses are hash-pinned and independently rechecked in `evidence/registry_audit.json` and `evidence/dense_prior_certificate.json`. Every one of the nine historical bests already exceeds the 70% threshold against at least one other historical file *and* against the lattice (>99.1% overlap), confirming the rule's strictness. For complete evidence, see the [literal registry stop proof](research/evidence-and-sources.md#parallel-h1-candidate--independent-post-merge-audit) and [portfolio pairwise matrix](data/portfolio.json).

**Consequence:** Under the current literal rule, no 37,654-dot prediction can pass the novelty gate — regardless of geology. A smaller budget (≤22,163 dots) evades only the lattice bound, not the continuous-prior bound under the literal support definition. This is why `evidence/run_card.json` shows `ok_to_submit: false` and this review lane generated no TIF.

## 5. What would be required to beat 0.2778 honestly

1. **Resolve the registry policy** without quietly exempting witnesses: is the lattice intended as a calibration control? Does a continuous field's >0 support count as dots? The decision must be documented before any submission.
2. **Restore authenticated inputs:** official DrivenData sample/labels, 19-band grid, shared derived feature bank, and current weekly quota (requires login; unattainable in this sandbox due to network allowlist).
3. **Preregister one lane**, run each feature-alone leakage canary (AUC >0.90 = stop), and evaluate pooled HOLDOUT-DTI on identical spatially-blocked, whole-segment folds with catalogue features derived from visible faults only.
4. **Prove improvement** via paired bootstrap CIs against the same-fold incumbent, then validate format (`[0,1]`, float32, EPSG:32611, single band, footprint mask) with the shared writer and a separate freshness/registry check.

Only then can a new TIF be labeled **OK TO DOWNLOAD AND SUBMIT** with an evidence class of HOLDOUT-DTI (and later ORGANIZER-CONFIRMED upon receipt).

## 6. Highest-ranked research proposal — not an assigned lane

The method lane remains UNASSIGNED; P1 is not nominated or authorized for an experiment. The highest-ranked desk proposal in `research/hypotheses.md` is **P1: upward-continuation ridge trajectories**, using the mirrored `rtp` field with terrain and magnetic-gradient context:

- **Physical signature:** track oriented magnetic ridge maxima across several upward-continuation heights, with explicit mask, seam and FFT-boundary controls.
- **Why it could find a missing fault:** a covered rock-property boundary might remain visible in geophysical data where surface mapping is incomplete. A boundary is not necessarily a fault.
- **Difference from reviewed repository work:** MSPTCD implements multiscale gradients and magnetic tilt, not ridge trajectories through a computed continuation series. GEMSDOE32 has used an upward-continued magnetic band, so the family is related; a [README-only review](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/focus-head-readme-review-20261027.md) is not an exhaustive fleet novelty check. The earlier phase-congruency proposal was withdrawn because GEMSDOE32 reports ARENA49-PCG.
- **Non-fault mimic:** lithologic contacts, dikes, remanence, survey striping, and FFT edge artifacts.
- **Expected DTI improvement:** ranked first qualitatively, medium–high cost; no numeric forecast or independent holdout.

If a method is explicitly assigned and all pre-placement gates are resolved, any future candidate must pass feature canaries, matched shared-evaluator holdouts, complete-registry checks, and format validation before a separate slot selector. The ranking itself authorizes nothing.

## 7. Practical submission guidance and the [0,1] error

The exact bytes behind the user's earlier portal error (`Predicted values must be in range [0, 1]`) were not supplied, so its cause is unknown. Potential range, non-finite, masking and metadata problems can be diagnosed separately without guessing or clipping. Our read-back validator (`python scripts/validate_tif.py file.tif --reference authenticated_sample.tif --strict-all-finite`) checks:

- Single band, float32, EPSG:32611, identical shape/transform to reference
- All in-footprint values finite and in [0,1]; no NaN inside footprint
- No masked interior cells (the shared gate's known finite-NoData=0 edge case is checked separately)

The optional strict flag also flags outside-footprint NaNs even though the official format describes null/NaN outside the bounds; use it as an extra diagnostic, not as a substitute for the official wording. A format pass alone is **not** scientific approval. See the [executive summary submission checklist](executive-summary.html#novelty) and [format specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format).

## 8. Limitations and what we need

- No authenticated DrivenData bytes, private truth, or submission-page receipts.
- No complete current registry; nine-file audit is sufficient to prove duplicates, not to prove uniqueness.
- No USGS/GDR binary downloads were verified in this sandbox; relevant direct download hosts were outside its network allowlist.
- No explicit single-method lane assignment in the prompt — the active lane is UNASSIGNED, and P1 is not nominated or authorized.

Resolving these is the next session's work. The current repository decision remains **DO NOT SUBMIT — no new TIF is approved** (`evidence/run_card.json` verdict: negative, ok_to_submit: false).

---
*Links for manual review: [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/), [Problem & metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [GEMSDOE32 historical page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [GeoDAWN release (CC0)](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR INGENIOUS (CC BY 4.0)](https://gdr.openei.org/submissions/1391), [USGS Argenta Rise](https://pubs.usgs.gov/publication/70271418), [INN play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and).*
