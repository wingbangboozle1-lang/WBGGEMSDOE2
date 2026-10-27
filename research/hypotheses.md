# Geological Hypotheses & Preregistered Experiment Ranking (`WBGGEMSDOE2`)

Every hypothesis below specifies:
1. **Exact data layers used** (verified against the 19-band GeoDAWN stack and official sources),
2. **Physical signature**,
3. **Why it catches uncatalogued / blind faults**,
4. **Non-fault geological and acquisition mimics**,
5. **How it differs from existing methods in this repo and the 144-entry GEMSDOE fleet**, and
6. **Expected DTI upside vs engineering/compute cost**.

> **Important provenance & channel forensic checks verified before feature design:**
> - **Band 6 (`tc`):** Public mirror strings label Band 6 `"Tilt angle or total curvature"`, whereas the official DrivenData problem page lists GeoDAWN **total radiometric counts (`tc`)**. Direct byte inspection across all `5,164,300` finite footprint pixels shows `q01 = 7.637`, `median = 18.490`, `q99 = 29.020` (strictly positive counts/s, zero negative values), proving Band 6 is airborne gamma-ray total counts rather than a `[-\pi/2, \pi/2]` magnetic tilt angle. True potential-field tilt angles (Miller & Singh, 1994) must therefore be computed directly from vertical and horizontal potential-field derivatives.
> - **Band 15 (`depth_to_base_surf`):** Official competition text describes this layer as *depth to conductive base surface* (mirror notes say *depth to basement*). All transforms below treat Band 15 strictly as an electrical/cover thickness proxy without assuming crystalline basement equivalence.

---

## Ranked Hypotheses (Best Expected `HOLDOUT-DTI` Upside vs Cost First)

| Rank | ID | Hypothesis | Layers Used | Execution Status in `WBGGEMSDOE2` |
|---:|---|---|---|---|
| **1** | **H1** | **Depth-Shifted Potential-Field Tilt & Gravity–Magnetic Discontinuity Concordance** | `rtp` (B2), `tmi_vg` (B9), `iso_grav_anom` (B13), `iso_grav_anom_vg` (B11), `depth_to_base_surf` (B15) | **Executed in `EXP-1` / `EXP-3`** (`+49.4%` to `+81.8%` `HOLDOUT-DTI` over 19-band control) |
| **2** | **H2** | **Cross-Strike Conductive-Flank Asymmetry, Terrain-Normalized Radiometric Edge & Multi-Scale Hessian Scarp Ridges** | `cond_surf` (B17), `depth_to_base_surf` (B15), `tc` (B6), `det_elev` (B12), `det_elev_slope` (B19) | **Executed in `EXP-1` / `EXP-3`** |
| **3** | **H3** | **Active Transtensional Strain-Rate & Log-Microseismicity Structural Conditioning + Cover-Relief PU Debiasing** | `geod_2ndinv` (B4), `geod_shearrate` (B7), `geod_dilaterate` (B8), `deq_n100a15` (B10), `ieq_n100a15` (B16), `det_elev_slope` (B19), `depth_to_base_surf` (B15) | **Executed in `EXP-2` / `EXP-3`** (strongest in Walker Lane Fold 1: `0.0536` vs `0.0278` control) |
| **4** | **H4** | **Bayes-Calibrated 300 m Triangular-Kernel Submodular Greedy Allocation (`MSPTCD-SubmodGreedy`)** | Calibrated OOF probability field from `H1+H2+H3` + `gems57.emit.greedy_allocate` | **Executed in `EXP-3`** (`HOLDOUT-DTI = 0.042554`, paired $\Delta = +0.019145$ vs control) |
| **5** | **H5** | **Catchment-Normalized 1 m LiDAR Drainage Deflection & Airborne Flight-Line Repeatability Veto (External Official Data)** | USGS 3DEP 1 m / 1/3 arc-sec DEM (`1m_DEM_links.csv` in GDR `#1391`) & USGS GeoDAWN flight/tie-line CSVs | **Deferred / Blocked in Sandbox** (official sources verified free & unrestricted; raw tiles not downloadable under sandbox host allowlist) |

---

