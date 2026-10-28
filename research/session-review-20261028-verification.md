# Session review — 28 October 2026 (independent re-verification)

**Lane status:** UNASSIGNED. This session ran **no candidate experiment**, placed **no dots**,
spent **0 weekly slots**, and generated **no new TIFF**. Its deliverable is an **independent
re-verification** of the repository's central claims plus a decision-critical policy finding.

**What this session actually did**

1. Installed the pinned runtime (`requirements.txt`) and ran the full suite:
   **350 passed, 12 skipped** (`pytest`) and **41 passed, 11 skipped** (`checks/`).
2. Ran the documented build pipeline end to end
   (`build_hypotheses → build_run_card → build_site_data → sync_msptcd_evidence →
   build_msptcd_site → build_site → build_release`): **all exit 0**, all gates stay closed.
3. Restored the two hash-pinned owner-mirror reference grids
   (`reference_grid_mirror.tif`, `existing_faults_mirror.tif`) from the pinned GitHub blobs and
   hash-verified them.
4. Re-ran the registry audit **with fetch** (`scripts/audit_registry.py --fetch`) to
   independently re-derive the lattice-coverage bound and the B2 lineage from the pinned
   registry bytes. Output: `evidence/registry_audit_20261028.json`.
5. Read back the on-disk TIFF bytes of the best local candidates and checked format/range/hash.

Every number below marked **VERIFIED** was reproduced in this session from pinned bytes, not
copied from prose.

---

## 1. Independent re-verification of the literal uniqueness bound (VERIFIED)

Reproduced from the pinned 13GEMSDOE lattice and the mirrored footprint:

| Quantity | Value | Status |
|---|---:|---|
| Footprint cells | 5,167,373 | VERIFIED |
| Cells within inclusive 3 px of the lattice | 5,160,724 | VERIFIED |
| Fraction of footprint covered | 0.99871327 | VERIFIED |
| Uncovered cells | 6,649 | VERIFIED |
| Uncovered cells within 3 px of a footprint edge/hole | 6,485 | VERIFIED |
| Max distance from an uncovered cell to the footprint exterior | 48.01 px | VERIFIED |
| Standard budget | 37,654 dots | — |
| Minimum possible 3-px lattice overlap at that budget | **0.82341849** | VERIFIED |
| Stop limit | 0.70 | — |
| Feasible under the limit at standard budget? | **false** | VERIFIED |
| Largest budget that could possibly meet the limit | **22,163** | VERIFIED |

**Consequence (counting bound, not a score):** for any 37,654-distinct-dot map, at least
82.34% of dots lie within 3 px of the registered lattice, above the 70% stop. Passing the
literal rule at the standard budget is therefore **arithmetically impossible**; it would require
a budget below 22,164 dots placed almost entirely in the 6,649 uncovered cells — which the repo
correctly classifies as *footprint-edge gaming* that confounds acquisition geometry with geology,
not as a scientific submission.

The separate 17GEMSDOE continuous prior is positive on **all 5,167,373** footprint cells
(VERIFIED). Under the shared literal finite-positive support rule every nonempty candidate
overlaps it 100%. Whether a continuous prior "counts as dots" is a **policy question**, not a
measurement; this session applies no exemption.

## 2. Independent re-verification of the B2 lineage (VERIFIED)

From the pinned GEMSDOE25/27/28/30/31/32/33/36 masks:

| Claim | Result |
|---|---|
| GEMSDOE25 and GEMSDOE30 identical in-footprint | **true** (both 44,090 dots) |
| GEMSDOE32 B2 = GEMSDOE25 minus dots within 2 px of catalogue | **true** (37,654 dots) |
| GEMSDOE36 additions to GEMSDOE32 | **1,200** (0 removals) |
| Reference sample positives == catalogue positives | **true** (60,988) |

This confirms the repo's lineage: the nine "champions" are not nine independent methods; they are
one dotted mask plus deterministic prunings/additions. **B2 is not a genuinely new method** relative
to the GEMSDOE25/30 lineage.

## 3. Nine-site executive decision (all VERIFIED against pinned bytes)

`fraction_within_3px_of_lattice` is the candidate's own dots falling within 3 px of the registered
lattice. `max_focus_peer` is the best overlap with any other named focus file (directed). All nine
are literal duplicates; **none is submit-able**.

