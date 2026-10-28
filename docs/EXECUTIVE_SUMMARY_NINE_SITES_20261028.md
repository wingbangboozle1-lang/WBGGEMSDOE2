# Executive summary — GEMSDOE nine-site review and the one TIF file (2026-10-28)

> **Verdict in one line:** Do **not** spend a weekly slot on any file in this repository as a leaderboard attempt. Four files pass the format gate and the nine-site uniqueness check. The best measured proxy among them is the **distal2 TIF** (`wbg2-distal2-…-zeros.tif`). You may download it for the record, but **nothing here shows it can beat the 0.2778 reference, and it is not a leaderboard pick.**

Labels used below: **ORGANIZER-CONFIRMED** = copied from an official submission-page receipt (none exists for any file here) · **USER-REPORTED** = score supplied in the request, no receipt · **HOLDOUT-DTI** = local proxy (evaluator and count given) · **PROJECTION** = model output, never a score · **MEASURED** = re-computed this session from bytes.

---

## 1. Download box

| Item | Value |
|---|---|
| **File to download** | [`downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif`](downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif) (zip: [`…-zeros.zip`](downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.zip)) |
| **SHA-256** | `0ebf5e2d717361af83f507bb2f64ba7bc9d7266de73907e4c4769574d0a56b10` (134,932 bytes) — MEASURED; matches `config/release_register.json` |
| **Format gate** | **PASS** — repo validator `ok: true`; 0 NaN; values in [0, 1]; EPSG:32611; 3730 × 3292; 38,000 positive cells |
| **Unique vs the nine sites** | **PASS** — worst share of its dots within 3 px of any one site: **63.7 %** (limit 70 %); worst smoothed rank correlation **0.42** (limit 0.90). MEASURED, `evidence/nine_site_recheck_20261028.json` |
| **Best proxy in the repo** | HOLDOUT-DTI **0.1771 [0.1570, 0.1983]**, 60,988 withheld positives, `gems57-pooled-hide-v2`, folds regenerated per fold (its run card). **Caveat:** fixed-raster on the same folds gives 0.0289, and the proxy is unvalidated against the leaderboard (§5). |
| **Submit?** | **NO — hold.** Its own run card says `ok_to_submit: False`; the literal all-registry stop is unresolved; no organizer receipt exists. See §3 and §5. |
| **Do not use (both triphysics variants)** | Lowest measured proxy (0.0121 fixed-raster; 0.0086 in its run card). The NaN-outside file also **fails** the repo gate (7,111,787 NaN pixels); the README's earlier "PASS" was wrong. |

---

## 2. Nine focus sites — best file per site

Every site's best file is a near-copy of the others. Each site shares **at least 86.7 %** of its dots within 3 px of another site's dots, so **none of the nine is unique relative to the others.** MEASURED, `evidence/nine_site_recheck_20261028.json` (sha256 of each re-fetched file matched `registry/focus_sites.json`).