### Hypothesis H1 — Depth-Shifted Potential-Field Tilt & Gravity–Magnetic Discontinuity Concordance (`Rank #1`, Low–Medium Cost)
- **Exact layers:** `rtp` (Band 2), `tmi_vg` (Band 9), `iso_grav_anom` (Band 13), `iso_grav_anom_vg` (Band 11), `depth_to_base_surf` (Band 15).
- **Physical signature:** Computes true Miller & Singh (1994) potential-field tilt horizontal gradients $|\nabla_h \arctan(\text{VG} / (s|\nabla_h F| + \epsilon))|$ for both RTP magnetics and isostatic gravity (Verduzco et al., 2004), plus a dip-shifted cross-normal concordance $\sqrt{|\nabla_h G|(x)\cdot \max_{s\in\{0,\pm 1\}}|\nabla_h M|(x + s\,\delta(x)\hat{n}_g)}$ with $\delta(x)=\text{clip}(\text{depth\_to\_base\_surf}(x)/200\text{ m}, 0, 4)\text{ px}$ and azimuthal orientation coherence $|\cos 2(\phi_g - \phi_m)|$.
- **Why it catches uncatalogued faults:** Normal and transtensional range-front/intrabasin faults dip $45^\circ\text{–}65^\circ$ beneath Cenozoic valley fill, displacing dense footwall basement from magnetic volcanic/intrusive horizons by $100\text{–}400\text{ m}$ ($1\text{–}4\text{ px}$) downdip while attenuating raw gradient amplitude with burial depth. Ratio-based tilt derivatives equalize shallow and buried fault edge amplitudes, and symmetric $\pm\delta\hat{n}_g$ evaluation remains invariant to reversely magnetized Tertiary volcanics.
- **Non-fault mimics:** Unfaulted pluton/caldera margins, Tertiary feeder dikes, paleochannel paleotopography, and airborne drape clearance steps.
- **How it differs from repo & fleet methods:** Existing fleet entries (`GEMSDOE76`, `GEMSDOE79`, `GEMSDOE91`, `WBGGEMSDOE2` archived `stepxasym`) either treated Band 6 `tc` as a magnetic tilt angle, used unshifted pixelwise gravity×magnetic products that miss dipping contacts, or omitted two-sided remanence polarity invariance.

### Hypothesis H2 — Cross-Strike Conductive-Flank Asymmetry, Terrain-Normalized Radiometric Edge & Multi-Scale Hessian Scarp Ridges (`Rank #2`, Low–Medium Cost)
- **Exact layers:** `cond_surf` (Band 17), `depth_to_base_surf` (Band 15), `tc` (Band 6), `det_elev` (Band 12), `det_elev_slope` (Band 19).
- **Physical signature:** Measures signed lateral conductivity contrast $|\text{cond\_surf}(x+3\hat{n}_d)-\text{cond\_surf}(x-3\hat{n}_d)|/\text{IQR}$ across log-depth steps $|\nabla_h \log(1+\text{depth\_to\_base\_surf})|$, terrain-slope-normalized radiometric horizontal gradient $|\nabla_h \text{tc}|/(1+0.2\,\text{det\_elev\_slope})$, and principal negative Hessian crest curvatures $-\lambda_{\min}(H_\sigma)$ at $\sigma=150\text{ m}$ and $350\text{ m}$.
- **Why it catches uncatalogued faults:** Blind hydrothermal and basin-bounding faults act as cross-strike permeability barriers/conduits—producing smectite clay alteration or saline fluid plumes on one side of a buried structural step, subtle K/U/Th juxtaposition across alluvial fan surfaces, and degraded multi-hundred-meter piedmont scarps missed by 1:24k Quaternary mapping.
- **Non-fault mimics:** Playal evaporite/clay pans, stratigraphic tuff contacts, Pleistocene Lake Lahontan shoreline risers, and aircraft terrain-clearance variations over steep ridges (explicitly damped by the $(1+0.2\,\text{slope})^{-1}$ normalization).
- **How it differs from repo & fleet methods:** Replaces point `cond_surf` values and raw `tc` (previously misread as tilt angle) with cross-strike flank differences across electrical-base normals and slope-damped radiometric edges, avoiding the synthetic placeholder arrays found in the rejected `conduit` script.

