# WBG2-GVCD Preregistered Geological Hypotheses (`GVCD-H1` through `GVCD-H5`)

**Lane:** `WBG2-GVCD` (Geothermal-Vent Conduit, Axial Stress-Dilation & 100% Spatial-OOF Dual-Regime Synthesis)  
**Machine-readable preregistration:** [`config/gvcd_hypotheses.json`](../config/gvcd_hypotheses.json)  
**Holdout protocol:** `gems57-pooled-hide-v2` (`60,988` withheld fault pixels across 4 whole-segment `8.0 km`-buffered spatial folds, $\alpha=0.2, \beta=0.8$, 300 m triangular kernel, single-feature leakage canary threshold $\text{AUC} \le 0.90$)  
**Budget discipline:** Preregistered prior to training; strictly capped at $\le 3$ holdout experiments (`GVCD-EXP1`, `GVCD-EXP2`, `GVCD-EXP3`) and `0` weekly submission slots consumed.

---

## Executive Rationale: Why Geothermal-Vent Conduit & Blind Subsurface Physics?

Byte-level forensic analysis of the prior `WBGGEMSDOE2` campaigns (`CTRL-19B`, `WBG2-MSPTCD`, `H3-BLIND`, `WBG2-DPHS`) and all `499` verified GeoTIFFs across the 8 GitHub organizations in the prompt ledger revealed two structural bottlenecks:

1. **In-Sample Range-Front Memorization (`DPHS EXP-3` Failure Mode):** `existing_faults.tif` (`60,988` pixels) is strongly enriched along steep (`> 8°`) exposed bedrock range fronts where 1:24,000–1:250,000 USGS/INGENIOUS airphoto mapping is already near-complete. Refitting tree ensembles in-sample (`55%` weight in `DPHS EXP-3`) starved concealed alluvial/piedmont basins (`frac_gt_32px = 3.64%`) and triggered `45` discrete 3-px overlap violations (`max = 95.87%` vs `GEMSDOE12`).
2. **Missing Blind Geothermal-Vent Feeder Physics:** Roughly `75%` of Great Basin geothermal systems are *blind* (no surface hot spring or travertine mound; Faulds & Hinz, 2015, World Geothermal Congress), fed by concealed fault stepovers, intersections, and dilatant fault tips beneath Quaternary play-fairway cover where surface LiDAR scarps have been buried by Holocene fan aggradation or reworked by Pleistocene Lake Lahontan/Bonneville shorelines.

To discover these uncatalogued geothermal-hosting faults without collapsing onto exposed range-front topography, we preregistered five novel candidate hypotheses (`GVCD-H1..H5`), ranked below by expected spatially blocked `HOLDOUT-DTI` improvement and implementation cost.

---

## Ranked Candidate Geological Hypotheses

