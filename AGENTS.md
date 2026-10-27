# Project working agreement

At the start of a session read `README.md`, `docs/DECISION.md`, `evidence/decision.json`, `evidence/h1_run_card.json`,
`research/findings.md`, and `docs/PROJECT_CHARTER.md`. Treat the preserved original prompt as historical context, not
as evidence or perpetual authorization. Respect the active branch and current higher-priority instructions.

**Current state (2026-10-27):** the decision is **OK TO DOWNLOAD AND SUBMIT** — one genuinely new, unique,
machine-validated TIF (`downloads/wbg2-h1-crossphysics-dualpop-…tif`). The earlier review-lane `DO NOT SUBMIT`
card (`evidence/run_card.json`, verdict `negative`) is preserved as history; the authoritative current decision is
`evidence/decision.json`, byte-bound to the raster, backed by `evidence/decision_validation.json` (43/43 automated
checks) and `evidence/h1_run_card.json`. Re-verify any time with `python scripts/wbg_verify_decision.py`
(exit 0 = OK, exit 1 = DO NOT SUBMIT). Do not flip the decision or the raster without re-running that verifier and
all tests; the site builders are fail-closed on the byte binding.

- **No real competition slot** is spent by a research lane; the actual upload, the single-final-submission choice
  and the weekly cap (up to 3) are a separate selector decision. `weekly_submission_slots_used` stays 0 until a
  human submits. No copies disguised as novel predictions.
- **Duplicate rule, with the resolved policy decision.** Enforce the surface rank-correlation branch (|ρ|≤0.90)
  and the 3 px final-dot overlap branch (≤70%) before placement and on final dots. The two space-filling registry
  controls (a stride-5 lattice and a fully-positive continuous probability prior) are compared by the SURFACE
  correlation branch, not the dot branch, because a literal dot reading of them would reject every candidate —
  including the 0.2778 champion. This is an **explicit, flagged, reviewable policy decision** (`IR-DECISION-01`
  in `decision.json` / `docs/sources.html`), NOT a silent exemption. Do not re-open it without surfacing it again.
  An incomplete registry still cannot prove global uniqueness: say so (only 13 locally-pinned rasters were
  byte-audited).
- **Use the unchanged pinned shared template** (feature cache, `evaluate_holdout.py`, `submission_writer.py`);
  fix shared tools upstream, not in a private fork. Derive catalogue features from **visible faults only** for each
  spatial holdout, and run single-feature leakage canaries (AUC > 0.90 = leakage until proven otherwise).
- **Do not call a leaderboard projection or user claim an organizer receipt.** Label observed leaderboard values,
  HOLDOUT-DTI proxies (evaluator version, withheld positives, 95% CI), and CIs accurately. The candidate's
  leaderboard score is UNKNOWN; never write a projection as a score. Do not silently repair candidate values.
- **Keep data and large generated assets out of Git** (`/data/`, `/.cache/`, `/.venv/`, `*.npy`); document sources,
  rights, hashes, limitations, stale states and negative results. The submission TIF/.zip ARE committed
  (small, byte-bound deliverables) and must stay byte-consistent with `decision.json`.
- **Fail closed if evidence, data access or policy blocks completion**, instead of fabricating a candidate. A green
  "OK TO DOWNLOAD AND SUBMIT" is only legitimate when `wbg_verify_decision.py` passes and the raster is byte-bound.
- Flag irregularities for review; never hallucinate official verification, receipts, data provenance or scores.
