# WBGGEMSDOE2 — DOE GEMS Prize: lane H1 (magnetic/radiometric step × lidar asymmetry)

**READ THIS FIRST, every session.** Core values: **Maximize P(Win)** — every
weekly slot is an experiment, not a lottery ticket. **Own the Outcome** — every
number carries an evidence label; defects in our own work are published, not
quietly dropped.

## Standing orders (from the project prompt, paraphrased without loss)
- Focus sites: GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36. Their best live
  scores are **OWNER-REPORTED** (no organizer receipts): champion is
  GEMSDOE32 `h33-h33-2-b2 … e5eb6e7e-zeros` = **0.2778**. All nine bests are
  one duplicate family (dotted H19-5/H27-4 re-emissions) — never copy or
  resubmit them.
- **Generate a UNIQUE TIF.** Lane rule: if rank-correlation with any registry
  raster > 0.90, or >70% of dots within 3px of one registry raster → duplicate,
  log and stop. Check on the surface before placement AND on final dots.
- Holdout = hide-and-recover: withhold whole fault segments + buffer, derive
  catalogue features only from visible faults, mask visible faults
  pixel-exactly, pooled DTI (α=0.2, β=0.8, 300 m triangular kernel).
- Label every number **HOLDOUT-DTI** (evaluator version, n withheld, CI) or
  **ORGANIZER-CONFIRMED** (receipt copy) — a projection is never a score.
- Leakage canary: any single feature AUC > 0.90 = leakage until proven otherwise.
- Submission TIF must pass the strict validator on saved bytes (single-band,
  CRS/shape/transform match, no NaN in footprint, values in [0,1]) — this fixes
  the reported `Predicted values must be in range [0, 1]` error by construction.
- Budget: ≤3 experiments. End with the JSON run card. Promotion to a real slot
  is a separate selector step. Negative results are deliverables.
- No hallucinations: verify line by line from official sources (links in
  `docs/index.html`), flag irregularities (see executive summary IR-1…IR-5),
  no manual input required to run the pipeline.

## Current state (2026-10-26)
- Lane H1 tested: HOLDOUT-DTI (WBGGEMSDOE2-HIDE-RECOVER-v2.0, 58,016 withheld
  positives, fold-bootstrap 95% CI) — E2 (no catalogue-distance) **0.1321
  [0.129, 0.135]** vs E1 (with it) 0.0227. Canary max AUC 0.593 PASS.
- Unique candidate generated + validator PASS + uniqueness PASS
  (ρ ≤ 0.316, overlap ≤ 41.4%) but **PROJECTION 0.15–0.24 < 0.2778 → verdict
  negative, DO NOT SUBMIT as a champion-beater.** Full table, submit
  instructions and irregularities: `docs/executive-summary/index.html`.
- Leaderboard top is quoted in the brief as both 0.4413 and 0.3195 (IR-1,
  unverified).

## Run it
```bash
bash scripts/download_data.sh            # public sibling repos -> /tmp/wbg_data
pip install numpy scipy rasterio scikit-learn pytest
python -m pytest tests/ -q               # DTI vs brute force
WBG_DATA=/tmp/wbg_data python scripts/run_lane.py          # holdout (3 exps)
WBG_DATA=/tmp/wbg_data python scripts/generate_final.py    # unique TIF
python scripts/validate_submission.py docs/downloads/*.tif /tmp/wbg_data/sample_submission.tif
python scripts/audit_uniqueness.py docs/downloads/*.tif <registry tifs...>
```
Limitations: 4 GB RAM here (band-list pipeline, no full cube); labels/sample
are GEMSDOE24 public bridge copies pending byte-check vs the official
login-gated data page (IR-3); DrivenData auth is unavailable in this sandbox.
