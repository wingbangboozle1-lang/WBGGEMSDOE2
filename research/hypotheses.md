# Ranked geological hypotheses — explicit candidate lanes (3–5 required, validated before any slot)

**Status 2026-10-27:** Desk proposals, not executed experiments. This review lane ran **0** experiments; two parallel lanes reported 4 combined experiments, all independently rejected for literal registry overlap and masking. No weekly slot was used. Rankings are qualitative judgments of **expected DTI improvement vs. implementation cost**, not score forecasts. “Not tried in this repo” means absent from `evidence/run_card.json` and `research/findings.md`; novelty across all 90+ GEMSDOE sites is not proven.

**Lane requirement:** The prompt's “single method paragraph” was not uniquely identified. We provisionally nominate **H1** as the only lane if this sandbox is asked to proceed, but no TIF is generated until the literal registry policy is resolved and the shared template is authenticated. Every candidate must pass: (i) surface rank-correlation ≤0.90 and final-dot 3px overlap ≤70% vs. **every** registry raster (before placement and on final dots), (ii) per-feature canary AUC ≤0.90, (iii) pooled HOLDOUT-DTI win with paired 95% CI >0 vs. same-fold incumbent, (iv) byte-level format validation (`[0,1]`, float32, EPSG:32611, footprint mask).

---

## H1 — Depth-shifted, multi-scale gravity/magnetic discontinuity [RANK 1: highest expected DTI improvement, medium cost]

| Field | Specification |
|---|---|
| **Layers used** | `iso_grav_anom` (isostatic gravity anomaly), `rtp` (reduced-to-pole magnetics / TMI), `depth_to_base_surf` (conductive-base depth — *not* assumed to be basement/sediment thickness), `det_elev` (detrended elevation). All four exist in the cached 19-band owner-mirrored stack (`docs/data/feature_cache.json`), rebuilt as label-free raw bands; the shared **derived** bank is absent from pinned template. |
| **Physical signature (transform)** | Multi-scale **signed directional gradients**: at 300 m, 600 m, 1200 m Gaussian scales compute gravity gradient vector **g** and magnetic gradient **m**; estimate dominant gravity-edge normal **n̂** (structure tensor eigenvector); test whether a magnetic edge exists at displacement **d = k·depth_to_base_surf·tan(dip_proxy)** along **n̂**, where **k** is bounded (|k|≤1) and `dip_proxy` is derived per-fold from visible faults only. Test both magnetic polarities; a density contrast does not determine polarity. Output is a scalar concordance score, not a raw field. |
| **Why it could catch a fault missing from USGS/INGENIOUS catalogue** | A buried lithologic offset (e.g., basin-basement step or intrabasinal fault) can be concealed beneath basin fill where no surface scarp is mapped. Gravity senses density contrast; magnetics senses susceptibility contrast; a depth-dependent spatial offset is expected for a dipping contact. Requiring a **shifted** coincidence suppresses purely surficial coincidences. |
| **How it differs from already implemented in this repo** | This repo has **no implementation** — only proposals. It differs *as proposed* from GEMSDOE31's pseudo-gravity residual ([site](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)) and GEMSDOE36's HVG fusion ([site](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)), which use coincident (not shifted) fusion. Related shifted-edge ideas may exist in unpublished parallel lanes; not proven absent. |
| **Named non-fault process that could mimic it** | Unfaulted lithologic contact, mafic dike, or acquisition striping. **Falsification:** cross-orientation test (rotate n̂ 90° should null signal), shuffled-field control (permute magnetic grid), held-out survey-block ablation; require persistence across ≥2 scales. |
| **Implementation cost / expected DTI** | **Medium cost** (uses cached 100 m grids; gradient + structure-tensor code). **Expected DTI: highest of shortlist** — potential-field edges are known fault proxies and the shift adds specificity, but basin geology is noisy. Qualitative; not a numeric forecast. **External data needed:** none beyond competition stack, if `depth_to_base_surf` semantics are accepted as conductive base. |

**Validation steps before any slot:** Run each of the 4 signed-gradient features alone on the 4 spatially-blocked, whole-segment holdouts (visible-faults-only catalogue features, 15px training buffer, visible faults pixel-masked) — stop if any canary AUC >0.90. Then evaluate the fused H1 surface with shared `evaluate_holdout.py` (α=0.2, β=0.8, 300 m triangular, pooled DTI, 58k withheld positives, 95% spatial-block CI). Only a paired delta CI lower bound >0 vs. incumbent justifies a placement attempt.

---

## H2 — Conductive-flank asymmetry conditioned on a structural step [RANK 2: medium-high expected DTI, medium cost]

