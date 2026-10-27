# Preregistered Geological Hypotheses — Lane `WBG2-DPHS` (2026-10-27)

**Preregistered BEFORE model implementation (`2026-10-27T19:15:00Z`)** under the Parallel-Run Protocol (`<= 3` experiments, single assigned lane `WBG2-DPHS`: *Dual-Regime Piedmont & Hydrothermal–Structural Synthesis*, unchanged shared evaluator `gems57-pooled-hide-v2` from `buffedlizard55-lab/57GEMSDOE@822a0ce5`).

## Ranking by Expected `HOLDOUT-DTI` Gain & Implementation Cost

| Rank | ID | Hypothesis | Expected `HOLDOUT-DTI` Gain (Qualitative) | Implementation Cost |
|---:|---|---|---|---|
| **1** | **DPHS-H1** | Dual-Scale 1 m / 10 m De-Confounded Piedmont Fault-Scarp Morphology with Native Missingness Routing | **High** — primary fine-scale localization across 100% of footprint | Low–Moderate (~120 LOC) |
| **2** | **DPHS-H2** | Fold-Visible-Only En-Echelon Stepover Relay-Breach & Strike-Projected Tip Continuation | **Moderate–High** — targets unmapped stepover bridges & plunging splays with zero leakage | Low (~85 LOC) |
| **3** | **DPHS-H3** | Shallow Hydrothermal Magnetite-Destruction (`RTP - TMI_up150`) & GeoDAWN `K/Th` Alteration | **Moderate** — isolates mineralized damage zones across 99.98% of footprint | Low (~60 LOC) |
| **4** | **DPHS-H4** | Blind Geothermal Upflow Conduits from Shallow 2 m Temperature Probes, Geothermometers & Paleo-Sinter | **Moderate** — detects zero-scarp intrabasin blind faults beneath >200 m basin fill | Low (~70 LOC) |
| **5** | **DPHS-H5** | Lazy-Greedy 300 m Submodular Max-Cover Decoding Outside the 2-Pixel Masked-Catalogue Collar | **High** — provable $(1 - 1/e)$ `TP_w` coverage without collinear `FP_w` waste or `d <= 2 px` mask bleed | Low (~90 LOC) |

---

## Detailed Mechanism Specification

