# Archived extended hypothesis drafts — superseded by the active shortlist

**Status 2026-10-27:** This five-item document is preserved as a detailed historical draft from an earlier review. The active four-proposal record is [`research/hypotheses.md`](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/hypotheses.md), generated from the [structured shortlist JSON](../data/research_hypotheses.json). No experiment was run in this review lane; two parallel lanes reported four combined experiments, both resulting TIFFs independently rejected for literal registry overlap; one also masks interior cells. No weekly slot was used. All rankings here are qualitative guesses about potential spatially blocked HOLDOUT-DTI improvement versus implementation cost—not measured HOLDOUT-DTI, numerical deltas, leaderboard forecasts, or win probabilities. Numeric values elsewhere in this archived draft are proposed scales/thresholds or registry measurements, not score results. Fleet-wide novelty is not established.

**Historical draft, superseded:** H1/H2 overlap methods now implemented in `src/wbggems/msptcd.py`; the old draft is not a shortlist of untested methods. See [current proposals](../../research/hypotheses.md).

**Lane requirement:** The prompt's “single method paragraph” was not uniquely identified. The current method lane is **UNASSIGNED**; H1 is not nominated or authorized. Do not use this archived draft to choose an experiment or spend a slot. Any future explicitly assigned candidate must pass surface-rank correlation and final-dot overlap gates against every registry raster, feature-alone leakage canaries, the pinned pooled HOLDOUT-DTI evaluator with paired 95% CI against a same-fold incumbent, and byte-level format validation. The literal registry stop and continuous-prior interpretation remain unresolved.

---

## H1 — Depth-shifted, multi-scale gravity/magnetic discontinuity [RANK 1: highest expected DTI improvement, medium cost]

| Field | Specification |
|---|---|
| **Layers used** | `iso_grav_anom` (isostatic gravity anomaly), `rtp` (reduced-to-pole magnetics / TMI), `depth_to_base_surf` (conductive-base depth — *not* assumed to be basement/sediment thickness), `det_elev` (detrended elevation). Earlier owner-mirror inventory records all four in a 19-band stack (`docs/data/feature_cache.json`); a later session restored hash-checked owner-mirror raw bands in ignored local storage; that provenance is not organizer-authenticated and the cache may not persist. The shared **derived** bank is absent from the pinned template. |
| **Physical signature (transform)** | Multi-scale **signed directional gradients**: at 300 m, 600 m, 1200 m Gaussian scales compute gravity gradient vector **g** and magnetic gradient **m**; estimate dominant gravity-edge normal **n̂** (structure tensor eigenvector); test whether a magnetic edge exists at displacement **d = k·depth_to_base_surf·tan(dip_proxy)** along **n̂**, where **k** is bounded (\|k\|≤1) and `dip_proxy` is derived per-fold from visible faults only. Test both magnetic polarities; a density contrast does not determine polarity. Output is a scalar concordance score, not a raw field. |
| **Why it could catch a fault missing from USGS/INGENIOUS catalogue** | A buried lithologic offset (e.g., basin-basement step or intrabasinal fault) can be concealed beneath basin fill where no surface scarp is mapped. Gravity senses density contrast; magnetics senses susceptibility contrast; a depth-dependent spatial offset is expected for a dipping contact. Requiring a **shifted** coincidence suppresses purely surficial coincidences. |
| **How it differs from already implemented in this repo** | This repo has **no implementation** — only proposals. It differs *as proposed* from GEMSDOE31's pseudo-gravity residual ([site](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)) and GEMSDOE36's HVG fusion ([site](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)), which use coincident (not shifted) fusion. Related shifted-edge ideas may exist in unpublished parallel lanes; not proven absent. |
| **Named non-fault process that could mimic it** | Unfaulted lithologic contact, mafic dike, or acquisition striping. **Falsification:** cross-orientation test (rotate n̂ 90° should null signal), shuffled-field control (permute magnetic grid), held-out survey-block ablation; require persistence across ≥2 scales. |
| **Implementation cost / expected DTI** | **Medium cost** if the inputs are authenticated and restored (100 m gradients and structure-tensor code; current arrays are absent). **Expected DTI: highest of shortlist** — potential-field edges are known fault proxies and the shift adds specificity, but basin geology is noisy. Qualitative; not a numeric forecast. **External data needed:** none beyond competition stack, if `depth_to_base_surf` semantics are accepted as conductive base. |

