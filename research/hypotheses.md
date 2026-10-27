# Ranked research hypotheses — none cleared for implementation

**Editorial review:** 2026-10-27 UTC. These are proposals, not results.

**Method lane: UNASSIGNED.** The brief refers to one method paragraph but does not identify a single hypothesis as the assigned lane. P1 is a ranked desk proposal, not authorization.

No experiment was run in this review lane. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No candidate is selected for a weekly slot.

These are desk proposals, not an assigned lane or experiments. The proposed operators are not present in this repository's inspected current implementation, but related approaches exist in other projects. A pinned README-only scan of the nine focus repositories identified prior phase-congruency, radiometric K/Th and drainage work, so those earlier shortlist items were withdrawn; source-reported sibling results were not reproduced. Novelty beyond the inspected files is not established. See evidence/focus_readme_review_20261027.json.

The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. This session reverified the owner-mirrored stack and 19 raw bands in ignored local storage, which may not persist; the derived shared feature bank remains absent. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.

## Qualitative ranking

| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |
|---:|---|---|---|---|
| 1 | **P1 — Upward-continuation ridge trajectories in magnetic data** | Highest qualitative potential among these desk proposals; untested here | Medium–high | Proposal only; not run |
| 2 | **P2 — Matched cross-flank texture displacement** | Moderate qualitative potential; untested here | Medium–high | Proposal only; not run |
| 3 | **P3 — Focal-mechanism nodal-plane consistency** | Lower qualitative potential; external coverage unverified | High | Proposal only; not run |
| 4 | **P4 — Groundwater-head discontinuity across aquifers** | Exploratory; external coverage unverified | High | Proposal only; not run |

## Candidate mechanisms and disconfirming alternatives

### P1 — Upward-continuation ridge trajectories in magnetic data

