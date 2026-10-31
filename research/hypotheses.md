# Ranked research hypotheses — N5 implemented and gate-passed; no slot spent

**Editorial review:** 2026-10-27 UTC; implementation record added 2026-10-31 UTC. These are proposals and one implementation record, not results.

**Method lane: ASSIGNED — N5 relay/stepover-aperture dots.** The assigned lane is N5 (relay/stepover-aperture off-catalogue dots); it was implemented, ran as Experiment 1 in this review lane, and passed all local gates. One unique TIFF is available to download; upload remains a separate DrivenData/selector decision and no experiment or submission slot was spent.

Experiment 1 (N5 relay-aperture) was run in this review lane and gate-passed; no weekly slot was spent. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No proposal other than N5 is selected for a weekly slot.

Revised after reading all local MSPTCD operators and historical generators: depth-shifted concordance, conductive-flank asymmetry, strain/seismicity conditioning and greedy placement have already been tried here. N1-N4 name unimplemented tests in this checkout, not globally novel methods. Nine priority-site HEADs differ from audited pins, and their newer raster bytes have not all been audited. Concurrent main research reviewed at 29abbf69 includes CBS subsurface-only HGB and E3 flexure/alteration/strain fusion. N1 requires signed cross-profile edge-pair geometry and a body-mimic veto, not their unsigned transforms or a soft weighting change; none of N1–N4 is a claim of globally novel geology or validated performance.

The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. This session reverified the owner-mirrored stack and 19 raw bands in ignored local storage, which may not persist; the separate shared derived feature bank remains absent. The historical MSPTCD feature code now has a versioned orientation correction; its old metrics must not be attributed to the corrected code. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.

## Qualitative ranking

| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |
|---:|---|---|---|---|
| 1 | **N1 — Signed edge-pair cancellation as a non-fault-body veto** | Highest qualitative potential in this revised shortlist; no measured improvement | Medium | Proposal only; not run |
| 2 | **N2 — Radiometric-quiet magnetic-edge transfer under conductive cover** | Moderate qualitative potential; targets a mapping-bias regime rather than more dots | Medium | Proposal only; not run |
| 3 | **N3 — Catalogue-free edge-orientation transport through structural junctions** | Exploratory qualitative potential; high cost and nonunique geological interpretation | High | Proposal only; not run |
| 4 | **N4 — Survey-axis notch-stability veto on gridded edge evidence** | Lowest direct discovery potential; an artefact-control test, not an independent survey | Low to medium | Proposal only; not run |
| — | **N5 — Relay/stepover-aperture off-catalogue dots** | Implemented; gate-passed locally; leaderboard performance unknown — not a score estimate | Low to medium | Implemented; gate-passed; download open; no slot spent |

## Candidate mechanisms and disconfirming alternatives

### N1 — Signed edge-pair cancellation as a non-fault-body veto

- **Layers:** rtp (owner-mirror band 2); iso_grav_anom (owner-mirror band 13); depth_to_base_surf (owner-mirror band 15; conductive-base depth proxy only).
- **Physical signature:** Along gravity-edge normals, sample signed cross-normal gradient profiles at fixed 200, 400 and 800 m smoothing scales. Distinguish a persistent monotonic step from a balanced pair of opposite-polarity lobes returning to background; penalize the latter as a finite-width body hypothesis. Require consistency along strike, not just a high local gradient.
- **Why it might find an uncatalogued fault:** A buried density step can persist under basin fill without a mapped surface trace. This hypothesis tries to reject finite-width magnetic bodies rather than reward proximity to the public catalogue. Some real fault zones also produce paired lobes, so the veto must earn its value on buffered hide-and-recover folds.
- **Difference from reviewed methods:** The local MSPTCD implementation uses unsigned shifted gradient amplitudes and local orientation products, not signed profile return-to-background or paired-lobe cancellation. This is a proposed discriminant, not the already-tested depth-shifted-concordance H1. Prior fleet-wide use cannot be excluded.
- **Named non-fault mimic:** A one-sided unfaulted intrusive or lithologic contact can still resemble a structural step; a real horst or narrow fault-bounded block can resemble a finite-width body and be incorrectly vetoed.
- **Data/access status:** All named raw bands were restored via the unchanged pinned shared cache builder from the 418,912,844-byte public mirror (SHA-256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5). No new external binary is needed for this proposed test. Mirror origin/units are not authenticated as organizer bytes; ignored caches must be verified again before use. No feature or model for this proposal was implemented or evaluated.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://pubs.usgs.gov/publication/70271418](https://pubs.usgs.gov/publication/70271418)