| Site | Best file (highest reported) | Reported score | Evidence | SHA-256 (prefix) verified | Unique vs other eight? | Max share of its dots in another site's 3-px halo |
|---|---|---|---|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif` | 0.2477 | USER-REPORTED | `68d0e2e4` ✔ | **NO** | 1.00 (GEMSDOE25) |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-…-nan.tif` | 0.2600 | USER-REPORTED | `91eae1ca` ✔ | **NO** | 1.00 (GEMSDOE24) |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-…-nan.tif` | 0.2449 | USER-REPORTED | `33003374` ✔ | **NO** | 0.980 (GEMSDOE24) |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-…-nan.tif` | **0.2710** | USER-REPORTED | `5556aa14` ✔ | **NO** | 1.00 (GEMSDOE24) |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-…tif` | 0.2600 | USER-REPORTED | `8cf893ea` ✔ | **NO** | 1.00 (GEMSDOE24) |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-…-nan.tif` | 0.2708 | USER-REPORTED | `07b6db44` ✔ | **NO** | 1.00 (GEMSDOE24) |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-…-zeros.tif` | **0.2778 (highest)** | USER-REPORTED | `c55bafc4` ✔ | **NO** | 1.00 (GEMSDOE24) |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-…tif` | 0.2632 | USER-REPORTED | `87f857d5` ✔ | **NO** | 0.997 (GEMSDOE27) |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` | 0.2750 | USER-REPORTED | `e1589102` ✔ | **NO** | 0.976 (GEMSDOE27) |

Download the exact files from each repo's `registry/focus_sites.json` `download_url`. The "reported" scores are **not** organizer receipts; no team name on the public leaderboard is linked to these repositories.

---

## 3. Candidate files in this repo — estimate and verdict

| File (repo path) | Downloadable | Format gate | Unique vs nine sites | Holdout evidence (label, count, CI) | Estimate | Submit? |
|---|---|---|---|---|---|---|
| triphysics — zero-outside `submissions/…-b7c1e4a2-zerooutside.tif` | Yes, not recommended (lowest proxy) | **PASS** | **PASS** (23.5 %, ρ 0.21) | HOLDOUT-DTI 0.0121 [0.0101, 0.0140], 60,988 withheld, `gems57-pooled-hide-v2`, fixed raster (this session) | **None supported** (see §5) | **NO — hold** |
| triphysics — NaN-outside `submissions/…-b7c1e4a2.tif` | Do not use | **FAIL** (7.1 M NaN) | PASS (same dots) | Same dots as above | None | **NO** |
| **distal2 — download pick** `docs/downloads/distal_exp2/…-062373ad-zeros.tif` | **Yes (pick)** | PASS | PASS (63.7 %, ρ 0.42) | HOLDOUT-DTI **0.1771 [0.1570, 0.1983]**, 60,988, `gems57-pooled-hide-v2`, **per-fold regenerated** (its run card). Fixed-raster on the same folds: 0.0289 [0.0247, 0.0332] | PROJECTION **0.1497** (fleet regression, LOSO R² 0.21, n = 93) | **NO — policy hold** (its run card: `ok_to_submit: False`; literal stop unresolved) |
| wbg4 EDTI `artifacts/wbg4/…-9f5dbc9b-zeros.tif` | Yes | PASS | PASS (46.8 %, ρ 0.39) | HOLDOUT-DTI 0.1171 (mean of 2 folds), evaluator `wbg4-edti-v1` — **not comparable** | None | **NO** |
| wbg4 SSCC `docs/downloads/wbg4-sscc-blind-66383dots-…tif` | Yes | PASS | PASS (64.1 %, ρ 0.25) | HOLDOUT-DTI 0.1086 [0.0783, 0.1301], 60,980, `wbg4-hide-recover-v1` — **not comparable** | None | **NO** |

Reading the table: the **distal2** row is the best proxy number the repo holds. Its holdout is a regenerated, per-fold protocol; the 0.2778 reference was only evaluated fixed-raster, so the two rows are **not on the same protocol** and cannot be ranked against each other.

Reference points (label **USER-REPORTED**, not receipts): GEMSDOE32 **0.2778**. Local proxy on the **same** shared evaluator and folds, fixed raster: **0.0067 [0.0060, 0.0074]**; uniform random dots at the same budget: **0.0686 / 0.0692 / 0.0694** (seeds 1–3). MEASURED, `evidence/fixed_raster_holdout_20261028.json`.

---

## 4. Why did GEMSDOE32 (0.2778) score highest? (PhD-level reading, labelled)

1. **It is the pruned member of one family.** Its 37,654 dots are the 44,090-dot "D2.8" mask with the dots within 2 px of the mapped catalogue removed (repo lineage note, `evidence/retired_20261027/why-b2-scored-2778.md.txt`). I re-measured that it has **0.000** of its dots within 2 px of the catalogue. Every other site's dots are ≥ 86.7 % inside another site's halo, so the nine scores differ by **budget and pruning, not by method.**
2. **Mapped-fault pixels are not penalised.** DrivenData staff state that known USGS/INGENIOUS fault pixels are masked from evaluation and do not count toward penalty terms ([community reply, "Sep 16"](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)). Dots on mapped faults therefore earn nothing and cost nothing; removing them frees budget for unmapped-fault candidates. **This is an inference from the official rule, not a confirmed cause.**
3. **Metric arithmetic.** DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w), with a 300 m triangular kernel ([official metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). The repo's inversion (USER-REPORTED scores, F = mass assumed) implies about 12,783 scored truth pixels and about 41 % weighted coverage at 0.2778 ([`data_public/gemsdoe_metric_model.json`](../data_public/gemsdoe_metric_model.json)). **PROJECTION-level; the assumption F = mass is conservative and unverified.**

## 5. Can we beat 0.2778? — honest answer: **not demonstrated.**

- The only local tool that uses the official formula and the shared fold code ranks GEMSDOE32 **below random dots** (0.0067 vs 0.069). That is because it scores withheld **mapped** faults, which the official metric masks, so **the local holdout measures the wrong target for this family.** HOLDOUT-DTI, MEASURED.
- The triphysics "0.15–0.28" band has no derivation in the repo. Its run card's only target is a footprint-reach envelope of 0.15–0.17 (fraction of the footprint within 3 px), which is not truth coverage. **Projection withdrawn.**
- The distal2 fleet regression (0.1497) has leave-one-site-out R² = 0.21 on 93 USER-REPORTED points. That is too weak to support a leaderboard claim.
- **Context:** the public leaderboard, fetched today, shows **#1 = 0.4544**, #2 = 0.3916, #22 = 0.3261, and #48 = 0.2895 — so 0.2778 sits below the top 48 ([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)). Beating 0.2778 would not reach the top; the gap to #1 is 0.18.

## 6. Official rules checked (verified 2026-10-28)

- **Metric & format:** distance-weighted Tversky, α = 0.2, β = 0.8, R = 300 m; submission is float32, single band, EPSG:32611, 100 m; values in [0, 1]; "data outside the bounds is null or nan." ([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))
- **Scored truth:** the public and private test sets are new faults not in the USGS database; the final round re-scores on an expanded label set. ([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))
- **Known faults masked:** see §4 item 2 ([community reply](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)).
- **NaN vs zero outside:** the official text permits NaN outside bounds. This repo's stricter all-finite gate rejects NaN, so the zero-outside file is the safer download. Both pass the official range rule.

## 7. Irregularities flagged for review

1. **README "START HERE" said the NaN triphysics file "PASS … ready to upload."** The repo's own validator fails it (`ok: false`). Corrected in README. [`evidence/run_card_nine_site_20261028.json`](../evidence/run_card_nine_site_20261028.json)
2. **`config/release_register.json` still lists both triphysics files as `PROMOTE`.** This conflicts with the validator result and with the holdout evidence. Left unchanged, because AGENTS.md forbids silently regenerating approvals; a reviewer should decide.
3. **The triphysics run card says the 0.2778 file scores 0.0048.** I measured 0.0067 on the same evaluator. Same conclusion, different number. Its own holdout (0.0086, 60,940 truth) uses an **unrecorded** evaluator, so it is not reproducible from the repo.
4. **The 0.15–0.28 triphysics band** has no derivation (§5).
5. **distal2's uniqueness.** The register records max halo 0.6792 against the focus sites; I measured **0.6372** against the nine pinned files. The register's extra "69 sparse peers" can't be re-checked here.
6. **EDTI "pooled" DTI is a mean of two folds** (`mean_dti` in `evidence/wbg4_exp2.json`). Its withheld count (15,816 per the register) also differs from the 60,988 in the file.
7. **Leaderboard top score conflicts across the brief:** the request says 0.4413 (current) and also 0.3195 ("highest right now"). The leaderboard fetched today shows **0.4544** at #1 and 0.3195 at #26. The brief's figures are not reconciled.
8. **Test failure:** `tests/test_release_safety.py::test_retired_entry_points_stop_before_writing[run_wbg2_dphs.py]`. The retired script still crashes with `ModuleNotFoundError` instead of printing `STOP`. I did **not** convert it to a stub, because `scripts/run_wbg2_distal.py`, `scripts/run_wbg2_distal_exp2.py` and `scripts/package_distal_arms.py` import it, and the distal2 pipeline depends on that import.
9. **The PARALLEL-RUN PROTOCOL's "single method paragraph" is a placeholder** (`[0.90]`, `[70%]` unfilled, no method text). Per AGENTS.md this is a lane blocker, so no new candidate was generated under a self-assigned method.
10. **README's "prompt" section is a paraphrase**, not the verbatim brief.
11. **Scores that are not receipts:** all nine site scores are USER-REPORTED. None is ORGANIZER-CONFIRMED.

## 8. What was done this session (2 experiments, within the 3-experiment budget)

- **Experiment 1:** re-fetched the nine pinned focus rasters (sha256 verified), re-ran the uniqueness and rank checks, and built the full 9×9 overlap matrix. Script: [`scripts/recheck_nine_site_20261028.py`](../scripts/recheck_nine_site_20261028.py).
- **Experiment 2:** scored fixed rasters on the shared folds and evaluator, with random-dot controls. Script: [`scripts/fixed_raster_holdout_20261028.py`](../scripts/fixed_raster_holdout_20261028.py).
- **No new TIFF was generated.** The file to download was chosen by measured proxy among existing files, not by any leaderboard evidence. The reason is §5 plus the missing lane. No weekly slot was spent. No submission was made.

## 9. Limitations and what would unblock a real attempt

- No organizer receipt exists for any file. The leaderboard is public-test only; the private round is hidden.
- The local holdout targets mapped faults, which the official metric masks. A valid proxy needs a truth set built from unmapped faults, and no such source is in this repo.
- Obtain a **lane assignment** (one method paragraph) so a single method can be tested under the protocol.
- Get the **literal all-registry duplicate rule** resolved by the requester. Under the repo's own 13GEMSDOE lattice finding, no non-empty file can pass it.
- Repair the `run_wbg2_dphs.py` import dependency before retiring it.

## 10. Sources (manual review)

- Problem & metric (fetched 2026-10-28): https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Leaderboard (fetched 2026-10-28): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Known-fault masking (staff reply, dated "Sep 16" on the forum): https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516
- Data page (login required, not reachable from sandbox): https://www.drivendata.org/competitions/306/competition-doe-gems/data/
- Official reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
- Grid template (owner mirror, SHA-256 pinned): https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d/data/official
- Nine focus rasters (pins): `registry/focus_sites.json`, each repo at its pinned commit.

Evidence files: [`evidence/nine_site_recheck_20261028.json`](../evidence/nine_site_recheck_20261028.json) · [`evidence/fixed_raster_holdout_20261028.json`](../evidence/fixed_raster_holdout_20261028.json) · [`evidence/run_card_nine_site_20261028.json`](../evidence/run_card_nine_site_20261028.json)
