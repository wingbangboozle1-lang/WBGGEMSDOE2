# WBG4-SSCC — strike-conditioned structural corridor lane (28 October 2026)

**Decision in one line:** a new, unique, format-valid GeoTIFF has been generated
(`downloads/wbg4-sscc-blind-66383dots-20261028T170239Z.tif`) from public
USGS-derived layers plus the official label grid. It is **not** a copy, a jitter,
or a re-threshold of any registry raster. It is validated on a strict
whole-fault holdout. It cannot be given a defensible leaderboard point estimate,
because the holdout metric was measured and found **not** to predict leaderboard
scores (Spearman +0.25, leave-one-out R² < 0, n = 38). Submitting it is a
judgement call with a stated, unresolved risk.

---

## 1. Why `h33-h33-2-b2` scored 0.2778 — and what beating it requires

**What the number is.** `0.2778` is an owner-reported value copied from the
submission page. No organizer receipt for those exact bytes exists in any of the
analysed repositories, and this repository has never held one. The file is
`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (219,065 bytes,
SHA-256 prefix `c55bafc470054e82…` per the GEMSDOE32 ledger).

**What the file is.** The GEMSDOE32 site's own score ledger
(`docs/score-ledger.csv`, row 61) records: *"GROUP BEST. == solo minus 2545 dots
within 2px of catalogue; projection was 0.2747"*. Our own byte audit
(`research/findings.md`, "Why the GEMSDOE32 B2 history is plausible, not proven")
found the GEMSDOE25/30 `d2.8` mask identical inside the footprint and B2 equal to
that mask after deleting every dot within 2 px of the catalogue: 44,090 → 37,654
dots.

**Why that structure pays under the official metric.** With
`k(d) = max(1 − d/300 m, 0)`, 100 m cells, `α = 0.2` (false positive) and
`β = 0.8` (false negative):

* a false negative costs **four times** a false positive, so recall dominates;
* a predicted cell within 3 px of a truth pixel costs **nothing** (`1 − k = 0`);
* cells that land exactly on already-mapped fault pixels are **masked out of the
  score entirely** (the organiser's reply quoted by the sites: only the exact
  known-fault pixels are masked), so the 1–2 px collar around the catalogue is
  pure cost and pruning it is free upside.

B2 is therefore: a strong structural prior, emitted at 37,654 cells (0.73 % of
the 5,167,373-cell footprint), with the catalogue collar removed.

**What score arithmetic implies.** Let `F` be the hidden fault pixels. With
`FP_w ≤ mass` and the reported 0.2778:

```
0.2778 = TP/(TP + 0.2·FP + 0.8·(F − TP))
⇒ TP ≥ 0.235·F        (FP = 0 bound)
⇒ TP ≈ 0.271·F        (FP = mass bound)
```

If the experts' new-fault set is comparable in size to the catalogue (60,988 px),
B2 recovered **14,300–16,600 pixels, i.e. 23–27 % of the hidden truth**. This is
an algebraic rearrangement of the official formula, not a leaderboard
measurement.

**Can it be beaten?** Beating 0.2778 needs `TP ≥ 24,400` at bounded FP — about
40 % of the hidden truth. No filter on an existing dot pattern reaches that: it
requires a detector that fires on faults the catalogue does not contain. That is
the design target of WBG4, and the measured result below is that this lane
recovers far more *held-out catalogue* faults than any registry file measured
(17.8 % vs 0.5–3 %), while the transfer of that ability to *unmapped* faults
remains unproven.

---

## 2. Five candidate hypotheses (ranked; only rank 1 was run)

Machine-readable: [`config/wbg4_hypotheses.json`](../config/wbg4_hypotheses.json).

| # | Hypothesis | Layers | Physical signature | Why it can catch an *unmapped* fault | Named non-fault mimic | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Strike-conditioned structural corridor (SSCC)** | lidar scarp morphology (10 bands), GeoDAWN radiometrics K/Th/U/TC, GeoDAWN extensions ThK/UK/UTh/TMI_up150, SGMC fault raster, GDR-1391 spring density | multi-scale (0.1–5 km) scarp/curvature relief with strike continuity, supported by radiometric contrast and an independent structural map | the detector is fitted to recover *withheld whole components* from geophysics alone (blind variant), so it can fire where no catalogue trace exists | bedrock ridge crests, landslide head scarps, fluvial terrace edges; alluvial-fan radiometric boundaries | medium | **tested** |
| 2 | Radiometric K–Th disequilibrium alteration corridor | `geodawn_rad` K, Th; `geodawn_extensions` ThK, UK | along-strike K enrichment with Th depletion from hydrothermal K-metasomatism | alteration halos extend beyond mapped traces and survive burial | playa/lacustrine clays, evaporites, rhyolitic ash | low–medium | proposal |
| 3 | Magnetic-lineament continuity under cover | `TMI_up150` (cached); full RTP/vertical-derivative/euler stack needs organizer `training_features.tif` | upward continuation reveals deep basement lineaments independent of topography | faults under basin fill have no scarp at all | lithological contacts, basalt flow margins, intrusions | medium (**blocked**: 19-band file is login-gated) | proposal |
| 4 | Geothermal-discharge-weighted structural linkage | GDR-1391 springs + geothermometry; INGENIOUS 2 m temperature probes | hot springs and high geothermometry cluster at fault intersections and relay zones | the mapped trace commonly stops short of the discharging structure | evaporite brines, magmatic heat without faulting, agricultural wells | low | proposal (a "thermal-pop" lane already reached 0.1894 user-reported) |
| 5 | Multi-scale relief-texture entropy | `lidar_scarp_features` relief, lapneg/lappos | band-limited, scale-invariant roughness of fault-controlled topography | blind to catalogue and to scarp polarity | drainage networks, bedrock-ridge fields, landslide complexes | low | proposal |

Ranking is by expected HOLDOUT-DTI gain per unit cost. Only rank 1 was
implemented inside the session's three-experiment / two-hour budget.

---

## 3. Method

* **Grid.** Official 3,730 × 3,292, 100 m, EPSG:32611, transform
  `(100, 0, 243350, 0, −100, 4508550)`, footprint 5,167,373 cells — read from the
  organizer `sample_submission.tif` mirror (SHA-256 `2176d08e…`).
* **Labels.** 60,988 positive pixels, 3,191 connected components
  (`data/labels.tif`, SHA-256 `7ba308cc…`; byte-identical to
  `existing_faults.tif`).
* **Hide-and-recover.** Components are assigned by centroid to the four
  footprint quadrants. For each fold the whole components of that quadrant are
  withheld (29,328 / 12,571 / 9,643 / 9,438 px), a 3 px buffer is excluded from
  feature derivation, every catalogue-derived feature is rebuilt from the
  visible components only, and the scorer masks the visible faults pixel-exactly
  so the withheld faults stay active.
* **Features (47).** Lidar: 10 scarp channels, validity, down-face minus up-face
  polarity, five σ=8 smoothed channels, two gradient magnitudes. Radiometrics:
  K/Th/U/TC + ThK/UK/UTh/TMI_up150, two σ=8 smoothings, two gradients.
  Structure tensor: coherence, cos 2θ, sin 2θ. Distance to SGMC faults + SGMC
  mask. Spring, hot-spring and geothermometry densities (σ=6). Catalogue-derived
  (fold-specific): distance to visible faults, visible density at σ=5/15/40,
  along-strike continuation over 8 strikes to 4 km, and cardinal N–S / NE
  continuations.
* **Leakage canaries.** Each feature alone, held-out positives vs buffered
  background: maximum AUC **0.8569** (`D_vis_log`), 0 of 47 features above the
  0.90 stop ([`evidence/wbg4_canaries.json`](../evidence/wbg4_canaries.json)).
* **Model.** `HistGradientBoostingClassifier` (250 iterations, lr 0.06, 31
  leaves, L2 = 1.0, min 60 samples/leaf), trained on visible fault pixels plus a
  3:1 random background sample from the training quadrants.
* **Operating point.** The emitted set is the **top-k model scores** over the
  scoring footprint. k is chosen from the pooled holdout DTI curve, so the
  emitted mass is exact and independent of probability calibration.

---

## 4. Results (HOLDOUT-DTI, evaluator `wbg4-hide-recover-v1`, 60,980 withheld positives)

| Emitted mass (share of footprint) | Cells per fold | Withheld positives covered | Pooled DTI |
|---|---|---|---|
| 0.2 % | 10,243 | 6.2 % | 0.0670 |
| 0.4 % | 20,486 | 9.4 % | 0.0887 |
| 0.6 % | 30,729 | 11.8 % | 0.0999 |
| 0.9 % | 46,093 | 14.8 % | 0.1070 |
| **1.3 %** | **66,581** | **17.8 %** | **0.1086** |
| 2.0 % | 102,432 | 21.8 % | 0.1041 |
| 3.0 % | 153,649 | 26.6 % | 0.0967 |
| 4.5 % | 230,473 | 32.7 % | 0.0875 |

**Negative result (deliberate, and it changed the design).** The identical model
with catalogue-proximity features enabled scored **0.0156** pooled. Under
hide-and-recover, "be near the mapped catalogue" is not a fault detector: it
re-detects the faults that were *not* withheld and earns nothing for the
withheld ones. The emitted file therefore uses the **blind** feature set.

**Matched-fold registry comparison** (`scripts/score_registry_folds.py`, same
folds, same evaluator, 38 rasters including every high scorer that could be
fetched):

| File (site) | Reported | Same-fold HOLDOUT-DTI |
|---|---:|---:|
| `h33-h33-2-b2…-zeros` (GEMSDOE32) | 0.2778 | **0.0048** |
| `anderson-geothermal-pinn-38854…` (GEMSDOE36) | 0.2750 | 0.0049 |
| `h36-1-rung30-blind-r1…` (GEMSDOE28) | 0.2710 | 0.0330 |
| `h27-4-solo-d28…` (GEMSDOE31) | 0.2708 | 0.0464 |
| `dotted-h19-5-d2-8…` (GEMSDOE25) | 0.2600 | 0.1115 |
| `d28-poisson300m-offcat-44090…` (GEMSDOE30) | 0.2600 | 0.1115 |
| `topo-gap-closure-t-v2-on-d1-5…` (GEMSDOE27) | 0.2449 | 0.1085 |
| `h25-1-dotted-h19-5-d1-5…` (GEMSDOE24) | 0.2477 | 0.1086 |
| `h33d-analog-tip-stepover-r30…` (GEMSDOE33) | 0.2632 | 0.0602 |
| **WBG4-SSCC (this lane)** | — | **0.1086** |

**And the honest limitation of that table:** across the 38 rasters the same-fold
DTI and the reported leaderboard score correlate at Spearman **+0.25**, and a
linear calibration has leave-one-out **R² = −0.055**. The holdout metric ranks
*how well a file recovers withheld catalogue faults*; the leaderboard rewards
*finding faults that are not in the catalogue*. Those are different tasks, and
this study measures that they are different. **No point estimate of the
leaderboard score for the new file is therefore defensible.**

A conditional projection can still be stated explicitly: if the new file
recovers the new-fault truth at the same 23–27 % rate the algebra implies for the
0.2778 file, and its extra 76 % of mass behaves like the average collar cell
(`FP` cost 0.2 each), the DTI lands near **0.10–0.20**; if its geophysical
coverage transfers better than the dot family's, it lands near **0.26–0.31**.
That is a projection, not a result.

---

## 5. The emitted file

| Property | Value |
|---|---|
| Name | `wbg4-sscc-blind-66383dots-20261028T170239Z` |
| File | `downloads/wbg4-sscc-blind-66383dots-20261028T170239Z.tif` (+ `.zip`) |
| SHA-256 | `494afc75279346b6d5a43389e62e2932bec29ad8181bb68ac6e34a72cab61d59` |
| Bytes | 263,991 (zip 179,085) |
| Positive cells | 66,383 (1.285 % of footprint); 3,117 components, median 3 px, max 1,440 px |
| Values / dtype | {0, 1} / float32; 0.0 outside the footprint (no NaN anywhere) |
| Grid | EPSG:32611, (3730, 3292), transform matches the official sample |
| Format validation | all 10 checks pass on the saved bytes ([`evidence/wbg4_candidate.json`](../evidence/wbg4_candidate.json)) |

Uniqueness: see [`evidence/wbg4_uniqueness.json`](../evidence/wbg4_uniqueness.json)
and section 6 of the [executive summary](../docs/wbg4/index.html).

---

## 6. Irregularities flagged for review

1. **The official `sample_submission.tif` is not an all-zero template.** It
   carries exactly the 60,988 catalogue positives (values {0, 1, NaN}), whereas
   the problem page describes "a sample submission that predicts total fault
   absence". `labels.tif` and `existing_faults.tif` are byte-identical
   (`7ba308cc…`). Both mirrors are cross-corroborated by an independent
   repository and by our own earlier restore receipt, but **none is
   authenticated against the login-gated organizer download**.
2. **Leaderboard values in every GEMSDOE site are owner-reported.** The only
   organizer-published observation available here is the public leaderboard
   snapshot of 2026-10-28 (top 0.4544, participant `xiaofanhu`).
3. **The catalogue-proximity trap.** A model given "distance to mapped faults"
   scores 0.0156 on a whole-fault holdout while *looking* excellent in-sample.
   Any lane in this project that scores itself by in-sample fit, or by
   random-point holdout, will overstate itself badly.
4. **Fold imbalance.** Fold 0 holds 48 % of the catalogue pixels, so the pooled
   metric is dominated by one quadrant.
5. **The emitted field is a supervised re-detection.** 63.5 % of its cells lie
   within 3 px of the catalogue, where the scorer masks exactly the catalogue
   pixels. Suppressing that collar and re-measuring is the next experiment; it
   was **not** applied here because it was not validated within budget.

---

## 7. Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_wbg4_registry.py        # registry rasters into data/registry (ignored)
.venv/bin/python scripts/run_wbg4_lane.py canaries     # leakage gate (~25 s)
.venv/bin/python scripts/run_wbg4_lane.py folds        # 4 folds, both feature variants (~13 min)
.venv/bin/python scripts/score_registry_folds.py       # matched incumbent baseline (~20 s)
.venv/bin/python scripts/run_wbg4_lane.py final --variant blind   # emit + validate (~6 min)
.venv/bin/python scripts/audit_wbg4_uniqueness.py downloads/<file>.tif
.venv/bin/python scripts/build_wbg4_site.py            # regenerate the executive-summary page
```

Inputs (ignored by Git, hashes pinned in `config/wbg4_lane.json`): `data/labels.tif`,
`data/sample_submission.tif`, `data/external/{lidar_scarp_features,geodawn_rad,
geodawn_extensions,derived_sgmc_faults_100m}_u8.tif`,
`data/external/gdr_wellspring_in_footprint.csv`, `data/acquisition_block_id_100m.tif`.