### N2 — Radiometric-quiet magnetic-edge transfer under conductive cover

- **Layers:** tc (owner-mirror band 6; radiometric interpretation plausible, units require source metadata); rtp (owner-mirror band 2); depth_to_base_surf (owner-mirror band 15); cond_surf (owner-mirror band 17; fold-local rank strata, units unverified); det_elev_slope (owner-mirror band 19).
- **Physical signature:** Find magnetic ridges that persist across 300–1000 m smoothing but lose their co-located surface total-count edge in low-relief, deeper-conductive-base strata. Match sampling within fold-local B17 conductivity-rank strata and train any regime threshold on visible-training cells only. Compare this radiometric-quiet branch with the same magnetic-edge model and sampling without the branch.
- **Why it might find an uncatalogued fault:** A subsurface contrast may remain magnetically visible while young sediment conceals a surface lithologic or scarp expression, a plausible omission regime for surface mapping. Radiometric quietness is a cover/measurement hypothesis, not positive evidence of a geothermal vent or a fault by itself.
- **Difference from reviewed methods:** MSPTCD treats terrain-normalized total-count edges as an additional positive feature. This proposal instead tests explicit cross-modal edge disappearance as a cover-conditioned transfer rule, with matched sampling and a negative control. The earlier conductivity-flank and depth-offset ideas are already implemented and are not reused as new hypotheses.
- **Named non-fault mimic:** Moist soil, uniform sediment composition, variable aircraft clearance, weak radiometric signal or a buried non-faulted volcanic/plutonic contact can produce the same discordance.
- **Data/access status:** All named raw bands were restored via the unchanged pinned shared cache builder from the 418,912,844-byte public mirror (SHA-256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5). No new external binary is needed for this proposed test. Mirror origin/units are not authenticated as organizer bytes; ignored caches must be verified again before use. No feature or model for this proposal was implemented or evaluated.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#provided-features) · [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [https://pubs.usgs.gov/publication/70271418](https://pubs.usgs.gov/publication/70271418)

### N3 — Catalogue-free edge-orientation transport through structural junctions

