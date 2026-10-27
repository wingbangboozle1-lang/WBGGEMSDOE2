# Executive summary — 27 October 2026 (current decision)

**Decision: OK TO DOWNLOAD AND SUBMIT one newly generated TIFF** — conditional on the
documented [two-reading registry policy](../docs/PROJECT_CHARTER.md) and on the human
selector checking the weekly cap. This repository does **not** upload anything.

**Download:** [`docs/downloads/wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros.tif`](../docs/downloads/wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros.tif)
· [one-TIFF ZIP](../docs/downloads/wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros.zip)
· SHA-256 `d75bf8ee99576a80fe26d00c0afca6cc76ad54a4caae196b96bfdb742404b05f`
(217,821 bytes; 100,000 dots; single float32 band; EPSG:32611, 100 m, 3730×3292).

**Submission name:** `wbg2-20261027-blind-discontinuity-unique`
**Short note (≤140 chars):** `Blind-discontinuity E3_fusion soft88; HOLDOUT-DTI proxy only; 126-raster audit; no organizer score.`

## The table the request asked for

| What file to download | Estimate score | Unique submission? | Verdict |
|---|---|---|---|
| **NEW** [`wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros.tif`](../docs/downloads/wbg2-blind-discontinuity-E3-soft88-20261027T185715Z-606d02c9c1-zeros.tif) | **No leaderboard estimate exists.** Measured **HOLDOUT-DTI 0.1452**, 95% CI **[0.1287, 0.1626]**, evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, 4 buffered folds, 2,000 spatial-block bootstrap draws. Paired win vs matched collar-only control: **+0.0135** [0.0068, 0.0198]. A holdout proxy is **not** a public/private leaderboard score. | **YES.** 126 accessible public rasters checked (121 distinct SHA-256); worst like-for-like 3 px dot overlap **67.65%** (limit 70%); worst \|Spearman\| **0.431** (limit 0.90); zero duplicate firings. Unique against **all nine focus sites** (worst overlap 54.93%). Literal reading still fires on 3 space-filling controls — see policy note. | **Download & submit** (selector decides slot). |
| GEMSDOE24 — `gems24-h25-1-dotted-h19-5-d1-5-…` | 0.2477 **USER-REPORTED**, not an organizer receipt; no estimable score for a new file. | NO — historical raster; new-file overlap 33.07%. | Research only. |
| GEMSDOE25 — `gems25-dotted-h19-5-d2-8-…` | 0.2600 USER-REPORTED. | NO — new-file overlap 54.93%. | Research only. |
| GEMSDOE27 — `gems27-topo-gap-closure-t-v2-…` | 0.2449 USER-REPORTED. | NO — new-file overlap 13.09%. | Research only. |
| GEMSDOE28 — `gems28-h36-1-rung30-blind-r1-…` | 0.2710 USER-REPORTED. | NO — new-file overlap 11.37%. | Research only. |
| GEMSDOE30 — `gemsdoe30-d28-poisson300m-offcat-44090-…` | 0.2600 USER-REPORTED. | NO — new-file overlap 37.50%. | Research only. |
| GEMSDOE31 — `gemsdoe31-h27-4-solo-d28-…` | 0.2708 USER-REPORTED. | NO — new-file overlap 11.01%. | Research only. |
| GEMSDOE32 — `gemsdoe32-h33-h33-2-b2-…` | **0.2778 USER-REPORTED** — the best supplied claim, not a receipt. Its mask is D2.8 pruned at 2 px from the mirrored catalogue; pruning plausibly reduces false-positive mass under the recall-dominated metric, but hidden truth and receipts are unavailable, so causation is not proven. | NO — new-file overlap 10.29%. | Research only. |
| GEMSDOE33 — `GEMSDOE33-h33d-analog-tip-stepover-r30-…` | 0.2632 USER-REPORTED. | NO — new-file overlap 11.49%. | Research only. |
| GEMSDOE36 — `gemsdoe36-anderson-geothermal-pinn-38854-…` | 0.2750 USER-REPORTED. | NO — new-file overlap 11.02%. | Research only. |

Sources for every number: [`evidence/soft_novelty_refinement.json`](../evidence/soft_novelty_refinement.json),
[`evidence/final_uniqueness.json`](../evidence/final_uniqueness.json),
[`evidence/final_format.json`](../evidence/final_format.json),
[`evidence/run_card.json`](../evidence/run_card.json),
[`config/registry_inputs.json`](../config/registry_inputs.json).

## Why the GEMSDOE32 B2 claim is high, and whether we can beat it

