# Repository review and next-step decision — 2026-10-28

## Executive decision

**Negative / DO NOT SUBMIT.** This review found no candidate eligible for a competition slot. It did not generate a TIFF, place dots, run a model experiment or canary, submit to DrivenData, or consume a weekly slot. The working agreement does not assign a method lane; current readiness is blocked; the existing TIFFs remain research-only. Do not download one of them for scoring.

The user's 0.3195 public-high statement is stale relative to the official public leaderboard page retrieved during this review: its first row displayed **0.4544** for xiaofanhu. This is an **ORGANIZER-PUBLISHED PUBLIC LEADERBOARD OBSERVATION**, not a receipt for any local or GEMSDOE TIFF, not HOLDOUT-DTI, and not evidence a new model can attain that value. The official page can change; its current visible state was checked on 2026-10-28. A separately saved 2026-10-28 capture records the same 0.4544 value ([JSON evidence](../evidence/public_leaderboard_observation_20261028.json)).

## Three review passes

### Pass 1 — identify the project state and answer the B2 question carefully

- Read `AGENTS.md`, this repository's session-start files, the canonical run card, release audit, current checkout-readiness output, and the previous repo review. The README already preserves the full original project brief and puts the negative release decision first.
- Confirmed that the site has the requested nine per-site summaries and a nine-site decision table. They label historical values as claims, estimated new leaderboard score as unavailable, and every historical raster as **DO NOT SUBMIT**.
- The strongest historical claim among the nine is GEMSDOE32 B2 at **0.2778 USER-REPORTED**. It is not an organizer-confirmed score tied to the audited file's SHA-256. The official competition description says the target is newly identified geological faults and acknowledges the public fault inventory can be incomplete or inaccurate; it does not provide hidden fault labels to this review.
- The repository's byte-level lineage analysis reports: the GEMSDOE25 and GEMSDOE30 decoded prediction masks match inside the footprint; GEMSDOE32 B2 is the D2.8 mask after removing 6,436 points within two pixels of the mirrored known-fault catalogue (44,090 to 37,654); GEMSDOE36 adds 1,200 points to B2. These are mask comparisons, not evidence of why an organizer score changed.
- A plausible mechanism is that sparse pruning reduces false-positive mass while retaining useful distance-weighted coverage. The official metric uses a 300 m triangular distance kernel and alpha=0.2 for false positives, beta=0.8 for false negatives. But pruning may also remove points earning true-positive distance credit. Without the exact receipt and hidden labels, the causal explanation is **not established**; neither this review nor the historical score proves B2 beats a newly validated method.

### Pass 2 — compare the nine named sites, audit novelty and assess blockers

Values below are the highest values recorded for the named historical artifacts in the pinned repository ledger, matching the user's supplied list. Every value is **USER-REPORTED / NOT ORGANIZER-CONFIRMED**. The downloaded/hashed TIFF is identified in each linked site page and in `config/registry_inputs.json`; no score receipt was available. Newer lower reported attempts mentioned in the prompt do not replace these maxima.

| Site | Historical best file (research reference only) | Reported value | New score estimate | Unique under the requested registry rule? | Decision |
|---|---|---:|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 USER-REPORTED | Unavailable | No; its decoded mask matches GEMSDOE30 inside the footprint | DO NOT SUBMIT |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 USER-REPORTED | Unavailable | No; its decoded mask matches GEMSDOE25 inside the footprint | DO NOT SUBMIT |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 USER-REPORTED | Unavailable | No; focus-site proximity audit fails | DO NOT SUBMIT |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 USER-REPORTED | Unavailable | No; it adds 1,200 points to B2 and the focus-site proximity audit fails | DO NOT SUBMIT |

The nine values and paths are reproducible from `config/registry_inputs.json`, [`evidence/registry_audit.json`](../evidence/registry_audit.json), and the corresponding [`docs/sites/`](../docs/sites/) pages. The recorded directed overlap matrix (`data_public/focus_overlap_matrix.json`) counts the fraction of a row-site's points within three pixels of a column site's points; the best-match row overlap ranges from 97.40% to 100% across these nine. Thus every focus file fails the stated >70% final-dot stop against at least one other focus raster. The pinned registry is deliberately incomplete. A duplicate witness is sufficient to fail the stated stop; a pass against the incomplete witness set would not establish uniqueness. Exact mask equality between GEMSDOE25 and GEMSDOE30 is an additional direct non-uniqueness finding. The user's 0.2778 claim is the maximum among these nine, not an authenticated organizer result. The original pre-placement surfaces were not available in this review, so their rank correlations were not tested.

The current checkout-readiness gate returned **BLOCKED / DO NOT SUBMIT** (exit 2). The checkout diagnostic recorded missing local official inputs, derived feature bank/shared-cache artifacts, unresolved lane assignment, incomplete fresh registry, unresolved continuous-prior support interpretation, and no corrected matched holdout/canary. This is a checkout snapshot; ignored caches may differ elsewhere. Do not confuse the previously restored owner mirror or previous-session reports with inputs present and authenticated in this checkout.

### Pass 3 — verify candidate planning, official sources, build and test behavior

The already documented N1–N4 shortlist satisfies the requested *planning* format. It is proposal-only and supplies no numeric score forecasts:

