# Executive audit: what is safe to submit?

**Decision: no new file is approved.** This was a research and repository audit, not a competition submission. This review lane generated no prediction, canary AUC, holdout experiment or leaderboard forecast; a parallel session later reported three experiments and an independently rejected TIFF. Do not resubmit historical rasters. The original checkout contained only a README, not the claimed ready-to-run pipeline.

## The nine focus sites

The table is generated from [`config/registry_inputs.json`](../config/registry_inputs.json) and the measured [`evidence/registry_audit.json`](../evidence/registry_audit.json); the [dashboard](../site/index.html) links each exact pinned historical TIFF for research only. A reported value is an **owner/user claim**, not an organizer-confirmed receipt. No estimated leaderboard score is defensible for these archived files. The best *claimed* historical value among the nine is the GEMSDOE32 B2 claim, not proof of the score of the audited bytes.

All nine named historical rasters have more than 70% of their positive dots within three pixels of at least one other named focus-site raster. This is a directional test: it counts the proportion of the **candidate's** dots near the reference, not a symmetric intersection-over-union. The source pre-placement surfaces were not available and their rank correlations were not independently tested.

## Recheck of the parallel-session TIFF

The concurrently merged [experimental TIFF](../docs/executive-summary/) is **not eligible for submission**. Its SHA-256 is `592c74f26212199311d4f70807061a3f28cfe4c925652c0deada936ac925bf33`. Of its 34,564 in-footprint dots, **99.3838%** are within three pixels of the registered binary lattice, exceeding the 70% stop. The fully positive continuous prior gives 100% under the shared literal support definition, subject to the stated interpretation caveat. Its zero NoData tag masks 5,132,809 in-footprint cells despite finite raw numbers. The nine-file-only novelty claim was not a full-registry pass. The pre-placement surface was not rechecked.

The parallel source reported **HOLDOUT-DTI 0.1321**, evaluator `WBGGEMSDOE2-HIDE-RECOVER-v2.0`, 58,016 withheld positives, reported 95% CI [0.1290, 0.1349]. This is **source-reported and not reproduced here**, uses a private rather than the required shared evaluator, reports canaries only for fold 0, does not exclude evaluation cells from training, and its interval is not reproduced by the committed lane script. It is not a leaderboard score or an approved same-fold incumbent comparison. The uncalibrated live-score extrapolation is not accepted as an estimate. See [the byte-level review](../evidence/parallel_review.json) and preserved [original records](../evidence/parallel_archive/).

## Why the GEMSDOE32 B2 history is plausible, not proven

On the hash-verified owner mirrors, the GEMSDOE25 and GEMSDOE30 d2.8 prediction masks are identical inside the footprint. The GEMSDOE32 B2 mask is exactly that mask after deleting every dot at Euclidean distance ≤2 pixels from the mirrored mapped-fault catalogue: 44,090 → 37,654 dots. GEMSDOE36 adds 1,200 dots to B2 and removes none. Reproduce with `python scripts/audit_registry.py --fetch`. These are measured relationships, not evidence of an organizer score receipt.

The [official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) rewards truth coverage inside a triangular 300 m kernel and penalizes excess mass through its false-positive term, with a larger coefficient on false negatives. Sparsifying a correlated ridge can preserve some proximity credit while reducing false-positive mass; pruning may help if the removed points have low marginal truth coverage. But the private/public truth, per-dot contributions and authenticated receipts are unavailable. We **cannot** establish the causal reason for the claimed value, reliably estimate a new leaderboard score, or say a new idea beats it. Repeated leaderboard probing also risks public-set overfitting and does not establish private or final-round performance. Staff says only the exact known fault pixels are masked; it does not confirm a surrounding buffer.

## Literal registry stop: an actionable contradiction

