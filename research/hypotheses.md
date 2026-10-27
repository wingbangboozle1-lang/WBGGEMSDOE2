# Ranked research hypotheses — none cleared for implementation

**Editorial review:** 2026-10-27 UTC. These are proposals, not results.

**Method lane: UNASSIGNED.** The brief refers to one method paragraph but does not identify a single hypothesis as the assigned lane. H1 is a ranked proposal, not an authorization.

No experiment was run in this review lane. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No candidate is selected for a weekly slot.

Not implemented or tested in this repository's present review lane. The currently observed refs for all nine priority sites have changed since the pinned rasters; their new contents have not been audited. Therefore no claim is made that these ideas have never been tried anywhere across the fleet.

The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. The local cache and derived shared feature bank are absent in this checkout. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.

## Qualitative ranking

| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |
|---:|---|---|---|---|
| 1 | **H1 — Depth-shifted, multiscale gravity–magnetic discontinuity** | Highest qualitative potential of this shortlist; untested | Medium | Proposal only; not run |
| 2 | **H2 — Conductive-flank asymmetry conditioned on a potential-field edge** | Moderate qualitative potential; overlaps a previously explored family | Medium | Proposal only; not run |
| 3 | **H3 — Repeated cross-drainage deflection across a candidate structure** | Lower qualitative potential; external-data feasibility unverified | High | Proposal only; not run |
| 4 | **H4 — Cross-flight-line repeatability of buried magnetic edges** | Lowest direct prediction potential; primarily an artefact-control experiment | High | Proposal only; not run |

## Candidate mechanisms and disconfirming alternatives

### H1 — Depth-shifted, multiscale gravity–magnetic discontinuity

- **Layers:** iso_grav_anom (owner-mirror band 13); rtp (owner-mirror band 2); depth_to_base_surf (owner-mirror band 15; official metadata says conductive-base depth, not verified basement depth); det_elev (owner-mirror band 12).
- **Physical signature:** At several fixed spatial scales, compare signed gravity-edge normals with magnetic-gradient ridges at a bounded cross-normal offset informed by a depth/dip proxy; test both magnetic polarities and retain only scale-persistent paired edges.
- **Why it might find an uncatalogued fault:** A buried structural discontinuity may juxtapose density and magnetic properties beneath basin fill where a surface trace is weak or absent. The proposal uses subsurface physical-property contrasts rather than catalogue proximity. This is a plausible target for unmapped segments, not proof that the catalogue omits only surface-visible faults.
- **Difference from reviewed methods:** Different as proposed from the named pseudo-gravity residual, simple potential-field fusion, dotted-ridge, catalogue-gap and geothermal-PINN families: it tests a depth-conditioned spatial offset between paired signed edge responses. Related methods elsewhere are not exhaustively audited.
- **Named non-fault mimic:** An unfaulted lithologic contact or intrusive dike can produce aligned gravity and magnetic edges; flight-line striping and gridding artefacts can also create apparent paired boundaries.
- **Data/access status:** The 19-band feature names are recorded in a hash-checked owner mirror, not an authenticated DrivenData download. The local data/cache and derived shared feature bank are absent in this checkout; the pinned shared template must be restored and provenance rechecked before any run.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://pubs.usgs.gov/publication/70271418](https://pubs.usgs.gov/publication/70271418) · [https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and)

### H2 — Conductive-flank asymmetry conditioned on a potential-field edge

- **Layers:** cond_surf (owner-mirror band 17); depth_to_base_surf (owner-mirror band 15; official metadata terminology must be retained); iso_grav_anom_hg (owner-mirror band 18) and iso_grav_anom_vg (owner-mirror band 11); det_elev_slope (owner-mirror band 19) as topographic context.
- **Physical signature:** Estimate signed conductivity contrast on opposite sides of a persistent gravity edge, normalize each flank against its local background and depth, and test whether the asymmetry is stable across scales rather than using raw conductivity or a symmetric buffer.
- **Why it might find an uncatalogued fault:** A concealed fault-related fluid or alteration pathway could make the two flanks electrically asymmetric even where a mapped trace is missing. It is a conditional physical-property test, not a rule that high conductivity means a fault.
- **Difference from reviewed methods:** The proposed statistic is a signed, edge-conditioned cross-flank contrast rather than simple co-location or a vent-proximity prior. However, the user-provided history includes conductivity/flank-labelled methods, so this is not claimed to be globally novel and should rank below H1 unless exact old code shows a meaningful distinction.
- **Named non-fault mimic:** Saline basin fill, clay-rich strata, groundwater, and non-faulted lithologic boundaries can all create conductivity asymmetry.
- **Data/access status:** Uses bands named in the owner-mirrored numerical feature stack; the original competition bytes and current local derived cache are not available/authenticated here.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

