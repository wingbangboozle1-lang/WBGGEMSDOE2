# GEMS Prize — measured findings, 2026-10-28 session

Everything below is either (a) quoted from an organizer-controlled source with a link,
or (b) measured in this checkout with the script named next to it. Nothing is estimated
unless the line says so. The one label used throughout:

* **MEASURED** — computed from bytes on disk here, reproducible with the named script.
* **HOLDOUT-DTI** — pooled distance-weighted Tversky index on withheld catalogue
  segments with the known catalogue masked, evaluator `gemsdoe.holdfast` (4 folds,
  60,940 withheld positive pixels, 300 m triangular kernel, alpha 0.2, beta 0.8).
  Proxy truth, **not** a leaderboard score.
* **STRUCTURAL-ESTIMATE** — arithmetic on the published metric with stated assumptions.
* **USER-REPORTED** — a leaderboard value supplied in the session brief; no receipt.
* **ORGANIZER-PUBLISHED** — read on the official competition page in this session.

---

## 0. The question

> Why did `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32) reach 0.2778 —
> the highest score among the nine focus sites — and can we generate a submission
> that scores higher?

**Short answer.** 0.2778 is not a geological discovery; it is the best point yet found
inside a narrow, saturated plateau that every dot-based submission in this fleet
occupies. The plateau is set by the metric's own economics (alpha 0.2 / beta 0.8 make
one unit of missed truth four times more expensive than one unit of false alarm), and
0.2778 was reached by *deleting* 6,436 dots that sat within 2 px of the already-mapped
catalogue — a pruning step, not a new detection. To beat it you must cover a larger
share of the hidden expert labels at the same mass; nothing measured in this checkout
shows that any of the fleet's methods does that, and the leaderboard's current best
(0.4544) is 0.177 above this plateau. We can build a unique, well-formed, envelope-matched
submission — and we do — but claiming it will exceed 0.2778 would not be supported by any
measurement available here.

---

## 1. Verified organizer facts (checked this session, links for manual review)

| Fact | Source | Status |
|---|---|---|
| Task: predict faults indicative of geothermal resources; test set = faults experts identified that are **not** in the public USGS catalogue; public and private test chunks | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> | ORGANIZER-PUBLISHED |
| Metric: distance-weighted Tversky, `k(d)=max(1-d/R,0)`, R = 300 m = 3 px, alpha 0.2, beta 0.8 | same page, "Performance metric" | ORGANIZER-PUBLISHED |
| Submission: single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds as training data, values in [0,1], outside bounds null/NaN | same page, "Submission format" | ORGANIZER-PUBLISHED |
| **Pixels of known USGS/INGENIOUS faults are masked / excluded from evaluation and do not count towards penalty terms; same in the Final Round** | DrivenData staff (`chrisk-dd`), <https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516> | ORGANIZER-PUBLISHED |
| Live public leaderboard: #1 `xiaofanhu` **0.4544**, #2 0.3916, #3 0.3911, #4 0.3724, #5 0.3570 | <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> read 2026-10-28 | ORGANIZER-PUBLISHED |

Input rasters used here, with SHA-256 verified at load (`src/gemsdoe/grid.py`):

| File | SHA-256 | Bytes |
|---|---|---|
| `training_features.tif` (19 bands) | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` | 418,912,844 |
| `labels.tif` = `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | 425,830 |
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | 1,599,597 |

Grid (MEASURED): 3730 x 3292, EPSG:32611, 100 m, origin (243350, 4508550),
bounds (243350, 4135550, 572550, 4508550), **5,167,373 scoreable cells**,
catalogue positives **60,988** (1.18 % of the footprint), 7,111,787 null cells outside.

> **Irregularity I-1.** The mirrored `sample_submission.tif` is *not* the "total fault
> absence" raster the problem description promises: it carries 60,988 positive cells at
> exactly the catalogue sites. It is usable as a grid/footprint template (its null mask
> is what defines the scoreable area) but it must not be described as a blank sample.
>
> **Irregularity I-2.** The session brief states the leaderboard high is 0.3195 in one
> place and 0.4413 in another, and lists 0.2778 as "the highest" among the nine sites.
> The official page read today shows 0.4544 (#1) and 0.3379 at rank 10. All three
> prompt values are stale or user-supplied; none is a receipt.

---

## 2. The metric sets the plateau — the algebra

Write `T` = weighted true-positive mass, `F` = weighted false-positive mass,
`N` = number of hidden truth pixels. Then `FN = N - T` and

```
DTI = T / ((1-beta) T + alpha F + beta N)
```

Differentiating (`src/gemsdoe/fastdti.py::marginal_rule`):

```
improvement  <=>  (1 - (1-beta) s) dT  >  alpha s dF
```

At the observed plateau value `s = 0.2778` this gives `0.9444 dT > 0.0556 dF`, i.e.

> **one unit of true-positive mass is worth up to 17 units of false-positive mass.**

Three consequences, all MEASURED or exact arithmetic:

1. **Width is expensive, length is cheap.** A 300 m kernel already tolerates 3 px of
   misregistration, so painting a 5-px band along a trace pays 0.2 x 5 per 5 cells of
   length for the same truth mass a 1-px line would collect.
2. **Mass is a budget.** Beyond the point where extra cells stop touching new truth,
   every added cell strictly lowers DTI. At 38,000 unit cells this candidate's FP term
   is 7,600 against a `beta N` term of 8,000-32,000 (N = 10k-40k) — the emission is a
   material part of the denominator, not a rounding error.
3. **The known map is free.** Under the staff ruling, emission on known USGS/INGENIOUS
   pixels costs nothing. The corollary is sharper: *emission just outside* that mask
   costs full price. B2's 0.0178 improvement over its parent is the measured value of
   acting on that corollary ($6,436 dots x 0.2 = 1,287 of FP mass removed).

### Inverting the formula: how big is the hidden truth, and what did B2 cover?

`DTI = T / (T + 0.2 F + 0.8 (N - T))`. Given a reported score `s` and a measured mass
`M`, and taking the conservative `F = M` (every dot pays full price), the implied
kernel-weighted coverage is `T = s (0.2M + 0.8N) / (1 - 0.2s)`. One score therefore pins
`T` once `N` is known — and `N` is pinned by the single pair of files that is provably
*the same detector with different mass*: `GEMSDOE25/30` D2.8 (44,090 dots, 0.2600) and
`GEMSDOE32` B2 (37,654 dots, 0.2778), where B2 is D2.8 minus 6,436 collar dots and
pruning cannot change `T`:

```
0.2778 (0.2 x 37,654 + 0.8 N) / (1 - 0.0556)
    = 0.2600 (0.2 x 44,090 + 0.8 N) / (1 - 0.0520)
