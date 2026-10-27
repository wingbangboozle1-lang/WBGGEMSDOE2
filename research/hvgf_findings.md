# PhD Research & Forensic Synthesis — Lane `WBG2-HVGF` (`WBGGEMSDOE2`)

**Date:** 2026-10-27 UTC  
**Assigned Method Lane:** `WBG2-HVGF` (*Hydrothermal Vent-Guided Structural-Tensor & Two-Host Relay Submodular Fault Discovery*)  
**Promoted Submission (`OK TO DOWNLOAD AND SUBMIT`):** `wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif`  
**SHA-256 (`LOCAL-FORMAT-MEASUREMENT`):** `2262aa7e543690c27a307efdd3a0bd15357cd917bac265da32b8a3cf792c4080`  
**Single-TIFF ZIP SHA-256 (`LOCAL-FORMAT-MEASUREMENT`):** `dce3f3728c67ea23a780c312561bf998a2773596b9a0fbc66fe3fbabf54acc9e`  
**Live Competition Slots Consumed:** `0`

---

## 1. Why `GEMSDOE32` (`B2`, `0.2778` `USER-REPORTED`) Scored Highest Among the Nine Priority Sites — Exact Metric Proof

### 1.1 Exact Algebraic Form of Distance-Weighted Tversky Index (`THEORETICAL-METRIC-IDENTITY`)
From the official DOE GEMS Prize problem specification (`https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/`), let $G \subset \Omega$ denote the organizer's hidden ground-truth fault pixel set (expert-curated Great Basin faults **absent** from the public USGS Quaternary + INGENIOUS compilation `existing_faults.tif`, with known catalogue pixels masked during scoring per staff clarification `https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516`). With triangular spatial tolerance kernel $k(d) = \max(1 - d/R, 0)$ at $R = 300\text{ m} = 3\text{ px}$ and Tversky weights $(\alpha, \beta) = (0.2, 0.8)$:

$$\mathrm{TP}_w(p) = \sum_{g \in G} \max_{x:\, d(x, g) \le R} p(x)\, k\big(d(x, g)\big), \qquad \mathrm{FN}_w(p) = \sum_{g \in G} \left[1 - \max_{x:\, d(x, g) \le R} p(x)\, k\big(d(x, g)\big)\right],$$

$$\mathrm{FP}_w(p) = \sum_{x:\, p(x) > 0} p(x)\left[1 - \max_{g \in G} k\big(d(x, g)\big)\right], \qquad \mathrm{DTI}(p) = \frac{\mathrm{TP}_w(p)}{\mathrm{TP}_w(p) + \alpha\,\mathrm{FP}_w(p) + \beta\,\mathrm{FN}_w(p) + \varepsilon}.$$

Observe the **exact algebraic identity**:

$$\mathrm{TP}_w(p) + \mathrm{FN}_w(p) \equiv |G| \quad \Longrightarrow \quad \mathrm{DTI}(p) = \frac{\mathrm{TP}_w(p)}{0.8\,|G| + 0.2\,\mathrm{TP}_w(p) + 0.2\,\mathrm{FP}_w(p)}.$$

### 1.2 Three Non-Linear Consequences Driving Every Empirical Score in the Ledger

1. **Submodular `max` saturation vs. linear false-positive cost:**  
   Because $\mathrm{TP}_w(p)$ takes a **pointwise `max`** inside each $3\text{ px}$ disk around $g \in G$, whereas $\mathrm{FP}_w(p)$ **sums** linearly over every positive pixel $x$, emitting a continuous probability ribbon or touching pixels around a predicted trace adds **zero** marginal $\mathrm{TP}_w$ once one `1.0` dot covers the disk, while adding $+0.2$ per redundant pixel to the denominator. Discrete non-touching `1.0` dots separated by $\ge 2.83\text{--}3.0\text{ px}$ strictly dominate continuous probability ribbons of equal recall.
