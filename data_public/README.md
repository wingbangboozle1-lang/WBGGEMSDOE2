# Historical data_public snapshot — not current submission authorization

The JSON candidate, audit, estimate, and run-card files in this directory preserve an older DZ-16 research lane. Some records contain `verdict: promote`, `ok_to_submit: true`, or a calibrated-gate PASS. Those fields describe that lane's historical disposition only. They are **not** the current project-level release decision.

The current canonical disposition is [`../evidence/run_card.json`](../evidence/run_card.json): `verdict: negative`, `ok_to_submit: false`, and no candidate raster hash or holdout. The current project also has no complete-registry pass and no separate byte-bound weekly-slot selector record. The historical DZ-16 card records `holdout.status: NOT RUN` and a literal novelty failure; it must not be downloaded or submitted.

The old `scripts/build_site_v2.py` positive download page has been replaced with a fail-closed research archive. Do not use `data_public/candidate.json`, `run_card.json`, or `final_audit.json` as current approval. Preserve their measurements as historical provenance; do not infer current eligibility from them.