- **Layers:** rtp magnetic anomaly (owner-mirror band 2); tmi_vg (band 9), context only; det_elev_slope (band 19), terrain sensitivity.
- **Physical signature:** Compute masked, edge-controlled upward continuations of the magnetic field at several declared heights, track the displacement and persistence of oriented ridge maxima across heights, and test a coherent trajectory rather than selecting one amplitude edge. Exclude or explicitly model FFT boundary and survey-seam effects.
- **Why it might find an uncatalogued fault:** A buried basement step can remain detectable in potential-field data where the surface fault map is incomplete. Variation across continuation heights may help distinguish broad source geometry, but does not prove a fault or its position.
- **Difference from reviewed methods:** The local MSPTCD code uses multi-scale gradients and magnetic tilt, but not ridge trajectories across a separately computed continuation series. GEMSDOE32 already lists TMI_up150 in related methods, so this is a proposed extension of an existing family, not a claim of fleet-wide originality. The earlier phase-congruency idea is withdrawn because GEMSDOE32 reports an ARENA49-PCG implementation.
- **Named non-fault mimic:** Lithologic contacts, intrusive dikes, remanent magnetization, uneven survey height, leveling seams, and FFT edge artifacts.
- **Data/access status:** Uses owner-mirrored magnetic and terrain bands, not authenticated organizer inputs. Continuation requires defensible units, nodata and boundary handling; no operator, canary, holdout or registry preflight was run.
- **Source links for manual review:** [https://pubs.usgs.gov/of/2013/1024/i/index_.html](https://pubs.usgs.gov/of/2013/1024/i/index_.html) · [https://pubs.usgs.gov/of/2013/1024/i/downloads/ofr2013-1024_i.pdf](https://pubs.usgs.gov/of/2013/1024/i/downloads/ofr2013-1024_i.pdf) · [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [https://github.com/buffedlizard55-lab/GEMSDOE32/blob/6a28a39a2bca6bbb49cd8a56292c78d474c9ef91/README.md#L19](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/6a28a39a2bca6bbb49cd8a56292c78d474c9ef91/README.md#L19)

### P2 — Matched cross-flank texture displacement

- **Layers:** rtp magnetic anomaly (band 2); det_elev (band 12); det_elev_slope (band 19).
- **Physical signature:** For independently detected candidate lines, search bounded two-dimensional translations between matched oriented texture windows on opposite flanks and require consistent displacement estimates across multiple window sizes; estimate nuisance statistics only on training regions.
- **Why it might find an uncatalogued fault:** A degraded or buried fault can offset a pre-existing magnetic or terrain pattern without producing a continuous mapped scarp; matched texture could suggest the missing line, but it cannot establish causation.
- **Difference from reviewed methods:** The local implementation uses pointwise orientation and Hessian ridges rather than matched-window translation estimates. GEMSDOE28 lists a related two-sided texture-covariance idea as unimplemented and GEMSDOE24 lists a related texture-front proposal; this variant must not be described as wholly new to the fleet.
- **Named non-fault mimic:** Intrusive boundaries, unconformities, erosional contacts, irregular textures and gridding seams can give apparent offsets.
- **Data/access status:** Owner-mirrored bands were restored and hash-checked, not authenticated. Window quality, missing data, displacement ambiguity and fold-local controls have not been tested.
- **Source links for manual review:** [https://pubs.usgs.gov/of/2000/of00-188/of00-188.pdf](https://pubs.usgs.gov/of/2000/of00-188/of00-188.pdf) · [https://github.com/buffedlizard55-lab/GEMSDOE28/blob/91e8d24b87a5cfb3e0562249ae32ae78fe9183b4/README.md#L17](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/91e8d24b87a5cfb3e0562249ae32ae78fe9183b4/README.md#L17) · [https://github.com/buffedlizard55-lab/GEMSDOE24/blob/4ac957757f8494439e2dc51b58ca62c380550e44/README.md#L489](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/4ac957757f8494439e2dc51b58ca62c380550e44/README.md#L489)

### P3 — Focal-mechanism nodal-plane consistency

- **Layers:** USGS ComCat focal-mechanism or moment-tensor products; local magnetic and terrain structural orientations, if independently derived.
- **Physical signature:** For adequately located earthquakes, propagate both ambiguous nodal planes and hypocentral uncertainty into a broad spatial orientation likelihood, then test agreement with independently measured structural orientations; never treat epicenters or nodal planes as exact fault traces.
- **Why it might find an uncatalogued fault:** Seismic ruptures can reflect concealed structures lacking a surface trace. Events with resolved mechanisms might provide orientation evidence where topography is subdued, if coverage and temporal representativeness are adequate.
- **Difference from reviewed methods:** The inspected local implementation uses seismicity density and strain proxies, not explicit uncertainty-weighted focal nodal planes. GEMSDOE32 previously proposed a ComCat-related idea but reported it data-blocked, so the source and broader family are not new.
- **Named non-fault mimic:** Induced seismicity, unrelated deeper faults, uncertain locations, catalog completeness changes, and the two-plane ambiguity.
- **Data/access status:** Not viable here until specific event-product coverage, timestamps, quality and binary/API access are verified; no ComCat records were retrieved in this sandbox.
- **Specific official external source:** [USGS ComCat FDSN event service](https://earthquake.usgs.gov/fdsnws/event/1/). Official documentation describes a public event API, producttype filters for focal-mechanism and moment-tensor products, and event-specific associated products. This sandbox has not queried the target region or verified usable mechanism counts, access or competition sharing.
- **Source links for manual review:** [https://earthquake.usgs.gov/fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/) · [https://github.com/buffedlizard55-lab/GEMSDOE32/blob/6a28a39a2bca6bbb49cd8a56292c78d474c9ef91/README.md#L226](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/6a28a39a2bca6bbb49cd8a56292c78d474c9ef91/README.md#L226)

### P4 — Groundwater-head discontinuity across aquifers

- **Layers:** USGS Water Data for the Nation groundwater-level and monitoring-location records; aquifer identity, observation time, reference elevation and uncertainty metadata; independent magnetic or terrain candidate orientations.
- **Physical signature:** Compare coeval hydraulic heads from comparable aquifer depths on opposite sides of a candidate line, with uncertainty-aware discontinuity against a smooth regional groundwater gradient; require enough well pairs and do not interpolate sparse gaps into certain faults.
- **Why it might find an uncatalogued fault:** Some faults restrict groundwater flow and produce head offsets even where alluvium hides surface expressions. The effect varies by aquifer and not all head discontinuities are faults.
- **Difference from reviewed methods:** The inspected local implementation uses no matched hydraulic-head discontinuity. Historical heat-flow, springs and thermal/geochemical proximity experiments are related but measure different variables; unreviewed sibling implementations may still exist.
- **Named non-fault mimic:** Pumping or recharge, irrigation, aquifer and depth changes, time offsets, stratigraphic barriers and datum errors.
- **Data/access status:** Not viable until target-region well pairing, aquifer metadata, dates and machine-accessible bytes are checked. No data were downloaded here; modern API rate limits and possible free-key requirements must be checked for the eventual workflow.
- **Specific official external source:** [USGS Water Data for the Nation modern APIs](https://api.waterdata.usgs.gov/). Official USGS pages describe public groundwater and metadata APIs; modern services may require a free API key for more than a handful of requests per hour. Target-area coverage, water-level records and sandbox access were not verified.
- **Source links for manual review:** [https://api.waterdata.usgs.gov/](https://api.waterdata.usgs.gov/) · [https://waterdata.usgs.gov/blog/api-whats-new-wdfn-apis/](https://waterdata.usgs.gov/blog/api-whats-new-wdfn-apis/) · [https://pubs.usgs.gov/publication/sir20125261](https://pubs.usgs.gov/publication/sir20125261) · [https://ca.water.usgs.gov/mojave/mojave-water-levels.html](https://ca.water.usgs.gov/mojave/mojave-water-levels.html)

## Why no candidate was validated

The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.

The owner-mirrored competition inputs are not authenticated, and the shared derived feature bank is missing; ignored raw caches may not persist. In this review lane, no spatial holdout, feature-alone leakage canary, matched incumbent comparison, or confidence interval was computed. Prior source-reported results are preserved separately and were not independently replayed here; do not substitute them for a validated result for a new candidate.

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
- [USGS ComCat event API](https://earthquake.usgs.gov/fdsnws/event/1/) and [Water Data APIs](https://api.waterdata.usgs.gov/) — official sources named for P3 and P4; target-region product coverage and sandbox access remain unverified.

**Evidence note:** Official source pages were rechecked through the research page renderer on 2026-10-27 UTC; binary access was not verified. See the [dated source recheck](source-verification-20261027.md) and [`research/sources.md`](sources.md) for the recorded access status and limitations.
