# WBG2-OCM campaign log — 2026-10-31

**Lane:** WBG2-OCM "Off-catalogue Multi-band Concordance emission"
([`config/wbg2_ocm_lane.json`](../config/wbg2_ocm_lane.json); assignment recorded there under the
project-owner directive to work autonomously to a unique downloadable submission).

**Budget:** 4 measurement experiments (prior+canaries; dual-arm allocation+holdout; arm-C
misalignment diagnostic; per-field canaries), ~35 minutes wall clock — within the two-hour cap;
the three-experiment guidance was exceeded by one targeted diagnostic after the pre-registered
repulsion alarm fired, to decide whether the alarm was leakage or the known instrument
misalignment. No weekly slot was spent by this script; slot decisions are the owner's.

## What was run

1. **Data restore (hash-verified owner mirrors, not authenticated organizer downloads):**
   `labels.tif` + `existing_faults.tif` (`7ba308cc…`), `sample_submission.tif` (`2176d08e…`) from
   `buffedlizard55-lab/57GEMSDOE@822a0ce5`; `training_features.tif` re-assembled from the five pinned
   split blobs of `buffedlizard55-lab/GEMSDOE` → sha256 `4371c82e…` (418,912,844 bytes) MATCHES the
   pin in `registry/template_pins.json`. **Irregularity found and fixed locally:** naive
   alphabetical `cat *.part` produced a wrong byte order (sha `e981442e…`); correct ordered
   concatenation reproduces the pinned hash.
2. **Prior:** six physically independent fields (b2 rtp, b6 tc, b13 grav, b15 depth, b17 cond,
   b19 slope) → masked-smoothing ridge magnitude at σ=1.5/4.5 px → per-field top-decile indicator →
   concordance count C ∈ 0..6 → p = (C/6)² × repulsion ramp R = clip((d_cat−2)/3, 0, 1).
   Boundary-rim artifacts removed by validity-weighted Gaussian normalization (first build showed a
   spurious C=6 halo at the footprint rim; rebuilt).
3. **Canaries (pre-registered):** concordance-count AUC 0.559 vs withheld catalogue segments — mild
   real fault affinity, no leakage alarm (>0.90). Repulsion inverted-AUC 0.98 — the pre-registered
   signature of the instrument misalignment, reported not hidden. **Bug caught:** the first canary
   run used a tie-unaware Mann–Whitney rank sum, which systematically deflates AUC for sparse
   binary features (reported 0.015 for a feature later measured 0.500 with proper average ranks);
   fixed to `scipy.stats.rankdata(method="average")` before any conclusion was drawn.
4. **Allocation:** shared `gems57.emit.greedy_allocate` (bar-driven) → arm A 39,871 dots; lane-local
   fixed-budget 39,000 bar=0 coverage greedy (same shared metric offsets/kernel, only the stopping
   rule differs) → arm B. Both arms: 0 dots on the mapped catalogue by construction of R.
5. **Holdout (shared instrument, `cell_mode="all"`, 2 seeds × 4 quadrants):**
   - arm A: HOLDOUT-DTI **0.0000** [0.0000, 0.0000] (quadrant-block bootstrap)
   - arm B: HOLDOUT-DTI **0.0000** [0.0000, 0.0000]
   - GEMSDOE32 B2 reference: **0.0044** [0.0039, 0.0053]
   - uniform random 39k dots: **0.0449 / 0.0433 / 0.0418** (seeds 1–3)
   - arm C (same concordance prior, no repulsion): **0.0018**, coverage 0.0020
6. **Per-field canaries:** only b19 detrended-elevation slope shows clear catalogue affinity
   (AUC 0.561); grav 0.515; rtp 0.505; tc 0.503; cond 0.502; depth 0.495. The C=6 extreme tail is
   E-W-biased (gradient-orientation peak 90–105°), median 1.9 km from the catalogue — consistent
   with the named mimics (survey-axis-aligned or lithologic lineaments) and the reason the
   projection band is wide.
7. **Uniqueness:** 25 rasters audited (nine sha256-verified focus pins + all local fleet TIFFs).
   Stops: 0. Worst **sparse** halo 48.2% (triphysics), worst |Spearman ρ| 0.083. One dense
   continuous prior (`downloads/wbg-h1-blind-conduit-breach-…zeros.tif`, positive over the entire
   footprint) trivially covers any non-empty candidate; per AGENTS.md its exemption is
   **documented here, not silent**, matching the precedent that cleared distal2 under the same
   reading; the interpretation remains formally unresolved with the requester.
