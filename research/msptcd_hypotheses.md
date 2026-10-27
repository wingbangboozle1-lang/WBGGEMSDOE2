# Historical MSPTCD design — corrected interpretation

**DO NOT SUBMIT.** This is an account of already-implemented local features, not a novel shortlist or a new lane assignment. Original notes are preserved in [`evidence/reconciliation_archive/msptcd_hypotheses.md`](../evidence/reconciliation_archive/msptcd_hypotheses.md). The [new N1–N4 proposals](hypotheses.md) are unimplemented and unvalidated.

## What the code actually implements

The [source](../src/wbggems/msptcd.py) combines 19 raw mirror bands with 12 local operators. The former web renderer incorrectly described Bouguer gravity, heat-flow and aspect bands that do not exist in this stack. Use the actual band aliases/descriptions in [`feature_cache.json`](../evidence/feature_cache.json), not a generic geological schema.

| Already-tried feature family | Exact local inputs / implemented calculation | Physical possibility, not a demonstrated fault interpretation | Named non-fault mimic |
|---|---|---|---|
| Potential-field derivative-ratio edges | RTP B2 and TMI vertical gradient B9, sigma 1.5/3.5 px; isostatic gravity B13 and its vertical gradient B11, sigma 2/4 px. Robustly rescaled ratios followed by tilt-like horizontal gradients. | A buried property boundary can persist without a surface scarp. These are heuristic ratios: physical calibration and compatibility of RTP/TMI derivatives are not verified. | Unfaulted intrusive or lithologic margin, remanent-magnetization/gridding artefact. |
| Unsigned, depth-shifted cross-field concordance | B2/B13 horizontal-gradient amplitudes; B15-based shift `clip(smoothed_depth / 200, 0, 4)` pixels along a gravity normal, sampled on both sides. | A lateral offset might recover a dipping/buried contrast. The depth/unit assumption is unverified; B15 is officially conductive-base depth, not authenticated geological basement. | An unrelated adjacent contact or finite-width igneous body. |
| Conductive-flank asymmetry and conductive-base step | B17 values sampled ±3 px along the B15 log-depth gradient normal; divide contrast by robust scale and gate by the depth gradient. | A conductivity contrast might accompany a covered fault. No thermal/heat-flow band is used, and conductivity is not uniquely hydrothermal. | Playa clay/salt, basin-fill facies or water-table change. |
| Terrain/radiometric edge context | Detrended elevation B12 Hessian ridge at sigma 1.5 px; detrended-elevation slope B19 ridge at 3.5 px; B6 gradient divided by `1 + 0.2*slope`. | A degraded scarp or unit boundary may have surface evidence. The ratio is not a calibrated aircraft-clearance correction. | Terrace/shoreline, erosion, road/canal embankment, variable survey clearance. |
| Strain/seismicity conditioning | Dilatation B8 / (nonnegative second invariant B4 + 1); shear B7 gradient times an edge envelope; `log1p(max(B16,0)) − 0.5*log1p(max(B10,0))`. | Regional deformation or seismicity may contextualize a structure. These are neither a Mohr–Coulomb inversion nor an injection/mining classifier. | Smooth geodetic interpolation halos, volcanic/injection/mining seismicity. |
| Local orientation agreement | B13/B2 gradient normals. **Corrected v2** uses squared axial cosine, weighted by joint edge amplitude. | Parallel normals are more consistent with a common boundary than perpendicular ones, but consistency is not fault truth. | A common non-fault contact or aligned acquisition artefact. |

The v1 absolute double-angle cosine incorrectly gave **parallel and perpendicular** normals maximum coherence. Current v2 tests parallel/antiparallel = 1, perpendicular = 0, 45° = 0.5 and zero-amplitude = 0. **No real-data v2 feature computation, training, holdout or score was run in this review.**

## Metadata is a blocker, not a discovery claim

The official page illustrates radiometric total counts, while the owner mirror describes B6 as “Tilt angle or total curvature.” The restored raw values exclude an **unscaled** tilt angle in radians. Positive counts alone do not prove channel identity or units. The [new raw diagnostic](../evidence/feature_semantics_review.json) differs from some old published quantiles; a historical feature-source hash is not bound to the campaign scores.

B15 has negative values in the restored mirror. The implementation clips those values to zero before a depth transform, an assumption that needs authenticated metadata and explicit quality/missing-data treatment. Do not silently identify that layer with basement depth or infer a physical dip angle from its shift.

## Validation status

The [historical card](../evidence/RUN_CARD_MSPTCD.json) preserves source-reported v1 HOLDOUT-DTI, confidence intervals, evaluator version and withheld-positive count. They were not reproduced here and **do not validate v2**. Canary AUC ≤0.90 is required but not proof of no leakage. The alternate detached-mask calculation rescores the same OOF predictions and is not independent validation.

Whole-segment buffered holdout, visible-only catalogue features, exact known-pixel masking, pooled DTI, paired spatial confidence intervals, a matched corrected-code incumbent, and complete pre/post-placement registry checks are still required before considering an eligible candidate. The historical entry point is guarded before feature/model/output work. [Current release decision](../docs/release.html) · [source-by-source verification](source-verification-release-20261027.md).
