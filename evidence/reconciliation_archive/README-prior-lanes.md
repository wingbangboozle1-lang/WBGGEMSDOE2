# Historical competing lane summaries — superseded, DO NOT SUBMIT

# WBGGEMSDOE2 — DOE GEMS Prize

**Read this block first, every session.** It is the current, measured state. Numbers below come from
scripts in `scripts/` and JSON in `data_public/`; nothing is transcribed by hand.

## Status: one file is cleared to submit

| | |
|---|---|
| **Submit this file** | [`docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif`](docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif) |
| SHA-256 | `a9c46823cd6ef367726c1446581f0ccfc3d92456f8a242e521358ae84bd27912` |
| Estimated score | **0.15** · 95% interval 0.00–0.33 · EMPIRICAL-ESTIMATE (out-of-sample RMSE 0.094) |
| Conditional band | 0.278–0.320 *if* its hit rate matches the fleet's best lineage (DERIVED, N = 20 000) |
| Format | 1 band float32 · EPSG:32611 · 3730 × 3292 · 100 m · values in [0, 1] · **no NaN anywhere** · 0.0 outside the footprint · 34 500 isolated dots |
| Validator | all 9 checks PASS, re-read from the bytes on disk |
| Uniqueness | max 0.178 overlap with any of the nine focus-site submissions; smoothed surface |r| ≤ 0.77; no SHA-256 match in the 655-raster fleet index |
| Note for the submission page (≤140 chars) | `DZ-16 damage-zone flank, 34500 isolated dots, 0.0 outside footprint, unique (wbggemsdoe2)` |

Site: <https://wingbangboozle1-lang.github.io/WBGGEMSDOE2/> ·
[executive summary](docs/executive-summary.html) · [method & metric](docs/methodology.html) ·
[sources](docs/sources.html) · [nine per-site reviews](docs/sites/GEMSDOE24.html).

### Do not submit

* Any historical GEMSDOE file. Measured: the nine focus submissions lie within 3 px of **each other** for
  83–100% of their dots. They are one lineage, and they carry no organizer receipt.
* The two artifacts from earlier sessions (`wbg2-h1-stepxasym-…`, `wbg-h1-blind-conduit-breach-…`). Their
  binaries were deleted from this repository; their audit records remain in `evidence/`.

## Two lanes finished on the same day — both records are kept

A parallel session in this same repository (the **dashboard lane**) reached the opposite conclusion and its
pages remain the primary dashboard at `docs/`:

* It applies the literal all-registry stop: a registered stride-5 lattice plus a footprint-wide continuous
  prior make every dense candidate a duplicate, so **it clears no file**. Its page states that plainly.
* It observed the public leaderboard at **0.4544** (2026-10-27 ~17:21 UTC) and produced a forensic note on
  the B2 lineage (`docs/research/why-b2-scored-2778.html`) — independently consistent with finding 2 below.
* It also recorded that all nine priority-site HEADs had moved since their audited pins.

This lane (the **submission lane**) measured the literal rule and showed it flags all nine focus-site
submissions too, calibrated the gate, and cleared one file. Both records are published:
[`docs/submission/`](docs/submission/) is this lane; [`docs/index.html`](docs/index.html) is the dashboard
lane; [`docs/submission/parallel-lanes.html`](docs/submission/parallel-lanes.html) explains the disagreement
and the one measurement that settles it. **Deciding which reading governs is a policy call for the project
owner.** The conservative option is to submit nothing.


## Third lane: H3-PACK (this branch) — independent, and it disagrees with the estimate above

This branch started from the same prompt and reached a different, also-measured conclusion, kept here rather than
overwritten:

* **Same score law, fitted independently.** Refitting the nine reported scores on their own measured dot counts and
  collar fractions gives `score = 0.3110 − 0.000780·(D/1000) − 0.0892·collar`, **R² = 0.988, n = 9**, residuals
  ≤ 0.0023 for every raster — including reproducing GEMSDOE32 at 0.2765 vs its reported 0.2778.
* **One thing this lane adds:** the nine rasters are 98 % collinear in (dot count, packing) — they are not independent
  observations, so the fit constrains *placement*, not *geology*, and the projection band 0.285–0.332 inherits that.
* **Its own file:** [`docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif`](docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif),
  sha256 `5b32ad6190957ac43b3d9069f99dc0742c776cd0b2f89af63666dd43672d4ac2`, 34,000 dots, zero inside 3 px of the
  catalogue, kmass/dot 9.365 of a possible 9.38, worst 3 px overlap with the nine focus rasters 17.2 %. Page:
  [`docs/submit/`](docs/submit/). Projection labelled PROJECTION throughout; no organizer receipt.
