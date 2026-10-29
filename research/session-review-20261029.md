# Session review — 2026-10-29 (UTC)

**Status: BLOCKED / DO NOT SUBMIT.** No new TIFF was generated, no experiment was run, no weekly slot was used, and no leaderboard score is claimed.

## 1. Why no unique TIFF is offered for download today

The request asks for a unique GeoTIFF that is "OK TO DOWNLOAD AND SUBMIT". The repo's governing rules (`AGENTS.md`, README START HERE) only allow a candidate when all of these hold. Today they do not:

| Requirement | State today | Evidence |
|---|---|---|
| Explicitly assigned method lane | **Missing.** Lane is UNASSIGNED. Ranked proposals are not an assignment. | `research/hypotheses.md`, `evidence/checkout_readiness.json` (gate `lane`) |
| Derived feature bank / cache | **Missing.** Raw bands are hash-verified; the derived bank is not built. | `evidence/checkout_readiness.json` (gate `raw-band-cache`) |
| Holdout HOLDOUT-DTI with paired CI | **Not run.** No canaries, no matched experiment. | gate `scientific-validation` |
| Complete registry uniqueness check | **Incomplete.** Only pinned witnesses audited; dense-prior support policy unresolved. | gate `registry` |
| Portal-format validator that matches the shared writer | **Defect open upstream.** Mask-validator defect is documented; no corrected upstream pin. | gate `shared-format` |
| Separate slot selector and quota receipt | **Not run.** Account quota not observable from this sandbox. | gate `selector` |

Generating a raster now would produce a file with no holdout score, no lane and no complete uniqueness check. The repo's rule is that such a file is not offered for download. This is the fail-closed decision.

## 2. What was verified this session (2026-10-29)

Commands were run in this checkout. Labels below follow the README taxonomy.

- **Network reachability** (`curl` HTTP status, run 2026-10-29):
  - `https://www.drivendata.org/` → 000 (unreachable from the sandbox)
  - `https://www.dropbox.com/` → 000
  - `https://gdr.openei.org/` → 000
  - `https://docs.nlr.gov/` → 000
  - `https://www.usgs.gov/` → 000
  - `https://epsg.io/32611` → 000
  - `https://github.com` → 200; `https://api.github.com` → 200; `https://registry.npmjs.org` → 200; `https://pypi.org/simple/rasterio/` → 200
  - **Consequence:** official competition files cannot be downloaded from DrivenData or Dropbox from this sandbox. Only GitHub, npm and PyPI are reachable.
- **Official reference repo** `drivendataorg/gems-prize-reference-solution` (GitHub API tree, 200): contains code, a notebook and environment files, **no data**. Source: https://github.com/drivendataorg/gems-prize-reference-solution
- **Owner-mirror restore** (`scripts/prepare_data.py --fetch`, pinned template repo `buffedlizard55-lab/57GEMSDOE` at commit `822a0ce5546c7b6749cdd82eb145b6b3e616603d`, dated 2026-10-11 per GitHub API). It is an **OWNER-MIRROR**, not an authenticated DrivenData download (`evidence/data_preparation.json`: `authenticated_organizer_copy: false`).
- **SHA-256 of restored files** (computed locally with `sha256sum`):
  - `data/official/training_features.tif` = `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` (418,912,844 bytes, 19 bands, EPSG:32611, 3730×3292, 100 m, transform `100,0,243350; 0,-100,4508550`)
  - `data/official/labels.tif` = `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` (425,830 bytes, int8, values −1/0/1, 60,988 cells equal to 1)
  - `data/official/existing_faults.tif` = `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`
  - `data/official/sample_submission.tif` = `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` (float32, NaN outside footprint, values 0/1 inside)
- **Readiness gate** (`PYTHONPATH=src python scripts/check_readiness.py --check`, exit 2): `shared-code` and `mirror-inputs` now show **verified** (hash identity only). `lane`, `raw-band-cache`, `registry`, `shared-format`, `scientific-validation` and `selector` remain **blocked/not-run**. Output: `evidence/checkout_readiness.json`.
- **Test suite** (`PYTHONPATH=src pytest -q -rs`): **378 passed, 18 skipped, 0 failed**. Skips are for absent labels, the pinned template, and the feature stack; they are not passes of those checks.

## 3. Irregularities flagged for manual review