| Site | Dots | 3-px lattice overlap | Best focus peer | Verdict |
|---|---:|---:|---|---|
| GEMSDOE32 (B2) | 37,654 | 0.99915 | GEMSDOE24 1.000 | DO NOT SUBMIT |
| GEMSDOE36 | 38,854 | 0.99918 | GEMSDOE27 0.9758 | DO NOT SUBMIT |
| GEMSDOE28 | 37,660 | 0.99910 | GEMSDOE24 1.000 | DO NOT SUBMIT |
| GEMSDOE31 | 40,199 | 0.99918 | GEMSDOE24 1.000 | DO NOT SUBMIT |
| GEMSDOE33 | 41,865 | 0.99914 | GEMSDOE27 0.9971 | DO NOT SUBMIT |
| GEMSDOE25 | 44,090 | 0.99916 | GEMSDOE24 1.000 | DO NOT SUBMIT |
| GEMSDOE30 | 44,090 | 0.99916 | GEMSDOE24 1.000 | DO NOT SUBMIT (== GEMSDOE25) |
| GEMSDOE24 | 60,069 | 0.99922 | GEMSDOE25 1.000 | DO NOT SUBMIT |
| GEMSDOE27 | 61,328 | 0.99923 | GEMSDOE24 0.9802 | DO NOT SUBMIT |

**Answer to "which is the best submission to submit to obtain a high score":** none of the nine.
The highest *user-reported* claim (GEMSDOE32 B2, 0.2778) is also a literal duplicate and cannot be
resubmitted. The table the requester asked for (file / estimate / unique?) is therefore all
"DO NOT RESUBMIT" with estimate **Unavailable** — there is no defensible leaderboard forecast for
any archived file, and resubmitting a duplicate wastes a weekly slot.

## 4. Why B2 may have reached 0.2778 — and whether we can beat it

**Why (plausible, not proven).** The official metric is
`DTI = T / [(1−β)T + αF + βN + ε]` with α=0.2, β=0.8, 300 m triangular kernel. B2 removes 6,436
dots within 2 px of the mapped catalogue from the 44,090-dot D2.8 mask. Removing dots can raise DTI
only if the lost false-positive mass `ΔF` outweighs the lost truth coverage `ΔT`; the improvement
condition is `[1−(1−β)s]·ΔT > α·s·ΔF`. **Both ΔT and ΔF were not measured**, so the 0.2778
mechanism is a hypothesis, not a verified decomposition. (An older claim that the removal saved
`0.2·ΔFP ≈ 12,074` is withdrawn as impossible: even at one mass unit per removed dot the weighted
reduction is ≤ 1,287.2.)

**Can we beat it?** Unknown, and not currently testable here:
- The method lane is UNASSIGNED, so no candidate may be implemented.
- No authenticated competition feature stack / labels are present in this checkout
  (`data/` holds only the two small reference mirrors; the 418 MB training stack is not restored).
- The best measured candidate in the repository is **WBG2-DISTAL `natural_oof`**,
  **HOLDOUT-DTI 0.1770**, 95% CI [0.1549, 0.1976], evaluator `gems57-pooled-hide-v2`,
  60,988 withheld positives, 61/61 leakage canaries ≤ 0.6180 — but it **also fails the literal
  all-registry rule** (max registry dot overlap 0.9066 > 0.70) for the same blanket-control reason.
- The empirical fleet model's point estimate for the archived candidate is **0.1493**,
  95% PI **[0.000, 0.333]**, external-test RMSE 0.094; it **cannot certify anything above the
  observed 0.2778** and gives no evidence about the 0.33–0.45 leaderboard band.
- The organizer-published public leaderboard high observed on 2026-10-27 was **0.4544**
  (xiaofanhu). This is a public observation, **not** a per-file receipt.

## 5. The `[0, 1]` submission error — cause identified (VERIFIED against on-disk bytes)

The requester's upload failed with *"Predicted values must be in range [0, 1]"*. The repository's
recorded cause (`data_public/candidate.json`) is a **NaN-filled variant**; the fix is to write
**zeros everywhere** (no NaN, no NoData mask) inside and outside the footprint. This session
read back the two best local TIFFs and confirmed they already satisfy the portal's range rule:

