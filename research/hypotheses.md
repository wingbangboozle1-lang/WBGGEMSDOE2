# Ranked research hypotheses — none cleared for implementation

**Editorial review:** 2026-10-27 UTC. These are proposals, not results.

**Method lane: UNASSIGNED.** The brief refers to one method paragraph but does not identify a single hypothesis as the assigned lane. H1 is a ranked proposal, not an authorization.

No experiment was run in this review lane. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No candidate is selected for a weekly slot.

Current source review found that the prior H1 depth-shift and H2 conductive-flank proposals are already implemented in src/wbggems/msptcd.py. They are NOT new hypotheses. H1 and H2 below replace those stale proposals with unimplemented patch-displacement and physical-null-model tests. H3/H4 remain unimplemented external-data proposals. Novelty is bounded to reviewed local source, not proven across the whole fleet; all nine site heads have changed.

The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. The release-review session restored and reverified the owner-mirrored stack and 19 raw bands in ignored local storage, which may not persist; the derived shared feature bank remains absent. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.

## Qualitative ranking

| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |
|---:|---|---|---|---|
| 1 | **H1 — Cross-fault marker displacement by paired patch registration** | Highest qualitative potential of this shortlist; untested | Medium–high | Proposal only; not run |
| 2 | **H2 — Basin-margin gravity-step model versus intrusive-body null** | Moderate qualitative potential; overlaps a previously explored family | High | Proposal only; not run |
| 3 | **H3 — Repeated cross-drainage deflection across a candidate structure** | Lower qualitative potential; external-data feasibility unverified | High | Proposal only; not run |
| 4 | **H4 — Cross-flight-line repeatability of buried magnetic edges** | Lowest direct prediction potential; primarily an artefact-control experiment | High | Proposal only; not run |

## Candidate mechanisms and disconfirming alternatives

### H1 — Cross-fault marker displacement by paired patch registration

- **Layers:** tc total radiometric counts (owner-mirror band 6; not magnetic tilt); det_elev (owner-mirror band 12); rtp (owner-mirror band 2); iso_grav_anom (owner-mirror band 13).
- **Physical signature:** Along candidate gravity/magnetic boundaries, register radiometric and detrended-terrain texture patches on opposite sides. Compare a shared nonzero along-strike translation with a zero-displacement null using held-out texture pixels; require repeated marker offsets across independent patches, not merely two parallel edges.
- **Why it might find an uncatalogued fault:** An eroded or concealed strike-slip component may displace inherited surface markers without producing a continuous mapped scarp. Coherent cross-boundary displacement is a kinematic hypothesis for an unmapped segment; it is not a fault label and may fail beneath thick cover.
- **Difference from reviewed methods:** MSPTCD uses depth-shifted edge-amplitude concordance and conductive-flank asymmetry. This proposal instead estimates displacement of repeated marker texture across a boundary, compares against a zero-offset null, and demands spatial replication. No patch-registration displacement estimator was found in the reviewed local Python source.
- **Named non-fault mimic:** Drainage capture, terrace migration, lithological texture changes, and georegistration offsets between surveys can create apparent marker displacement.
- **Data/access status:** Raw 19-band owner-mirrored inputs were restored and SHA-256 verified in this review, with 19 raw cached bands. They are not organizer-authenticated; the shared derived feature bank and a compliant release path are still missing. No new external dataset is required, but this proposal is blocked by lane/registry gates.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://pubs.usgs.gov/publication/70271418](https://pubs.usgs.gov/publication/70271418) · [https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and)

### H2 — Basin-margin gravity-step model versus intrusive-body null

- **Layers:** iso_grav_anom (owner-mirror band 13); iso_grav_anom_hg (owner-mirror band 18); rtp (owner-mirror band 2); det_elev (owner-mirror band 12).
- **Physical signature:** Fit short cross-boundary gravity profiles to competing forward-response families: an asymmetric buried density step and a compact symmetric intrusive lens, each with the same nuisance trend and penalized parameter count. Rank held-out profile likelihood improvement of the step model, requiring stable parameters along strike and at multiple window sizes; use magnetic response as a consistency check, not a fault label.
- **Why it might find an uncatalogued fault:** A buried basin-bounding fault can juxtapose density units without a visible trace. Explicitly preferring a persistent asymmetric step over a compact-body null could reject strong non-fault magnetic anomalies missed by simple edge ranking.
- **Difference from reviewed methods:** Existing code calculates derivative amplitude, tilt, Hessian ridges and orientation concordance. It does not fit competing gravity forward-model families on cross-boundary profiles with held-out residuals. This is physical model discrimination rather than another edge-fusion score. Nonunique gravity inversion remains a major limitation.
- **Named non-fault mimic:** An unfaulted depositional basin edge or dipping lithological contact can fit a density step; regional trend removal and shallow topographic mass can mimic asymmetry.
- **Data/access status:** Raw 19-band owner-mirrored inputs were restored and SHA-256 verified in this review, with 19 raw cached bands. They are not organizer-authenticated; the shared derived feature bank and a compliant release path are still missing. No new external dataset is required, but this proposal is blocked by lane/registry gates.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