**Draft validation checklist (not run):** On four spatially blocked, whole-segment holdouts, derive catalogue features from visible faults only, apply the pre-registered buffer, and mask visible faults pixel-exactly. Run each feature-alone canary and treat AUC >0.90 (or its inverse) as a leakage alarm. If approved to continue, use the shared pooled evaluator (α=0.2, β=0.8, 300 m triangular kernel) and report the actual evaluator version, withheld-positive count, pooled HOLDOUT-DTI, and spatial-block 95% CI against a same-fold incumbent. No positive count or DTI result is asserted here; the checklist does not authorize a run or a slot.

---

## H2 — Conductive-flank asymmetry conditioned on a structural step [RANK 2: medium-high expected DTI, medium cost]

| Field | Specification |
|---|---|
| **Layers** | `cond_surf` (surface conductivity), `depth_to_base_surf`, `iso_grav_anom` gradients, `det_elev`. |
| **Physical signature** | At each candidate cell, estimate the dominant depth/gravity step orientation; compare mean conductivity on opposite sides (flank difference) normalized by local background and depth: `asym = (cond_left − cond_right) / (cond_local + ε) · w(depth)`, where `w` down-weights shallow basin fill. A candidate requires both a step and a significant asymmetric flank, not conductivity alone. |
| **Why it could catch a missing fault** | Concealed fault zones can host fluid pathways / clay alteration producing a **lateral** conductivity contrast alongside a potential-field step. A flank asymmetry is more specific than a raw conductivity high. |
| **Difference from repo** | No implementation. Differs from simple `cond_surf` thresholding and from broad GEMSDOE29 conductivity fusions by testing **signed side asymmetry** conditioned on an independent step. |
| **Mimic / falsification** | Clay-rich sediments, saline groundwater, non-faulted stratigraphic pinch-out. Test: permute conductivity grid, compare vs. symmetric-gradient control; test inside/outside mapped basin footprints. |
| **Cost / DTI** | **Medium cost** if the same provided grids are authenticated and restored (currently absent). **Expected DTI: medium-high** — physically motivated for geothermal-associated faults, but conductivity is confounded by lithology. |

---

## H3 — Slope-direction asymmetry along a persistent buried edge [RANK 3: medium expected DTI, low–medium cost]

| Field | Specification |
|---|---|
| **Layers** | `det_elev` (and optional 1 m 3DEP DEM if obtainable), plus a persistent gravity/magnetic edge orientation from `iso_grav_anom`/`rtp` (multi-scale structure tensor). |
| **Physical signature** | Along each persistent potential-field edge, sample detrended-elevation slope/curvature profiles perpendicular to the edge at multiple widths (100–500 m), requiring consistent profile sign (e.g., down-to-west) over ≥1 km strike length. Detects subtle displaced piedmont surfaces even where no scarp is mapped. |
| **Why it could catch a missing fault** | Fault throw can generate a subtle topographic asymmetry (faulted alluvial fan, piedmont step) that persists along strike while being invisible as a single-pixel scarp. Conditioning on a subsurface edge reduces purely erosional false positives. |
| **Difference from repo** | No implementation here. Differs from individual scarp detectors (e.g., GEMSDOE27 topo-gap-closure, GEMSDOE10 lidar scarps) by testing **profile-along-edge** rather than isolated scarp pixels. |
| **Mimic / falsification** | Drainage incisions, alluvial-fan margins, shorelines, roads, landslides. Ablate the asymmetry requirement; test road-buffer exclusion; compare vs. slope-magnitude-only control. |
| **Cost / DTI** | **Low–medium cost** if `det_elev` is authenticated and restored; higher-resolution 3DEP might help but exact coverage is unverified and the current data arrays are absent. **Expected DTI: medium** — good where piedmont is preserved, weak where eroded/buried. |

