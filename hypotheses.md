# Candidate geological hypotheses (ranked)

Competition context (verified from the problem page [drivendata page/967]):
- Metric: distance-weighted Tversky index, alpha=0.2 (FP), beta=0.8 (FN),
  triangular kernel R=300 m (=3 px at 100 m). Score is pixel-wise probability
  vs expert-labeled faults; test faults are NOT in the USGS/INGENIOUS
  catalogue (private label set for round 1).
- Provided layers: RTP magnetics, TMI and its vertical/horizontal slope,
  top-of-crustal magnetic source depth, surface conductivity, depth to
  conductive base, detrended elevation + slope, dilatation/shear/2nd invariant
  of strain-rate tensor, isostatic gravity anomaly + slope, earthquake density.
- Existing public lanes (from the GEMSDOE sites): dotted-ridge / catalogue
  seeding, SPCP + SAR-PU, MDRC ridge concordance, PGRN-PU, LLI coupling. All
  either seed from catalogue faults or target already-mapped ridge lineaments.

| Rank | Hypothesis | Layers | Physical signature | Why it catches catalogue-missing faults | Difference from repo/lane work | Exp. DTI gain | Cost |
|------|------------|--------|--------------------|-----------------------------------------|--------------------------------|---------------|------|
| 1 | H1 blind-conduit hydrothermal breach | RTP magnetics horizontal gradient; radiometric K + eTh/K; detrended elevation curvature; strain-rate 2nd invariant | Demagnetization + K alteration halo + damage-zone convergence along blind structures; decayed with 300 m triangular kernel | Blind faults under cover have no surface scarp -> absent from USGS/INGENIOUS maps -> absent from every catalogue-seeded lane; geophysical alteration halo still visible | Not seeded from any catalogue fault; geophysical-edge first (others are ridge/dot-first on mapped traces) | High | Low (uses provided stack) |
| 2 | H2 relay-ramp / stepover dilation density | detrended elevation curvature sign reversal; lineament-intersection density; magnetics gradient | Dilational jogs between en-echelon faults localize permeability; blind stepovers are unmapped | Stepovers are small, offset, and frequently missing from fault catalogues | Targets junctions, not traces; complement to trace-following lanes | Medium | Low-Medium |
| 3 | H3 second-derivative curvature edge ("edge of edge") | detrended elevation (2nd derivative / Laplacian of curvature) | Subtle blind scarps invisible to first-derivative ridge lanes | First-derivative lanes need a visible scarp; second derivative catches low-amplitude warps | Different derivative order than existing curvature lanes | Medium | Low |
| 4 | H4 seismicity x strain-rate product | earthquake density + strain-rate 2nd invariant | Active aseismic/b blind shear zones where seismicity and strain co-locate without mapped faults | Active structures missing from Quaternary maps | Uses earthquake density (little-used layer) | Medium | Low |
| 5 | H5 catalogue-misalignment inversion (contrarian) | distance-to-catalogue-fault + magnetics gradient | Existing fault data may be misaligned (problem page); true fault may sit offset from mapped trace | Corrections to misaligned catalogue faults count as discoveries | Predicts AWAY from catalogue traces near geophysical edges — opposite polarity to all seeded lanes | High (if misalignment is systematic) | Low |

Top candidate for validation: **H1** — lowest implementation cost, targets the
private test set directly (blind/off-catalogue faults), uses only layers already
in the provided 19-channel stack (no new external data required).

Validation gate (protocol): run evaluate_holdout.py on the spatially-blocked
holdout BEFORE using a weekly submission slot; promote only if holdout-DTI +
95% CI beats the current same-evaluator repo best.  Blocked today because
labels.tif requires a DrivenData login (see scripts/download_competition_data.sh).