| Rank (qualitative) | Existing proposal | Layers and physical signature | Why it could expose a missing fault / distinction in this repo | Named non-fault mimic | Cost |
|---:|---|---|---|---|---|
| 1 | N1, signed edge-pair cancellation | RTP magnetics, isostatic gravity anomaly, conductive-base depth; test signed multi-scale cross-normal gravity profiles for persistent steps versus balanced opposite-polarity lobes | A buried density boundary could persist under cover; proposed signed-profile/body-veto differs from the repo's unsigned shifted-gradient amplitudes | Unfaulted intrusive or lithologic contact; fault-bounded blocks can also be wrongly vetoed | Medium |
| 2 | N2, radiometric-quiet magnetic-edge transfer | Total radiometric counts, RTP, conductive-base depth, conductivity, detrended slope; test magnetic edge persistence where a co-located surface radiometric edge fades under cover | Tests a cover-conditioned cross-modal transfer rather than adding another positive edge layer; distinguishes from existing flank/depth-shift work | Moist soil, uniform sediment, aircraft clearance, weak radiometry, buried non-faulted contact | Medium |
| 3 | N3, catalogue-free edge-orientation transport | Isostatic gravity anomaly, RTP, detrended elevation; track axial edge normals and cross-field supported junctions | Tests blind structure junctions without catalogue endpoints; new graph transport differs from per-pixel ridges and local orientation products already in the repo | Dikes, intrusions, drainage intersections, acquisition seams | High |
| 4 | N4, survey-axis notch-stability veto | Magnetic anomaly/RTP, total counts, plus published GeoDAWN line context; test local edge stability under orientation-selective spectral perturbation and rotated controls | Artefact sensitivity test, not another positive prior; current local implementation has no such spectral stability check | Real faults aligned with a survey axis, dike swarms, anisotropic lithology, gridding artefacts | Low–medium |

Full N1–N4 layer provenance, operations, disconfirming alternatives, prior-art comparison and caveats are in [`research/hypotheses.md`](hypotheses.md). These proposals are not globally novel claims or results. No new candidate was selected or run because no lane is assigned and the checkout gate is closed. Creating a ranked shortlist does not override the explicit lane, cache, evaluator, canary, registry or selector gates.

Official pages retrieved during this review support the following limited facts:

- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) describes the target as geological faults, says the public known-fault set may be incomplete or inaccurate, lists the supplied geophysical feature families, and defines the distance-weighted Tversky index. It states alpha=0.2, beta=0.8, a 300 m triangular kernel, and GeoTIFF submission at EPSG:32611 / 100 m / one float32 band / values in [0,1] with null/NaN outside bounds.
- [Official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) displayed 0.4544 at rank 1 when retrieved in this review. Public leaderboard state is not a per-file receipt and can change.
- [Organizer reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution) is a repository starting point; reading its landing page does not validate a local candidate or establish its competition score.
- The USGS GeoDAWN page request returned a gateway timeout in this review. We make no claim of having freshly verified its page content or downloaded new external data here. Its link remains a lead in the existing source register, not verification performed now.

### Verification commands and results

- Installed repository requirements into ignored `.venv/` because the base interpreter lacked NumPy, Rasterio, SciPy, scikit-learn and pytest.
- Re-ran CI's evidence/site build sequence: `build_hypotheses.py`, `build_run_card.py`, `build_site.py`, `build_site_data.py`, `build_msptcd_site.py`, `build_release.py`, `build_release_review.py`; each exited successfully. `check_readiness.py` correctly returned the negative blocked diagnostic.
- Ran `.venv/bin/python -m pytest -q`: **350 passed, 12 skipped, 32 warnings**. Warnings were Rasterio affine-operation pending deprecations. Skipped tests are data-dependent; no competition data or feature bank was reconstructed or inferred from those skips.
- `git diff --check` passed. This review performed zero candidate experiments, used zero weekly slots and produced zero new TIFFs.

## Outcome and work order

The project now has a same-session repository review, an up-to-date official leaderboard observation, an auditable nine-site score table and an existing ranked geological proposal set. It still has **no approved or defensibly score-estimated TIFF**. The answer to “can we beat 0.2778?” is: *not established by this evidence*. It would be irresponsible to promise or project a score.

Before the next model experiment: (1) explicitly assign one method paragraph/lane; (2) settle how continuous probability rasters are counted by the literal dot-overlap rule; (3) refresh/hash-pin the full current registry, including concurrent repositories; (4) restore and authenticate organizer inputs and the exact shared derived feature cache; (5) resolve the shared writer/format defect upstream; (6) use the pinned shared buffered whole-segment evaluator and run every feature-alone canary; (7) compare a preregistered proposal against a matched corrected incumbent with pooled HOLDOUT-DTI, evaluator version, withheld-positive count and spatial 95% CI; (8) only after all gates pass, use the separate selector to check actual quota and produce a named file with a note under 140 characters. Do not upload or spend a slot before that selector step.

## Current run card

```json
{
  "hypothesis": "No newly assigned or tested candidate; the repository's N1-N4 remain proposal-only.",
  "mechanism": "No prediction surface or dots generated in this review. B2 pruning is a plausible but unproven false-positive-mass/recall tradeoff.",
  "named_non_fault_mimic": "Unfaulted lithologic or intrusive contact can produce paired geophysical edges.",
  "holdout_dti": null,
  "holdout_evaluator_version": null,
  "withheld_positive_count": null,
  "holdout_ci95": null,
  "holdout_status": "NOT RUN; lane unassigned and checkout readiness blocked.",
  "preplacement_rank_correlation_vs_registry": null,
  "final_dot_overlap_vs_registry": null,
  "raster_sha256": null,
  "validator": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "No TIFF generated."
  },
  "submission_name": null,
  "submission_note": null,
  "verdict": "negative",
  "ok_to_download_and_submit": false,
  "experiments_run": 0,
  "weekly_slots_used": 0
}
```
