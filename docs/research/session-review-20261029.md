# Repository review and current research decision — 2026-10-29

**Decision: NEGATIVE / DO NOT SUBMIT. No TIFF was generated.** This is the correct protocol-compliant outcome for this checkout, not a claim that the hypotheses are scientifically disproven. The explicit three-experiment/two-hour limit was respected: **0 experiments, 0 submission slots used**.

## Executive findings

| Request | Review result |
|---|---|
| Highest of the nine supplied site claims | GEMSDOE32 B2, **0.2778 USER-REPORTED**. No organizer receipt binds this value to exact raster bytes. |
| Why B2 may be higher | The existing byte-level lineage audit says GEMSDOE25 and GEMSDOE30 share an in-footprint mask and GEMSDOE32 B2 is a pruned family member. Pruning can reduce weighted false-positive mass, but can also remove true positives; without hidden truth and a receipt, this is a plausible mechanism, not causal attribution. |
| Can this repo demonstrate a score higher than 0.2778? | **No. Unknown.** No new candidate was run, and no calibrated estimate is supported. A projection must not be presented as a score. |
| Highest current public leaderboard observation | **0.4544 at rank 1 (xiaofanhu), ORGANIZER-PUBLISHED PUBLIC-LEADERBOARD SNAPSHOT**, fetched 2026-10-29. Not a receipt for this project's TIFF and not HOLDOUT-DTI. See [`evidence/public_leaderboard_observation_20261029.json`](../evidence/public_leaderboard_observation_20261029.json) and [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). |
| Nine-site submission choice | None. The table in [`docs/executive-summary.html`](../docs/executive-summary.html) is historical evidence and uniqueness review, not release authority. All nine entries are research references; new estimate is unavailable; all say DO NOT SUBMIT. |
| New TIF, download, hash, and validator result | None. No candidate was created or validated. There is no file that is OK to download or submit. |

The public rank-1 value above is also a correction to stale numbers in the prompt: the prompt's 0.3195 and 0.4413 were not the value displayed by the official leaderboard retrieval made for this review. The 0.2778 remains a user-provided historical site claim, not an organizer-confirmed score.

## Why B2 may have scored 0.2778 — evidence-bounded explanation