### Rank 1 — `GVCD-H1`: Geothermal-Vent Structural Conduit Coupling (Deep Well Heat-Flow + Quaternary Volcanics + Smectite Clay-Cap + Tilt-Edge Intersection)
- **Specific Layers Involved:**
  - `usgs_heat_flow_wells_epsg32611.csv` (`1,546` USGS borehole temperature-gradient & heat-flow wells; SHA-256 `9773bf5924f0c5f4...`, official source: [USGS Great Basin Heat Flow](https://www.usgs.gov/centers/gmeg) / [SMU Geothermal Lab via DOE GDR #1391](https://gdr.openei.org/submissions/1391))
  - `derived_gdr_volcanics_100m_u8.tif` (DOE GDR #1391 INGENIOUS Quaternary–Neogene volcanic vent & dike compilation on the exact `EPSG:32611` 100 m grid; SHA-256 `c219bd64617954b1...`, official source: [DOE GDR Submission #1391](https://gdr.openei.org/submissions/1391))
  - `gdr_1391_geothermal_points.csv` (INGENIOUS thermal springs & wells with `dist_known_fault_px` stripped prior to ingestion)
  - Official GeoDAWN `training_features.tif` Bands `2` (`isostatic_grav`), `3` (`mag`), `5–8` (`tc`, `k`, `u`, `th`), `15` (`depth_to_base_surf`), `16` (`heatflow`), and `17` (`cond_surf`)
- **Targeted Physical Signature:** Multiplicative structural-upflow coupling index (`vent_structural_conduit_ridge`, `vent_claycap_demag_coupling`, `volcanic_dike_edge_grad`) combining:
  1. Excess conductive borehole heat-flow residuals (`well mW/m² > regional P65` kernel-interpolated at `2.5 km` / `6.0 km` scales),
  2. Quaternary–Neogene volcanic vent/dike perimeter gradients (`|\nabla V_{\text{GDR}}|` smoothed at `600 m`),
  3. Shallow magnetotelluric smectite clay-cap conductivity (`cond_surf`) co-located with epithermal K-metasomatism (`K/Th`) and hydrothermal magnetite destruction (`RTP` magnetic trough), gated by
  4. Potential-field structural contact edges (`cos(|tilt_grav|)` and `cos(|tilt_mag|)` near zero-crossings).
- **Why It Catches Faults Missing from the USGS/INGENIOUS Catalogue:** Blind geothermal upflow zones (`75%` of Great Basin systems) occur along concealed accommodation zones, fault terminations, and buried range-front stepovers beneath `50–800 m` of unconsolidated basin fill where zero surface scarp survives. Conductive thermal plumes in shallow temperature-gradient wells, shallow MT smectite alteration caps, and Quaternary dike/vent alignments directly illuminate the permeable blind fault conduit from below.
- **Named Non-Fault Mimic & Countermeasure:**
  - *Mimic:* Lateral outflow plumes in permeable alluvial fan aquifers (warm water migrating `2–5 km` down-gradient from a range-front fault) and conductive saline playa evaporite pans (`cond_surf` sheets without structural offset).
  - *Countermeasure:* Multiply thermal/clay-cap anomalies by potential-field tilt-zero structural contact sharpness and depth-to-basement step gradients so flat evaporite pans and un-faulted lateral outflow sheets collapse toward zero.
- **How It Differs from Existing Repo Implementations:** Neither `WBG2-MSPTCD` (19 official bands only) nor `WBG2-DPHS` (`60` features) ingested `usgs_heat_flow_wells_epsg32611.csv` (`1,546` heat-flow boreholes) or `derived_gdr_volcanics_100m_u8.tif` (GDR #1391 volcanic vent/dike map), nor did either formulate a multiplicative geothermal-vent $\times$ clay-cap $\times$ potential-field contact ridge index.
- **Expected `HOLDOUT-DTI` Gain & Cost:** `+0.0010 .. +0.0030` pooled `HOLDOUT-DTI` (higher on concealed basin faults) · **Low cost** (`~18 s` vectorized NumPy/SciPy).

---

### Rank 2 — `GVCD-H2`: Regional $S_{h\min}$ Axial Stress-Resolved Potential-Field Dilation & Slip Tendency (`Morris et al., 1996`)
- **Specific Layers Involved:**
  - `gb_regional_stress_grid_10km.csv` (`999` 10-km regional minimum horizontal stress azimuth $\theta_{S_{h\min}}$ blocks across the Great Basin; SHA-256 `9e01d5deb013d920...`, official source: [World Stress Map](https://www.worldstressmap.org/) / [USGS Lund & Townend Great Basin Stress inversions](https://www.usgs.gov/programs/earthquake-hazards))
  - Official GeoDAWN `training_features.tif` Bands `2` (`isostatic_grav`), `3` (`mag`), `18` (`strain_2nd_inv`), and `19` (`dilation_rate`)
- **Targeted Physical Signature:** Branch-cut-free $180^\circ$-periodic axial resolved dilation tendency $T_d$ (`stress_grav_dilation_tendency`, `stress_mag_dilation_tendency`, `transtensional_shear_dilation_product`) on potential-field structural strikes. On the north-up `EPSG:32611` raster (`+col` East $g_x$, `+row` South $g_y$), a buried fault step's geographic strike tangent is $(t_E, t_N) = (g_y, g_x)$, giving exact double-angle components:
  $$\cos(2\theta_{\text{strike}}) = \frac{g_x^2 - g_y^2}{g_x^2 + g_y^2 + \varepsilon}, \qquad \sin(2\theta_{\text{strike}}) = \frac{2 g_x g_y}{g_x^2 + g_y^2 + \varepsilon}$$
  and tensile normal-opening tendency relative to local $S_{h\min}$ azimuth $\theta_{S_{h\min}}$ (measured clockwise from North):
  $$T_d = \frac{1}{2}\Bigl(1 - \cos\bigl(2(\theta_{\text{strike}} - \theta_{S_{h\min}})\bigr)\Bigr) = \sin^2(\theta_{\text{strike}} - \theta_{S_{h\min}}) \in [0, 1]$$
  weighted by normalized potential-field horizontal gradient magnitude and geodetic transtensional strain rate.
- **Why It Catches Faults Missing from the USGS/INGENIOUS Catalogue:** Pre-Cenozoic thrust ramps, pluton margins, and caldera ring contacts produce strong gravity/magnetic gradients (`|\nabla g|, |\nabla M|`) even when tectonically dead and sealed. Conversely, NNE-striking normal faults perpendicular to WNW–ESE $S_{h\min}$ ($\theta_{\text{strike}} - \theta_{S_{h\min}} \approx 90^\circ \Rightarrow T_d \approx 1$) experience active tensile aperture dilation and host concealed geothermal fluid flow beneath young basin fill.
- **Named Non-Fault Mimic & Countermeasure:**
  - *Mimic:* Mesozoic contractional thrust contacts, paleochannel edges, or Miocene volcanic flow lobes whose strike runs parallel to $S_{h\min}$ ($T_d \approx 0$).
  - *Countermeasure:* Suppresses unfavorably oriented contacts via $\sin^2(\theta_{\text{strike}} - \theta_{S_{h\min}})$ and couples $T_d$ with geodetic `strain_2nd_inv * max(0, dilation_rate)`.
- **How It Differs from Existing Repo Implementations:** `WBG2-MSPTCD` measured *inter-band* gradient alignment (`cos^2(theta_grav - theta_mag)`) without any regional stress field; `WBG2-DPHS` used isotropic gradient magnitudes without $\theta_{S_{h\min}}$. `WBG2-GVCD` is the first lane in `WBGGEMSDOE2` to resolve buried potential-field strike tensors onto spatially varying Great Basin $S_{h\min}$ stress trajectories.
- **Expected `HOLDOUT-DTI` Gain & Cost:** `+0.0008 .. +0.0025` pooled `HOLDOUT-DTI` · **Low cost** (`~12 s`).

---

### Rank 3 — `GVCD-H3`: Dual-Regime Slope-Deconfounded Subsurface Specialist + 100% Spatial-OOF Probability Calibration
- **Specific Layers Involved:**
  - Strict **60-feature Subsurface + Geothermal-Vent Specialist subset** (`SUBSURFACE_VENT_INDICES` in `src/wbggems/gvcd.py`) that **completely excludes all 12 raw topographic slope/relief/scarp features** (`det_elev`, `det_elev_slope`, `dem1m_*`, `dem10_*`), blended with the 72-feature multi-sensor ensemble (`clf_deep` + `clf_reg`) via fold-internal isotonic probability calibration (`IsotonicRegression`) and label-free piedmont cover gating (`compute_piedmont_concealed_gate` from `det_elev_slope` and `depth_to_base_surf`).
  - **100% Spatial Out-of-Fold (`OOF`) Full-Map Inference (`0%` In-Sample Refit):** Because the 4 `gems57-pooled-hide-v2` `fold["region"]` blocks partition `100.000%` of the `5,167,373` footprint pixels and each `fold["train"]` mask is buffered by $\ge 8.0\text{ km}$ (`80 px`) from `fold["region"]`, stitched OOF predictions evaluate *every* pixel strictly out-of-sample.
- **Targeted Physical Signature:** Eliminates range-front topographic shortcutting (`det_elev_slope > 10°`) during concealed-basin inference (`d_cat > 32 px`) and prevents tree memorization of `existing_faults.tif` during full-map emission.
- **Why It Catches Faults Missing from the USGS/INGENIOUS Catalogue:** Standard gradient-boosted trees trained on `existing_faults.tif` split heavily on topographic slope because mapped faults sit on steep mountain fronts; when asked to predict across flat alluvial basins (`slope < 3°`), slope-dominated trees assign near-zero probability even over major buried horst-graben steps. A dedicated slope-blind subsurface/vent specialist is *forced* to learn pure gravity, magnetic, MT conductivity, heat-flow, stress-dilation, and microseismic signatures of faults, transferring directly into concealed basins.
- **Named Non-Fault Mimic & Countermeasure:**
  - *Mimic:* Eroded bedrock range-front facets (`slope > 15°`) lacking active basin-bounding fault offset, and tree memorization halos around `existing_faults.tif`.
  - *Countermeasure:* `0%` in-sample refit + explicit slope-blind 60-feature specialist + smooth label-free piedmont/basin gate (`low_slope` $\times$ `deep_cover`).
- **How It Differs from Existing Repo Implementations:** `WBG2-DPHS` trained both of its HGBRs on all `60` features including LiDAR/3DEP slope and blended `55%` in-sample full-map refit (`frac_gt_32px = 3.64%`, `45` discrete overlap violations). `WBG2-GVCD` enforces `0%` in-sample refit and introduces the first **100% slope-blind subsurface/vent specialist** in `WBGGEMSDOE2`.
- **Expected `HOLDOUT-DTI` Gain & Cost:** `+0.0010 .. +0.0030` pooled `HOLDOUT-DTI` + **eliminates all 45 discrete fleet overlap violations** · **Medium cost** (`~160 s` across 4 folds).

---

### Rank 4 — `GVCD-H4`: Post-Catalogue ANSS ComCat Relocated Microseismicity (`2021–2026`) & Multi-Scale Earthquake Lineament Halo
- **Specific Layers Involved:**
  - `usgs_comcat_geodawn.csv` (`3,977` relocated USGS ANSS ComCat earthquakes inside the GeoDAWN bounding box, including `541` post-2021 events recorded *after* the 2021 INGENIOUS fault compilation freeze; SHA-256 `c580226bdad748c6...`, official source: [USGS ANSS ComCat](https://earthquake.usgs.gov/earthquakes/search/))
- **Targeted Physical Signature:** Depth- and magnitude-weighted (`1 + max(0, M)` for shallow brittle crust `0 < z <= 18 km`) multi-scale earthquake density and Hessian ridge anisotropy (`comcat_all_seis_density`, `comcat_post2021_blind_halo`, `comcat_seis_aniso_ridge`), isolating active blind Walker Lane / Central Nevada Seismic Belt shear zones and geothermal swarm lineaments (`2021–2026`) missing from the 2021 static map.
- **Why It Catches Faults Missing from the USGS/INGENIOUS Catalogue:** Active blind strike-slip and normal transfer zones frequently rupture in $M\,1.0\text{–}4.5$ earthquake swarms (`5–14 km` depth) beneath young playas and volcanic plateaus with zero mapped surface trace in the 2021 INGENIOUS compilation.
- **Named Non-Fault Mimic & Countermeasure:**
  - *Mimic:* Shallow (`< 1.5 km`) open-pit mine blasts and isolated epicentral location scatter (`±1.5 km`).
  - *Countermeasure:* Down-weight near-surface (`< 1.0 km`) blast-like events, extract Hessian ridge coherence (`lambda_max / (|lambda_min| + eps)`), and require co-registration with gravity/magnetic/strain features inside the regularized ensemble.
- **How It Differs from Existing Repo Implementations:** Neither `WBG2-MSPTCD` nor `WBG2-DPHS` (`src/wbggems/dphs.py`) actually computed any feature from `usgs_comcat_geodawn.csv`. `WBG2-GVCD` ingests all `3,977` events and explicitly separates the `541` post-2021 blind discovery events.
- **Expected `HOLDOUT-DTI` Gain & Cost:** `+0.0005 .. +0.0018` pooled `HOLDOUT-DTI` · **Low cost** (`~8 s`).

---

### Rank 5 — `GVCD-H5`: Concealed Basement-Depth Step Hessian & Dual-Regime (`>32 px` Distal + `2.25..32 px` Proximal) 300 m Submodular CELF Allocator
- **Specific Layers Involved:**
  - Official GeoDAWN Band `15` (`depth_to_base_surf`), Band `2` (`isostatic_grav`), `src/wbggems/gvcd.py` (`basement_step_hessian_ridge`, `piedmont_blind_step_index`, `allocate_dual_regime_submodular_300m`)
- **Targeted Physical Signature:** Second-order Frangi/Hessian crest (`max(0, -lambda_min)`) of the horizontal gradient of Cenozoic basin thickness (`|\nabla(\text{depth\_to\_base\_surf})|`) paired with two-stage non-overlapping 300 m triangular-kernel CELF submodular allocation (`44.0%` distal `> 32 px` quota + `56.0%` proximal `2.35 < d <= 32 px` quota, strict `min_sep = 2.65 px` across the regime boundary).
- **Why It Catches Faults Missing from the USGS/INGENIOUS Catalogue:** Concealed intrabasin horst-bounding faults create sharp steps in depth-to-Mesozoic/Paleozoic basement beneath flat Quaternary playas. Standard single-stage top-N or global greedy allocators spend `>95%` of their dot budget along proximal mountain fronts (`d_cat <= 32 px`); two-stage submodular allocation guarantees dedicated 300 m kernel coverage (`16,456` distal dots) across concealed basins while maintaining non-overlapping spacing across the `d_cat = 32 px` seam.
- **Named Non-Fault Mimic & Countermeasure:**
  - *Mimic:* Eroded paleovalleys or asymmetric granitic batholith roofs lacking brittle fault offset.
  - *Countermeasure:* Require co-aligned shallow MT conductivity (`cond_surf`), axial stress dilation tendency ($T_d$), or 1 m/10 m micro-scarp expression, and enforce minimum marginal DTI gain per placed 300 m kernel disk.
- **How It Differs from Existing Repo Implementations:** `WBG2-DPHS` used a single global `allocate_submodular_300m` call (`frac_gt_32px = 3.64%`), starving distal basins. `WBG2-GVCD`'s `allocate_dual_regime_submodular_300m` enforces regime-stratified budgets with exact cross-boundary `min_sep_px` exclusion (`frac_gt_32px = 44.00%`).
- **Expected `HOLDOUT-DTI` Gain & Cost:** Preserves pooled `HOLDOUT-DTI` (`0.17591`) while raising distal off-catalogue SGMC coverage and achieving **`0 / 496` discrete 8-org overlap violations** · **Low cost** (`~25 s`).

---

## Preregistration Summary Table

| Rank | ID | Primary Physical Mechanism | Key New Verified Inputs | Expected `HOLDOUT-DTI` Lift | Compute Cost | Implemented in Campaign? |
|---:|---|---|---|---|---|---|
| **1** | **GVCD-H1** | Geothermal-Vent, Borehole Heat-Flow, Volcanic Dike & Clay-Cap Structural Conduit | `usgs_heat_flow_wells_epsg32611.csv` (`1,546` wells), `derived_gdr_volcanics_100m_u8.tif` | `+0.0010 .. +0.0030` | Low (`~18 s`) | **Yes (`EXP-1..3`)** |
| **2** | **GVCD-H2** | Regional $S_{h\min}$ Axial Stress-Resolved Gravity/Magnetic Dilation Tendency | `gb_regional_stress_grid_10km.csv` (`999` 10-km stress blocks) | `+0.0008 .. +0.0025` | Low (`~12 s`) | **Yes (`EXP-1..3`)** |
| **3** | **GVCD-H3** | Slope-Blind 60-Feature Subsurface Specialist + 100% Spatial-OOF Isotonic Fusion | Zero-slope feature subspace + 4-fold `8 km`-buffered OOF (`0%` refit) | `+0.0010 .. +0.0030` | Medium (`~160 s`) | **Yes (`EXP-2..3`)** |
| **4** | **GVCD-H4** | Post-2021 ANSS ComCat Relocated Microseismicity (`2021–2026`) & Swarm Ridge | `usgs_comcat_geodawn.csv` (`3,977` events; `541` post-2021) | `+0.0005 .. +0.0018` | Low (`~8 s`) | **Yes (`EXP-1..3`)** |
| **5** | **GVCD-H5** | Basement-Step Hessian Crest + Two-Stage Dual-Regime 300 m CELF Submodular Allocator | Band `15` (`depth_to_base_surf`) Hessian + `allocate_dual_regime_submodular_300m` | `+0.0000 .. +0.0010` + `0/496` discrete dupes | Low (`~25 s`) | **Yes (`EXP-3`)** |