### 1. `DPHS-H1` — Dual-Scale 1 m / 10 m De-Confounded Piedmont Fault-Scarp Morphology
1. **Specific layers:** Competition `det_elev` (Band 12), `det_elev_slope` (Band 19), `depth_to_base_surf` (Band 15); [USGS 3DEP 1 m LiDAR](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) (`ex_max`, `ex_mean`, `step_max`, `lapneg_max`, `lappos_max`, `downface_max`, `upface_max`, `coh100`); [USGS 3DEP 1/3 arc-second (~10 m) seamless DEM](https://apps.nationalmap.gov/downloader/) (`slope_max`, `steep_ratio_max`, `hgm20_max`, `hgm50_max`, `curv_absmax`, `onesided3`); [US Census Bureau TIGER/Line Roads](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) (`tiger_road_distance_m`).
2. **Physical signature:** Quaternary Basin-and-Range normal faults cutting unconsolidated piedmont alluvial fans produce 0.5–8 m asymmetric steps characterized by paired crest-convex / toe-concave Laplacian dipoles ($\sqrt{\text{lapneg}\cdot\text{lappos}}$), persistent 100 m strike coherence (`coh100`), and one-sided cross-strike elevation jumps (`onesided3`).
3. **Why it catches faults missing from USGS/INGENIOUS catalogue:** Pre-3DEP mapping missed low-throw (<3 m) Holocene/late-Pleistocene piedmont scarps, distributed synthetic/antithetic graben splays 250–3,000 m basinward of range fronts, and scarps across the `24.7%` un-flown 1 m LiDAR gaps where LiDAR-only models (`GEMSDOE66`) collapse to zero. Routing `q == 0 -> NaN` lets gradient-boosted trees exploit 1 m LiDAR where flown (`75.3%`) while seamless 10 m 3DEP bridges `100%` of the footprint.
4. **Non-fault mimic:** Highway/railroad causeway embankments (`<250 m` from TIGER roads), Pleistocene Lake Lahontan wave-cut shorelines (`1,315–1,348 m` highstand benches), and symmetric incised ephemeral fan arroyos. Explicitly suppressed via TIGER road-distance and Lahontan elevation de-confounding.
5. **How it differs from this repo:** `DZ-16` used only 19 coarse 100 m bands truncated at `d <= 32 px`; `H3-PACK` used zero geology; `WBG2-MSPTCD` used only 19 coarse 100 m bands without 1 m LiDAR, 10 m 3DEP, or road/shoreline de-confounding.

### 2. `DPHS-H2` — Fold-Visible-Only En-Echelon Stepover Relay-Breach & Tip Continuation
1. **Specific layers:** Strictly fold-visible fault mask (`fold["visible"]` during buffered 4-quadrant CV; `existing_faults.tif` only at final full-map inference), coupled with competition `det_elev`/`det_elev_slope` (Bands 12, 19) structure-tensor strike and `iso_grav_anom_hg` (Band 18) / `cond_surf` (Band 17).
2. **Physical signature:** Normal faults grow by radial tip propagation and mechanical linkage across 0.3–3.0 km en-echelon relay ramps and stepovers (Peacock & Sanderson, 1991; Faulds & Hinz, 2015), concentrating Coulomb shear stress along the inter-strand Voronoi medial bridge between two distinct fault components (`c1 != c2` at `3 px <= d1 <= 26 px`) and along strike-projected tip lobes.
3. **Why it catches faults missing from USGS/INGENIOUS catalogue:** Regional `1:100k–1:250k` compilations map primary range-bounding master strands cleanly but systematically omit short breaching cross-faults inside relay ramps and plunging tip splays under young fan cover.
4. **Non-fault mimic:** Isotropic radial halos around known faults (`DZ-16`'s `d <= 32 px`) falsely illuminate barren footwall granite and hanging-wall playas perpendicular to strike where no tip or relay strain exists, and putting raw `EDT(~visible)` directly into `X_train` under quadrant holdout would memorize `EDT == 0` on training positives. We prevent both by keeping `X` 100% zero-catalogue and applying `DPHS-H2` strictly as a bounded `[1.0, 1.25]` relay/tip decoding modulator outside `d_vis <= 2.05 px`!
5. **How it differs from this repo:** `DZ-16` used isotropic distance truncation (`d <= 32 px`); `WBG2-MSPTCD` was zero-catalogue (`HOLDOUT-DTI 0.0329`). Neither computed distinct-component Voronoi relay-breach bridges or strike-projected tip lobes strictly on `visible` strands without distal starvation.

### 3. `DPHS-H3` — Shallow Hydrothermal Magnetite-Destruction (`RTP - TMI_up150`) & GeoDAWN `K/Th` Alteration
1. **Specific layers:** Competition `rtp` (Band 2), `tmi_hg` (Band 3), `tmi` (Band 14), `iso_grav_anom_hg` (Band 18), `tc_radiometric` (Band 6); [USGS GeoDAWN Airborne Magnetic & Radiometric Survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) (`K`, `Th`, `U`, `ThK`, `TMI_up150`; `doi:10.5066/P9X8K366`).
2. **Physical signature:** Hydrothermal fluids ascending permeable fault gouge oxidize/sulfidize ferromagnetic magnetite into non-magnetic hematite and pyrite—creating narrow shallow magnetic troughs in `z(RTP) - z(TMI_up150)`—while precipitating potassium-rich adularia and illite (`K/Th` enrichment) along co-planar gravity–magnetic contacts (Gallardo & Meju, 2003).
3. **Why it catches faults missing from USGS/INGENIOUS catalogue:** Faults cutting Tertiary volcanic plateaus or concealed under thin colluvium often lack crisp topographic scarps due to talus shedding yet preserve permanent shallow demagnetization troughs and `K/Th` metasomatic halos across `99.98%` of the footprint.
4. **Non-fault mimic:** Unaltered felsic rhyolite domes/ash-flow tuffs (high K and high Th, cancelled by `K/Th` normalization), broad reversed-polarity basalt flows (persist in `TMI_up150`), and K-evaporite playas.
5. **How it differs from this repo:** `WBG2-MSPTCD` only had unseparated gamma total-count (Band 6) and lacked 150 m upward-continued magnetic vertical differencing.

### 4. `DPHS-H4` — Blind Geothermal Upflow Conduits from 2 m Temperature Probes, Geothermometers & Paleo-Sinter
1. **Specific layers:** Competition `depth_to_base_surf` (Band 15), `cond_surf` (Band 17), `iso_grav_anom_hg` (Band 18), `ieq_n100a15` (Band 16); [DOE Geothermal Data Repository (GDR) #1391](https://gdr.openei.org/submissions/1391) INGENIOUS thermal wells/springs `(row, col, temp_c, geothermquartz_c, geothermchalc_c)`, shallow 2 m temperature probes (`derived_gdr_2m_probes_100m_u8.tif`), paleo-sinter/travertine/tufa deposits (`derived_gdr_paleo_100m_u8.tif`), and Quaternary volcanic vents `(row, col)`.
2. **Physical signature:** Blind intrabasin normal faults leak buoyant thermal fluids into shallow 2 m temperature surveys, elevate silica geothermometer equilibrium temperatures in gradient wells, and precipitate opaline sinter / travertine mounds above conductive `cond_surf` roots.
3. **Why it catches faults missing from USGS/INGENIOUS catalogue:** Over ~40% of Great Basin geothermal systems are blind (zero surface scarp or hot spring) beneath >200 m of Quaternary basin fill and are systematically absent from surface geologic fault maps.
4. **Non-fault mimic:** Lateral shallow-aquifer thermal outflow plumes kilometres down-gradient from the feeder fault, mitigated by requiring tree-interaction coupling with `iso_grav_anom_hg` / `cond_surf` structural roots.
5. **How it differs from this repo:** No model in `WBGGEMSDOE2` ingested DOE GDR #1391 thermal wells/springs, 2 m probes, or paleo-sinter deposits; our loader explicitly strips `dist_known_fault_px` at CSV read time to guarantee zero catalogue leakage.

### 5. `DPHS-H5` — Lazy-Greedy 300 m Submodular Max-Cover Decoding Outside the 2-Pixel Masked Collar
1. **Specific layers:** Isotonically calibrated OOF fault probability surface $p(y, x)$, fold-visible distance transform $\text{EDT}(\neg\text{visible}) > 2.05\text{ px}$, and exact $R = 300\text{ m}$ (`3.0 px`) triangular DW-Tversky kernel $K(r) = \max(0, 1 - r/3)$.
2. **Physical / metric coupling:** Under organizer DW-Tversky ($\alpha=0.2, \beta=0.8$) with pixel-exact masking of `existing_faults.tif`, dots at $d \le 2.0\text{ px}$ bleed 35%–70% of their kernel onto masked pixels while paying full `0.2 * FP_w` penalty on flanking barren pixels, and 1-px ridges pay $3\times$–$6\times$ redundant `FP_w`.
3. **Why it improves DTI on hidden test faults:** Minoux (1978) lazy-greedy (CELF) maximization of $\mathbb{E}[\text{TP}_w(S)] = \sum_u p(u)\max_{s\in S} K(\|u-s\|_2)$ subject to $d_{\text{vis}} > 2.05\text{ px}$ and $r_{\min} \ge 2.2\text{ px}$ achieves $(1 - 1/e)$ optimal weighted recall across both near-corridor splays (`2–32 px`) and distal intrabasin faults (`>32 px`) without distal truncation.
4. **Non-fault mimic / failure mode:** Over-packing barren playas if $p(u)$ is uncalibrated (`H3-PACK` fallacy), prevented by isotonic OOF probability calibration and marginal-gain stopping.
5. **How it differs from this repo:** Replaces uniform `H3-PACK` lattices, `DZ-16`'s hard `d <= 32 px` truncation, and `WBG2-MSPTCD`'s unweighted `3.0 px` greedy disks.

---

## Pre-Registered 3-Experiment Schedule (`<= 3` Experiments)

1. **`EXP-1` (`DPHS-ScarpSpec` — tests `DPHS-H1 + DPHS-H3`):** `51` zero-catalogue features (`31` MSPTCD + `7` 1 m LiDAR scarp with `q==0 -> NaN` + `7` seamless 10 m 3DEP de-confounded piedmont scarp + `6` GeoDAWN K/Th/U, shallow demag `RTP - TMI_up150`, Gallardo–Meju cross-gradient) trained with 4-quadrant spatially buffered `HistGradientBoostingClassifier` and decoded via matched `greedy_allocate`.
2. **`EXP-2` (`DPHS-HydroMultiScale` — tests `+ DPHS-H4` + strike-coherent multi-scale ridge integrators):** Expands to `60` zero-catalogue features by adding `4` DOE GDR #1391 blind hydrothermal conduit halos (`gdr_wellspring_geotherm`, `gdr_2m_probe_halo`, `gdr_paleo_sinter_halo`, `gdr_volcanic_vent_halo`) + `5` multi-scale strike-coherent scarp & electrical-hydrothermal ridge integrators.
3. **`EXP-3` (`DPHS-CalibratedSubmodular` — tests `+ DPHS-H2 + DPHS-H5`):** Diversified dual-tree ensemble (`EXP-2` features), nested out-of-fold Isotonic probability calibration, bounded `[1.0, 1.25]` fold-visible relay-breach & tip-propagation prior modulation (`visible = fold["visible"]` in CV, `existing_faults` at full-map emission; never starving distal pixels), and Minoux CELF 300 m (`R=3.0 px`) submodular max-cover outside `EDT(~visible) <= 2.05 px` with `min_sep >= 2.2 px`.