### H3 — Repeated cross-drainage deflection across a candidate structure

- **Layers:** USGS 3DEP bare-earth digital elevation model (specific tiles and resolution not established here); det_elev_slope (owner-mirror band 19) for comparison only.
- **Physical signature:** Derive channels from absolute elevation, measure repeated channel azimuth changes, knickzones, and opposing-bank relief across the same candidate line, and normalize by upstream contributing area; require several independent crossings rather than a single scarp.
- **Why it might find an uncatalogued fault:** A buried or eroded fault may deflect multiple channels without leaving a continuous scarp, creating a geomorphic expression beyond catalogue segment endpoints. Channel behaviour is supporting evidence, not a fault label.
- **Difference from reviewed methods:** Different from single-scarp, slope-asymmetry, chi-corridor and dotted-ridge methods because it tests repeated cross-channel geometry using an absolute DEM and catchment normalization. Fleet-wide novelty is unverified.
- **Named non-fault mimic:** Lithologic contacts, differential erosion, alluvial fans, inherited drainage, capture, roads, and terraces can deflect channels.
- **Data/access status:** Not viable in this checkout until the exact official DEM tiles, coverage, resolution and permitted download are verified; none were downloaded.
- **Specific official external source:** [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services). The cited USGS page is recorded in the source register as describing free, unrestricted 3DEP products. Study-area tile coverage and actual binary access have not been checked; therefore the data are not yet verified obtainable for this experiment. Current sandbox allowlist excludes this host; exact binary obtainability remains unverified and the proposal is not viable here.
- **Source links for manual review:** [https://www.usgs.gov/3d-elevation-program/about-3dep-products-services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)

### H4 — Cross-flight-line repeatability of buried magnetic edges

- **Layers:** USGS GeoDAWN magnetic flight-line observations and acquisition-direction metadata; mag_anom (owner-mirror band 1) and tmi_hg (owner-mirror band 3) for gridded comparison.
- **Physical signature:** Estimate edge normals independently from crossing flight-line directions and retain only anomalies whose location and orientation are reproducible across acquisition directions; use disagreement as an artefact veto, not as a positive fault label.
- **Why it might find an uncatalogued fault:** A real subsurface physical-property boundary potentially associated with an unmapped fault should be spatially stable across independent acquisition directions, unlike some flight-line artefacts. This test improves measurement reliability; it does not establish that a stable edge is a fault.
- **Difference from reviewed methods:** This is an acquisition-geometry robustness test, not another point-density, terrain-scarp, geothermal-proximity, or catalogue-gap score. No local implementation is present; fleet-wide novelty is unverified.
- **Named non-fault mimic:** A lithologic contact, dike, or non-fault magnetic body is also stable across flight directions; uneven line coverage can create false disagreement.
- **Data/access status:** The USGS release page is recorded as listing flight-line data and grids, but the line-level files and usable crossing coverage were not downloaded or verified in this environment. Not viable here until that check succeeds.
- **Specific official external source:** [USGS GeoDAWN airborne magnetic and radiometric survey release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). The public release page is recorded as available and CC0 in the source register; its binary source host was not reachable in the prior sandbox check. Exact flight-line file access and spatial overlap remain unverified. Current sandbox allowlist excludes this host; exact binary obtainability remains unverified and the proposal is not viable here.
- **Source links for manual review:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

## Why no candidate was validated

The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.

The owner-mirrored competition inputs are not authenticated, and the shared derived feature bank is missing; ignored raw caches may not persist. No spatial holdout, feature-alone leakage canary, matched incumbent comparison, or confidence interval can be reported. Do not substitute a projection or a previously reported parallel result for a protocol-valid HOLDOUT-DTI.

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

**Evidence note:** Official source pages were rechecked through the research page renderer on 2026-10-27 UTC; binary access was not verified. See the [dated source recheck](source-verification-20261027.md) and [`research/sources.md`](sources.md) for the recorded access status and limitations.
