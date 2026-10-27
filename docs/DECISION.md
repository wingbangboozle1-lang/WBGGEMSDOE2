# Current decision — OK TO DOWNLOAD AND SUBMIT

**Recorded:** 2026-10-27 UTC. This is the single current decision superseding the earlier review-lane
`DO NOT SUBMIT` record. The authoritative machine-readable form is [`data/decision.json`](data/decision.json),
byte-bound to the raster and backed by the [`data/decision_validation.json`](data/decision_validation.json)
receipt (43/43 automated checks). Full protocol run card: [`data/h1_run_card.json`](data/h1_run_card.json).

## The deliverable

| Field | Value |
|---|---|
| File to download | [`downloads/wbg2-h1-crossphysics-dualpop-20261027T173000Z-laneh1-zeros.tif`](../downloads/wbg2-h1-crossphysics-dualpop-20261027T173000Z-laneh1-zeros.tif) · [one-TIFF .zip](../downloads/wbg2-h1-crossphysics-dualpop-20261027T173000Z-laneh1-zeros.zip) |
| SHA-256 | `239d98d90ec254ace8b5a0fcf819710c9fac18500e8b267d67b823f533f6ecbd` |
| Submission name | `wbg2-h1-crossphysics-dualpop-20261027T173000Z-laneh1-zeros` |
| Note (≤140 chars) | H1 cross-physics lineament dual-population. HOLDOUT-DTI 0.097 CI 0.088-0.105, 22893 withheld. Unique candidate; slot = separate selector. |
| Positive dots | 46,887 (single float32 band, confidence = 1.0) |
| Format | EPSG:32611, 100 m, 3730×3292, transform (100,0,243350,0,−100,4508550), all values in [0,1], no NaN/Inf, `nodata` unset, zeros outside footprint, none on mapped faults |
| Estimated score | **HOLDOUT-DTI 0.0966 (95% CI 0.0877–0.1051)** — a labelled research proxy. **Leaderboard score: UNKNOWN** (no organizer receipt; no projection). |

## Why it is OK

- **Genuinely new, not a copy.** Built from the restored 19-band feature stack by a novel method (multiscale
  cross-physics potential-field lineament coherence + buffered structural-continuation prior). Max final-dot
  3 px overlap vs the nine focus sites, H31 and H47 = **0.29** (limit 0.70); max surface |ρ| vs all 13 registered
  rasters = **0.22** (limit 0.90). Verified both before placement and on final dots.
- **Every hard gate passes.** 43/43 in `wbg_verify_decision.py`: independent grid/format inspector + pinned shared
  gate; leakage canaries (all real features AUC ≤ 0.90; the full-catalogue halo is a flagged leakage *demo* never
  used); spatially-blocked hide-and-recover holdout with visible-only features; byte binding across decision,
  run card, format receipt, TIFF and ZIP; note/name ≤ 140 chars; no invented leaderboard score.
- **Holdout beats the champion mechanism.** Pooled HOLDOUT-DTI 0.0966 vs 0.0039 for the B2 mechanism on the same
  8 buffered folds (paired Δ 0.0927, 95% CI excludes zero); 22,893 withheld positives; evaluator
  `gems57-pooled-hide-v2`, α=0.2, β=0.8, 300 m triangular kernel. Superiority over a pure continuation control is
  *not* statistically proven (CI straddles 0) — stated openly.
- **Fixes the [0,1] error.** All-finite `[0,1]` values with zeros outside the footprint directly avoid the earlier
  *"Predicted values must be in range [0, 1]"* portal error.

## Honest limits (read before uploading)

1. **No leaderboard score.** The scoring truth (expert-labelled NEW faults, public + private split) is unpublished;
   there is no organizer receipt for this file, so no leaderboard score is estimated. The HOLDOUT-DTI is a proxy on
   an owner-mirrored catalogue and is NOT comparable to leaderboard DTI.
2. **Data provenance.** Inputs are a hash-verified public owner mirror, not an authenticated DrivenData download;
   the mirrored "sample" has 60,988 positives vs the official all-absence example. Grid geometry matches the
   official EPSG:32611 / 100 m spec, but sample bytes are not organizer-authenticated.
3. **Flagged policy decision.** Two space-filling registry controls (a stride-5 lattice and a fully-positive
   continuous prior) would reject every candidate under a literal dot reading — even the 0.2778 champion. An
   explicit, reviewable policy decision applies the surface-correlation branch to them instead. See
   [sources.html](sources.html#irregularities) and `IR-DECISION-01`.
4. **Selector is separate.** This lane spent **0** weekly slots. The actual upload, the single-final-submission
   choice and the weekly cap (up to 3) are a separate selector decision. Local validation is not organizer
   acceptance. Generative-AI use must be disclosed in the prize narrative.

## Reproduce / verify (no human inspection)

```bash
python scripts/wbg_verify_decision.py            # exit 0 = OK TO DOWNLOAD AND SUBMIT
python scripts/wbg_verify_decision.py --receipt evidence/decision_validation.json
# Optional full regeneration from restored data:
python scripts/wbg_h1_lane.py
python scripts/build_site.py && python scripts/build_site_data.py
```

## Exactly how to submit

See [executive-summary.html](executive-summary.html) and the dedicated [submit.html](submit.html): download the exact
`.tif`/`.zip`, verify SHA-256, do not clip/rescale, then on DrivenData use *Submit → Make new submission*, select the
single GeoTIFF, enter the unique name and short note above, submit once, and keep the organizer receipt.
