# Ranked research hypotheses — none cleared for implementation

**Editorial review:** 2026-10-27 UTC. These are proposals, not results.

**Method lane: UNASSIGNED.** The brief references one method paragraph but does not identify which one. This ranking is not a lane assignment.

No experiment was run in this review lane. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No candidate is selected for a weekly slot.

The proposals below are not implemented or tested as described in the reviewed MSPTCD campaign or this review lane. They are not claims of fleet-wide or scientific novelty: the pinned registry is incomplete and all nine priority repositories have changed since their last audited refs. Previous H1 depth-shifted gravity/magnetics and H2 conductive-flank asymmetry are retired from this untried shortlist because MSPTCD actually implemented closely related features.

The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. This session reverified the owner-mirrored stack and 19 raw bands in ignored local storage, which may not persist; the derived shared feature bank remains absent. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.

## Qualitative ranking

| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |
|---:|---|---|---|---|
| 1 | **H1 — Repeated, catchment-normalized cross-drainage deflections** | Highest qualitative potential in this shortlist; untested; no numerical uplift forecast | High: DEM processing and multiple hydrologic controls | Proposal only; not run |
| 2 | **H2 — Multi-depth magnetotelluric conductance coherence with uncertainty** | Moderate potential; explicitly limited by depth and resolution; untested | High: survey resolution, reprojection, independent source overlap and anti-leakage checks | Proposal only; not run |
| 3 | **H3 — Cross-flight-line repeatability veto for magnetic boundaries** | Uncertain direct uplift; primarily an artifact-control hypothesis; untested | High: raw line downloads, acquisition-geometry reconstruction and coverage checks | Proposal only; not run |
| 4 | **H4 — Repeat-pass deformation discontinuity with a pumping control** | Lower and highly uncertain potential; untested, including study-area data availability | High: independent acquisition, atmospheric correction, temporal control and georeferencing | Proposal only; not run |

## Candidate mechanisms and disconfirming alternatives

### H1 — Repeated, catchment-normalized cross-drainage deflections