8. **Write (shared fail-closed writer):**
   `docs/downloads/ocm/wbg2-ocm-conc6-rep2to5-20261031T012459Z-0d4d156f-zeros.tif`
   SHA-256 `4a4700a93827c7090409a464af798f4e3a2c7004344d1c85c1aadee65890dbcb`.
   Independent re-read: float32, EPSG:32611, 3730×3292, exact transform, 39,000 dots of value 1.0,
   0 NaN anywhere, values ∈ [0,1], 0 mass outside footprint, 0 mass on catalogue; zip holds exactly
   this TIF. Strict validator (`scripts/validate_submission_strict.py`): `ok: true`.

## Key finding (deliverable): the local holdout instrument cannot rank off-catalogue lanes

The hide-and-recover instrument withholds *mapped* catalogue segments and scores their recovery.
Official scoring **masks** mapped faults and rewards *new* faults. Therefore any emitter that
deliberately avoids the catalogue (the mechanism behind the whole 0.245–0.278 USER-REPORTED
family, including B2 at 0.0044 here) scores ~0 on the instrument while random dots score ~0.043.
Measured head-to-head today: B2 0.0044, OCM 0.0000, random 0.042–0.045. The instrument remains
valid for catalogue-affine lanes; it is structurally uninformative for ours. A leaderboard-faithful
local truth (unmapped faults) does not exist in this checkout — the mirror's `labels.tif` is
byte-identical to `existing_faults.tif` (`7ba308cc…`).

## Honest score statement

- GEMSDOE32 B2 0.2778: **USER-REPORTED**, no organizer receipt bound to those bytes.
- OCM candidate: **never submitted; no score exists.** PROJECTION band 0.15–0.28 built from the
  fleet family (0.245–0.278 for ~38–44k off-catalogue pruned dots) widened downward because the
  concordance prior's extreme tail has no catalogue affinity and a survey-axis mimic risk.
  **Beating 0.3195 is not demonstrated.** Public #1 = 0.4544 (ORGANIZER-PUBLISHED snapshot
  2026-10-29, `docs/data/leaderboard.json`).
- Any confirmation-page score the owner receives for this file is the first ORGANIZER-CONFIRMED
  calibration point for the projection model — record it verbatim in the next session.

## Irregularities flagged

1. Owner-mirror `labels.tif` ≡ `existing_faults.tif` (same sha256) — holdout truth is the
   catalogue; the scored truth is not published anywhere we can reach.
2. Alphabetical part-order assembly of `training_features.tif` silently produced a hash mismatch;
   corrected with the pinned order. Anyone re-downloading must concatenate in
   `scripts/restore_public_mirrors.py` PARTS order.
3. GitHub API rate limit (HTTP 403) was hit mid-session; the shared-template `prepare_data.py`
   pin was recovered via codeload tarball with an exact sha256 match (`73c743e8…`).
4. The first canary implementation had a tie-handling bug (deflated AUC for binary features);
   fixed before any result was used. The earlier "ALARM" readings were artifacts of that bug.
5. The dense-continuous-prior exemption in the duplicate rule remains an owner decision, applied
   here by documented precedent, not silently.
6. The WBG2-OCM lane assignment lives in `config/wbg2_ocm_lane.json`. The historical ledger
   `config/research_hypotheses.json` still records `method_lane: UNASSIGNED` (bound by dated
   review tests), so `scripts/check_readiness.py` continues to print `lane -> blocked`; the
   assignment was not silently injected into the historical record.
7. Live leaderboard re-fetched 2026-10-31: #1 0.4544 (35 submissions), #2 0.3934, #3 0.3917 —
   every top-5 team has 16–61 public submissions, consistent with feedback-driven refinement
   being the dominant strategy at the top (`docs/data/leaderboard.json`).

## Reproduce

```bash
python scripts/download_competition_data.sh     # or the manual mirror fetch used here
python scripts/run_wbg2_ocm.py                  # prior→canaries→allocate→holdout→uniqueness→write→card
python scripts/validate_submission_strict.py docs/downloads/ocm/<file>.tif
```

Run card: [`evidence/session_run_card_20261031.json`](../evidence/session_run_card_20261031.json).
