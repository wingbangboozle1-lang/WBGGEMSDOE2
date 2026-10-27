# MSPTCD campaign — historical findings and independent stop review

**Decision: negative. DO NOT SUBMIT the archived MSPTCD raster.** This page supersedes earlier claims that the canaries proved “zero leakage,” that the result was independently reproduced, or that proximity pruning necessarily improves the organizer score. The original machine records remain in [`evidence/wbg2_msptcd_results.json`](../evidence/wbg2_msptcd_results.json) and [`evidence/wbg2_msptcd_canaries.json`](../evidence/wbg2_msptcd_canaries.json); the [current byte-level stop audit](../evidence/local_artifact_audit_20261027.json) is separate. This review did not rerun the campaign or generate a candidate.

## What the historical report says

The prior lane reported four buffered spatial folds with 60,988 withheld positive pixels, `gems57-pooled-hide-v2`, and 1,000 20 km spatial-cluster bootstrap draws. The following **HOLDOUT-DTI values and CIs are source-reported and not independently reproduced in this review**, not organizer-confirmed scores:

| Arm | Reported pooled HOLDOUT-DTI | Reported 95% spatial-block CI |
|---|---:|---|
| 19-band control | 0.023409 | [0.015356, 0.031895] |
| MSPTCD core | 0.034975 | [0.025587, 0.045475] |
| MSPTCD strain/PU | 0.028575 | [0.020416, 0.038058] |
| MSPTCD submodular allocation | 0.042554 | [0.032059, 0.054765] |

The report gives a paired difference of 0.019145 versus its own control, with CI [0.010977, 0.028755]. The best arm was chosen from multiple arms; intervals conditional on the fixed folds and fits do not account for that selection and are not a forecast of hidden-truth performance. The nine historical focus-site TIFFs were not evaluated against this control on the same folds.

The prior canary record reports 124 individual-feature/fold checks (31 × 4), maximum two-sided AUC 0.6131, below the predeclared 0.90 alarm. This is a useful diagnostic but **cannot prove absence of leakage**, including multivariate, spatial, temporal, preprocessing or selection leakage. Its metrics have not been replayed in this review.

## What was actually checked this session

The retained raster has SHA-256 `fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614`, with 25,594 positive in-footprint cells. Reopened against a hash-pinned owner mirror, it matched the local grid and had no masked interior cells or out-of-range values. This is not organizer authentication or portal acceptance. The same read-back found **100%** of its positive cells within three pixels of the registered binary lattice. A continuous prior also has 100% overlap under the shared finite-positive support definition; whether a probability field counts as “dots” is a policy question, not a silent exemption. The full registry is not audited.

Inspection of the historical script shows that it allocated dots before computing its surface/registry report. That does **not** satisfy the requested pre-placement stop, regardless of the subsequent negative card. Its executable entry point is disabled; helper functions and archived records remain available for review. No new file or slot was produced here.

## Physical interpretation and alternatives

The implemented module uses tilt-gradient, magnetic/gravity cross-gradient, electrical flank, topographic Hessian and other operators, as documented in [`research/msptcd_hypotheses.md`](msptcd_hypotheses.md). Such edges can reflect contacts, dikes, topography, flight-line leveling, surface cover or cultural features; none is automatic proof of a fault or geothermal system.

The official inventory calls `depth_to_base_surf` a conductive-base depth; the mirror metadata calls it basement depth. The distinction is unresolved and the two must not be treated as synonymous. The official inventory describes `tc` as a radiometric total count, while the mirror band description calls it tilt/curvature; the local positive-value distribution is consistent with total counts but cannot authenticate units or origin. An authenticated organizer stack is needed to resolve this discrepancy.

The reopened owner mirrors show GEMSDOE32 B2 equals the GEMSDOE25/30 D2.8 mask after removing points within two pixels of the known-fault mirror. Pruning may reduce false-positive mass, but could also discard useful true-positive coverage; neither the USER-REPORTED 0.2778 nor a causal counterfactual is confirmed by a per-file receipt. [Organizer staff](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) explicitly specify a pixel-exact known-fault mask with no buffer, and new truth may lie within 300 m of known traces.

## Future work

Assign one lane, clarify the continuous-prior policy, acquire a complete current registry and authenticate the official grid and features. Repair the shared validator upstream; check surface novelty before placing dots, run feature canaries and matched same-fold holdouts, then let a separate selector decide whether an independently validated candidate merits a competition slot. [Current untested proposals](hypotheses.md) are desk research, not an assignment.