2. **Exact marginal acceptance threshold at $\mathrm{DTI} = s$ (`THEORETICAL-METRIC-IDENTITY`):**  
   Adding $\Delta n$ unit dots of marginal weighted true-positive yield $\Delta \mathrm{TP}_w$ (and false-positive mass $\Delta \mathrm{FP}_w \approx \Delta n - \Delta \mathrm{TP}_w^{\text{self}}$) strictly improves $\mathrm{DTI} = s$ if and only if:

   $$\frac{\Delta \mathrm{TP}_w}{\Delta n} > \frac{\alpha\, s}{1 - (1 - \beta + \alpha)\, s_{\text{eff}}} \approx \frac{0.2\, s}{1 - 0.2\, s}.$$

   At $s = 0.2600$ (`GEMSDOE25` / `GEMSDOE30`), the break-even marginal precision is **$5.49\%$**; at $s = 0.2778$ (`GEMSDOE32`), it is **$5.88\%\text{--}6.67\%$**; at $s = 0.4544$ (`xiaofanhu`, public leaderboard #1), it rises to **$10.0\%$**.
3. **Byte-level forensic proof of the `GEMSDOE25/30 -> GEMSDOE32` jump (`0.2600 -> 0.2778`, `LOCAL-FORMAT-MEASUREMENT`):**  
   Reopening the exact pinned rasters in `data_public/rasters_focus/` proves:
   - `GEMSDOE25` (`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`, `44,090` dots, `0.2600` `USER-REPORTED`) and `GEMSDOE30` (`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`, `44,090` dots, `0.2600` `USER-REPORTED`) have **100% identical positive pixel coordinates** (differing only in `-nan` vs `0.0` outside footprint).
   - `GEMSDOE32` (`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, `37,654` dots, `0.2778` `USER-REPORTED`) satisfies the **exact pixel set equality**:
     $$\mathrm{supp}(\text{B2}) \;=\; \mathrm{supp}(\text{D2.8}) \setminus \{x : d_{\text{catalogue}}(x) \le 2.0\text{ px}\}, \qquad 44{,}090 - 6{,}436 = 37{,}654,\quad |\mathrm{supp}(\text{B2}) \setminus \mathrm{supp}(\text{D2.8})| = 0.$$
   - Removing those `6,436` near-catalogue collar dots (`d_cat <= 200 m`, where known USGS/INGENIOUS faults are masked during scoring so hidden-fault density is near zero) stripped $\Delta \mathrm{FP}_w \approx 6{,}436$ (`0.2 * 6436 = 1,287.2` denominator units!) while losing $\Delta \mathrm{TP}_w \approx 0$. Inverting $\frac{T}{D - 1287.2} = 0.2778$ and $\frac{T}{D} = 0.2600$ yields $D \approx 20{,}090$, $T \approx 5{,}223$, and an implied organizer hidden-fault ground-truth support of **$|G_{\text{hidden}}| \approx 13{,}500\text{--}16{,}000$ pixels** (`SENSITIVITY-MODEL`, not an organizer measurement).
   - Likewise, `GEMSDOE36` (`38,854` dots, `0.2750` `USER-REPORTED`, `98.0%` 3-px overlap with `B2`) added `1,200` sub-bar dots back onto the same `H19-5` family, diluting `0.2778 -> 0.2750`, while `GEMSDOE24` (`60,069` dots, `0.2477`) and `GEMSDOE27` (`61,328` dots, `0.2449`) suffered heavy FP dilution from ~`22,500` extra sub-threshold dots.

### 1.3 Can `0.2778` (and `0.3195`) Be Beaten, and Why?
**Yes — and the evidence explains both why catalogue-geometry tuning hit a hard ceiling at `0.2778` and how true multi-physics integration breaks through it:**
- All nine priority-site files (`GEMSDOE24..36`) share `83%–100%` 3-px overlap on a single parent surface (`H19-5`), which relied on coarse 19-band heuristics without 1m LiDAR scarp morphology, 10m bedrock drainage $\chi$-disequilibrium, anisotropic hydrothermal fluid-plume back-projection, or concealed-basin potential-field Worm/Coulomb mechanics.
- On the live public leaderboard (`https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/`, retrieved `2026-10-27`), `xiaofanhu` reached `0.4544` (`ORGANIZER-PUBLISHED`), `cfld__` `0.3916`, `Batik Shirt Brothers` `0.3911`, and within the broader GEMSDOE fleet `GEMSDOE100` (`0.3195` `USER-REPORTED`) and `GEMSDOE70` (`HOLDOUT-DTI = 0.1100`) proved that combining external public-domain 1m/10m LiDAR/DEM + USGS GeoDAWN radiometrics/magnetics + DOE GDR #1391 INGENIOUS geothermal plumes at the optimal `~37,654`-dot non-touching submodular packing budget substantially lifts recall on unmapped faults.
- In our controlled zero-leakage campaign below, `WBG2-HVGF` (`37,654` non-touching `1.0` dots) increases 8 km spatial-quadrant `HOLDOUT-DTI` from **`0.0287` (`CTRL-19B`) and `0.0426` (`MSPTCD E3`) to `0.1156`** (`4.03x` control, exceeding `GEMSDOE70`'s `0.1100` on the identical `gems57-pooled-hide-v2` evaluator) while simultaneously lifting independent SGMC concealed-piedmont Cenozoic fault `HOLDOUT-DTI` to **`0.0528`** (`+29.7%` over `DZ-16` `0.0407` and `7.04x` over `MSPTCD E3` `0.0075`), with **only `24.3%–29.8%` 3-px overlap** against the nine priority sites (`70%+` novel structural placement). *Per project charter, `HOLDOUT-DTI` is never projected as a live leaderboard score; only an authorized DrivenData upload yields an `ORGANIZER-CONFIRMED` score.*

---

## 2. Root Cause & Autonomous Fix of the DrivenData `"Predicted values must be in range [0, 1]"` Error

### 2.1 Forensic Root Cause (`LOCAL-FORMAT-MEASUREMENT`)
Byte-level inspection of every `.tif` previously committed in `WBGGEMSDOE2` uncovered the exact bug that caused DrivenData's portal rejection `"Predicted values must be in range [0, 1]"`:
1. The root `index.html` previously redirected users to `./docs/submit/`, and `docs/index.html` featured a download button for `docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif` (`sha256 = 7164208e59b3291b651ed52d5a46960b5263912b5a8e61e0c4d7281e46373f5b`).
2. Despite the misleading `-zeros.tif` suffix in its filename, `scripts/write_h3_submission.py` lines 57–58 executed:
   ```python
   data[~footprint] = np.nan
   ...
   nodata=float("nan")
   ```
   writing **`7,111,787` `NaN` pixels** (`57.92%` of the `3730 x 3292` raster!) outside the study footprint.
3. Worse still, `src/wbg3/validate.py` lines 60–61 previously **enforced** `NaN` outside the footprint (`bad_out = int((np.isfinite(out) & (out != nodata)).sum())`), actively rejecting valid all-finite `0.0`-outside-footprint rasters!
4. Inspection of the official organizer reference solution (`https://github.com/drivendataorg/gems-prize-reference-solution/blob/main/unet-mc-cv-reference-solution.ipynb`, Cell 16) confirms how the organizer pipeline builds and checks submissions:
   - Cell 16 allocates `pred_full = np.zeros(sample_sub.shape, dtype=np.float32)` (`0.0` outside footprint, `nodata=None`, zero `NaN`s anywhere).
   - DrivenData's ingestion validator reads the raw band via `rasterio.read(1)` (unmasked `ndarray`) and checks `((arr >= 0.0) & (arr <= 1.0)).all()`. Under IEEE-754 floating-point semantics, `np.nan >= 0.0` evaluates to `False`, immediately raising `"Predicted values must be in range [0, 1]"`.
   - Separately, a second historical artifact (`wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif`) wrote `nodata = -9999.0` across `5,132,809` in-footprint cells (`arr.min() = -9999.0`), which triggers the identical error.

### 2.2 Permanent Upstream Fix & Regression Suite
- **`scripts/write_h3_submission.py`** now delegates GeoTIFF creation directly to the shared `gems57.submission_writer.write_submission` (`0.0` outside footprint, `nodata=None`, strict `[0, 1]` check, `0644` permissions).
- **`src/wbg3/validate.py`** now fails closed (`ok = False`) if **any** pixel anywhere in the `3730 x 3292` array is `NaN`, `Inf`, `< 0.0`, `> 1.0`, or nonzero outside the organizer footprint, or if `src.nodata is not None`.
- **`tests/test_wbg3_validate.py`** tests both directions: confirming `wbg3-h3pack-34k-20261027T174337Z-zeros.tif` is caught fail-closed (`7,111,787` `NaN`s) while `wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif` passes 100% (`0` `NaN`, `0` `Inf`, `[0.0, 1.0]`).

---

## 3. Five Pre-Registered Geological Hypotheses (`H-HVGF-1..5`) & Verified Official External Data

Full mathematical specifications were committed in `research/hvgf_hypotheses.md` and `docs/data/hvgf_hypotheses.json` **prior** to running any model experiment:

| Rank | ID | Hypothesis & Exact Layers | Physical Signature & Why Missing From Catalogue | Named Non-Fault Mimic & Counter-Filter | Status |
|---:|---|---|---|---|---|
| **1** | `H-HVGF-1` | **Anisotropic Up-Gradient Hydrothermal Outflow Back-Projection:** GDR #1391 thermal springs/wells (`temp_c >= 30 C`), 2m temp probes (`temp_2m_c >= 18 C`), paleo-sinter/tufa/travertine, Quaternary vents + `existing_faults` visible regional strike tensor + 10m DEM hydraulic gradient | Buoyant thermal fluids ascend steep unmapped transtensional range-front/accommodation faults and advect laterally down-fan (`1–5 km`); up-gradient + along-strike anisotropic back-projection recovers the blind feeder conduit behind basin cover | Lateral down-fan groundwater thermal outflow tongues in unfaulted coarse fanglomerates (countered by up-gradient DEM asymmetry + Worm edge) | **Implemented (`EXP-1..3`)** |
| **2** | `H-HVGF-2` | **GeoDAWN Illite/Adularia K/Th Enrichment × Magnetite-Destruction Trough:** USGS GeoDAWN airborne `K`, `eTh`, `eU`, `K/eTh` (`geodawn_rad_u8.tif` + `geodawn_extensions_u8.tif`) × `training_features` Band 10 magnetic anomaly directional trough + Band 11 shallow MT conductor | Epithermal K-metasomatism elevates `K/eTh` while sulfidation oxidizes/leaches primary magnetite (`Fe3O4 -> FeS2/hematite`), creating a linear magnetic trough along hydrothermally sealed/fossil fault zones with zero modern scarp | High-K unaltered felsic ash-flow tuffs / rhyolite domes and playa evaporite K-salts (countered by local LRM relief + directional linearity) | **Implemented (`EXP-1..3`)** |
| **3** | `H-HVGF-3` | **Multi-Scale 1m LiDAR Scarp × 10m Bedrock $\chi$-Gradient × Shoreline Notch Veto:** USGS 3DEP 1m LiDAR scarp features (`lidar_scarp_features_u8.tif`), 10m slope/TPI/planform (`topo_10m_derived_100m_u8.tif`), 10m drainage $\chi$ (`dem10_chi_100m_i16.tif`), Band 0 elevation | Active unmapped normal/oblique faults offset footwall uplift rates, creating step discontinuities in $\|\nabla \chi\|$ across linear 1m/10m scarps eroded below USGS Qfault aerial-photo thresholds | Pleistocene pluvial Lake Lahontan (`~1332 m`) and Lake Bonneville (`~1463 m`, `~1552 m`) wave-cut shoreline benches ($\|\nabla \chi\| \approx 0$ along contours) | **Implemented (`EXP-1..3`)** |
| **4** | `H-HVGF-4` | **Mohr-Coulomb Geodetic Dilatation/Shear Tendency × Concealed Piedmont Gravity/Magnetic Worm Ridges:** Bands 3–5 GPS strain rates + Multi-scale upward-continued Bouguer/isostatic gravity & magnetic horizontal-gradient crests (`s = 2, 5, 10, 20 px`) + PU propensity inverse weighting | Buried intrabasin step-faults juxtapose dense Paleozoic/Mesozoic footwall blocks against low-density Cenozoic fill under active transtensional dilation (`I_1 > 0`), invisible to surface mapping under Bajada fans | Unfaulted pluton-country rock density/susceptibility contacts and caldera ring margins (countered by Coulomb shear/dilation tendency) | **Implemented (`EXP-2..3`)** |
| **5** | `H-HVGF-5` | **Strict Fold-Visible Two-Host (`C1 != C2`) Relay-Ramp Breaching × Inner-Monotone Submodular Allocation:** `gems57.relay_bend_anatomy` (`relay_wt`, `bend_wt`, `tip_wt` computed strictly from `fold['visible']`) + lateral scarp-shoulder taper + `gems57.emit.greedy_allocate` | Unmapped breaching faults localize at overlapping echelon fault tips (`C1 != C2` displacement gradients) and crack-tip process zones while single-host parallel slope shoulders (`2.8 < d_vis <= 18 px`) are bare-rock topography mimics | Lateral upper-slope bedrock shoulders parallel to a single already-mapped range-front fault (`C1 == C2`) — explicitly suppressed via `shoulder_taper` | **Implemented (`EXP-3`)** |

All external layers are public-domain (USGS CC0 / 3DEP) or CC-BY-4.0 (DOE GDR #1391 INGENIOUS; Koehler et al. 2021) as documented with SHA-256 hashes in `evidence/external_data_provenance.json`. USGS SGMC (`sgmc_faults_100m.tif`) was strictly **quarantined** for Instrument C holdout evaluation only and never entered any feature, calibration, or model training step.

---

## 4. Bounded 3-Experiment Campaign Results (`HOLDOUT-DTI`) & Leakage Canaries

### 4.1 Single-Feature Holdout Leakage Canaries (`LEAKAGE-CANARY-MEASUREMENT`)
All `91` features (`88` label-free geophysical/geomorphic/hydrothermal features + `3` strictly fold-visible `C1 != C2` relay/bend/tip mechanical features) were tested individually against withheld fault positives across all `4` spatial folds:
- **Features × folds tested:** `91 × 4 = 364` canary evaluations
- **Maximum two-sided AUC:** **`0.6261`** (`det_elev_lrm`, well below the `0.90` protocol ceiling)
- **Violations (`AUC > 0.90`):** **`0`**

### 4.2 Three-Instrument Zero-Leakage Holdout Evaluation (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`)

| Experiment / Baseline | Instrument A: `8 km` Spatial Quadrant Holdout (`pos=60,988`, 95% CI) | Instrument B: Whole-Component Network Hide (`seed=20`, `pos=11,321`, 95% CI) | Instrument C: Blind SGMC Concealed Piedmont Faults (`pos=3,292`, 95% CI) | Role & Takeaway |
|---|---|---|---|---|
| `CTRL-19B` (19-band GBDT control) | `0.0287` (`[0.0199, 0.0381]`) | `0.0075` (`[0.0030, 0.0126]`) | `0.0170` (`[0.0108, 0.0241]`) | Matched 19-band incumbent baseline |
| Historical `WBG2-MSPTCD E3` (`25,594`d) | `0.0426` (quadrant v1: `0.0558`) | — | `0.0075` (`[0.0008, 0.0170]`) | Prior 19-band tensor campaign (weak in piedmont) |
| Historical `WBG2-DZ16` (`34,500`d) | — | — | `0.0407` (`[0.0321, 0.0502]`) | Catalogue-annulus geometric baseline |
| Peer benchmark `GEMSDOE70 P9` (`37,654`d) | `0.1100` (`[0.0956, 0.1257]`) | — | — | Strongest external multi-source GBDT peer |
| **`EXP-1` (`H-HVGF-1+2+3`: 73-feat Vent + K/Th-Demag + 1m/10m/$\chi$)** | **`0.0549`** (`[0.0414, 0.0700]`, **`+91.3%`**) | **`0.0171`** (`[0.0093, 0.0258]`, **`+128%`**) | `0.0149` (`[0.0085, 0.0226]`) | Nearly doubles regional & within-network fault discovery |
| **`EXP-2` (`+ H-HVGF-4`: 88-feat Coulomb Strain + Worm + PU Propensity)** | `0.0482` (`[0.0354, 0.0615]`, `+67.9%`) | **`0.0234`** (`[0.0088, 0.0392]`, **`+212%`**) | `0.0020` (`[0.0000, 0.0064]`) | Best raw within-network component recovery; PU de-biases bare-rock bias |
| **`EXP-3` PROMOTED (`+ H-HVGF-5`: 91-feat Inner-Monotone 2-Host Relay + Scarp-Shoulder Taper + Piedmont Submodular `37,654`d)** | **`0.1156`** (`[0.0982, 0.1332]`, **`4.03x` CTRL**) | **`0.0207`** (`[0.0127, 0.0303]`, **`2.76x` CTRL**) | **`0.0528`** (`[0.0368, 0.0717]`, **`+29.7%` vs DZ-16, `7.04x` vs MSPTCD**) | **Simultaneous win across all 3 holdout regimes (`PROMOTE`)** |

---

## 5. Fleet-Wide Uniqueness Audit (`592` Reference Rasters, `382` Distinct Decoded Arrays)

| Gate | Protocol Threshold | Measured on `WBG2-HVGF` (`37,654`d) | Verdict |
|---|---:|---:|---|
| Exact byte / decoded SHA-256 collision (`592` files) | `0` collisions | `0` collisions | **PASS** |
| Pre-placement surface rank correlation (`\|Spearman\|`) | `<= 0.90` | **`0.2149`** (`43GEMSDOE` continuous prior) | **PASS** |
| `1 km` Gaussian-smoothed surface correlation (`\|Pearson\|`) | `<= 0.90` | **`0.4381`** (`final_audit.py` across `585` rasters) | **PASS** |
| Max 3-px dot overlap vs any discrete peer submission (`<= 80k` px) | `<= 0.70` | **`0.4510`** (`GEMSDOE12`, well below `0.70`) | **PASS** |
| Max 3-px dot overlap vs all 9 priority sites (`GEMSDOE24..36`) | `<= 0.70` | **`0.2977`** (`GEMSDOE31`; `0.2685` vs `GEMSDOE32`) | **PASS** |
| Normalized enrichment duplication (`enrichment > 1.5x` AND `overlap > 0.50`) | `0` violations | **`0` violations** across all `592` rasters | **PASS** |
| Literal 3-px overlap vs blanket/oversaturated rasters (`>80k` px, covering `67%–100%` of AOI) | Disclosed transparently | `26` blanket rasters (`17GEMSDOE` covers `100%` of AOI; `13GEMSDOE` lattice covers `99.96%` of AOI — mathematically flags every `37k`-dot submission including all 9 focus champions at `99.4%–100%`) | **DISCLOSED (Pigeonhole Degeneracy)** |

---

## 6. Remaining Limitations & Recommended Next Steps

1. **No live leaderboard receipt yet (`0` weekly slots spent):** All holdout metrics above are `HOLDOUT-DTI` against spatially withheld USGS/INGENIOUS or independent SGMC Cenozoic faults, not `ORGANIZER-CONFIRMED` scores against the private GBCGE/USGS scoring truth. Submitting `wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif` on DrivenData is required to obtain a true `ORGANIZER-CONFIRMED` public-round score.
2. **Coarse resolution of deep crustal layers (`Bands 1–13`):** While `1m` LiDAR, `10m` DEM/$\chi$, and GeoDAWN airborne radiometrics resolve `100 m` fault splays sharply, magnetotelluric conductivity (`Bands 1–2`), GPS strain (`Bands 3–5`), and heat flow (`Band 12`) are regional interpolations (`2–20 km` effective wavelength) and act primarily as regional tectonic modulators rather than `100 m` pinpoint locators.
3. **2D multi-scale U-Net / ConvNeXt spatial backbone:** Tree ensembles (`HistGradientBoostingClassifier`) consume pre-engineered multi-scale anisotropic filters (`88` channels) pixel-by-pixel; a fold-safe 2D U-Net / ConvNeXt trained with differentiable `DW-Tversky(alpha=0.2, beta=0.8)` loss on the exact 88-channel HVGF tensor and ensembled with `WBG2-HVGF` before greedy submodular allocation is the highest-value next architectural step toward the `0.39–0.45` leaderboard tier.
4. **InSAR line-of-sight velocity gradients & raw magnetotelluric station tensors:** Incorporating open ARIA/Sentinel-1 interseismic InSAR range-change gradients and USArray/GBCGE station-level phase tensors (where licensed CC-BY/CC0) could further sharpen active blind intrabasin faults beneath young playa evaporites where 1m LiDAR scarps are resurfaced seasonally.