- **Layers:** iso_grav_anom (owner-mirror band 13); rtp (owner-mirror band 2); det_elev (owner-mirror band 12; detrended, not an absolute hydrologic DEM).
- **Physical signature:** Build an edge graph from label-free gravity and magnetic ridges. Transport axial normals along each ridge across scales, measure tangent continuity and curvature at independently supported intersections, and retain junction branches only when both fields support their geometry. Do not seed the graph with catalogue endpoints.
- **Why it might find an uncatalogued fault:** Blind transfer structures can interrupt or join subsurface property boundaries where no continuous surface fault is mapped. The proposed graph tests independent geophysical geometry rather than completing a known catalogue trace. Geometric complexity alone is not evidence of heat or permeability.
- **Difference from reviewed methods:** The local implementation has per-pixel Hessian ridges, local cross-field alignment and greedy coverage, but no along-edge orientation-transport graph or cross-field junction consistency. It is not another tip-extension or mapped-stepover prior; global novelty is unverified.
- **Named non-fault mimic:** Intersecting dikes, unfaulted intrusive boundaries, erosional drainage intersections and acquisition seams can generate stable junctions.
- **Data/access status:** All named raw bands were restored via the unchanged pinned shared cache builder from the 418,912,844-byte public mirror (SHA-256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5). No new external binary is needed for this proposed test. Mirror origin/units are not authenticated as organizer bytes; ignored caches must be verified again before use. No feature or model for this proposal was implemented or evaluated.
- **Source links for manual review:** [https://pubs.usgs.gov/publication/70271418](https://pubs.usgs.gov/publication/70271418) · [https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and) · [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

### N4 — Survey-axis notch-stability veto on gridded edge evidence

- **Layers:** mag_anom (owner-mirror band 1); rtp (owner-mirror band 2); tc (owner-mirror band 6); USGS published flight-line geometry metadata, no new line-level binary required for this gridded stress test.
- **Physical signature:** In identically tapered local windows of the cached grids, stress-test magnetic/radiometric edges with conservative orientation-selective spectral attenuation around the documented survey-axis directions. Fit allowable attenuation only on visible-training data and compare with rotated-axis controls. Retain only positions whose cross-field edge evidence remains stable, while measuring loss of genuine faults parallel to the axes. Do not impose one global survey-block filter.
- **Why it might find an uncatalogued fault:** Reducing acquisition-line false positives could leave more emission budget for unmapped geological structures. Stability under a notch is only an artefact-sensitivity test; it cannot prove independent repeatability or establish fault presence.
- **Difference from reviewed methods:** No survey-axis spectral perturbation stability test is implemented in the local MSPTCD feature set. Unlike the older cross-flight-line proposal, this can be tested using cached grids; true independent flight/tie-line confirmation still needs external observations and is not claimed viable here.
- **Named non-fault mimic:** Real east-west or north-south faults may be attenuated; gridding, resampling, dike swarms and anisotropic lithology can also appear directionally stable.
- **Data/access status:** All named raw bands were restored via the unchanged pinned shared cache builder from the 418,912,844-byte public mirror (SHA-256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5). No new external binary is needed for this proposed test. Mirror origin/units are not authenticated as organizer bytes; ignored caches must be verified again before use. No feature or model for this proposal was implemented or evaluated. The USGS release documents east-west flight lines, north-south ties, variable clearance and distinct survey areas; a single global notch would be inappropriate. This proposal is limited to a local-grid sensitivity test; independent flight-line validation still needs unavailable binaries.
- **Source links for manual review:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

### N5 — Relay/stepover-aperture off-catalogue dots (implemented)

- **Layers:** labels.tif / existing_faults.tif (USGS/INGENIOUS catalogue) — catalogue-derived only, per buffered whole-segment fold from visible faults.
- **Physical signature:** facing fault-end pairs 3–12 px apart whose segment directions point across the gap form a relay node at the gap midpoint; binary dots within 300 m (3 px) of nodes, more than 600 m (6 px) from visible traces, 3 px apart, top-K by node strength.
- **Why it might find an uncatalogued fault:** stepovers and relay ramps are structural apertures between catalogue segments where geothermal flow localizes; such junctions are typically absent from linear trace catalogues.
- **Difference from reviewed methods:** not ridge-thinness dots (the GEMSDOE24–36 family), not damage-zone flanks, not power-law/tilt budgets: dots sit at segment-end apertures away from all mapped traces.
- **Named non-fault mimic:** unfaulted intrusive/lithologic contact, erosional segmentation, or a volcanic neck producing paired fault-like endpoints.
- **Data/access status:** all inputs from the hash-checked owner-mirrored catalogue (existing_faults.tif); mirror not organizer-authenticated. No new external binary required.
- **Source links for manual review:** [https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)
- **Measured result:** Experiment 1 pooled HOLDOUT-DTI 0.00034 (95% CI [0.000239, 0.000465]) over 60,940 withheld positives; fold AUC canaries 0.4984–0.4991 (< 0.90, no leakage alarm); 4,727 unique dots; unique vs all 14 registry rasters checked (max |rank ρ| 0.0054 ≤ 0.90; max 3-px dot overlap 36.45% ≤ 70%). Format pass. No slot spent and no organizer receipt; upload is a separate decision.

## Why no candidate was validated

The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.

The owner-mirrored competition inputs are not authenticated, and the shared derived feature bank is missing; ignored raw caches may not persist. No new spatial holdout, feature-alone leakage canary, matched incumbent comparison, or confidence interval was measured in this review. Historical MSPTCD statistics do not validate the revised N1-N4 shortlist or the corrected orientation feature. Do not substitute a projection or a previously reported parallel result for a protocol-valid HOLDOUT-DTI.

## Gates before any experiment or slot selector

1. Resolve the continuous-prior interpretation and restore an immutable, complete, fresh registry; do not move dots to exploit edge cells.
2. Record the explicit assigned method lane: ASSIGNED — N5 (relay/stepover-aperture dots), implemented and gate-passed.
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
- [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) — the official source for deferred drainage studies; exact tiles/coverage remain unverified.

**Evidence note:** Official source pages were rechecked through the research page renderer on 2026-10-27 UTC; binary access was not verified. See the [dated source recheck](source-verification-release-20261027.md) and [`research/sources.md`](sources.md) for the recorded access status and limitations.
