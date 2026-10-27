# Unimplemented Geothermal-Vent & Structural Fault Hypotheses (`WBG2-HVGF` Pre-Experiment Formulation)

**Date**: 2026-10-27  
**Repository**: `wingbangboozle1-lang/WBGGEMSDOE2` (`arena/633e84b3-wbggemsdoe2`)  
**Competition**: [DOE GEMS Prize — Geothermal Exploration with Machine learning and Structural geology](https://www.drivendata.org/competitions/306/competition-doe-gems/)  
**Protocol Checkpoint**: Formulated *prior* to executing any new experiment in this session, in strict compliance with Requirement 4 and the Parallel-Run Protocol (`<= 3` experiments budget; `gems57-pooled-hide-v2` shared evaluator; single-feature leakage canaries `AUC <= 0.90`; pre-placement surface & post-placement discrete dot uniqueness audits).

---

## Scientific Premise: Why Geothermal Vent Discovery Requires Coupling Hydrothermal Upflow Physics with Concealed Piedmont Mechanics

Across the northwestern Great Basin and Walker Lane (>400 catalogued geothermal systems; [INGENIOUS / Great Basin Center for Geothermal Energy](https://gbcge.org/current-projects/ingenious/)), over **75% of commercial-grade hydrothermal systems are "blind"** — lacking active boiling geysers or prominent Holocene range-front scarps at the land surface (Faulds et al., 2011, 2016, 2021). However, high-permeability geothermal upflow conduits are **not** distributed randomly along fault mid-segments: they localize systematically at **dilational fault step-overs (relay ramps), fault terminations (horse-tail splays), fault intersections, and transtensional accommodation zones** buried beneath 200–1,500 m of Cenozoic piedmont / basin-fill sediments (`depth_to_base_surf >= 200 m`).

Previous lanes in `WBGGEMSDOE2` left major physical observables completely untouched:
- **`DZ-16` (`scripts/make_candidate.py`)**: Used *zero* geophysical, topographic, radiometric, or geothermal layers — only smoothed `existing_faults.tif` plus a `1,600 m` Euclidean distance ring (`EMPIRICAL-ESTIMATE = 0.15`).
- **`H3-PACK` (`scripts/generate_h3_pack.py`)**: Blurred 4 competition bands at `sigma = 56 px` (`5.6 km`) for macro-density only and scattered uniform Poisson dots (`NaN` outside footprint also triggered DrivenData's `"Predicted values must be in range [0, 1]"` error).
- **`WBG2-MSPTCD` (`scripts/run_wbg2_msptcd.py`)**: Used only the 19 coarse 100 m competition bands (`HOLDOUT-DTI = 0.0426` on `buffer_px=80` quadrant holdout; `78.34%` 3-px overlap with `GEMSDOE27_H31`), omitting **all** direct geothermal vent observations (2 m temperature probes, thermal springs/wells & chemical geothermometers, paleo-geothermal sinter/travertine/tufa vents), airborne gamma-ray radiometrics (K/eTh/eU alteration ratios), 1 m LiDAR scarp dipoles, seamless 10 m DEM / fluvial $\chi$ knickzones, and exact two-host (`C1 != C2`) structural relay geometry.

Below are **five concrete, previously unimplemented hypotheses** ranked by expected `HOLDOUT-DTI` impact versus implementation cost.

---

## Summary Ranking Table (Expected `HOLDOUT-DTI` Impact vs. Implementation Cost)

| Rank | ID | Hypothesis Title | Primary Layers (19-Band + Verified Public External) | Named Non-Fault Mimic | Expected `HOLDOUT-DTI` Impact | Implementation Cost | Session Status |
|---:|---|---|---|---|---|---|---|
| **1** | **`H-HVGF-1`** | **Structurally Guided Anisotropic Hydrothermal Plume Back-Projection & Vent-Alteration Coupling** | B3, B12, B15, B17, B18, B19 + DOE GDR #1391 2m probes, thermal wells/geothermometers, paleo-sinter/tufa + USGS GeoDAWN K/Th/U & 150m TMI + USGS 3DEP 1m LiDAR & 10m DEM/$\chi$ + visible-only `gems57` two-host relay | Distal down-fan lateral thermal outflow plumes; felsic ash-flow tuff K highs; Lahontan/Bonneville pluvial shorelines | **Highest** (targets exact blind geothermal vent + piedmont fault intersection habitat) | Moderate (~10 min CPU with `float32` memmap) | **Selected Lane (`E1`–`E3`)** |
| **2** | **`H-HVGF-2`** | **Mohr–Coulomb Geodetic Principal-Strain Dilation & Slip Tendency ($T_d, T_s$) on Subsurface Potential-Field Fault Planes** | B4 (`geod_2ndinv`), B7 (`geod_shearrate`), B8 (`geod_dilatrate`), B10 (`deq_n100a15`), B16 (`ieq_n100a15`), B18 (`iso_grav_anom_hg`), B15 (`depth_to_base_surf`) + INGENIOUS visible slip-sense (`RL`/`LL`/`N`) | Long-wavelength GPS station interpolation halos & groundwater/mining subsidence bowls | **High** (especially across Walker Lane / Basin-and-Range transtensional transfers) | Low (~2 min CPU) | **Tested as `E2` ablation step** |
| **3** | **`H-HVGF-3`** | **Cross-Fan Fluvial $\chi$–$k_{sn}$ Disequilibrium & Interfluve 1 m LiDAR Graben Scarp Polarity** | USGS 3DEP 10 m `chi_step_max`, `chi_ksn_max`, `chi_zmean_m` + USGS 3DEP 1 m `lidar_lapneg_max`, `lidar_lappos_max`, `lidar_upface_max`, `lidar_downface_max` + B19 (`det_elev_slope`) | Resistant welded-tuff / basalt caprock knickpoints & Pleistocene pluvial wave-cut benches (1332 m / 1463 m / 1552 m) | **Moderate–High** (recovers wash-dissected piedmont scarps) | Low–Moderate (~3 min CPU) | Core geomorphology module in `E1` |
| **4** | **`H-HVGF-4`** | **Multi-Altitude Potential-Field Tilt-Angle Zero-Crossing & Upward-Continued Worm Persistence** | B2 (`rtp`), B3 (`tmi_hg`), B9 (`tmi_vg`), B11 (`iso_grav_anom_vg`), B13 (`iso_grav_anom`), B14 (`tmi`), B18 (`iso_grav_anom_hg`) + GeoDAWN `ext_TMI_up150` | Pre-Cenozoic mafic dike swarms, pluton aureole edges, and tilted Neogene basalt flows | **Moderate** (strong subsurface depth-persistence filter; lower standalone 300 m surface precision due to dip shift) | Low (~2 min CPU) | Core potential-field module in `E1` |
| **5** | **`H-HVGF-5`** | **3-D Magnetotelluric Mid-Crustal Fluid-Ascent Chimneys Coupled to Shallow Clay-Cap Conductivity** | B17 (`cond_surf`), B18 (`iso_grav_anom_hg`), B15 (`depth_to_base_surf`) + USGS ScienceBase / EarthScope USArray Great Basin 3-D MT resistivity models | Saline evaporitic lithium/borate playas & Paleozoic graphitic black shales (Roberts Mountains allochthon) | **Low–Moderate at 300 m DTI** (MT station spacing is 15–70 km vs 100 m scoring grid) | High (3-D MT voxel regridding + outbound host blocked in sandbox) | Documented for future work |

---

## Detailed Hypothesis Specifications

### Hypothesis 1 (`H-HVGF-1`, Rank 1): Structurally Guided Anisotropic Hydrothermal Plume Back-Projection & Vent-Alteration Coupling

- **Exact layers used**:
  1. **Competition 19-band stack (`training_features.tif`)**: `iso_grav_anom_hg` (B18), `tmi_hg` (B3), `depth_to_base_surf` (B15), `cond_surf` (B17), `det_elev` (B12), `det_elev_slope` (B19).
  2. **DOE GDR #1391 INGENIOUS Well & Spring Temperature + Chemical Geothermometers** (`gdr_wellspring_in_footprint.csv`: `temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c`; *`dist_known_fault_px` explicitly blocked and asserted unused*):
     - Official source: <https://gdr.openei.org/submissions/1391> | DOI: <https://doi.org/10.15121/1881483> (CC-BY-4.0).
  3. **DOE GDR #1391 INGENIOUS Shallow 2-Meter Temperature Survey Probes** (`2m_temperature_probe_INGENIOUS_regional_data.zip`: `T2m`, `F2mDAB` seasonal baseline anomaly across >3,800 probe stations):
     - Official source: <https://gdr.openei.org/submissions/1391> (CC-BY-4.0).
  4. **DOE GDR #1391 INGENIOUS Paleo-Geothermal Deposits & Quaternary Volcanic Vents** (`paleo_geothermal_regional.zip` — 709 opaline sinter, travertine, calcareous tufa, and silicified fault-breccia occurrences + `gdr_volcanic_vents_in_footprint.csv`):
     - Official source: <https://gdr.openei.org/submissions/1391> (CC-BY-4.0).
  5. **USGS GeoDAWN Airborne Gamma-Ray Spectrometry & Upward-Continued Magnetic Grids** (`geodawn_rad_u8.tif`: `rad_K`, `rad_Th`, `rad_U`, `rad_TC`; `geodawn_extensions_u8.tif`: `ext_ThK`, `ext_UK`, `ext_UTh`, `ext_TMI_up150`):
     - Official source: <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> | ScienceBase DOI: <https://doi.org/10.5066/P93LGLVQ> (CC0 Public Domain).
  6. **USGS 3DEP 1 m LiDAR & Seamless 10 m DEM / Fluvial $\chi$ Grids** (`lidar_scarp_features_u8.tif` with explicit `has_lidar` coverage mask; `topo_10m_derived_100m_u8.tif`; `dem10_chi_100m_i16.tif`):
     - Official source: <https://www.usgs.gov/3d-elevation-program> (US Public Domain).
  7. **Visible-Only Structural Relay & Slip-Sense Anatomy** (`gems57.anatomy`, `gems57.relay_bend_anatomy.two_host_frame`, and INGENIOUS `trace_segments_utm11.csv` computed *strictly from `visible` faults per holdout fold*).
- **Physical signature**:
  Ascending $120\text{–}250^\circ\text{C}$ hydrothermal fluids along concealed piedmont/basin-margin faults create four coupled observables:
  1. **Anisotropic strike-aligned & up-gradient thermal plumes**: Warm brines discharging from a concealed range-front or intra-basin fault flow *down-slope* into permeable alluvial-fan aquifers (`det_elev` gradient) while migrating *along-strike* inside the fracture damage zone. Back-projecting thermal anomalies (`gdr_wellspring`, `2m_probes`, `paleo_sinter_tufa`) up the local hydraulic/topographic gradient ($\nabla z_{\text{det}}$) and anisotropically along the local geopotential–topographic strike tensor $\mathbf{J}(x)$ refocuses diffuse basin-floor thermal halos onto the actual controlling fault conduit.
  2. **Coupled Magnetite-Destruction $\times$ K-Metasomatism $\times$ Smectite Clay-Cap Alteration**: Boiling/ascending neutral-chloride and bicarbonate fluids oxidize/sulfidize host-rock magnetite to pyrite/hematite (creating a local **150 m upward-continued magnetic demagnetization trough** `tmi_demagnetization`), enrich adularia/illite potassium relative to immobile thorium (**low `ext_ThK` / positive local `rad_K_alteration_halo`**), mobilize redox-sensitive uranium (`ext_UTh`), and form a shallow conductive smectite/illite clay cap (`cond_surf` B17).
  3. **Fossil Self-Sealed Vent Aprons**: Opaline sinter, travertine, and tufa mounds (`paleo_geothermal_regional.zip`) precipitate directly at water-table-intersecting fault breaches even after silica self-sealing shuts off modern surface boiling.
- **Why USGS/INGENIOUS catalogues miss it**:
  Rapid Holocene alluvial-fan aggradation, eolian silt/sand mantles, playa sedimentation, and hydrothermal silica/carbonate self-sealing erase or bury <1.5 m surface scarps within $10^3\text{–}10^4$ yr, causing aerial-photo scarp compilations to terminate mapped traces several kilometers short of active blind geothermal step-overs and relay ramps.
- **How it differs from existing implementations in `WBGGEMSDOE2`**:
  None of `DZ-16`, `H3-PACK`, `WBG2-MSPTCD`, `stepxasym`, or `blind-conduit-breach` ingests *any* of the DOE GDR #1391 thermal/paleo-sinter datasets, USGS GeoDAWN radiometrics, 1 m LiDAR scarps, or 10 m fluvial $\chi$ layers; and unlike peer isotropic-blur approaches (`GEMSDOE70`), `H-HVGF-1` introduces **hydraulic up-gradient thermal back-projection + structure-tensor strike anisotropy + coupled K/Th–demagnetization–clay-cap vent alteration + exact visible-only two-host (`C1 != C2`) relay anatomy + cross-strike ridge skeletonization**.
- **Named non-fault mimic**:
  1. *Lateral down-fan groundwater outflow plumes* (warm water advected 2–6 km down-gradient into unfaulted playa flats) — mitigated by up-gradient $\nabla z_{\text{det}}$ back-projection and requiring subsurface basement/gravity gradient support;
  2. *Unfaulted high-K rhyolitic ash-flow tuffs* — mitigated by subtracting 1 km lithologic background (`rad_K_alteration_halo`) and requiring co-located magnetic destruction + Cenozoic basin fill (`depth_to_base_surf`);
  3. *Pleistocene Lake Lahontan (1332 m) & Lake Bonneville (1463 m / 1552 m) wave-cut shorelines* — mitigated via `pluvial_shoreline_elev_dist_m`.

---

### Hypothesis 2 (`H-HVGF-2`, Rank 2): Mohr–Coulomb Geodetic Principal-Strain Dilation & Slip Tendency ($T_d, T_s$) on Subsurface Potential-Field Fault Planes

- **Exact layers used**: `geod_2ndinv` (B4), `geod_shearrate` (B7), `geod_dilatrate` (B8), `deq_n100a15` (B10), `ieq_n100a15` (B16), `iso_grav_anom_hg` (B18), `tmi_hg` (B3), `depth_to_base_surf` (B15), plus visible-only `trace_segments_utm11.csv` (`SLIPSENSE`: `RL`, `LL`, `N`; official source: <https://gbcge.org/current-projects/ingenious/>).
- **Physical signature**:
  Fault permeability in the brittle upper crust peaks on fault planes oriented near optimal Mohr–Coulomb shear-dilation failure ($25^\circ\text{–}35^\circ$ to $\sigma_{H\max}$) and inside **transtensional strain-transfer zones** where high geodetic shear rate (`geod_shearrate`) transitions into positive areal dilatation (`geod_dilatrate > 0`) and elevated declustered microseismicity (`deq_n100a15`). Coupling fault-strike azimuth $\theta(x)$ (from gravity/basement horizontal gradients) with the transtensional partitioning ratio $\mathcal{R}_{\text{trans}} = \text{geod\_dilatrate} \cdot \text{geod\_shearrate} / (\text{geod\_2ndinv} + \varepsilon)$ highlights critically stressed fluid conduits.
- **Why USGS/INGENIOUS catalogues miss it**:
  Distributed transtensional belts (exemplified by the 2020 $M_w$ 6.5 Monte Cristo Range rupture across previously unmapped Candelaria transfer strands; Koehler et al., 2021, <https://doi.org/10.1785/0220200371>) accommodate strain across dense networks of short, discontinuous en-echelon shears whose individual scarps sit below classical Quaternary mapping thresholds.
- **Difference from existing repo implementations**:
  `WBG2-MSPTCD` summed scalar z-scores of `geod_2ndinv` and `geod_dilatrate` without computing strike-dependent geomechanical coupling, transtensional shear-dilatation products, seismicity-to-strain efficiency, or visible slip-sense (`RL`/`LL` vs `N`) kinematic transitions.
- **Named non-fault mimic**:
  *Smooth GPS station-spacing interpolation lobes and agricultural/mining pumping subsidence bowls* — suppressed because subsidence produces contractional negative dilatation (`geod_dilatrate < 0`) without sub-kilometer basement density steps.

---

### Hypothesis 3 (`H-HVGF-3`, Rank 3): Cross-Fan Fluvial $\chi$–$k_{sn}$ Disequilibrium & Interfluve 1 m LiDAR Graben Scarp Polarity

- **Exact layers used**: USGS 3DEP 10 m seamless fluvial & topographic grids (`dem10_chi_100m_i16.tif`: `chi_step_max`, `chi_ksn_max`, `chi_log10_area`, `chi_zmean_m`; `topo_10m_derived_100m_u8.tif`: `topo10_curv_prof_absmax`, `topo10_aspect_coherence`) + USGS 3DEP 1 m LiDAR scarp stack (`lidar_scarp_features_u8.tif`: `lidar_lapneg_max`, `lidar_lappos_max`, `lidar_upface_max`, `lidar_downface_max`, `lidar_step_max`, `has_lidar`; official source: <https://www.usgs.gov/3d-elevation-program>).
- **Physical signature**:
  Active piedmont normal faults uplift their footwall relative to local base level, generating **aligned steepness index ($k_{sn}$) and $\Delta\chi$ knickzones across parallel ephemeral washes** flanked on preserved fan interfluves by paired crest-convex / toe-concave **1 m LiDAR Laplacian scarp dipoles** ($\sqrt{\max(0, \text{lapneg} \cdot \text{lappos})}$) and synthetic–antithetic graben face polarity (`upface` + `downface`).
- **Why USGS/INGENIOUS catalogues miss it**:
  Flash-flood sedimentation in braided desert washes repeatedly planes off 0.5–1.5 m Holocene scarps across channel floors, leaving isolated interfluve bevels too fragmented for continuous photogeologic lineament compilation.
- **Difference from existing repo implementations**:
  Zero scripts in `WBGGEMSDOE2` read either the 1 m LiDAR scarp bands or the 10 m fluvial $\chi / k_{sn}$ stack, and earlier attempts using 100 m `det_elev_slope` could not resolve meter-scale piedmont bevels.
- **Named non-fault mimic**:
  *Pleistocene Lake Lahontan (~1332 m) and Lake Bonneville (~1463 m Provo / ~1552 m Bonneville) shoreline benches and fluvial terrace risers* — rejected using elevation proximity to known pluvial highstands (`pluvial_shoreline_elev_dist_m`) and drainage-area scaling (`chi_log10_area`).

---

### Hypothesis 4 (`H-HVGF-4`, Rank 4): Multi-Altitude Potential-Field Tilt-Angle Zero-Crossing & Upward-Continued Worm Persistence

- **Exact layers used**: `rtp` (B2), `tmi_hg` (B3), `tmi_vg` (B9), `iso_grav_anom_vg` (B11), `iso_grav_anom` (B13), `tmi` (B14), `iso_grav_anom_hg` (B18), `depth_to_base_surf` (B15), plus USGS GeoDAWN `ext_TMI_up150` (DOI: <https://doi.org/10.5066/P93LGLVQ>).
- **Physical signature**:
  Miller & Singh (1994) potential-field tilt angle $\theta_{\text{tilt}} = \arctan(\text{VG} / \sqrt{\text{HG}^2 + \varepsilon})$ normalizes amplitude across deep sedimentary basins so blind intra-basin horst-bounding faults produce sharp $\theta_{\text{tilt}} \approx 0$ zero-crossings (`cos(theta_tilt)` ridge) whose horizontal gradient $|\nabla \theta_{\text{tilt}}|$ equals $1/z_{\text{top}}$ at the contact; persistence of horizontal-gradient ridges between surface TMI and 150 m–800 m upward continuation isolates deep crustal fault contacts from shallow volcanic clutter.
- **Why USGS/INGENIOUS catalogues miss it**:
  Intra-basin structural highs (e.g., McGinness Hills, Desert Peak, Soda Lake style buried horsts) sit beneath hundreds of meters of unconsolidated valley fill with zero surface topographic scarp.
- **Difference from existing repo implementations**:
  `WBG2-MSPTCD` multiplied unnormalized `iso_grav_anom_hg` and `tmi_hg` Hessian ridges, which systematically under-weights deep basin-interior faults whose raw horizontal gradient amplitude decays as $1/z_{\text{top}}^2$.
- **Named non-fault mimic**:
  *Mesozoic pluton margins, pre-Tertiary thrust contacts, and buried basaltic lava-flow edges* — distinguished by dip-slip basin-depth asymmetry and lack of Quaternary strain or hydrothermal alteration.

---

### Hypothesis 5 (`H-HVGF-5`, Rank 5): 3-D Magnetotelluric Mid-Crustal Fluid-Ascent Chimneys Coupled to Shallow Clay-Cap Conductivity

- **Exact layers used**: `cond_surf` (B17), `iso_grav_anom_hg` (B18), `depth_to_base_surf` (B15), `deq_n100a15` (B10) + external **USGS ScienceBase / EarthScope USArray 3-D Magnetotelluric Electrical Resistivity Models of the Great Basin** (official sources: <https://www.sciencebase.gov/catalog/item/5fb70a9fd34eb413d5e14977> and <https://ds.iris.edu/spud/emtf>, US Public Domain / CC0).
- **Physical signature**:
  Sub-vertical mid-crustal conductive zones (<10 $\Omega\cdot$m at 5–15 km depth) map deep magmatic/metamorphic fluid roots feeding shallow smectite clay caps (`cond_surf`) along major range-bounding and accommodation-zone faults.
- **Why USGS/INGENIOUS catalogues miss it**:
  Deep crustal fluid-rich shear zones need not rupture the Holocene surface cleanly where ductile/brittle transition temperatures are shallow.
- **Difference from existing repo implementations**:
  No script in `WBGGEMSDOE2` incorporates 3-D crustal MT resistivity slices.
- **Named non-fault mimic**:
  *Saline evaporitic playas (e.g., Carson Sink, Columbus Marsh) and graphitic/pyritic Paleozoic marine shales* — both exhibit extreme bulk conductivity (`<2` $\Omega\cdot$m) unrelated to active Quaternary faulting, and regional MT station spacing (15–70 km) is too coarse to localize 300 m DW-Tversky fault traces without fine-scale scarp/gravity sharpening.
