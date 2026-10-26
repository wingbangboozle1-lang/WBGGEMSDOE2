# WBGGEMSDOE2

GEMS Prize Challenge (DOE / DrivenData competition #306) — reproducible fault-discovery submission pipeline.

**Branch:** `arena/3dc38570-wbggemsdoe2` (fixed by Arena; all work, commits, pushes and PRs go here only)
**Live leaderboard (2026-10-26):** #1 0.4437 DW-Tversky — https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

## Project purpose

Generate a **unique TIF submission** for the GEMS Prize Challenge that can place at the top of the leaderboard, with an executive summary that makes it obvious which file to download and whether it is OK to submit. No copying of previous submissions; every number is labeled HOLDout-DTI (evaluator version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (submission-page receipt). A projection is never written as a score.

## Core values

- **Maximize P(Win)** — every decision weighs tradeoffs and risk to maximize the probability of winning.
- **Own the Outcome** — end-to-end results; problems are acted on without waiting for permission.

## Parallel-run protocol (binding)

1. **LANE** — if a raster's rank-correlation with any registry raster exceeds 0.90, or >70% of dots fall within 3 px of one registry raster's dots: log as duplicate and stop. Check on surface AND on final dots.
2. **REUSE, DON'T REBUILD** — cached feature stack, `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover: withhold whole fault segments with buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel).
3. **LABEL EVERY NUMBER** as HOLDout-DTI or ORGANIZER-CONFIRMED. A projection is never written as a score.
4. **LEAKAGE CANARY** — AUC above 0.90 on a feature alone means leakage until proven otherwise.
5. **RUN CARD** — one JSON card: hypothesis; mechanism; named non-fault mimic; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name + note <=140 chars; verdict promote/negative. Negative results are deliverables.
6. **BUDGET** — stop after 3 experiments or 2 hours.

## Focus sites (highest submissions)

GEMSDOE24 (0.2477), GEMSDOE25 (0.2600), GEMSDOE27 (0.2449), GEMSDOE28 (0.2710), GEMSDOE30 (0.2600), GEMSDOE31 (0.2708), GEMSDOE32 (0.2778 <- best of the set), GEMSDOE33 (0.2632), GEMSDOE36 (0.2750). All owner-reported; all flagged duplicate-family by the source sites.

## Generated submission (this build)

`downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif`
- Format validator: PASS (EPSG:32611, 3730x3292, 100 m, float32, [0,1], no NaN, zeros outside footprint)
- Lane uniqueness vs 58-raster registry: PASS (max |rho| = 0.0021; max 3-px overlap 21.72%)
- Holdout-DTI: BLOCKED — `labels.tif` requires DrivenData login (see `scripts/download_competition_data.sh`)
- Verdict: **negative — DO NOT SUBMIT** until holdout-DTI beats repo best
- SHA-256: `95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad`
- Run card: `reports/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros_run_card.json`

## Full task prompt (operating document — read at the start of every session)

The following is the full prompt for this project. It is the authoritative statement of what is being built.

***

## Core Values

Maximize P(Win)
"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Focus
The highest scoring submissions from these sites: GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36. An executive summary on every site, clear and obvious which is the best submission to submit to obtain a high score on the leaderboard. Unique — not an exact duplicate of any previous submission. Iterate and test until we have the highest scoring submission to download and submit.

We should be able to estimate the score for a submission. The executive summary contains a table listing: what file to download, what the estimate score is, and whether it is a unique submission unlike any of the other GEMSDOE sites.

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. WE MUST GENERATE A UNIQUE TIF SUBMISSION. It must be obvious whether it is OK to download and submit the generated TIF submission. Easy-to-download submission TIF as described by the prompt. Inspection must be done through the project and validated for submission without human intervention.

Parallel-run protocol: LANE / REUSE / LABEL / LEAKAGE CANARY / RUN CARD / BUDGET (as above).

Best result to study: https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html — h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778. Why and how did it get the highest score, can we generate a submission scoring higher than 0.2778? Answer at PhD level, then generate a unique TIF submission, unique unlike any within the GEMSDOE sites. Verify line by line, no hallucinations.

Current competition leaderboard GEMSDOE high score: 0.4413 (site text) / live leaderboard now shows 0.4437 (#1 xiaofanhu).

Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
GEMS_96647.pdf: https://docs.nlr.gov/docs/fy26osti/96647.pdf
Submission page error to avoid: "Predicted values must be in range [0, 1]"
Submission needs: unique name + note (<=140 chars, e.g. clustering with k=25). Single-band GeoTIFF (.tif) or .zip containing a single GeoTIFF, matching CRS/shape/geotransform.

Three to five candidate geological hypotheses not yet tried: layers involved, physical signature, why it catches faults missing from USGS/INGENIOUS catalogue, how it differs from repo implementations; ranked by expected DTI improvement and implementation cost. Validate top candidate on the spatially-blocked holdout before touching a weekly submission slot. If a candidate needs new external data, name the specific free official source and check obtainability.

Work line by line verifying from official verified trusted sources; provide links for manual review; no manual input; flag irregularities; no hallucinations.

Goal: full list following requirements; no hallucinations; verify line by line.

Design a new strategy, research, testing, analyzing, generation system scoring higher than 0.3195; unique, contrarian but smart; deep research into scientific discovery of geothermal vents; store knowledge from official verified sources; find data sources others overlook.

Put this prompt into the repo README and read it every time we work on the project.

Submission page: New submission — File to submit (single-band GeoTIFF .tif or .zip), Note (optional, <=140 chars). Error seen: "Predicted values must be in range [0, 1]". Need unique name and short comment.

Executive summary subpage explaining exactly how to make a submission into the contest.

Goal: place top of the leaderboard. Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
Overview/description: page/967/ ; about page/968/ ; data page (login required): /data/ ; reference solution github.com/drivendataorg/gems-prize-reference-solution.
Download competition data into data/ (requires DrivenData login — verified redirect to login; no credentials available in this environment).
Public mirrors referenced by the competition documentation: GEMS_96647.pdf (dropbox), example_submission.tif (dropbox), existing_faults.tif (dropbox), gems-geodawn-numerical-features.tif (dropbox), DEM-links JSON.pdf (dropbox).
Additional official sources: gdr.openei.org/submissions/1391 ; USGS GeoDAWN ; GBCGE INGENIOUS ; epsg.io/32611 ; Tversky index wikipedia.

Site creation: GitHub Page for this repo — clean UI, user friendly, simple, organized, all relevant information easy to read with official verified links.

The single remaining blocker to training: run `bash scripts/download_competition_data.sh` on any unrestricted machine into data/, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready (GPU needed for training; metric/losses/validation verified working here on CPU).

Repo layout

- `scripts/download_competition_data.sh` — data sources and staging notes (DrivenData login required; public dropbox mirrors documented)
- `scripts/prepare_data.py` — verify staged data matches the competition grid (EPSG:32611, 3730x3292, 100 m)
- `scripts/evaluate_holdout.py` — DW-Tversky metric (self-tested against hand-computed cases), hide/recover holdout, block-bootstrap 95% CI, leakage canary
- `scripts/submission_writer.py` — strict format validator + GeoTIFF writer (re-reads saved bytes)
- `scripts/make_submission.py` — generates the unique H1 submission, validates, audits lane uniqueness vs registry, writes run card + audit JSON
- `hypotheses.md` — 3–5 candidate hypotheses ranked by expected DTI gain/cost
- `downloads/` — generated TIF + .zip (the downloadable submission)
- `reports/` — run card + uniqueness audit JSON
- `docs/` — GitHub Pages site (`index.html`) and `executive-summary.md`

Limitations

- No DrivenData credentials in this environment -> `training_features.tif`, `labels.tif`, `sample_submission.tif` cannot be staged; holdout scoring and leakage canary blocked until data is placed in `data/`.
- Public leaderboard != private round-1 test set.
- GPU required for reference U-Net training; metric/loss/validation code is CPU-verified here.
- Weekly submission cap applies; promotion to a slot is a separate selector step.