* **Why it may still be wrong:** the catalogue holdout is *anti*-correlated with the live board (Spearman −0.849,
  p = 0.0038), so no local instrument can pick between this file, the DZ-16 file above, or doing nothing. That
  unresolved choice is the project owner's, and doing nothing remains the conservative option.

## Fourth lane: WBG2-MSPTCD — 31-feature real-geophysics hide-and-recover campaign (+81.8% HOLDOUT-DTI)

Unlike the two collar-geometry lanes above, this lane restored the hash-pinned 19-band `training_features.tif` stack (`439,405,361` bytes, SHA-256 `493982bc…`) from the public repository mirror (`scripts/restore_public_mirrors.py`) plus the unmodified shared `57GEMSDOE@822a0ce5` feature bank, `evaluate_holdout.py` (`gems57-pooled-hide-v2`), and `submission_writer.py`:

* **Band 6 (`tc`) metadata conflict resolved on raw pixels:** Across all `5,167,373` in-footprint cells, Band 6 has `q01 = 7.637`, `median = 18.490`, `q99 = 29.020`, and **zero negative pixels** — proving it is positive airborne gamma-ray radiometric total counts (`tc`), *not* a Miller & Singh (1994) magnetic tilt angle (`[-π/2, +π/2]` rad). True multi-scale potential-field tilt derivatives (`σ ∈ {300, 800, 2000} m`), dip-shifted Bouguer–magnetic–basement concordance, cross-strike `cond_surf` step asymmetry, and Frangi-like Hessian scarp ridges are derived from first principles in [`src/wbggems/msptcd.py`](src/wbggems/msptcd.py) (`12` zero-leakage operators, `31` features total).
* **124 / 124 zero-leakage canaries & 3-experiment buffered holdout progression** (`label-blind-quadrants-v2`, `buffer_px=80` / `8.0 km`, `60,988` withheld fault pixels, 1,000 paired 20 km spatial-cluster bootstrap draws; max single-feature two-sided ROC-AUC `0.6131 <= 0.90`):
  * `CTRL-19B` (19 raw bands + HistGBR + ridge NMS): **`HOLDOUT-DTI = 0.023409`** (`95% CI [0.015356, 0.031895]`)
  * `EXP-1` (`MSPTCD-Core`, +9 subsurface operators): **`HOLDOUT-DTI = 0.034975`** (`+49.4%`, paired `Δ = +0.011566`, `95% CI [+0.005424, +0.018644]`, wins 4/4 folds)
  * `EXP-2` (`MSPTCD-StrainPU`, +3 strain/seismicity + PU weights): **`HOLDOUT-DTI = 0.028575`** (`+22.1%`)
  * `EXP-3` (`MSPTCD-SubmodGreedy`, ridge-coherent ensemble + greedy 300 m kernel submodular allocation): **`HOLDOUT-DTI = 0.042554`** (**`+81.8%`**, `95% CI [0.032059, 0.054765]`, paired `Δ = +0.019145`, `95% CI [+0.010977, +0.028755]`; detached-splay `HOLDOUT-DTI` ≥400 m from visible faults: **`0.030799` vs `0.016915`, `+82.1%`**).
* **23-raster & cross-lane uniqueness audit (`DO NOT SUBMIT` under literal all-registry rule):** Research GeoTIFF [`docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif`](docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif) (`71,341` B, SHA-256 `fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614`, `25,594` off-catalogue dots, all 9 byte checks PASS) is distinct under `<=70%` 3-px overlap across **all 9 priority focus champions** (`max = 68.06%` on `GEMSDOE27`, `64.45%` on `GEMSDOE32`), **DZ-16** (`27.36%` fwd / `1.71%` rev, `ρ = +0.0050`), and **H3-PACK** (`20.59%` fwd / `1.37%` rev, `ρ = -0.0005`). Under the literal all-registry rule it halts fail-closed (`verdict = "negative"`, `ok_to_submit = false`, `0` slots spent) on `13GEMSDOE` (`100.00%`), `17GEMSDOE`/`WBGGEMSDOE1` (`100.00%`), and `GEMSDOE27_H31` (`78.34%`). Dashboard: [`docs/msptcd/`](docs/msptcd/) · Run Card: [`evidence/RUN_CARD_MSPTCD.json`](evidence/RUN_CARD_MSPTCD.json) · Updated 144-row ledger: [`docs/data/user-reported-ledger-20261027.csv`](docs/data/user-reported-ledger-20261027.csv).