- **Layers:** USGS 3DEP bare-earth DEM, exact study tiles unverified; derived drainage network and upstream contributing area; owner-mirrored slope only as a comparison.
- **Physical signature:** Ask whether several independent streams change direction or bed gradient consistently on crossing a candidate line, normalized for drainage area and relief; compare with randomized orientations and other lithology boundaries.
- **Why it might find an uncatalogued fault:** A structure may leave consistent offsets across several streams even where the surface trace is interrupted; the signals are hypothesized evidence, not proof that unmapped faults must be surface-expressed.
- **Difference from reviewed methods:** Requires replicated cross-channel geometry and catchment normalization, unlike MSPTCD's multiscale Hessian scarp and flank features or a single slope/chi corridor. The exact relevant newer fleet implementations were not checked.
- **Named non-fault mimic:** Lithological boundaries, terraces, alluvial fans, stream capture, roads and inherited drainage can create repeated deflections.
- **Data/access status:** Official 3DEP products are free and unrestricted; exact AOI tiles, resolution and binary access have not been established. No new data or features downloaded.
- **Specific official external source:** [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services). Public page checked 2026-10-27: free without use restrictions. Study tiles, coverage and binary access not verified; this is not yet demonstrated obtainable in this sandbox.
- **Source links for manual review:** [https://www.usgs.gov/3d-elevation-program/about-3dep-products-services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) · [https://pubs.usgs.gov/fs/2015/3028/pdf/fs2015-3028.pdf](https://pubs.usgs.gov/fs/2015/3028/pdf/fs2015-3028.pdf)

### H2 — Multi-depth magnetotelluric conductance coherence with uncertainty

- **Layers:** USGS Great Basin conductance maps at five depth ranges; original MT station/uncertainty metadata; potential-field edge orientation only as context.
- **Physical signature:** Compare the orientation and location of conductance transitions across separately resolved depth intervals, propagate uncertainty and covariance from the common inversion, and reject apparent continuity in undersampled areas; do not treat the intervals as independent observations.
- **Why it might find an uncatalogued fault:** A buried crustal electrical boundary could be associated with a concealed fault, but a deep conductor need not map to a 100 m surface trace and resolution may be far too coarse.
- **Difference from reviewed methods:** Uses externally derived multiple depth slices and resolution/uncertainty rather than MSPTCD's single conductive-surface flank comparison or gravity-magnetic dip shift; shared source data and overlap must first be established.
- **Named non-fault mimic:** Clays, saline fluids, lithologic contacts and gridding artefacts also create conductance boundaries; a conductor can be geologically unrelated to a fault.
- **Data/access status:** USGS describes five depth ranges from 2 to 200 km; the release is marked CC0. Exact binary access, study-area coverage and relationship to the organizer feature bands have not been verified.
- **Specific official external source:** [USGS Electrical Conductance Maps of the Great Basin](https://www.usgs.gov/data/electrical-conductance-maps-great-basin-usa). Public release page checked 2026-10-27 and marked CC0. Actual raster download, local resolution and usable overlap remain unverified.
- **Source links for manual review:** [https://www.usgs.gov/data/electrical-conductance-maps-great-basin-usa](https://www.usgs.gov/data/electrical-conductance-maps-great-basin-usa) · [https://data.usgs.gov/datacatalog/data/USGS:60d39cc1d34e12a1b009c64b](https://data.usgs.gov/datacatalog/data/USGS:60d39cc1d34e12a1b009c64b)

### H3 — Cross-flight-line repeatability veto for magnetic boundaries

- **Layers:** USGS GeoDAWN magnetic flight and tie-line measurements; line orientation, altitude and acquisition metadata; owner-mirrored magnetic raster for comparison.
- **Physical signature:** Compare independently observed boundary locations and orientations from crossing flight and tie lines; downweight structures that shift with acquisition direction or clearance.
- **Why it might find an uncatalogued fault:** A reproducible buried property contrast may support a candidate unseen structure; the test is an artifact veto and cannot establish that a stable contrast is a fault.
- **Difference from reviewed methods:** Tests raw acquisition repeatability, rather than MSPTCD's raster-only gradients and multiscale transforms. Crossing coverage and true acquisition independence are unverified.
- **Named non-fault mimic:** Dikes and unfaulted lithologic contacts are stable across flight directions; sparse crossings or variable clearance can generate false disagreement.
- **Data/access status:** The official release describes flight lines and grids and is marked CC0. Direct binary host is outside this sandbox's allowlist; usable crossing coverage and file access were not verified.
- **Specific official external source:** [USGS GeoDAWN airborne magnetic and radiometric surveys](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Public CC0 release page checked 2026-10-27. Binary download, coverage and crossing geometry remain unverified.
- **Source links for manual review:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

### H4 — Repeat-pass deformation discontinuity with a pumping control

- **Layers:** USGS InSAR deformation observations, specific target-area product not identified; multi-epoch coherence and uncertainty; available groundwater pumping or recharge context.
- **Physical signature:** Look for persistent, independently repeated displacement gradients across a candidate trace while controlling for pumping, atmospheric artefacts, phase unwrapping and seasonal changes.
- **Why it might find an uncatalogued fault:** If a hydraulically or tectonically active concealed boundary produces a repeatable displacement contrast, it may reveal structures outside mapped traces; many faults are inactive and invisible to InSAR.
- **Difference from reviewed methods:** Uses multi-epoch observed deformation and a human-activity control, not MSPTCD's static geodetic and seismic raster features. No relevant-area product has been verified.
- **Named non-fault mimic:** Groundwater pumping, recharge, atmospheric delay, landslides, mines, phase-unwrapping errors and radar decorrelation.
- **Data/access status:** USGS describes downloadable InSAR observations for Las Vegas Valley, not necessarily the competition area. This is a methodological example, not proof of AOI coverage, obtainable binaries, usable temporal alignment or the reuse rights of underlying imagery.
- **Specific official external source:** [USGS Las Vegas Valley InSAR example](https://www.usgs.gov/publications/interferograms-showing-land-subsidence-and-uplift-las-vegas-valley-nevada-1992-99). Public USGS publication page checked 2026-10-27 and describes downloadable GIS products. Their overlap with the competition area, binary access and dataset-specific reuse rights have not been established; do not run until these are verified.
- **Source links for manual review:** [https://www.usgs.gov/publications/interferograms-showing-land-subsidence-and-uplift-las-vegas-valley-nevada-1992-99](https://www.usgs.gov/publications/interferograms-showing-land-subsidence-and-uplift-las-vegas-valley-nevada-1992-99) · [https://www.usgs.gov/centers/land-subsidence-in-california/science/interferometric-synthetic-aperture-radar-insar](https://www.usgs.gov/centers/land-subsidence-in-california/science/interferometric-synthetic-aperture-radar-insar)

## Why no candidate was validated

The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.

For these newly ranked hypotheses, no spatial holdout, feature-alone canary, matched incumbent comparison, or confidence interval was run. A previous three-experiment MSPTCD mapped-fault proxy is reported separately with substantial limitations; it is not a result for these proposals or a valid promotion test. The owner-mirrored inputs are not authenticated and ignored caches may not persist.

The MSPTCD experimental budget was exhausted; this separate documentation review does not grant a new campaign. Feature-alone canaries can flag leakage but passing them cannot prove its absence.

## Gates before any experiment or slot selector

1. Resolve the continuous-prior interpretation and restore an immutable, complete, fresh registry; do not move dots to exploit edge cells.
2. Record the explicit assigned method lane. This shortlist does not assign one.
3. Restore and authenticate the competition inputs and exact shared cached feature stack. Keep the pinned shared evaluator/writer unchanged; report any defect upstream.
4. For each feature alone, compute the leakage canary on every spatially blocked fold. Treat AUC above 0.90 (or its inverse) as leakage until disproven. Derive all catalogue-based features only from visible faults, withhold whole segments plus a buffer, and mask visible faults pixel-exactly.
5. Use the shared pooled DTI evaluator (alpha 0.2, beta 0.8, 300 m triangular kernel), compare against a matched incumbent on identical folds, and report evaluator version, withheld-positive count, and a spatial-block 95% CI.
6. Stop at three experiments or two hours. A holdout result is not an organizer-confirmed score; a format pass is not uniqueness or promotion. Slot selection remains a separate, quota-aware action.

## Official and scientific references

- [DrivenData problem description and provided-feature inventory](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — faults are the prediction target; geothermal favorability is not itself a fault label.
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — magnetic/radiometric survey context and acquisition limitations.
- [USGS Argenta Rise study](https://pubs.usgs.gov/publication/70271418) — independent multi-physics context; does not validate the proposed transforms.
- [USGS blind geothermal play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and) — geothermal context; not a direct submission-score result.
- [DOE GDR INGENIOUS release 1391](https://gdr.openei.org/submissions/1391) — regional data compilation and license information; specific files were not fetched here.
- [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) — the source named for H1; exact tiles/coverage remain unverified.
- [USGS conductance maps](https://www.usgs.gov/data/electrical-conductance-maps-great-basin-usa) — CC0 release for H2; exact local coverage and data access unverified.
- [USGS InSAR example](https://www.usgs.gov/publications/interferograms-showing-land-subsidence-and-uplift-las-vegas-valley-nevada-1992-99) — methodological example for H4, not verified competition-area data.

**Evidence note:** Official source pages were rechecked through the research page renderer on 2026-10-27 UTC; binary access was not verified. See the [dated source recheck](source-verification-20261027.md) and [`research/sources.md`](sources.md) for the recorded access status and limitations.