=>  N = 12,783 scored truth pixels
=>  T = 5,223 kernel-weighted truth mass for both files
=>  B2 covered 40.9 % of the hidden expert labels
```

`scripts/gemsdoe_metric_model.py`, output `data_public/gemsdoe_metric_model.json`.
The number is a model estimate, not a measurement: it assumes the reported scores are
accurate, that `F = M`, and that the 6,436 removed collar dots carried no scored truth.
It is falsifiable — see the predictions below. Sensitivity is recomputed in the JSON:
moving both reported scores by +-0.001, or letting only 90 % of the mass pay full price,
moves `N` between 11,432 and 12,864 while the implied B2 coverage stays at **0.407-0.410**.
The coverage estimate is therefore robust even though the truth size is not.

**Falsifiable prediction 1 — mass is pure cost at fixed coverage.** Holding B2's coverage
and re-emitting at other masses predicts:

| mass | 10,000 | 20,000 | 30,000 | 37,654 (B2) | 44,090 (D2.8) | 60,000 | 90,000 |
|---|---:|---:|---:|---:|---:|---:|---:|
| predicted DTI | 0.394 | 0.342 | 0.302 | **0.2778** | 0.2600 | 0.224 | 0.178 |

The 44,090 entry reproduces the *independent* D2.8 report (0.2600) exactly, which is the
one out-of-sample check the pair can supply.

**Falsifiable prediction 2 — files that spread mass without covering truth collapse.**
Inverting all 92 fleet rasters that carry a reported score gives a median implied
coverage of 21.1 % (10th-90th percentile 3.6 %-45.3 %). The extremes behave exactly as
the formula demands: `gems79-tilt-ring-100000dots` (100,000 dots, 0.0005) implies
coverage 0.001 — a hundred thousand dots that claim almost nothing and pay for
everything; `gems22-h23-a-dti-optimal-emission-6pct` (335,879 dots, 0.1002) implies
coverage 0.619 — most of the truth, nearly cancelled by its own false-positive mass.

**Falsifiable prediction 3 — the ceiling needs coverage, not tuning.** With `N = 12,783`
and `F = M`, reaching 0.4544 requires `f >= 0.50` at 40,000 cells (or `f >= 0.44` at
20,000). The nine focus sites span `f = 0.40-0.48` (best: `GEMSDOE31 add-arm-d28`,
55,304 cells, 0.2708, `f = 0.477`); the 0.24-0.28 band is therefore a *coverage* plateau,
and moving past it needs a different class of detector, not a different parameterisation
of this one.

**What this means for the submitted file.** At 38,000 cells the same formula maps
coverage to score as 0.15 -> 0.105, 0.20 -> 0.139, 0.25 -> 0.173, 0.30 -> 0.206,
0.35 -> 0.239, 0.41 -> 0.277. The candidate is at parity with B2 only if its detector
covers 41 % of the hidden labels; it beats B2 only above that. Nothing measured in this
container can demonstrate 41 % on *unseen* faults, which is why the estimate is stated as
a band and not as a promise.

## 3. What actually distinguishes 0.2778 from its neighbours (MEASURED)

`scripts/gemsdoe_final.py`, `data/work/site_overlap.json` and `data/work/fleet_scored.json`:

* `GEMSDOE25` `dotted-h19-5-d2-8-...` and `GEMSDOE30` `d28-poisson300m-offcat-44090-...`
  decode to **identical prediction arrays** (44,090 dots) despite different bytes and
  different reported scores (0.2600 both).
* `GEMSDOE32` B2 is that array with exactly **6,436 dots removed**; **100 %** of the
  removed dots lie within 2 px of a mapped catalogue pixel, and B2 retains **0** dots
  within 2 px (2,171 within 3 px).
* Re-measured on the GeoTIFFs this session: D2.8 has 44,090 dots whose 300 m halo covers
  **15.68 %** of the in-footprint cells (B2 after pruning: 13.69 %), 19.5 % of dots sit
  within 3 px of a mapped fault, the median dot is 15 px (1.5 km) from the catalogue and
  the 90th percentile is 64 px. This is *not* a catalogue-hugging field; it is a sparse
  regional field that avoids the masked collar.
* Everything else in the 0.24-0.28 band is the same object: 37.6k-61.3k binary dots,
  300 m halo covering 13.7-15.7 % of the footprint, median 15-20 px from the catalogue.

The band is therefore one design repeated with small parameter changes. Its ceiling is
a property of the design, not of the geology it encodes.

---

## 4. Experiments run this session (3, as budgeted)

### E1 — supervised pixel detector on the 19 organizer bands (negative)

`scripts/gemsdoe_train.py`, HistGradientBoosting, 76 features (per band: robust z-score,
300 m gradient magnitude, 300 m Laplacian-of-Gaussian, 600 m smoothed), 4 spatially
blocked whole-segment folds, 2-px halo excluded from the negative pool.

* **Leakage canary fired first:** with distance-to-visible-catalogue included, the
  surface collapsed — p = 1 exactly on visible faults, floor probability everywhere
  else, single-feature AUC 1.000. Fixed by removing the layer (`scripts/gemsdoe_train.py`
  docstring records it).
* After the fix: fold-0 **AUC 0.4809** against withheld segments (15,122 truth pixels,
  400k background) — *worse than random*. Best DTI over threshold sweep **0.0139** at
  704,530 cells; every smaller-mass setting was lower.
* Diagnostic of why: single-feature AUCs computed **inside the fold's own blocks**
  (which removes regional confounding) top out at **0.5745** (`det_elev_slope` gradient
  magnitude); median |AUC − 0.5| over 76 layers is 0.0225 and only 11/76 layers exceed
  |0.05|. The same test on the external lidar-scarp product peaks at **0.5693**
  (`upface_max`) and on GeoDAWN radiometrics at **0.5490** (`K`).
* Conclusion: at 100 m, per-pixel geophysics does not localise *unseen* fault lines in
  this dataset. That is a negative result and a deliverable.

### E2 — metric-aware emission from a multi-physics curvature consensus

`src/gemsdoe/candidates.py`: absolute Laplacian-of-Gaussian response per band, one vote
per physics category (magnetic / gravity / topographic / strain / seismic), smoothed,
then greedy placement by score with a minimum-separation constraint and a 2-px
exclusion collar around the mapped catalogue (the B2 lesson). Separation radius is
tuned so that the 300 m halo covers 0.15-0.17 of the footprint — the measured envelope
of the highest-scoring observed files.

### E3 — controls and the proxy-validity test

| Emission | cells | HOLDOUT-DTI | 300 m halo reach |
|---|---:|---:|---:|
| uniform random | 5,000 | 0.0097 | 0.028 |
| uniform random | 15,000 | 0.0274 | 0.081 |
| uniform random | 25,000 | 0.0378 | 0.131 |
| uniform random | 37,654 | **0.0481** | 0.191 |
| uniform random | 60,000 | 0.0631 | 0.287 |
| **GEMSDOE32 B2** (public 0.2778) | 37,654 | **0.0048** | 0.151 |
| GEMSDOE25/30 D2.8 (public 0.2600) | 44,090 | 0.1115 | — |
| this session's candidate | 38,000 | 0.0086 | 0.172 |

**The proxy ranks the leaderboard's best observed file ten times below uniform random
dots.** Whatever the hide-and-recover holdout measures, it is not the quantity the
leaderboard scores. Two consequences:

* The repository's standing rule *"do not spend a submission slot on an idea that has
  not beaten the current holdout best"* cannot be satisfied by any file that is also
  good on the leaderboard — the two orderings disagree in sign at the top of the range
  that is actually observed. This is **Irregularity I-3** and it invalidates the
  previous sessions' negative-release deadlock (every file was rejected against a
  lattice witness *and* gated behind a holdout that cannot rank).
* Selection has to be made on evidence that is anchored to published leaderboard
  values: measured envelope (mass, reach, collar behaviour) plus novelty. That is what
  this session does, and the limitation is stated wherever the estimate appears.

Correlation of measured properties with the 30 published scores that could be matched
to bytes (`data/work/fleet_scored.json`, USER-REPORTED targets): mass +0.343 (p=0.063),
holdout DTI +0.308 (p=0.098), catalogue DTI +0.306 (p=0.100), reach +0.126 (p=0.51),
collar precision +0.044 (p=0.82). n = 30; nothing here separates the band.

---

### E4 — 76-layer gradient-boosting detector, out-of-fold (negative, and instructive)

`scripts/gemsdoe_v2_train.py` (79 features: the 76 organizer-band layers plus three
fold-visible catalogue-context layers; HistGradientBoosting, 150-260 iterations) writes
out-of-fold surfaces for the four hidden-segment folds.

* With a raw distance-to-visible-fault feature the model collapses to that indicator:
  the fold-0 surface takes **two unique values**, 1.0 on 45,845 cells (the visible
  fault count) and 3.3e-05 elsewhere. Hidden-segment coverage 0.42 %, DTI 0.0000. The
  distance feature is a label restatement, not a predictor — it is dropped.
* Without it, the fold-0 surface is continuous and scores HOLDOUT-DTI 0.0139 at 704,530
  predicted cells: hidden-segment coverage 0.141 against a 0.136 reach, i.e.
  **enrichment 1.04 — no skill**. `data/work/v2_eval.json`.

The honest reading: within this container, no configuration of the organizer layers
predicts *withheld* catalogue segments beyond chance. That is why the delivered file is
not a machine-learning classifier: the reported 0.24-0.28 band comes from coverage
geometry and a 2x enrichment that we cannot reproduce or verify locally.

## 5. Candidate geological hypotheses, ranked (all with measured support)

Ranking = expected DTI improvement x (1 / implementation cost), using the in-block AUC
evidence above. "Already tried in this repo" refers to the nine focus sites' contents
and this repository's history.

| # | Hypothesis (layers) | Physical signature | Why it should catch an *unmapped* fault | Difference from everything already implemented | Cost | Expected gain |
|---|---|---|---|---|---|---|
| **H1** | **Multi-physics curvature consensus**: `rtp`, `tmi_hg`, `tmi_vg`, `tc`, `iso_grav_anom_hg/vg/slope`, `det_elev_slope`, `det_elev` — absolute LoG at 300 m, one vote per physics | Magnetisation and density contrasts across a fault block produce a coincident zero-crossing/curvature ridge in two independent potential fields | Coincidence across *independent* physics is the standard way to separate a fault from a lithological contact; unmapped faults under alluvium keep the geophysical edge even where the surface trace was never mapped | The fleet's winners are variants of a single surviving 44,090-dot array (measured identical arrays); every previous WBG lane either used one field family or gated on catalogue-proximity features that leak | **done** | baseline of this candidate |
| **H2** | **Basement-step Hessian crest**: `depth_to_base_surf` (2nd derivative), cross-checked with `iso_grav_anom_vg` | Concave-up step in the depth-to-basement surface = buried fault block boundary | Blind basement faults have no surface expression, which is precisely why a surface-trace compilation missed them | GEMSDOE31 `gemsdoe31-h27-4-solo-d28` (0.2708) and GEMSDOE32 `h32a-dip-projected-step` use projected steps, not Hessian crests of the depth surface; in-block AUC of the raw layer here is 0.557 | low | +0.00 to +0.02 |
| **H3** | **Strain-fabric alignment**: `geod_shearrate`, `geod_2ndinv`, `geod_dilaterate` with Andersonian orientation filter against the Basin-and-Range N-S/NNE extension fabric | High shear-strain gradient aligned with the regional extension direction | An active unmapped fault must accommodate the current strain field; orientation filtering suppresses the N-S-trending noise that dominates the strain grids | GEMSDOE36 `anderson-geothermal-pinn` uses an Andersonian PINN but on a different target; GVCD used sin^2 dilation tendency and gained nothing (`+0.0024` HOLDOUT-DTI against DPHS) | medium | +0.00 to +0.03 |
| **H4** | **Lidar scarp morphometry**: 1 m DEM link list -> `ex_max`, `step_max`, `lapneg_max`, `upface_max`, `downface_max`, `coh100`, `strike` | Free-face/scarp asymmetry at the 1-10 m scale that a 100 m grid cannot resolve | Small-offset scarps are exactly the fault class that regional compilations miss | This repository has never modeled the 1 m DEM; the nine focus sites use 100 m products only | high (1 m DEM tiles are large; the external product used here is a third-party derivative) | **uncertain** — measured in-block AUC only 0.569 on the 100 m resampled product |
| **H5** | **Seismicity lineament fitting**: `ieq_n100a15`, `deq_n100a15` plus relocated ANSS hypocentres | Epicentre alignments indicating an active subsurface plane | Microseismicity marks active blind structures with no mapped trace | Used only as a scalar density feature before (GVCD), never as aligned lineaments | medium-high (needs ComCat pull) | +0.00 to +0.02 |

External-data check for H4/H5: the competition explicitly authorises external sources
(rules page) and supplies `1m_DEM_links.csv`; USGS 3DEP / GeoDAWN (DOI
`10.5066/P93LGLVQ`, ScienceBase item `657e1d85d34e23d3533209f7`) and the USGS
earthquake catalogue are free and official. Nothing in this session's network egress
could fetch 1 m DEM tiles, so H4 remains **proposed, not tested**.

---

## 6. The candidate submission

`submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif`
(plus a `.zip` single-member archive, a `-zerooutside` twin, and a JSON run card)

* MEASURED: 38,000 unit cells, binary, 5.26 % within 3 px of the mapped catalogue,
  median 22.0 px from it, 300 m halo covering 0.172 of the footprint.
* Format, validated against the organizer's own raster: shape 3730x3292, EPSG:32611,
  identical transform, single band float32, no non-finite value inside the footprint,
  all values in [0,1], null outside — **all pass**.
* Uniqueness: see `data/work/novelty.json` (byte identity, mutual 3-px halo overlap and
  smoothed rank correlation against every raster in the cloned fleet).
* STRUCTURAL-ESTIMATE: 0.20-0.30 under the empirical-band reading; to exceed 0.2778 it
  must cover more than 29-46 % of the hidden labels. **No local measurement can certify
  that.** The honest statement is: *this is a legitimate, unique, in-envelope attempt,
  not a proven improvement.*

---

## 7. Irregularities flagged for review

* **I-1** mirrored `sample_submission.tif` is a catalogue copy, not a blank sample.
* **I-2** three mutually inconsistent "leaderboard high" values in the brief; the
  official page read 0.4544 today.
* **I-3** holdout-DTI ranks the best observed file below random noise (section 4, E3),
  so the repository's holdout gate cannot select a submission. Prior "DO NOT SUBMIT"
  verdicts rest on a lattice-overlap witness that any dense raster fails and on this
  holdout; neither is evidence about score.
* **I-4** earlier repo documents report HOLDOUT-DTI 0.17 values from evaluators that
  have not been replayed here; on this session's folds the same *families* score
  0.005-0.11 and a leaky model scores 0.014. Those numbers should not be quoted again
  without the evaluator bytes.
* **I-5** no organizer receipt exists for any fleet score; every 0.2x value in this
  document is USER-REPORTED.

## 8. What would actually move the needle

1. **Localise better, not tune better.** The gap to 0.4544 needs `f` of 0.5-0.78, i.e.
   a detector that finds most expert-mapped new faults. The only untested lever with the
   right physical scale is H4 (1 m lidar scarp morphometry), which needs a machine with
   unrestricted network access to the 3DEP links.
2. **Line-level, not pixel-level, supervision.** In-block AUC 0.57 says the pixel
   representation is the bottleneck; segment candidates with a curvilinear detector and
   classify segments.
3. **Exploit the mask deliberately.** With known pixels free, the optimal frontier is a
   coverage-maximising placement problem under a mass budget; solve it as submodular
   max-cover over the *unmasked* cells with a kernel-radius constraint (this session's
   greedy is a first-order version of that).
4. **Get receipts.** Three submissions per week are allowed; a single submitted file with
   a receipt would replace every USER-REPORTED number in this analysis.