### H3 — Repeated cross-drainage deflection across a candidate structure

- **Layers:** USGS 3DEP bare-earth digital elevation model (specific tiles and resolution not established here); det_elev_slope (owner-mirror band 19) for comparison only.
- **Physical signature:** Derive channels from absolute elevation, measure repeated channel azimuth changes, knickzones, and opposing-bank relief across the same candidate line, and normalize by upstream contributing area; require several independent crossings rather than a single scarp.
- **Why it might find an uncatalogued fault:** A buried or eroded fault may deflect multiple channels without leaving a continuous scarp, creating a geomorphic expression beyond catalogue segment endpoints. Channel behaviour is supporting evidence, not a fault label.
- **Difference from reviewed methods:** Different from single-scarp, slope-asymmetry, chi-corridor and dotted-ridge methods because it tests repeated cross-channel geometry using an absolute DEM and catchment normalization. Fleet-wide novelty is unverified.
- **Named non-fault mimic:** Lithologic contacts, differential erosion, alluvial fans, inherited drainage, capture, roads, and terraces can deflect channels.
- **Data/access status:** Not viable in this checkout until the exact official DEM tiles, coverage, resolution and permitted download are verified; none were downloaded.
- **Specific official external source:** [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services). The cited USGS page is recorded in the source register as describing free, unrestricted 3DEP products. Study-area tile coverage and actual binary access have not been checked; therefore the data are not yet verified obtainable for this experiment.
- **Source links for manual review:** [https://www.usgs.gov/3d-elevation-program/about-3dep-products-services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)

### H4 — Cross-flight-line repeatability of buried magnetic edges

- **Layers:** USGS GeoDAWN magnetic flight-line observations and acquisition-direction metadata; mag_anom (owner-mirror band 1) and tmi_hg (owner-mirror band 3) for gridded comparison.
- **Physical signature:** Estimate edge normals independently from crossing flight-line directions and retain only anomalies whose location and orientation are reproducible across acquisition directions; use disagreement as an artefact veto, not as a positive fault label.
- **Why it might find an uncatalogued fault:** A real subsurface physical-property boundary potentially associated with an unmapped fault should be spatially stable across independent acquisition directions, unlike some flight-line artefacts. This test improves measurement reliability; it does not establish that a stable edge is a fault.
- **Difference from reviewed methods:** This is an acquisition-geometry robustness test, not another point-density, terrain-scarp, geothermal-proximity, or catalogue-gap score. No local implementation is present; fleet-wide novelty is unverified.
- **Named non-fault mimic:** A lithologic contact, dike, or non-fault magnetic body is also stable across flight directions; uneven line coverage can create false disagreement.
- **Data/access status:** The USGS release page is recorded as listing flight-line data and grids, but the line-level files and usable crossing coverage were not downloaded or verified in this environment. Not viable here until that check succeeds.
- **Specific official external source:** [USGS GeoDAWN airborne magnetic and radiometric survey release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). The public release page is recorded as available and CC0 in the source register; its binary source host was not reachable in the prior sandbox check. Exact flight-line file access and spatial overlap remain unverified.
- **Source links for manual review:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

## Why no candidate was validated

The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.

The current checkout also lacks the competition rasters and derived feature cache. No spatial holdout, feature-alone leakage canary, matched incumbent comparison, or confidence interval can be reported. Do not substitute a projection or a previously reported parallel result for a protocol-valid HOLDOUT-DTI.

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
- [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) — the official source named for H3; exact tiles/coverage remain unverified.

**Evidence note:** Research/source pages were last checked in the repository's source register on 2026-10-26 UTC. This editorial review did not fetch the external non-GitHub hosts; see [`research/sources.md`](sources.md) for the recorded access status and limitations.
