# Scientific & Forensic Findings (`WBGGEMSDOE2` — 2026-10-27)

## 1. Evidence Labels Used Throughout This Repository
Per the Parallel-Run Protocol, every numeric figure carries an explicit provenance class:
- **`HOLDOUT-DTI`**: Measured locally on the **unmodified shared evaluator** (`gems57.evaluate_holdout`, `evaluator_version = "gems57-pooled-hide-v2"`, $\alpha=0.2, \beta=0.8$, $R=300\text{ m}$ triangular kernel, `60,988` withheld positive pixels across 4 label-blind spatial quadrants with `8.0 km` / `80 px` spatial buffer, 1,000 paired 20 km spatial-cluster bootstrap draws).
- **`ORGANIZER-CONFIRMED`**: Reserved strictly for an authenticated DrivenData submission receipt (`None` for local candidates — `0` competition slots used).
- **`OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT`**: Official DrivenData public leaderboard top team score (`0.4544` by `xiaofanhu`, verified `2026-10-27T17:15:00Z` via `https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/`). Not a receipt for any repository file.
- **`USER-REPORTED`**: Historical owner/prompt claims across the 144-row multi-repo ledger (`docs/data/user-reported-ledger.csv`); never treated as `ORGANIZER-CONFIRMED` without a portal receipt.

---

## 2. Why `GEMSDOE32` (`h33-h33-2-b2`, `0.2778` User-Reported) Topped the Nine Focus Sites — And Why Later Variants Dropped

Byte-exact inspection across the 9 priority focus champions (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`) and the 2026-10-26/27 sibling updates established an exact raster lineage on the `3730 × 3292` (`5,167,373` in-footprint pixel) EPSG:32611 grid:

1. **`GEMSDOE25` (`dotted-h19-5-d2-8`, `0.2600` user-reported) and `GEMSDOE30` (`d28-poisson300m-offcat-44090`, `0.2600` user-reported) are pixel-for-pixel identical inside the footprint (`44,090` binary dots, `Jaccard = 1.0000`).** Both discretize the `H19-5` multi-line corroborated ridge surface into ~300 m Poisson-spaced dots so adjacent pixels do not double-pay the $\alpha=0.2$ false-positive penalty inside the $R=300\text{ m}$ triangular kernel.
2. **`GEMSDOE32` (`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, `0.2778` user-reported, SHA-256 `c55bafc4...`) is algebraically identical to `GEMSDOE25` minus all `6,436` dots lying within Euclidean distance $\le 2\text{ px}$ ($200\text{ m}$) of `existing_faults.tif`, leaving exactly `37,654` dots (`0` additions, `6,436` removals).**
   - **Mathematical mechanism under DW-Tversky ($\alpha=0.2, \beta=0.8$):** On the DrivenData forum (`t/11516/2`), organizers confirmed that mapped `existing_faults.tif` pixels are masked during scoring, while unmapped continuation/splay truth pixels are evaluated via the 300 m linear distance kernel:
     $$\text{DTI} = \frac{\text{TP}_w}{\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w}.$$
     Dots placed at $d \le 200\text{ m}$ alongside already-mapped fault traces sit inside parallel rasterization/scarp halos where hidden new fault traces are scarce, contributing almost pure $\text{FP}_w$ (`~6,436` units, reducing denominator drag by $0.2 \times 6{,}436 \approx 1{,}287$) while dots at $d \ge 3\text{ px}$ retain nearly full triangular-kernel reach onto genuine off-catalogue fault continuations.
3. **`GEMSDOE36` (`anderson-geothermal-pinn-38854`, `0.2750` user-reported) keeps all `37,654` `GEMSDOE32` dots (`0` removals) and appends `1,200` extra dots (`38,854` total),** slightly diluting precision (`0.2778 -> 0.2750`).
4. **Why 2026-10-20..27 from-scratch models across the 144-entry fleet scored `0.0363 – 0.2478` (below `0.2778`):**
   - Best non-`D2.8` fleet entries: `GEMSDOE70` (`0.2478`), `GEMSDOE76` (`0.2343`), `GEMSDOE36 kpl36-exp3` (`0.2314`), `GEMSDOE27 h29` (`0.2190`), `KANLERGEMSDOE2 htcads-exp-2` (`0.1973`), `GEMSDOE91 s17-lftg` (`0.1823`), `EUGGEMSDOE3` (`0.1782`), `KANLERGEMSDOE1` (`0.1753`), `GEMSDOE28 s21-puhgb` (`0.1628`), `WBGGEMSDOE3 lst1-hybrid` (`0.1597`), `GEMSDOE91 S18-UNIQUE-curvtilt` (`0.1578`).
   - Failure modes observed in lower-scoring 2026-10-26/27 entries:
     - **`WBGGEMSDOE2` `wbg2-h1-stepxasym` (`0.0725` user-reported):** Wrote `nodata = 0.0` (marking `5,132,809 / 5,167,373` interior footprint pixels as missing) and relied on a leaky private evaluator (`0.1321` claimed local DTI without excluding test quadrant pixels from training).
     - **`GEMSDOE33` `s33-seisdil` (`0.0363` user-reported):** Weighted coarse GPS strain/seismicity kernels too heavily without sharp 100 m structural localization.
   - **Can `0.2778` (`GEMSDOE32`) be beaten?** Yes in principle — the live public leaderboard #1 stands at **`0.4544`** (`xiaofanhu`, +`0.1766` above `0.2778`), proving massive headroom exists — **but not by perturbing `D2.8`/`B2`, and no honest projection of live leaderboard DTI can be made without hidden organizer truth.**