The official metric is `DTI = TP_w/(TP_w + 0.2·FP_w + 0.8·FN_w)` with a 300 m
triangular kernel ([official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric)).
Since `FN_w = |G| − TP_w`, coverage dominates: a false positive costs 0.2, an
uncovered truth pixel 0.8. B2 is exactly D2.8 with 6,436 dots within 2 px of the
mirrored catalogue deleted (44,090 → 37,654). Removing low-marginal-coverage dots
near already-mapped faults can preserve most proximity credit while cutting
false-positive mass, which is a plausible explanation for a high claim. It is
**not** proven: the private labels and the per-file submission receipt are absent,
and repeated public probing risks public-set overfitting.

We cannot estimate a new leaderboard score from that claim. On identical buffered
folds the nine historical rasters score HOLDOUT-DTI 0.0037–0.0919; our new file
scores 0.1452 and beats a matched collar-only control with a paired 95% CI whose
lower bound is positive (+0.0068). That is the strongest *measurable* evidence we
can produce without spending a slot — it is a proxy, not a promise of beating
0.2778, 0.3195, 0.4413 or the observed 0.4544 live leader.

## What is new scientifically

Five hypotheses were preregistered in
[`research/hypotheses_20261027.md`](../research/hypotheses_20261027.md). The
winning lane fuses (1) low-slope **curvature dipoles** of detrended elevation
(blind fault-propagation folding), (2) **clay-capped alteration edges** (opposed
conductivity/magnetic gradients and magnetic-low × conductivity-high pairs), and
(3) **strain-partition boundaries** (dilatation zero-crossings along shear
gradients). Official grounding: [USGS YVO 2022](https://www.usgs.gov/observatories/yvo/news/novel-technique-peeks-beneath-ground-yellowstones-hot-water-plumbing-system),
[USGS Siler 2023](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa),
[USGS QFFD 28b](https://landslides.usgs.gov/static/lfs/nshm/qfaults/Reports/28b.pdf),
[USGS GeoDAWN (CC0)](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
Named non-fault mimics: alluvial-fan/terrace risers, playa clays, GPS
interpolation artifacts and flight-line striping.

A first pass trained with a distance-to-visible-fault column learned the trivial
identity "visible pixel → distance 0" and emitted zero-coverage dots. It was
discarded before any result was trusted. The promoted model sees **label-free
geophysics only**; the visible catalogue enters once at emission as a fixed
collar prior. A hard registry crowd cap was a decisive negative (HOLDOUT-DTI
0.0091); a graded dense-witness penalty (β = 0.88) both clears the duplicate
stop and improves the holdout score.

## Exact submission steps

1. Click the TIFF (or ZIP) link at the top; verify its SHA-256.
2. Sign in to the [GEMS Prize](https://www.drivendata.org/competitions/306/competition-doe-gems/);
   check the **displayed** weekly allowance — staff confirm the website limit
   prevails ([5 Oct 2026](https://community.drivendata.org/t/submission-amount-question/11553)).
3. **Submit → Make new submission**; choose the `.tif` or the one-TIFF `.zip`.
4. Paste the unique name and short note above (≤140 characters).
5. Keep the organizer receipt with filename, hash, note and timestamp. A local
   HOLDOUT-DTI is never that receipt.

The earlier "Predicted values must be in range [0, 1]" error is avoided by our
all-finite export: the file has zero NaN/Inf, no in-footprint NoData mask, all
values in [0,1], and zeros outside the footprint. Local validation is not
organizer acceptance; the reference grid is a hash-pinned owner mirror.

## Two readings of the duplicate rule — read before submitting

The literal rule ("any registry raster's dots") is **mathematically
unsatisfiable** here: the 13GEMSDOE stride-5 lattice's 3 px halo covers 99.87% of
the footprint, and the 17GEMSDOE continuous prior is positive on 100% of it.
Three control rasters therefore fire the literal rule on **any** nonempty file.
The [charter amendment](PROJECT_CHARTER.md) adopts the like-for-like reading for
clearance: the 70% dot test applies to geological dot fields, and the 0.90 rank
correlation applies to every raster. Both readings are computed and published in
`evidence/final_uniqueness.json`. **If you reject that policy decision, the answer
is DO NOT SUBMIT.** No threshold was weakened and no control was hidden.

## Irregularities and remaining work

See [`research/sources_20261027.md`](../research/sources_20261027.md) for the
line-by-line official source register. Key flags: the user's 0.3195/0.4413
"highest score" claims conflict with the observed 0.4544 official leader; the
mirrored sample has 60,988 positives equal to the catalogue although the official
page describes an all-absence sample; 8 of 126 ledger rows are unresolved in the
registry; HEAD-tree blobs are unpinned snapshots; organizer data, licence
confirmation, weekly quota and receipts are unavailable; two USGS pages returned
403/404 to our fetcher.

Next session: authenticate the official download with a logged-in account; pin
every registry raster to an immutable commit; obtain the free CC0 GeoDAWN line
CSV and test the flight-line repeatability veto; fix the shared validator's
finite-NoData-in-footprint gap upstream; and record an organizer receipt to
calibrate any future score estimate.