The official problem targets geological fault traces, not geothermal vents directly. The official metric is distance-weighted Tversky with `alpha=0.2`, `beta=0.8`, and a 300 m triangular kernel. It penalizes false negatives more strongly than false positives in its nominal weights, while proximity reduces the contribution of both errors. See the official [problem, metric, datasets, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

Repository forensic records describe GEMSDOE32 B2 as a sparse/pruned member of a closely related historical raster family. If removed pixels were mostly redundant false-positive mass and the retained pixels remained close to hidden expert faults, the precision/recall balance could improve. The opposite is also possible if pruning removed useful coverage. The mapping relationship alone cannot establish which occurred, and the submission-page receipt and hidden labels needed for attribution are unavailable. Therefore, neither a claimed causal explanation nor a projection above 0.2778 is justified.

## Ranked hypothesis preregistration (all proposals only)

These are the four proposals in [`config/research_hypotheses.json`](../config/research_hypotheses.json) and [`research/hypotheses.md`](hypotheses.md). They are locally differentiated ideas, not claims of global scientific novelty. Their ranking is qualitative expected value balanced against cost—not a measured DTI improvement.

| Rank | Hypothesis and exact named layers | Physical signature and uncatalogued-fault rationale | Local method distinction | Named non-fault mimic | Qualitative potential / cost |
|---:|---|---|---|---|---|
| 1 | **N1 — Signed edge-pair cancellation**. RTP magnetics (owner-mirror band 2), isostatic gravity anomaly (band 13), depth-to-conductive-base proxy (band 15). | Signed cross-normal profiles at multiple smoothing scales distinguish a persistent step from balanced opposite-polarity lobes returning to background. A buried density boundary may continue under cover without a mapped surface trace; catalogue endpoints are not used as seeds. | Local MSPTCD uses unsigned shifted gradients/orientation; N1 proposes signed profile shape and finite-width-body cancellation. Not yet implemented or tested. | Unfaulted intrusive/lithologic contact; a genuine narrow fault-bounded block could also be wrongly vetoed. | Highest qualitative rank; **medium cost**; no score forecast. |
| 2 | **N2 — Radiometric-quiet magnetic transfer under conductive cover**. Total radiometric count (band 6), RTP (band 2), depth proxy (band 15), surface conductivity (band 17), detrended-elevation slope (band 19). | Look for persistent magnetic edges with weaker co-located radiometric edges in deeper-cover/low-relief settings, where surface mapping can miss a buried structure. | Tests cross-modal edge disappearance as a control; prior work used radiometric edges positively and examined conductivity/depth flanks. | Moisture, uniform sediment, weak signal, flight-clearance variation, or non-fault contact. | Moderate qualitative rank; **medium cost**; no score forecast. |
| 3 | **N3 — Catalogue-free edge-orientation transport**. Isostatic gravity anomaly (band 13), RTP (band 2), detrended elevation (band 12). | Build a label-free ridge graph and assess transported axial-normal continuity at cross-field-supported junctions; a subsurface discontinuity may be unmapped and not connected to known catalogue endpoints. | Local code has Hessian ridges, local cross-field alignment and greedy coverage, but not along-edge orientation transport plus junction consistency. | Dike/intrusive intersections, drainage intersections, lithologic contacts, acquisition seams. | Exploratory qualitative rank; **high cost**; no score forecast. |
| 4 | **N4 — Survey-axis notch-stability control**. Magnetic anomaly (band 1), RTP (band 2), total counts (band 6), plus the published GeoDAWN survey geometry. | Local orientation-selective spectral perturbation against rotated controls can flag evidence sensitive to survey direction, helping reduce acquisition artifacts without asserting that stable edges are faults. | No equivalent local survey-axis perturbation stability test was identified in the reviewed local feature code; this is mainly an artifact control, not a direct detector. | Real faults parallel to flight/tie lines, anisotropic geology, dikes, gridding/leveling artifacts. | Lowest direct discovery rank; **low–medium cost**; no score forecast. |

All four ideas use named layers documented by the official [competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), with mirror-band mappings recorded in the repo. The current checked-out feature rasters and derived cache are missing, so availability of an owner-mirror name in a historical manifest is not availability of a usable layer now. No new external binary is required for N1–N3; N4 relies on the official [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), which was retrieved and describes different flight specifications and variable clearance. That page-level access does not establish that any missing data binary has been downloaded or that the proposed signature improves validation.

## Why the top candidate was not validated

The request's lane instruction says to use a single method paragraph, but the current governing config records `method_lane.status = UNASSIGNED`; no paragraph is explicitly assigned. The ranked N1 hypothesis is a proposal, not permission to self-assign the lane. In addition, `python scripts/check_readiness.py --check` returned **exit 2** and refreshed the local readiness snapshot:

- Organizer sample, labels, existing-fault raster, and training feature GeoTIFF are missing from the checkout.
- All 19 expected ignored per-band feature-cache arrays and the derived shared feature bank are missing. The unchanged shared-template source was restored from its immutable pinned commit in this session and its hashes verified; this makes the code available, but does not restore the derived cache or resolve the documented format/mask issue.
- The saved registry audit covers selected pinned witnesses, not the complete, current registry or every original score surface. A continuous positive prior's interpretation under the literal dot-overlap rule remains unresolved; no exemption was assumed.
- The shared template's format/mask issue is documented but not resolved upstream in the pinned implementation. A local replacement evaluator/writer would violate the reuse rule.
- No feature-alone leakage canary, prescribed whole-segment buffered hide-and-recover, matched incumbent test, or spatial 95% CI was run for these hypotheses.
- No separate selector receipt, account-specific weekly quota check, or organizer acceptance receipt exists.
- Prior owner-mirror records report identical SHA-256 values for `labels.tif` and `existing_faults.tif` (`7ba308cc…4093`). Both files are absent in this checkout, so I did not re-open them. If an authenticated organizer download also has this identity, a holdout that treats one as hidden positives and the other as known faults is degenerate; do not rely on such holdout results until official files are compared. See [`evidence/data_preparation.json`](../evidence/data_preparation.json). The official problem page was retrievable for source review, but competition binaries were not authenticated or downloaded.
- The exact TIFF that triggered the reported portal error “Predicted values must be in range [0, 1]” is not present, so its cause remains unknown. The shared validator mask defect is real in the pinned code but cannot be asserted as the cause of that distinct upload error.

Thus a HOLDOUT-DTI number, CI, validation claim, and unique TIFF would be fabricated if supplied. Stopping is required by the method-lane and data gates, as well as the request's explicit stop-on-duplicate rule. This review does not create or select a weekly submission.

## Three review passes and verification

### Pass 1 — scope and evidence

Read `AGENTS.md`, README's authoritative section, `docs/PROJECT_CHARTER.md`, `research/findings.md`, the focus-site summary, current run/release records, readiness diagnostic, and the existing ranked hypotheses. Confirmed this is an existing evidence-heavy project, not an empty stub. Reviewed the nine-site table, its source file inventory, and the B2 lineage caveats.

### Pass 2 — independent challenge

Checked missing expected inputs and shared cache files in the live checkout; confirmed the negative readiness outcome; challenged any inference from historical score to causal mechanism; retrieved the official DrivenData problem page, public leaderboard, organizer reference-solution page, and USGS GeoDAWN release. The official sources support the fault target, specified metric/format and acquisition context. They do not validate a proposed model or provide an estimate for this project. Updated the leaderboard JSON as a dated public observation, not an organizer receipt.

### Pass 3 — implementation and final checks

Updated the README to surface the current decision and quarantine contradictory older release claims as archive-only; added this review, a structured negative run card, a current review page, and a dated public leaderboard snapshot. Restored the unchanged shared-template source from its pinned public commit and verified its pinned hashes; did not restore/misrepresent the missing derived feature cache. `scripts/build_site.py` completed successfully and `git diff --check` passed. The full test suite returned **393 passed, 7 skipped, 0 failed, 37 warnings**; remaining skips require missing competition labels/sample rasters. `python scripts/check_readiness.py --check` still returns **exit 2**, BLOCKED / DO NOT SUBMIT. No science experiment, TIFF, or slot was created. The current result remains negative.

## Follow-up work, ordered by gate

1. Record the exact assigned method paragraph/lane in `config/research_hypotheses.json`; do not infer it from a ranked candidate.
2. Resolve the literal continuous-prior support policy with the evaluator owner and refresh a complete immutable registry that includes original surfaces, before-placement scores, and final dots.
3. Restore/verify competition files and the exact pinned shared cache/template; resolve the shared format/mask defect upstream, then update/pin the reviewed shared version. Do not use a private fork.
4. Only after these gates pass, preregister N1 as experiment 1. Run N1's constituent features individually through the leakage canary. AUC above 0.90 is an alarm, not evidence to ignore.
5. Compare the candidate and a corrected incumbent on identical buffered whole-segment spatial folds. Derive catalogue features from visible faults only; mask visible fault pixels exactly; pool DTI at alpha 0.2/beta 0.8 and 300 m; report evaluator version, withheld-positive count and paired spatial 95% CI. Stop at three experiments or two hours.
6. A separate selector may act only after improvement, pre-placement and final duplicate checks, format validation on saved bytes, a unique name and <=140-character note, and an account-specific quota check. Preserve the exact organizer receipt. Until then publish no candidate download.

## Official references reviewed for this report

- [DrivenData competition problem, provided features, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — retrieved; it says the target is fault structures, gives the 300 m triangular kernel and `alpha=0.2`, `beta=0.8`, and specifies projected UTM 11N EPSG:32611, 100 m, matching bounds, one float32 band with values in [0,1], and null/NaN outside bounds.
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — retrieved for the dated rank-1 observation; changing public values are not receipts for project files.
- [DrivenData organizer reference solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) — public README reviewed; it directs competitors to download challenge data from the competition website and place it in `data/`.
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — retrieved; official release documents airborne magnetic/radiometric surveys, acquisition blocks, varying flight height and survey-direction details. It does not support a specific leaderboard-score effect.

## Run card — negative result

See the machine-readable card at [`evidence/session_run_card_20261029.json`](../evidence/session_run_card_20261029.json). A score/CI and raster-specific validation fields are null/not applicable because no experiment or raster exists; no HOLDOUT-DTI is being claimed.
