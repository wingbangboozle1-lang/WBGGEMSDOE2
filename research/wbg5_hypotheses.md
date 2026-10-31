# WBG5 candidate hypotheses — ranked before implementation (2026-10-31)

Scope: the DOE GEMS Prize fault-prediction task (`https://www.drivendata.org/competitions/306/competition-doe-gems/`).
Everything below was ranked **before** implementation, with the exact available layers named. Scores quoted
after each hypothesis are outcomes, not forecasts, and are labelled with their evaluator.

## What the metric rewards (verified)

Distance-weighted Tversky with `k(d) = max(1 − d/300 m, 0)`:

```
DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)
TP_w = Σ_g max_x p(x)·k(d(x,g))
FP_w = Σ_x p(x)·[1 − max_g k(d(x,g))]
```

Source: competition page 967 (`.../page/967/`). The organizer masks all USGS/INGENIOUS fault pixels
(community thread 11516), scores one pooled index over the public subset (11550), and counts "new fault"
as any fault pixel not already captured by those sources, **including continuations and splays of known
systems** (11536). A dot within 1 px of a truth pixel earns 0.67 TP and 0.33 FP; a dot 3 px away earns
0 TP and 1.0 FP. **Sub-pixel alignment, not coverage, dominates.**

## Ranked hypotheses

### H1 — Independent state-map transfer (implemented; the selected lane)

| Field | Value |
|---|---|
| Layers | All 19 organizer bands; 11 `lidar_scarp_features` bands; 8 `geodawn_rad` bands; distance-to-catalogue, distance-to-springs, distance-to-vents |
| Physical signature | Multi-layer fault-likeness: magnetic/gravity gradient alignment, potassium–uranium enrichment, topographic steps and scarp coherence |
| Label source | USGS State Geologic Map Compilation structure layers for NV and CA (`NV_structure.shp`, `CA_structure.shp`, public domain, `https://mrdata.usgs.gov/geology/state/`), rasterised to the competition grid |
| Why it catches an uncatalogued fault | The SGMC records bedrock structures that are absent from the Quaternary USGS/INGENIOUS catalogue. Under the organizers' own definition those pixels are "not already captured", so a classifier trained on SGMC is directly targeting the un-catalogued class rather than re-drawing the catalogue |
| Named non-fault mimic | Fluvial terrace risers, landslide headwalls, Lake Lahontan shorelines, road cuts and lithologic contacts — all produce the same topographic step and magnetic contrast |
| Difference from prior repo methods | Prior lanes used catalogue-derived continuity/halo features or hand-tuned scarp rules. H1 never uses a competition label; its only label source is an external public map, so there is no circularity with the holdout |
| Expected gain vs cost | Highest expected gain, highest cost (training + full-grid inference, ~10 min). Ranked 1 |
| Outcome | **SGMC-PROXY-DTI 0.3234** (95% CI 0.3058–0.3415) at 150k dots, out-of-fold; 1.64× GEMSDOE32 B2 at equal budget on the same truth |

### H2 — Lidar scarp co-occurrence prior (implemented; weak)

| Field | Value |
|---|---|
| Layers | `lidar_scarp_features` bands `upface_max`, `downface_max`, `coh100`, `relief`, `strike` agreement |
| Physical signature | Aligned, coherent scarps with consistent facing direction |
| Why it catches an uncatalogued fault | Young surface rupture leaves a fresh scarp even where no Quaternary trace is mapped |
| Named non-fault mimic | Lake Lahontan shoreline terraces, alluvial fan edges, landslide headwalls |
| Difference from prior methods | Uses band agreement (facing + coherence), not a single-band threshold |
| Expected gain vs cost | Medium gain, low cost. Ranked 2 |
| Outcome | 0.2408 SGMC proxy at 150k (below topography alone); 0.0896 in hide-and-recover, the best single prior but only ~9% above random (0.0820) |

### H3 — Detrended topography percentile (implemented as a blend component)

| Field | Value |
|---|---|
| Layers | `det_elev`, `det_elev_slope` |
| Physical signature | Steep, high-relief range fronts and escarpments |
| Why it catches an uncatalogued fault | Active faults localise at range fronts where relief is being renewed |
| Named non-fault mimic | Canyons, glacial cirques, construction cuts, lithologic escarpments |
| Difference from prior methods | Detrended elevation is residual relief rather than raw elevation, so it does not simply pick the highest ground |
| Expected gain vs cost | Medium gain, very low cost. Ranked 3 |
| Outcome | 0.2801 SGMC proxy at 150k; 0.0634 in hide-and-recover (below random) — it helps on bedrock structures, not on withheld Quaternary segments |

### H4 — Multi-scale lineament coherence from magnetic + gravity + DEM (not implemented)

| Field | Value |
|---|---|
| Layers needed | Structure-tensor coherence and orientation on TMI, isostatic gravity, and 1 m lidar DEM — the first two exist at 100 m; the 1 m DEM is **not obtainable in this sandbox** (USGS 3DEP egress blocked) |
| Physical signature | Continuous linear gradients across several wavelengths, with consistent strike |
| Why it catches an uncatalogued fault | Lineaments persist laterally beyond mapped tips; coherence rejects isolated noise |
| Named non-fault mimic | Paleochannels, bedding strike in layered rocks, road/rail alignments |
| Difference from prior methods | Requires genuine orientation continuity, not per-pixel amplitude |
| Expected gain vs cost | Potentially high, high cost; **not validated because the required 1 m DEM is unobtainable here**. Ranked 4 |

### H5 — Catalogue-tip continuation and halo (implemented; rejected)

| Field | Value |
|---|---|
| Layers | Distance-to-catalogue, local strike extrapolation |
| Physical signature | Along-strike tip continuation and step-overs |
| Why it catches an uncatalogued fault | Organizers explicitly count continuations and splays (11536) |
| Named non-fault mimic | Erosional linear valleys continuing a fault trace |
| Difference from prior methods | Orientation-gated rather than radial distance only |
| Expected gain vs cost | Intuitive but circular: catalogue-derived features already encode the answer in the holdout |
| Outcome | `catcont` 0.0021 and `halo` 0.0638 in hide-and-recover — at or below random. **Rejected.** |

## Selection logic

H1 was the only hypothesis whose label source is independent of the competition catalogue, so it is the only
one that can be validated honestly against a withheld set (the SGMC off-catalogue faults). H2/H3 were folded in
as a 0.6/0.4 blend because they are cheap and partially decorrelated. H5 was dropped after it failed the
hide-and-recover test. H4 stays a proposal with an explicit data-blocker.

## What this does **not** claim

- `SGMC-PROXY-DTI` is not a leaderboard score. The organizer mask is not reproducible locally.
- The hide-and-recover holdout is weak and does not include the SGMC term; it is supporting evidence only.
- No weekly slot has been spent, and no organizer receipt exists.