| File | CRS | Shape | Transform | dtype | bands | min | max | NaN | <0 | >1 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `wbg2-distaloof-natural_oof-...-8237e99a-zeros.tif` | EPSG:32611 | 3730×3292 | 100 m | float32 | 1 | 0.0 | 1.0 | 0 | 0 | 0 |
| `wbg2-distal-blind-piedmont-...-7a3f9c1d-zeros.tif` | EPSG:32611 | 3730×3292 | 100 m | float32 | 1 | 0.0 | 1.0 | 0 | 0 | 0 |

On-disk SHA-256 re-checked this session: DISTAL `512609c1…aa9c` (matches its writer receipt);
GVCD `b625e13b…5218` (matches the README). A local range pass is **not** portal acceptance, and it
is **not** uniqueness or organizer approval.

## 6. The single decision-critical policy question

The repository applies the literal rule *"any registry raster"*, which includes three **synthetic
blanket controls** (the 13GEMSDOE stride-5 lattice, the 17GEMSDOE continuous prior, GEMSDOE22).
Under that literal reading **no standard-budget candidate can ever pass**, and the requester's own
0.2778 champion is itself rejected.

If — and only if — the rule-setter confirms that **synthetic space-filling / continuous controls are
not "submissions"** and are excluded from the duplicate gate, then the repository's best candidate,
**WBG2-DISTAL `natural_oof` (HOLDOUT-DTI 0.1770)**, becomes unique under the sparse-peer rule
(max 3-px overlap 0.679 vs 437 comparable-budget fleet rasters; ≤ 0.631 vs the nine focus
champions) and is the strongest available submission.

**This session does not resolve that question unilaterally and does not spend a slot.** Resolving it
is the single highest-leverage unblock. Until it is resolved, the correct action is to protect the
weekly slot and submit nothing.

## 7. Blockers (unchanged, all real)

1. **No assigned method lane** — the parallel-run protocol references a "single method paragraph"
   that is not present in the project inputs; the shortlist does not assign one.
2. **No authenticated competition data** — DrivenData requires login; `data/` is not populated with
   organizer features/labels. The owner mirror is **not** organizer-authenticated.
3. **Literal uniqueness gate is unpassable at the standard budget** (Section 1).
4. **Unresolved dense-prior interpretation** (Section 1/6).
5. **Shared template NoData-mask defect** — reproduced by regression tests; upstream issue creation
   was permission-denied. No private fork.
6. **No current complete registry** — a failed witness is conclusive, but no candidate can be
   declared globally unique from an incomplete inventory.

## 8. Next steps (ranked by P(Win) impact)

1. **Resolve the policy question in Section 6** (do synthetic blanket controls count?). This is the
   only change that can convert an existing candidate into an eligible submission.
2. **Assign an explicit method lane** and restore authenticated competition data
   (`bash scripts/download_competition_data.sh` on an unrestricted machine, then
   `python scripts/prepare_data.py`).
3. If (1) resolves in favour of sparse-peer uniqueness, run the separate **selector** step: confirm
   remaining weekly quota, assign a unique filename and a ≤140-character note, and archive the exact
   organizer receipt for the submitted SHA-256.
4. Only then consider new experiments — and only inside an assigned lane, with buffered whole-segment
   hide-and-recover holdouts, feature-alone leakage canaries, and the unchanged shared evaluator.

## 9. Session run card

- Hypothesis tested: none (no lane assigned; no experiment authorized).
- Mechanism: independent re-derivation of the lattice bound and B2 lineage from pinned bytes.
- Non-fault mimic (for any future N1–N4): unfaulted intrusive/volcanic body margins, alluvial
  edges, and survey striping can mimic paired multi-physics edges.
- Holdout DTI: **NOT RUN** (no lane, no authenticated data).
- Registry measurement: lattice overlap bound **0.82341849** (VERIFIED); all nine focus files
  literal duplicates (VERIFIED); dense prior full-footprint positive (VERIFIED).
- Raster SHA-256 generated: **none** (no new TIFF).
- Validator: existing local TIFFs re-read; range/CRS/shape/transform PASS; not portal acceptance.
- Submission name/note: **none**.
- Verdict: **negative** — protect the slot; resolve the policy question first.