---

## 3. Critical GeoDAWN Data Forensic Discovery: Band 6 (`tc`) Is Radiometric Total Counts, Not Tilt Angle

Direct quantile verification across all 19 cached bands (`.cache/features/band-01..19.npy`, `5,167,373` footprint pixels) revealed:
- **Band 6 (`tc`):** `min = 0.088`, `q01 = 7.637`, `median = 18.490`, `q99 = 29.020` (`5,164,300` finite pixels, `0` negative values). While mirror metadata strings called Band 6 `"Tilt angle or total curvature"`, the official DrivenData problem page figure explicitly labels `tc` as **total radiometric counts** from the USGS GeoDAWN airborne gamma-ray survey. Any model assuming Band 6 is a Miller–Singh magnetic tilt angle in $[-\pi/2, \pi/2]$ computes physically invalid features.
- **Bands 10 & 16 (`deq_n100a15`, `ieq_n100a15`):** Extreme heavy-tailed distributions (`deq_n100a15` `median = 622.8`, `q99 = 50,240`; `ieq_n100a15` `median = 755.9`, `q99 = 5,083`), requiring `log1p` compression.

---

## 4. `WBG2-MSPTCD` 3-Experiment Zero-Leakage Campaign Results (`HOLDOUT-DTI`)

All 3 preregistered experiments (`scripts/run_wbg2_msptcd.py`, `src/wbggems/msptcd.py`) were evaluated on the **exact unmodified `gems57.evaluate_holdout` (`gems57-pooled-hide-v2`)** across `gems57.spatial.folds(catalogue, footprint, buffer_px=80)` (`4` label-blind quadrants, `8.0 km` buffer, `0` shared train/truth components, `60,988` total withheld positive pixels, `155` 20-km bootstrap clusters, `1,000` paired draws, runtime `307.4 s`):

### 4.1 Single-Feature Holdout Leakage Canaries (124 Checks = 31 Features × 4 Folds)
- **Result:** **124 / 124 PASSED** (`threshold = 0.90` on symmetric $\max(\text{AUC}, 1-\text{AUC})$).
- **Highest two-sided AUC across all 31 features and 4 folds:** `0.6131` (`tc_radiometric`), followed by `seismic_structural_index` (`0.6086`), `geod_shearrate` (`0.5930`), `det_elev_slope` (`0.5917`), `strain_dilation_ratio` (`0.5874`), `scarp_hessian_ridge_s35` (`0.5776`), and `dip_offset_concordance` (`0.5483`). Full machine receipt: `evidence/wbg2_msptcd_canaries.json`.

### 4.2 Pooled `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `60,988` Withheld Positives)

| Arm | Features & Allocation | Pooled `HOLDOUT-DTI` | 95% Spatial-Block CI | Paired $\Delta\text{DTI}$ vs `CTRL-19B` (95% CI) | Detached-Splay DTI (`11,307` px) |
|---|---|---:|---|---:|---:|
| **`CTRL-19B`** (Control) | 19 raw GeoDAWN bands + Bayes-calibrated `allocate_by_marginal_bar` | **`0.023409`** | `[0.015356, 0.031895]` | Baseline (`0.000000`) | `0.016915` |
| **`EXP-1`** (`MSPTCD-Core`) | +9 tilt-grad, dip-offset concordance, cond flank asymmetry, Hessian scarp & rad residual features (`28` total) | **`0.034975`** | `[0.025587, 0.045475]` | **`+0.011566`** (`[+0.005424, +0.018644]`) | `0.027271` (`+61.2%`) |
| **`EXP-2`** (`MSPTCD-StrainPU`) | +3 active strain/seismicity features (`31` total) + cover-relief inverse-propensity PU weights | **`0.028575`** | `[0.020416, 0.038058]` | `+0.005166` (`[-0.002732, +0.012803]`) | `0.024312` (`+43.7%`) |
| **`EXP-3`** (`MSPTCD-SubmodGreedy`) | Ridge-coherent `0.5 EXP-1 + 0.5 EXP-2` OOF surface + multi-round 300 m submodular `greedy_allocate` | **`0.042554`** | `[0.032059, 0.054765]` | **`+0.019145`** (`[+0.010977, +0.028755]`) | **`0.030799`** (`+82.1%`) |