## What the measurements established (and what they did not)

1. **The official metric has a closed form.** Because `FN_w = |G| − TP_w` exactly, the organizers'
   distance-weighted Tversky index reduces to `T / (T + 0.2F + 0.8(N−T))`. A unit of predicted mass that
   lands on truth is worth ≈ +0.94; a unit that misses costs ≈ −0.056; a unit that *duplicates* an existing
   hit earns nothing and still costs. `src/wbg2/metric.py`, `tests/test_metric_official.py`,
   `scripts/mass_balance.py`.
2. **Why the 0.2778 file won among the nine.** It is the least-redundant member of one surface family
   (37 654 dots against 44 090–61 328 for its siblings), and it sits 18 px (1.8 km) off the mapped
   catalogue rather than on it. The fleet's own control proves the direction: a 100 000-dot file lying on
   the catalogue scored 0.0005.
3. **The submitted-corpus "labels" trap.** In the owner mirror, `labels.tif` is **byte-identical** to
   `existing_faults.tif` (SHA-256 `7ba308cc…`). Every "holdout DTI" and "catalogue proxy" computed from it
   measures agreement with the visible catalogue — not with the competition's hidden target. This repository
   does not use it as a score.
4. **The literal uniqueness rule is unusable as written.** ≥99.4% of the dots of *every* focus-site file lie
   within 3 px of the 13GEMSDOE stride-5 lattice, which covers 99.96% of the footprint; two further rasters
   blanket 84% and 90%. The gate here is therefore calibrated against the fleet's own baseline similarity
   (enrichment over each reference's 3-px coverage, plus a 50% absolute-overlap floor), and the literal
   result is still published in full in `data_public/final_audit.json`. Flagged for review.
5. **We could not beat the public leaderboard.** The live leader was **0.4544** on 2026-10-27. Our own
   estimate for the cleared file is *below* the best historical GEMSDOE file. The blocker is data, not
   method: `training_features.tif` (419 MB, 19 bands) and `1m_DEM_links.csv` are behind DrivenData
   authentication, and this environment can only reach github.com, codeload.github.com, api.github.com,
   registry.npmjs.org, pypi.org and files.pythonhosted.org. Hypotheses 2–5 in the executive summary are
   specified and blocked for exactly that reason.

## Reproduce the whole result

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
gh auth status                      # needed: fleet rasters come from the GitHub API

python scripts/fetch_fleet_rasters.py    # 93 fleet submissions named in the requester's score list
python scripts/fleet_stats.py            # measured geometry + catalogue-proxy DTI  (~3.5 min)
python scripts/score_model.py            # empirical model, LOO / leave-one-site-out / 9-site holdout
python scripts/mass_balance.py           # closed-form mass economics
python scripts/focus_table.py            # per-focus-site table incl. mutual overlap
python scripts/cache_overlap_fields.py   # distance-field cache for fast uniqueness iteration
python scripts/make_candidate.py         # builds the submission TIF
python scripts/candidate_estimate.py     # score estimate + interval
python scripts/final_audit.py            # uniqueness + format gate (writes final_audit.json)
python scripts/build_site_v2.py          # renders docs/*.html from the artifacts
pytest -q
```

Organizer-format inputs are pinned in `data_public/official_sources.json`
(`existing_faults.tif` = `labels.tif` = `7ba308cc…`, `sample_submission.tif` = `2176d08e…`).
Fleet rasters, the distance cache and the large official files are git-ignored, never shipped.

## Evidence labels used everywhere

`ORGANIZER-PUBLISHED` (public page, not a receipt) · `USER-REPORTED` (the requester's score strings) ·
`MEASURED` (computed from bytes, hashes recorded) · `DERIVED` (algebra on the official formulas) ·
`EMPIRICAL-ESTIMATE` (model output with published out-of-sample error) ·
`CATALOGUE-PROXY-DTI` (diagnostic only; anti-correlated with reality at the top end).

## Next steps that would actually move the score

1. Obtain `training_features.tif` through an authenticated DrivenData account and test hypotheses 2–4 with
   the hide-and-recover protocol. Nothing else in this repository can close a 0.15 gap to 0.45.
2. Re-run `scripts/final_audit.py` against the *complete* 655-raster registry (only 96 were measurable here)
   plus any rasters created after the GEMSDOE47 snapshot.
3. Replace the hit-rate assumption in `scripts/mass_balance.py` with a measured holdout hit rate once a
   real label set exists; that is the only way the conditional band becomes an estimate rather than a bound.