| Field | Specification |
|---|---|
| **Layers** | `cond_surf` (surface conductivity), `depth_to_base_surf`, `iso_grav_anom` gradients, `det_elev`. |
| **Physical signature** | At each candidate cell, estimate the dominant depth/gravity step orientation; compare mean conductivity on opposite sides (flank difference) normalized by local background and depth: `asym = (cond_left − cond_right) / (cond_local + ε) · w(depth)`, where `w` down-weights shallow basin fill. A candidate requires both a step and a significant asymmetric flank, not conductivity alone. |
| **Why it could catch a missing fault** | Concealed fault zones can host fluid pathways / clay alteration producing a **lateral** conductivity contrast alongside a potential-field step. A flank asymmetry is more specific than a raw conductivity high. |
| **Difference from repo** | No implementation. Differs from simple `cond_surf` thresholding and from broad GEMSDOE29 conductivity fusions by testing **signed side asymmetry** conditioned on an independent step. |
| **Mimic / falsification** | Clay-rich sediments, saline groundwater, non-faulted stratigraphic pinch-out. Test: permute conductivity grid, compare vs. symmetric-gradient control; test inside/outside mapped basin footprints. |
| **Cost / DTI** | **Medium cost** (cached grids). **Expected DTI: medium-high** — physically motivated for geothermal-associated faults, but conductivity is confounded by lithology. |

---

## H3 — Slope-direction asymmetry along a persistent buried edge [RANK 3: medium expected DTI, low–medium cost]

| Field | Specification |
|---|---|
| **Layers** | `det_elev` (and optional 1 m 3DEP DEM if obtainable), plus a persistent gravity/magnetic edge orientation from `iso_grav_anom`/`rtp` (multi-scale structure tensor). |
| **Physical signature** | Along each persistent potential-field edge, sample detrended-elevation slope/curvature profiles perpendicular to the edge at multiple widths (100–500 m), requiring consistent profile sign (e.g., down-to-west) over ≥1 km strike length. Detects subtle displaced piedmont surfaces even where no scarp is mapped. |
| **Why it could catch a missing fault** | Fault throw can generate a subtle topographic asymmetry (faulted alluvial fan, piedmont step) that persists along strike while being invisible as a single-pixel scarp. Conditioning on a subsurface edge reduces purely erosional false positives. |
| **Difference from repo** | No implementation here. Differs from individual scarp detectors (e.g., GEMSDOE27 topo-gap-closure, GEMSDOE10 lidar scarps) by testing **profile-along-edge** rather than isolated scarp pixels. |
| **Mimic / falsification** | Drainage incisions, alluvial-fan margins, shorelines, roads, landslides. Ablate the asymmetry requirement; test road-buffer exclusion; compare vs. slope-magnitude-only control. |
| **Cost / DTI** | **Low–medium cost** (100 m cached `det_elev`; higher-resolution 3DEP would improve signal but is not yet verified obtainable in this sandbox). **Expected DTI: medium** — good where piedmont is preserved, weak where eroded/buried. |

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
| **Physical signature** | Re-grid flight-line and tie-line magnetic data independently; estimate multi-scale magnetic edge normals separately; retain only locations where |Δazimuth| ≤15° and edge strength correlation ρ≥0.6 across acquisition directions. This is a **veto/filter**, not a new lineament source. |
| **Why it could help find a missing fault** | A geologic boundary should not depend on flight direction; an unmapped concealed trace should survive an acquisition-consistency filter, while striping/altitude artifacts are suppressed. |
| **Difference from repo** | No implementation. Unlike fused lineament methods, this tests **acquisition repeatability** rather than adding a geological layer. |
| **Mimic / falsification** | Real lithologic contacts and dikes also survive; uneven flight geometry may cause false disagreement. Validate: synthetic striping injection; compare vs. no-veto baseline on same holdouts. |
| **Cost / DTI** | **High cost** (line-level re-gridding). **Expected DTI: low** as a standalone — improves precision (reduces FP) more than recall. Useful only as a post-filter for H1/H2. |

**External data required:** [USGS GeoDAWN line CSVs and grids](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — marked **CC0** and publicly listed, but direct binary fetch is **blocked in this sandbox** (hosts outside allowlist). Therefore **not verified obtainable** — proposed as instrument-reliability theory only, not an operational lane.

---

## Ranking summary

| Rank | Hypothesis | Expected DTI upside (qualitative) | Implementation cost | Viability today |
|---|---|---|---|---|
| 1 | H1 depth-shifted gravity–magnetic discontinuity | Highest | Medium | Provisionally viable (uses cached competition stack) — but still blocked by literal registry policy |
| 2 | H2 conductive-flank asymmetry | Medium-high | Medium | Provisionally viable (cached stack) — same registry block |
| 3 | H3 slope-direction asymmetry along buried edge | Medium | Low–medium | Viable on 100 m `det_elev`; 1 m 3DEP upgrade not verified |
| 4 | H4 catchment-normalized drainage deflection | Low–medium | High | **Not viable** until 3DEP tiles verified obtainable |
| 5 | H5 flight-line repeatability veto | Low | High | **Not viable** until GeoDAWN lines verified obtainable |

No hypothesis is validated (canaries, HOLDOUT-DTI, uniqueness, format) in this lane. The next step, if authorized, is to run H1's per-feature canaries and pooled HOLDOUT-DTI on the shared evaluator before touching any weekly slot.

*Scientific grounding: [USGS Argenta Rise study](https://pubs.usgs.gov/publication/70271418) (multi-physics for possible blind geothermal system — does not validate H1's shift rule), [USGS play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and) (blind systems via multiple observations), [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) (acquisition geometry and limitations; CC0), [USGS structural discontinuities](https://www.usgs.gov/publications/structural-discontinuities-and-their-control-hydrothermal-systems-great-basin-usa) (stepovers → hydrothermal systems, but not proof of any raster cell).*
