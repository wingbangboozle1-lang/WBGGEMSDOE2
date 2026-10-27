# Limitations, next steps, and suggested future work

**Current state (2026-10-27):** one unique, machine-validated candidate is cleared to download and submit
(`OK TO DOWNLOAD AND SUBMIT`). This document is the honest list of what remains unknown and what to do next.
It is linked from the [executive summary](executive-summary.html) and [sources](sources.html).

## What is genuinely established
- A new GeoTIFF built from the restored 19-band feature stack by a novel, catalogue-independent method; byte-validated
  (single float32 band, EPSG:32611, 100 m, [0,1], no NaN, exact grid), unique vs all locally-pinned registry rasters.
- All leakage canaries pass; a full-catalogue halo is correctly flagged as leakage and never used.
- A leakage-free spatially-blocked hide-and-recover holdout (8 buffered folds, 22,893 withheld positives) gives
  HOLDOUT-DTI 0.0966 (95% CI 0.0877–0.1051) and beats the champion mechanism on the same folds.

## What is NOT established (read before uploading)
1. **No leaderboard score.** The public/private truth (expert-labelled NEW faults) is unpublished and no organizer
   receipt exists for this file. No score is projected; the HOLDOUT-DTI is a proxy on a mirrored catalogue and is
   not directly comparable to leaderboard DTI.
2. **Data provenance.** Inputs are a hash-verified public owner mirror, not an authenticated DrivenData download. The
   mirrored "sample" has 60,988 positives while the official example predicts absence. Grid geometry matches the
   official spec, but sample bytes are not organizer-authenticated.
3. **Registry completeness.** Uniqueness was verified against 13 byte-verified locally-pinned rasters. The broader
   ~126-row user-reported fleet was NOT exhaustively byte-audited; global uniqueness across every historical file is
   not proven.
4. **Policy decision.** The two space-filling controls (lattice, continuous prior) required an explicit, flagged
   decision to use the surface-correlation branch. This needs organizer/owner review (`IR-DECISION-01`).
5. **Portal acceptance.** Local format validity is not organizer acceptance. The optional strict all-finite,
   zero-outside encoding differs from the official "null/NaN outside" wording; the [0,1] error is avoided, but portal
   behavior is unconfirmed.

## Immediate next step for the human (the separate selector)
- Within the weekly cap (up to 3), download the exact file, verify its SHA-256, submit once on DrivenData with the
  supplied unique name and short note, and **record the organizer receipt**. That receipt — and only that — is the
  real score. Disclose generative-AI use in the prize narrative as the rules require.
- Do not spend more than one slot on this method until a receipt exists; use the remaining slots for genuinely
  different lanes (see ranked hypotheses below), not near-copies.

## Scientific next steps (ranked, each needs a spatially-blocked holdout first)
1. **Authenticate the inputs.** Obtain the official `sample_submission.tif`, `training_features.tif`, `labels.tif`
   and `1m_DEM_links.csv` from a logged-in DrivenData account; re-verify grid, feature-band metadata (band 15
   "conductive base" vs "basement", band 6 `tc`), and the weekly quota. This is the single highest-value action.
2. **Replace the mirrored catalogue with the authenticated one** and re-run the H1 lane. Confirm the canary and
   holdout numbers are unchanged; if the true test truth is ever released, calibrate HOLDOUT-DTI to leaderboard DTI.
3. **Test the off-catalogue regime directly.** The leaderboard rewards NEW faults, while hide-and-recover rewards
   catalogue continuity. Build an evaluation that withholds *whole fault systems* (not just segments) and report
   separate on-catalogue/off-catalogue DTI. The dual-population hedge should be re-tuned on that cleaner proxy.
4. **Run ranks 2–5 of the [hypotheses](research.html#hypotheses)** with fold-local features and canaries:
   conductivity/depth contacts, geodetic strain junctions, radiometric Th/K-low corridors, and 1 m DEM drainage
   deflection. Each needs its own single-feature canary before use.
5. **Model the metric explicitly.** With α=0.2/β=0.8 and a 300 m kernel, optimize dot placement/budget with the
   exact `gems57.emit.greedy_allocate` rather than a fixed NMS top-K, and sweep budget on the holdout.
6. **Fix shared tools upstream.** Correct `gems57.gates.format_report` so finite NoData=0 inside the footprint is
   rejected, and the `metric.py` truth-credit comment; add upstream regression tests. This project keeps an
   independent mask check but does not fork the shared code.

## Process next steps
- Keep `wbg_verify_decision.py`, `verify_all.py` (3 passes) and the byte-bound `build_site.py` guard in CI so no
  future edit can silently produce a green button.
- Refresh the registry with the full current fleet (byte-audit more rasters) to reduce the completeness caveat.
- If any organizer receipt shows a score, update `evidence/decision.json`'s `not_proven` list and the site's
  estimated-score column with a properly labelled ORGANIZER-CONFIRMED value.