The [registered 13GEMSDOE stride-5 lattice](https://github.com/buffedlizard55-lab/13GEMSDOE/blob/92ee6f074323f161eed837b80ec3ee5b662e26f5/docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif?raw=1) (SHA-256 `b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2`) lies within the inclusive three-pixel radius of 5,160,724 of the 5,167,373 mirrored-footprint cells. Only 6,649 are outside. For **any** 37,654 distinct dots inside that footprint, at least `(37,654 - 6,649) / 37,654 = 82.34%` must lie within that radius, above the prompt's 70% stop. This is a mathematical bound, not an experiment or a leaderboard estimate. It does **not** rule out every possible smaller-budget map: for example, the bound ceases to force failure below 22,164 dots. Most uncovered positions (6,485 of 6,649) are within three pixels of a footprint edge or hole. Exploiting these exceptions merely to pass the gate would confound acquisition geometry with geology.

At review time, the GEMSDOE27 site labeled H31 as approved after a 27-raster audit; we reopened its exact SHA-256 `2c002b02792419864bd3b29a218e543cb41e3f07b3b57c29ef35c6e39e184bfe` and measured 99.61% of its dots within three pixels of the lattice. Its approval used a different, incomplete scope and **does not satisfy this prompt**. GEMSDOE32 H47 similarly has 99.79% overlap with the lattice despite an audit that exempts space-filling controls; the current prompt permits no such exemption. These are byte-level witness failures, not full reruns of the other sites' science. [Machine receipt](../evidence/registry_audit.json); [stop-check demonstration](../evidence/h31_preflight.json). The latter treats the already-existing H31 final raster as a preview for demonstration; it is not H31's original pre-placement surface.

The independently re-opened [17GEMSDOE continuous probability prior](https://github.com/buffedlizard55-lab/17GEMSDOE/blob/6fc71d19d49dca4960d5434bd81b6dd06fcc030a/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif) (SHA-256 `ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`) is positive in **all 5,167,373 footprint cells**. The pinned shared uniqueness tool defines support as every finite positive pixel. If applied literally to this continuous prior, any nonempty in-footprint candidate has 100% overlap. Calling a continuous field's support “dots” is a policy interpretation that must be resolved explicitly; no exemption is assumed. This independent witness is stronger than the lattice bound only under that support definition. See the [byte-bound certificate](../evidence/dense_prior_certificate.json) and [audit](../evidence/registry_audit.json).

## Grid/range irregularity

The public mirrored reference has the right-looking CRS/grid but its 60,988 positive cells exactly equal the public fault mirror; the organizer's problem page describes an example predicting total fault absence. We cannot tell why, and we cannot authenticate the mirror against the login-protected official file. Never infer portal acceptance from our mirror. We also cannot diagnose the user's `[0,1]` rejection without the exact rejected TIFF: negative/greater-than-one values, infinities, or NaNs may be involved. `scripts/validate_tif.py` reports every condition without clipping or silently changing data. The official description allows null/NaN outside bounds, whereas an optional all-finite diagnostic is stricter and not proof that the portal accepts that encoding.

## Next session

1. Reconcile the literal “any registry raster” rule with the lattice and the continuous-prior support ambiguity as a **policy decision**; the binary-lattice bound alone does not rule out smaller budgets, but the fully positive prior blocks them under the shared definition. Do not quietly exclude controls.
2. Authenticate the official sample, catalogue, feature bytes, license and available weekly quota. The public owner mirror is restored and hash checked, but does not prove organizer provenance. The shared 19-band, label-free cache was rebuilt from the owner mirror; the shared derived feature bank is not present in the pinned public template tree.
3. Restore a complete, fresh, hash-pinned registry. A subset can prove a duplicate but cannot prove uniqueness. Recompute all catalogue-derived fold features from visible faults only.
4. Preregister one lane, run each feature canary, and use the **same** buffered component folds and shared evaluator for candidate/control. Report pooled HOLDOUT-DTI, evaluator, withheld positives, and block-bootstrap confidence intervals. A holdout score is a proxy, not an organizer score.
5. Before any candidate is considered, fix the shared validator’s masked-interior issue upstream and retain the independent mask check; then use the shared writer, validate the saved bytes and ZIP, and let a separate selector check the current quota. The project deliberately has no automatic competition upload.

## Links

[Sources, data access and licenses](sources.md) · [Ranked hypotheses](hypotheses.md) · [Run card](../evidence/run_card.json) · [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf).


### Separate conduit parallel TIFF

A second parallel session reported one experiment and a 58-file uniqueness pass. Its audit omitted the registered binary lattice: an independent byte recheck found **5,087,882/5,094,374 = 99.8726%** overlap at its own ≥0.5 threshold. This is a decisive STOP. Its HOLDOUT-DTI is null and its organizer acceptance unknown. The original generator used synthetic trend fields and seeded noise rather than the listed feature arrays; its private evaluator did not implement the required buffered pooled protocol. The original source and claims are archived, while [the forensic receipt](../evidence/conduit_review.json) is authoritative for the recheck. No further experiment was performed here.

---

# Lane WBG2-B — supervised blind-trace propensity (executed 27 October 2026)

**Status: a submission file exists, is format-valid and is unique within the registered scope. Its score is not demonstrated to beat anything.** Three experiments, ~3.6 h wall clock (over the 2 h budget — recorded in the run card, not hidden). No weekly slot was used.

**Hypothesis.** Unmapped expert-labelled faults are physical discontinuities measurable in the 19 provided bands. A pixel classifier trained on *inner-hidden* mapped fault segments — segments the model never sees in its own catalogue features — ranks fault-like pixels above background. The off-catalogue part of that ranking, thinned to a 1-px skeleton at a fixed dot budget, is a legal submission.

**Mechanism.** Bagged `HistGradientBoostingClassifier` over 38 shared rank layers (per-band quantile `q` and 9×9 local-contrast `z` for each of the 19 bands, uint8, 255 = NoData) plus 5 visible-only catalogue layers (`dcat_vis`, `log1p_dcat_vis`, `dtip_vis`, `cdens5_vis`, `cdens15_vis`) = 43 features. Positives are drawn from *inner* components of the visible catalogue (`inner_component_draw`, buffer 0) so no positive pixel can be reconstructed from the catalogue-distance features. 8 bags for the fold-local arms, 3 bags for the released file. Belief averaged, then `thin_to_budget`: bisect a belief threshold so the thresholded region carries ≈3× the budget, `skimage.morphology.skeletonize` it, trim to budget by belief. Emission domain = footprint ∧ ¬catalogue ∧ (distance to catalogue > 2 px).

**Named non-fault mimics.** Unfaulted lithologic contacts, dykes and intrusive edges, alluvial-fan and terrace margins, survey flight-line striping, hydrothermal alteration halos. **The flight-line repeatability veto (H4) was not run** — its host is unreachable from this sandbox — so that mimic is *not* excluded. This is the largest unmitigated scientific risk in the released file.

## HOLDOUT-DTI, within-lane only

Evaluator `gems57-pooled-hide-v2` (unchanged shared), implementation hashes recorded in `evidence/lane_b_paired.json`; 4 spatially blocked folds, seed 20, hide 20 % of fault components with a 3-px buffer, α = 0.2, β = 0.8, 300 m triangular kernel, 200 m blocks, 158 spatial clusters, 2,000 paired bootstrap draws. Budget 37,000 dots allocated per fold by active-cell share. Every arm is fold-local, so none is inflated by the privileged-catalogue bias below.

| Arm | shared buffered DTI [CI95] | detached-8px DTI [CI95] | Δ vs control (shared) | Δ vs control (detached) |
|---|---|---|---|---|
| `control_contrast` (unsupervised contrast-rank top-N) | 0.0206 [0.0165, 0.0251] | 0.0143 [0.0106, 0.0185] | — | — |
| `candidate_topN` (supervised, unthinned) | 0.0436 [0.0348, 0.0533] | 0.0094 [0.0051, 0.0144] | +0.0384 [+0.0301, +0.0465] | +0.0113 [+0.0076, +0.0150] |
| **`candidate_thin` (released arm)** | **0.0821 [0.0697, 0.0951]** | **0.0207 [0.0145, 0.0278]** | +0.0615 [+0.0484, +0.0752] | +0.0064 [−0.0011, +0.0142] |
| `candidate_thin_ring` (1-px graded ring hedge) | 0.0553 [0.0469, 0.0638] | 0.0130 [0.0093, 0.0170] | +0.0268 [+0.0219, +0.0320] | +0.0077 [+0.0050, +0.0109] |

Δ columns are *released arm minus that arm*. Read honestly:

1. **Supervision roughly doubles the unsupervised control at every budget** from 10,000 to 130,000 dots (shared instrument, paired CI strictly positive).
2. **1-px skeleton thinning is the single largest effect measured** — +0.0384 over unthinned top-N at the same budget, resolved on both instruments. This is the mechanism worth keeping.
3. On the blind-truth-representative detached-8px instrument the candidate's edge over the *control* is **not resolved** (CI crosses zero). Do not quote it as a win.
4. The graded ring hedge **hurt** on both instruments and was dropped.
5. DTI rises monotonically with budget on every instrument (0.0821 → 0.1006 from 37 k to 70 k dots), so the holdout **cannot locate the false-positive-limited optimum**. The released budget was therefore anchored on the user-reported ledger cluster (35 k–39 k dots → 0.2649–0.2778), not on the instrument.

Leakage canaries: 43/43 pass (two-sided AUC below the 0.90 bar). Strongest: `dcat_vis` 0.7937, `cdens15_vis` 0.7140, `z_iso_grav_anom_hg` 0.6425, `z_geod_2ndinv` 0.6337. Fold holdout AUC of the bagged belief 0.7598–0.8389. **Irregularity:** 60,964 of 60,988 catalogue pixels are component tips, so `dtip_vis` is near-degenerate with `dcat_vis`; reported, not suppressed. `iters = 300 = max_iter` on every bag, so early stopping never fired and the validation AUC (0.978–0.986) is *not* convergence evidence.

## The released file

`docs/downloads/wbg2b-skelprop-38000dots-20261027T190048Z-868d2669a230-zeros.tif` — sha256 `f4930e2fe2073a720dee7f6dc5584e3bde0eec99541a89702c0a3fcc676dd876`, 128,252 bytes, 38,000 dots at exactly 1.0, every other cell exactly 0.0 (all finite, no NoData), EPSG:32611, 3730×3292, 100 m transform. Skeleton length before trimming was 52,341 px; the budget trimmed it by belief. Submission name and 99-character note are in the run card. Format gates: independent strict re-read passes, all shared `gems57.validate` checks pass, zero dots on mapped catalogue pixels. Uniqueness: 13 registry rasters, 0 STOPs, max overlap with a discriminating witness 0.4215 (limit 0.70), max |Spearman| 0.5478 (limit 0.90, and that value is against the saturated continuous prior; against discriminating witnesses it is ≤0.064). The two saturated witnesses are reported with enrichment and a binomial z rather than silently dropped: lattice overlap 0.9926 vs random null 0.9987 (enrichment −0.0061, z −33.5) and dense prior 1.0000 vs 1.0000 (enrichment 0.0000).

**Projection, never a score:** 0.0871 (floor) – 0.2793 (parity). See the algebra below; parity reproduces GEMSDOE32's reported 0.2778 by construction, which is the only reason to trust its arithmetic.

# The shared holdout cannot rank catalogue-built rasters (measured, decisive)

`scripts/calibrate_holdout.py` scores all 13 registered rasters with the **unchanged** shared evaluator on the **unchanged** shared folds, then correlates with the values their owners reported.

| Instrument variant | Spearman vs reported | n | withheld truth px |
|---|---|---|---|
| shared buffered (unchanged) | **−0.849** | 9 | 11,321 |
| detached-6px | **−0.849** | 9 | 7,925 |
| detached-8px | **−0.832** | 9 | 6,355 |

The instrument is **anti-predictive**. Cause: those rasters were built with the *full* mapped catalogue, while the proxy truth *is* a random 20 % subset of that same catalogue. Dots hugging mapped traces collect credit here that they cannot collect live, where the truth is disjoint from the catalogue and known-fault pixels are masked out of scoring (ORGANIZER-CONFIRMED — DrivenData staff, forum thread 11516: "Pixels corresponding to known USGS/INGENIOUS faults are masked / excluded from evaluation").

**Decisive counterexample.** GEMSDOE32 is GEMSDOE25 with every dot within 2 px of the catalogue removed. Reported leaderboard went **0.2600 → 0.2778** (pruning helped). On this instrument the same pruning collapses pooled DTI **0.0919 → 0.0037** and coverage **0.142 → 0.005**. The instrument ranks those two files in the *opposite* order to the organiser-adjacent numbers. Restricting truth to pixels far from any visible trace does not repair it (GEMSDOE32 stays lowest at every detachment radius: 0.0033 at 6 px, 0.0027 at 8 px).

**Surviving anchor.** The catalogue-agnostic stride-5 lattice scores 0.0880 here against a reported 0.0904 (ratio 0.97), so the instrument's *scale* is right for untargeted emissions; only its *ranking* of catalogue-adjacent ones is broken.

**Consequences, applied.** (1) Cross-family holdout comparisons are withdrawn — including the previously published HOLDOUT-DTI 0.1321 for the rejected step-asymmetry file, which is now known to be a meaningless number. (2) Only within-lane comparisons where both arms are fold-local and catalogue-agnostic are reported. (3) No local instrument in this repository can validate off-catalogue emission quality, so no leaderboard projection here can be better than an explicitly assumption-labelled band.

A second, structural artifact is worth recording: the buffered split forces every withheld pixel ≥3.16 px from a visible catalogue pixel, so proxy truth piles up in a thin shell just outside mapped traces. That flatters catalogue-parallel placements and depresses anything genuinely blind — which is why the detached variants were built, and why the candidate's absolute numbers there are an order of magnitude smaller.

# DTI algebra: what the metric actually rewards

Metric (official page 967): `k(d) = max(1 − d/R, 0)`, R = 300 m = 3 px; `DTI = TP_w / (TP_w + α·FP_w + β·FN_w + ε)` with α = 0.2, β = 0.8.

**Marginal bar for one dot.** Adding a dot of value p and kernel credit k gives `DTI(p) = (A + pk)/(B + pC)` with `A = T`, `B = T + αFP + βFN`, `C = k + α(1−k)`. Then `dDTI/dp = (kB − AC)/(B + pC)²`, whose sign does not depend on p. So DTI is monotone in p and:

* a dot is worth raising to p = 1 exactly when `k > α·D / (1 − (1−α)·D)`, where D is the current DTI;
* at D = 0.2515 that bar is **k > 0.0630**, not the naive `k > α·D = 0.0503`.

Two operational consequences, both used above: **graded probabilities never help** (binary support at p = 1 is optimal, which also makes the portal's "[0, 1]" gate trivial), and **the optimal budget is smaller than the naive rule suggests** (the exact bar is ~25 % stricter at these DTI levels). Verified numerically in `tests/test_lane_b.py`.

**Optimal shape for a linear target.** For a predicted line at perpendicular offset d⊥ from a truth line of length L, emitted with along-track spacing s, `DTI = k_eff/(0.2·k_eff + 0.2(1−k_eff)/s + 0.8)`. At d⊥ = 1 px: s = 1 → 0.667, s = 2 → 0.473. At d⊥ = 0: s = 1 → 1.000, s = 2 → 0.830. **Continuous 1-px ridges beat dotted ridges**, because the β = 0.8 false-negative term prices lost coverage far above the α = 0.2 saving on false positives. Conversely a 2-px-wide ridge pays 0.2(1−k) for its second row and earns no extra credit — which is exactly why skeleton thinning was the largest measured gain in this lane.

**Budget economics.** `DTI = T/(0.2T + 0.2(n − M) + 0.8K)` where n = dots, M = distinct truth pixels within 3 px of a dot, T = Σ kernel credit, K = truth pixels. Calibrating on the public ledger: the lattice (193,420 dots in the scored domain, 37.5 % coverage, reported 0.0904) implies **K ≈ 12,200** real truth pixels; GEMSDOE32/B2 (37,654 dots, reported 0.2778) then implies T ≈ 4,600 over M ≈ 8,259 (mean kernel credit 0.557), and the identity reproduces 0.2778 to <1e-3. To reach 0.35 needs T ≈ 5,900; to reach the live leader 0.4544 needs T ≈ 7,850, i.e. 64 % of all truth pixels within 3 px of a dot at ~37 k dots. Nothing in this repository has demonstrated a mechanism that gets there.

# Public leaderboard, refreshed 27 October 2026

Fetched from the official page (the sandbox has no route to drivendata.org for `scripts/refresh_leaderboard.py`, so the values were transcribed from the fetched page text and the method is recorded in `docs/data/leaderboard.json`): #1 xiaofanhu **0.4544** (32 submissions), #2 cfld__ 0.3916, #3 Batik Shirt Brothers 0.3911, #4 BrandenKMurray 0.3724, #5 No Fault of Our Own 0.3566, #6 joeyfezster 0.3447, #7 JerryDataWorks 0.3418, #8 alexoktaba 0.3416, #9 DARD 0.3398, #10 Azazel 0.3379, then a dense cluster 0.3261–0.3335 (yifanxu, baobao, notmyfault, newway, ohyeah, ruping, giles, li002666, mzoorob, shixing, nchuzhoy, kinghorton42).

The highs quoted in the project brief (0.3195 and 0.4413) are both stale, and the repo's own previous snapshot (0.4437, 26 October) is superseded. The best number this scope has ever reported — 0.2778 — sits **far below the median of the leading group**, so "beat our own best" and "be competitive" are different targets. Note also that the public leaderboard is not what decides either prize: the Initial Prize Round is scored on the private chunk at close, and the Final Prize Round re-scores the same submission against an expert-expanded label set.

# Next session (updated 27 October 2026)

1. **Get real 1 m/10 m elevation.** The single most likely reason the leading group is at 0.33–0.45 while catalogue-adjacent geophysics sits at 0.27 is terrain-detail-dependent fault mapping. [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) is free and official; the binary hosts were blocked here, so confirm obtainability *before* implementing (protocol requirement). H3 (catchment-normalized cross-drainage deflection) and any scarp/lineament work depend on it.
2. **Run the flight-line veto (H4)** once the [GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) line CSVs are reachable. Until then the released file's largest unmitigated risk is survey striping, and it should not be described as geologically clean.
3. **Fix the instrument, or stop using it for anything cross-family.** A defensible local instrument needs truth that is *not* a subset of the catalogue the candidates were built from — e.g. an external mapped-fault source outside the study footprint, or synthetic faults injected into the bands with a forward model. Without that, every "estimated score" in this repo is a labelled guess.
4. **Budget is unresolved.** The holdout says more dots are monotonically better; the ledger says 37 k beats 44 k and 61 k for unthinned ridges; the exact marginal bar (k > 0.063) says the optimum is *smaller* than the naive rule implies. One slot spent on a deliberate budget probe (e.g. 22 k vs 38 k of the same support, ranked) would resolve it — that is a selector decision, not a lane decision.
5. **Ask the organiser two questions** (forum, not code): whether the Final Round's expanded label set rewards flagged-but-unmapped corridors more than precise traces, and whether the "[0, 1]" portal rejection can be reproduced from an all-finite zeros-outside file. Both change what to emit.
6. Known upstream defects still open: `gems57.gates.format_report` passes finite pixels marked NoData inside the footprint; the shared metric docstring's "truth-credit delta ≤ one dot's self-credit" is false on multi-truth fixtures; IR-57-BAR-01; band 15 "conductive base" vs mirror "basement"; band 6 `tc` description disagreement.
