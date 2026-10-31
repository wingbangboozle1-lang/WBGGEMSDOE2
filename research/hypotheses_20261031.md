# Candidate hypotheses — 2026-10-31 (ranked before implementation)

**Lane assigned:** WBG2-OCM, "Off-catalogue Multi-band Concordance emission" — full method
paragraph in [`config/wbg2_ocm_lane.json`](../config/wbg2_ocm_lane.json). Assignment follows the
project-owner directive of 2026-10-31 to work autonomously to a unique, validated, downloadable
submission. Ranked below by expected DTI improvement over the current local best proxy and by
implementation cost. Rankings are qualitative judgments, never scores.

Labels: **HOLDOUT-DTI** = local hide-and-recover proxy (evaluator + caveats given) ·
**USER-REPORTED** = fleet claim, no organizer receipt · **PROJECTION** = model output, never a score.

## Ranking

| Rank | Hypothesis | Layers (owner-mirror band ids) | Physical signature | Why it can catch an UNCATALOGUED fault | Named non-fault mimic | Distinct from everything already in this repo | Qualitative expected gain | Cost | Data obtainable? |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | **H1 → implemented as WBG2-OCM**: multi-field edge concordance × off-catalogue repulsion, greedy 300 m coverage | b2 rtp, b6 tc, b13 iso_grav_anom, b15 depth_to_base_surf, b17 cond_surf, b19 det_elev_slope | Ridge magnitude of six physically independent fields at 150/450 m scales; top-decile agreement count C∈0..6; prior (C/6)²·R | Unmapped blind faults express as *concordant* subsurface edges (mag+grav+conductivity) precisely where no surface trace exists; single-band priors (the 0.24–0.278 family) miss cover-hidden strands; repulsion keeps budget off the masked catalogue | Buried lithologic/intrusive contacts and dike swarms produce concordant edges without faulting | Repo priors are single-band ridge/dot or HGB-on-catalogue; no six-field concordance count, no built-in repulsion ramp, no shared-allocator placement on this surface | Moderate (family cluster 0.245–0.278 USER-REPORTED) | Low | Yes — cached mirrored stack |
| 2 | **H2**: H1 + signed cross-normal edge-pair veto (prior N1) | b2, b13 (+b15) | Reject finite-width bodies whose signed gradient returns to background across the edge | Removes intrusive-contact false positives from H1's budget | A narrow horst is a finite-width body and would be vetoed | No signed-lobe cancellation exists locally | Additive FP reduction, untested | Medium | Yes |
| 3 | **H3**: geothermal surface-expression weighting (springs/sinter/heat-flow density from USGS DGDS) | H1 prior × external point densities | Hydrothermal upflow leaves alteration-conductivity highs and spring-lineament clustering above blind faults | Targets the "geothermal vent discovery" axis directly; fleet geothermal-only attempts (0.086, 0.165) underperformed structural priors, so use as reweight not replacement | Volcanic fields and playas cluster springs without contemporary fault slip | Only fleet item with external hydrothermal points *reweighting* a concordance prior | Unknown; external fetch not available in this sandbox (needs usgs.gov / DGDS host) | Medium-high | Not from this sandbox — verify on unrestricted machine |
| 4 | **H4**: Euler-deconvolution depth-clustered edges | b1/b2/b13 derivatives | Cluster depth solutions along edges; emit only clusters with depth consistency | Already tried fleet-wide (GEMSDOE40: 0.034–0.098 USER-REPORTED) | Basin-edge artefacts | Low — duplicate of tried family | Low | Partially (derivative bands cached) |
| 5 | **H5**: supervised pixel model (GBM/U-Net) on all 19 bands trained against catalogue labels | all 19 | Learn catalogue decision function; extrapolate off-catalogue | Fleet ML attempts scored 0.018–0.044 USER-REPORTED; labels==catalogue teaches "predict what is already mapped", the anti-goal | N/A | High cost, poor fleet track record, GPU unavailable here | High | CPU-only here |

**Selected:** H1 (implemented). H2 is the first follow-up once H1's gates pass. H3 needs a network
fetch outside this sandbox. H4/H5 rejected on fleet evidence.

## Canary expectations (pre-registered)

- Concordance C alone vs withheld catalogue segments: expect modest AUC (0.55–0.75). AUC > 0.90 ⇒
  leakage alarm, stop.
- Repulsion R alone vs withheld catalogue segments: expect inverted AUC > 0.90 **by construction**
  (withheld segments sit next to visible catalogue). This is the pre-registered signature of the
  task misalignment (official scoring masks mapped faults; our mirror holdout truth IS the mapped
  catalogue), not silent leakage. It is reported, not hidden.

## Sources

- [DrivenData problem page (metric, format, masked known faults)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Forum staff reply: known USGS/INGENIOUS fault pixels masked from scoring](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS blind geothermal play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and)
- Owner-mirrored stack: buffedlizard55-lab/GEMSDOE split blobs, sha256 4371c82e… (hash-verified this session)