### Hypothesis H3 — Active Transtensional Strain-Rate & Log-Microseismicity Conditioning with Relief-Propensity PU Weighting (`Rank #3`, Low Cost)
- **Exact layers:** `geod_2ndinv` (Band 4), `geod_shearrate` (Band 7), `geod_dilaterate` (Band 8), `deq_n100a15` (Band 10), `ieq_n100a15` (Band 16), `det_elev_slope` (Band 19), `depth_to_base_surf` (Band 15).
- **Physical signature:** Computes dilatation-to-strain-invariant ratio $\text{geod\_dilaterate}/(\text{geod\_2ndinv}+1)$, shear-gradient×potential-field edge gating, log-stabilized seismic proximity-intensity $\log(1+\text{ieq})-0.5\log(1+\text{deq})$ (essential because raw `deq_n100a15` has `q99 = 50,240`), and fold-local inverse-propensity positive weights upweighting low-relief/deep-cover mapped faults.
- **Why it catches uncatalogued faults:** Separates Walker Lane right-lateral transtensional transfer zones from central Great Basin dip-slip domains while counteracting geological mapping bias toward exposed range fronts.
- **Non-fault mimics:** Broad GPS interpolation lobes, volcanic/mining seismic swarms, and over-emission inside aseismic playa interiors when cover weights are too aggressive.
- **How it differs from repo & fleet methods:** Unlike `GEMSDOE33` (`s33-seisdil`, `0.0363` user-reported) which emitted on smooth regional strain/seismicity fields directly, H3 gates coarse strain/seismicity strictly through sharp 100–400 m potential-field and scarp edges. Empirical `EXP-2` testing confirmed strong gains in Walker Lane (`Fold 1 DTI = 0.0536` vs `0.0278` control) alongside mild precision dilution in central/eastern quadrants (`Fold 2/3`), motivating the `0.5 EXP-1 + 0.5 EXP-2` blend in `EXP-3`.

### Hypothesis H4 — Bayes Prior-Odds Recalibration + Multi-Round 300 m Submodular Greedy Allocation (`Rank #4`, Low Cost, Direct Metric Optimization)
- **Exact layers:** Fold-calibrated out-of-fold probabilities from `H1+H2+H3` (`31` features) + `gems57.emit.greedy_allocate`.
- **Physical / mathematical signature:** Converts subsampled classifier posteriors ($\pi_s = 0.20$) to true grid fault density ($\pi_0 \approx 0.0118$, estimated strictly on `fold['train']`) via exact Bayes prior-odds recalibration before running iterative Dinkelbach-style greedy 300 m triangular-kernel coverage allocation (`R = 300 m`, $\alpha = 0.2, \beta = 0.8$).
- **Why it improves DTI:** Continuous or dense ridge masks pay an asymmetric $\alpha=0.2$ false-positive penalty on every redundant neighboring pixel inside the 300 m kernel, whereas greedy submodular spacing places isolated kernel centers spaced $\sim 250\text{–}350\text{ m}$ apart so each emitted pixel contributes fresh expected truth coverage $\Delta T(x)$.
- **Mimics / failure modes:** Miscalibrated probability floors over-emit in low-SNR basins; literal registry lattices (`13GEMSDOE`) still block competition promotion at standard dot budgets.
- **How it differs from repo & fleet methods:** Uses exact fold-local Bayes prior recalibration (zero test-fold density tuning) paired with the unmodified `gems57.emit.greedy_allocate` solver.

### Hypothesis H5 — Catchment-Normalized 1 m LiDAR Drainage Deflection & Airborne Flight-Line Repeatability Veto (`Rank #5`, High Cost, External Data Blocked in Sandbox)
- **Exact external official sources verified:**
  1. **USGS 3DEP 1 m LiDAR & 1/3 arc-second seamless DEM** — Official USGS 3DEP documentation (`https://www.usgs.gov/3d-elevation-program/about-3dep-products-services`) confirms public-domain, free availability without use restrictions; DOE GDR Submission `#1391` (`https://gdr.openei.org/submissions/1391`) explicitly distributes `1m_DEM_links.csv` indexing Great Basin 1 m LiDAR tiles.
  2. **USGS GeoDAWN airborne magnetic/radiometric line data** — USGS Data Release (`https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and`, DOI `10.5066/P9X84H76`) provides public-domain flight-line and tie-line survey releases.
- **Physical signature:** Systematic cross-fan stream channel deflections/knickpoints normalized by upstream drainage area (1–10 m DEM) and cross-over repeatability between orthogonal airborne flight and tie lines to reject tie-line leveling striping.
- **Non-fault mimics:** Lake Lahontan wave-cut shorelines, road embankments/canals, lithologic hogbacks, and uneven tie-line spacing.
- **Verification & sandbox status:** Free public availability is verified from official USGS/DOE GDR documentation, **but outbound network rules in this sandbox allow only `github.com` and Python/Node package registries (`usgs.gov` / `prd-tnm.s3.amazonaws.com` tile downloads are blocked)**. Per protocol, H5 is therefore classified as **not executable in this sandbox** rather than simulated or approximated.