1. **`labels.tif` and `existing_faults.tif` are byte-identical** in the owner mirror (same SHA-256 `7ba308cc…4093`, same 425,830 bytes, both 60,988 positive cells). In the competition the labels are the withheld positives and the existing faults are the public catalogue. If the official files are also identical, every holdout built on them (`60,988 withheld positives` in the README) would be degenerate. **Do not treat any holdout number in this repo as valid until the official files are compared against an authenticated DrivenData download.** Reviewer: check both files on the DrivenData data tab (login required). https://www.drivendata.org/competitions/306/competition-doe-gems/data/
2. **Leaderboard numbers conflict.** The user prompt cites both 0.4413 and 0.3195 as the "highest score right now". The README records a public observation of 0.4544 at rank 1 on 2026-10-28. This session could not re-check the leaderboard (drivendata unreachable). Reviewer: confirm the current leaderboard at https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
3. **The "Predicted values must be in range [0, 1]" upload error** has an unknown cause. Candidate causes that the repo has not resolved: NaN inside or outside the footprint, a writer producing values outside [0,1], or a mask-validator defect (`shared-format` gate). The repo's sample submission contains NaN outside the footprint, so NaN alone cannot be the whole explanation.
4. **Mirror ≠ organizer.** All numbers derived from the owner mirror (training features, labels, sample submission) are hash-identity evidence only. Organizer acceptance is not established by any local check.
5. **Historical scores are user-reported.** GEMSDOE32 B2 (0.2778), GEMSDOE36 (0.2750), and the other nine-site scores come from the user's report and the sites' text, not from organizer receipts (see `docs/executive-summary.html`).

## 4. Candidate hypotheses (not assigned, not run)

Grounding: band names are the official 19-band names from the restored `training_features.tif` metadata (`evidence/feature_cache.json`). "Repo use" counts how many `src/`+`scripts/` files and how many `config/`+`research/` files mention the band (this session's grep). These are desk proposals; no ranking claims a DTI gain.

| Rank (qualitative) | Candidate | Layers (official band name) | Physical signature | Why it could find an uncatalogued fault | Named non-fault mimic | Repo use (src+scripts / config+research) | Implementation cost |
|---:|---|---|---|---|---|---|---|
| 1 | **C1 — Gravity-slope ridge veto on magnetic edges** | `iso_grav_anom_slope` (band 5) + `rtp` (band 2) | Co-located ridge of the gravity gradient-slope with the RTP edge, after removing edges that have no gravity ridge | A density step under basin fill has no surface trace but can still show a gravity-slope ridge | Basin-margin density contrast with no fault | band 5: 2 / **0** | Low–medium (uses existing cache) |
| 2 | **C2 — Earthquake-intensity gradient as a weak prior** | `ieq_n100a15` (band 16), `deq_n100a15` (band 10) | Distance-decay of seismic intensity around ridge candidates, tested only in held-out folds | Historical seismicity is independent of the catalogue and can mark active structure | Anthropogenic or regional seismicity not on a fault; catalogue-blocked events | band 16: 2 / 3; band 10: 1 / 2 | Low (feature only) |
| 3 | **C3 — Conductive-base step under magnetic edges** | `depth_to_base_surf` (band 15) + `cond_surf` (band 17) | Step in conductive-base depth coincident with a magnetic edge | Basin-bounding faults can offset conductive base without surface expression | Lithologic basin edge, not a fault | 6–4 / 9–9 | Medium; **overlaps the repo's existing `GVCD` and `N2` work — low novelty** |
| 4 | **C4 — Strain-rate ridge coincidence** | `geod_shearrate` (band 7), `geod_dilaterate` (band 8) | Co-located shear and dilatation ridges with magnetic tilt | Shear strain can localize on buried structures | GPS/InSAR noise or orbital artefacts | 3 / 4 and 1 / 4 | Medium; **overlaps GVCD-H\* — low novelty** |

**Top candidate: C1.** It is the only candidate whose band has never been configured in this repo (`iso_grav_anom_slope` has 0 config/research mentions). Its validation requires: (a) feature-alone leakage canary (AUC > 0.90 is a leakage alarm); (b) buffered whole-segment hide-and-recover HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI; (c) registry-overlap check before any placement. **It cannot start until the lane is assigned by the user** (see §5).

## 5. Decisions needed before any candidate can be generated

1. **Assign one method lane** (e.g. C1 alone). The lane is a scientific decision, so it is not made here.
2. **Authenticate the official labels.** Download `labels.tif` and `existing_faults.tif` from the DrivenData data tab with the user's own login and compare them against the owner-mirror hashes. Irregularity 1 above depends on this.
3. **Confirm the current leaderboard** (irregularity 2).

## 6. Sources (manual review)

- Competition overview / problem: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Data tab (login): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Official reference repo: https://github.com/drivendataorg/gems-prize-reference-solution
- Submission-format PDF (NLR): https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Owner-mirror repo (pinned commit): https://github.com/buffedlizard55-lab/57GEMSDOE/commit/822a0ce5546c7b6749cdd82eb145b6b3e616603d
- USGS GEODAWN data: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- EPSG:32611 (CRS of the rasters): https://epsg.io/32611 (not reachable from this sandbox; verified only via the raster's own CRS metadata)

## 7. Limitations

- No DrivenData or Dropbox egress: official files cannot be re-downloaded here.
- No authenticated organizer copy; no organizer receipt for any file.
- The shared derived-feature bank and a validated format writer are not in this checkout.
- Leaderboard numbers could not be re-checked this session.
- This review ran no experiment; it uses 0 of 3 experiments and 0 weekly slots.