**External data check if pursued:** [USGS 3DEP 1 m DEM](https://www.usgs.gov/3d-elevation-program) — publicly free and unrestricted per USGS, but relevant tiles for the GEMS footprint and their coverage have **not been downloaded or verified in this sandbox** (network allowlist blocks direct fetch). Do **not** propose as viable until bytes, licensing, and alignment are checked.

---

## H4 — Catchment-normalized cross-drainage deflection (high cost, not yet viable) [RANK 4: low–medium expected DTI, high cost]

| Field | Specification |
|---|---|
| **Layers** | Absolute-elevation DEM (required — not in competition 19-band stack which has only `det_elev`); lithology proxy if available. |
| **Physical signature** | Build channel network from DEM (D8 flow); for each candidate line, measure repeated cross-channel deflections (sinuosity offset, knick-point alignment) and opposing-bank relief; normalize by catchment size and lithologic resistance. Repeated, catchment-normalized deflections are scored, not single-channel bends. |
| **Why it could catch a missing fault** | A buried strike-slip or normal fault can systematically deflect multiple drainages even where scarps are eroded; normalization prevents large catchments from dominating. |
| **Difference from repo** | Not implemented. Differs from chi-corridor (GEMSDOE60) and scarp-ridge methods by requiring **repeated, normalized cross-channel geometry** rather than single-ridge or profile metrics. |
| **Mimic / falsification** | Differential erosion at lithologic contacts, inherited paleochannels, roads/terraces. Compare vs. lithology-stratified null; require ≥3 independent deflections. |
| **Cost / DTI** | **High cost** (DEM hydrology, lithology lookup). **Expected DTI: low–medium** — high confounding; not clearly novel across the full fleet. |

**External data required:** Free, official source exists ([USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)), but **obtainability not verified** in this sandbox (tiles/coverage not fetched). Per prompt: **not viable until verified obtainable** — therefore ranked lower despite potential complementarity.

---

## H5 — Flight-line repeatability as an acquisition-artifact veto (instrument reliability test) [RANK 5: low expected DTI improvement, high cost]

| Field | Specification |
|---|---|
| **Layers** | Original [USGS GeoDAWN magnetic line data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — independent flight-line vs. tie-line grids. |
| **Physical signature** | Re-grid flight-line and tie-line magnetic data independently; estimate multi-scale magnetic edge normals separately; retain only locations where \|Δazimuth\| ≤15° and edge strength correlation ρ≥0.6 across acquisition directions. This is a **veto/filter**, not a new lineament source. |
| **Why it could help find a missing fault** | A geologic boundary should not depend on flight direction; an unmapped concealed trace should survive an acquisition-consistency filter, while striping/altitude artifacts are suppressed. |
| **Difference from repo** | No implementation. Unlike fused lineament methods, this tests **acquisition repeatability** rather than adding a geological layer. |
| **Mimic / falsification** | Real lithologic contacts and dikes also survive; uneven flight geometry may cause false disagreement. Validate: synthetic striping injection; compare vs. no-veto baseline on same holdouts. |
| **Cost / DTI** | **High cost** (line-level re-gridding). **Expected DTI: low** as a standalone — improves precision (reduces FP) more than recall. Useful only as a post-filter for H1/H2. |

**External data required:** [USGS GeoDAWN line CSVs and grids](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — marked **CC0** and publicly listed, but direct binary fetch is **blocked in this sandbox** (hosts outside allowlist). Therefore **not verified obtainable** — proposed as instrument-reliability theory only, not an operational lane.

---

## Ranking summary

| Rank | Hypothesis | Expected DTI upside (qualitative) | Implementation cost | Viability today |
|---|---|---|---|---|
| 1 | H1 depth-shifted gravity–magnetic discontinuity | Highest qualitative potential in this archived draft | Medium | Not authorized; lane unassigned, data absent, registry policy unresolved |
| 2 | H2 conductive-flank asymmetry | Medium-high qualitative potential in this archived draft | Medium | Not authorized; lane unassigned, data absent, registry policy unresolved |
| 3 | H3 slope-direction asymmetry along buried edge | Medium qualitative potential in this archived draft | Low–medium | Not authorized; required inputs and registry gates not verified |
| 4 | H4 catchment-normalized drainage deflection | Low–medium qualitative potential in this archived draft | High | Not viable until exact 3DEP tiles and coverage are verified |
| 5 | H5 flight-line repeatability veto | Low qualitative potential in this archived draft | High | Not viable until GeoDAWN line data and usable coverage are verified |

No proposal here is validated by canaries, HOLDOUT-DTI, uniqueness, or format checks. This is an archived draft, not an experiment selector. The active brief lists four proposals and retains **UNASSIGNED** lane status; no next experiment or slot is selected.

*Scientific grounding: [USGS Argenta Rise study](https://pubs.usgs.gov/publication/70271418) (multi-physics for possible blind geothermal system — does not validate H1's shift rule), [USGS play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and) (blind systems via multiple observations), [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) (acquisition geometry and limitations; CC0), [USGS structural discontinuities](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa) (stepovers → hydrothermal systems, but not proof of any raster cell).*