Key scientific takeaways:
1. **`EXP-1` beats `CTRL-19B` in all 4 spatial quadrants** (`Fold 0: 0.0269 vs 0.0139`, `Fold 1: 0.0464 vs 0.0278`, `Fold 2: 0.0532 vs 0.0452`, `Fold 3: 0.0273 vs 0.0254`) with a paired 95% bootstrap CI `[+0.005424, +0.018644]` strictly above zero, and jumps **+61.2%** on detached unlinked splays ($\ge 400\text{ m}$ from visible faults).
2. **`EXP-3` adds a second statistically significant gain over `EXP-1`** ($\Delta\text{DTI} = +0.007579$, 95% CI `[+0.002982, +0.011954]`), reaching **`0.042554` (`+81.8%` over `CTRL-19B`)**.
3. **Why zero-leakage whole-quadrant `HOLDOUT-DTI` (`0.0426`) is numerically much lower than interleaved/leaderboard DTI (`0.27–0.45`):** Holding out an entire $180\text{ km} \times 160\text{ km}$ quadrant behind an $8\text{ km}$ buffer removes 100% of along-strike fault continuation cues inside that quadrant, testing pure blind geophysical generalization rather than local tip extrapolation.

---

## 5. 21-Raster Novelty Audit & Why Verdict Remains Fail-Closed `negative` (`DO NOT SUBMIT`)

The cross-fitted off-catalogue candidate (`docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif`, `25,594` dots, SHA-256 `fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614`) was audited on both its pre-placement continuous OOF surface and final binary dots against **21 verified rasters**:
- **Genuine novelty vs all 9 priority focus champions (`GEMSDOE24..36`):** Forward 3-px overlap is **`64.45% – 68.06%`** (every single one $\le 70\%$; against `GEMSDOE32` `B2` it is **`64.45%`**, reverse `5.11%`, surface Spearman $\rho = +0.0673$).
- **Genuine novelty vs all 2026-10-26/27 discrete sibling submissions:** `GEMSDOE28_S21` (`36.07%`), `GEMSDOE33_S33` (`48.35%`), `GEMSDOE36_KPL36` (`59.12%`), `KANLERGEMSDOE2_HTCADS` (`53.63%`), `WBGGEMSDOE3_LST1` (`32.92%`), and local `STEPXASYM` (`33.70%`).
- **Why the literal all-registry gate triggers a mandatory `STOP` (`verdict = "negative"`, `ok_to_submit = False`):**
  1. `13GEMSDOE` (`206,574`-dot regular stride-5 calibration lattice) covers `99.8713%` of the footprint within 3 px (`100.00%` forward overlap on our interior ridges, even though Spearman $\rho = -0.0001$).
  2. Full-footprint continuous probability rasters (`17GEMSDOE_dense_prior`, `WBGGEMSDOE1_C1`, `WBGGEMSDOE2_PARALLEL_CONDUIT`) have `value > 0` on 100% of footprint pixels (`100.00%` literal support overlap).
  3. `GEMSDOE27_H31` (`56,161`-dot unpruned halo raster) reaches `78.34%` forward 3-px overlap (`6.48%` reverse, $\rho = +0.0866$).

Per protocol, we **do not exempt or bypass any registry witness**. The generated GeoTIFF and `.zip` are published strictly for **reproducible research and format verification (`DO NOT SUBMIT` to the competition)**.

---

## 6. Root Cause & Automated Prevention of `"Predicted values must be in range [0, 1]"`

DrivenData's scorer rejects uploads with `"Predicted values must be in range [0, 1]"` whenever saved raster bytes contain:
1. Unclipped raw logits, z-scores, Euler weights, or kernel sums ($<0$ or $>1$),
2. `NaN` or `±Inf` values on scored in-footprint pixels (e.g., from division by zero in tilt ratios or unfiltered missing GeoDAWN pixels), or
3. Ambiguous `nodata` metadata (`nodata = 0.0` or mismatched exterior/interior masks).

Our automated pipeline (`gems57.submission_writer.write_submission` + `scripts/validate_submission.py` + `scripts/validate_tif.py`) re-opens the written `.tif` from disk and verifies without human intervention: single-band `float32`, `EPSG:32611`, `3730 × 3292`, `(100, 0, 243350, 0, -100, 4508550)`, `min = 0.0`, `max = 1.0`, `0` NaN, `0` Inf, and `0` masked in-footprint pixels—never silently clipping invalid inputs during validation.
