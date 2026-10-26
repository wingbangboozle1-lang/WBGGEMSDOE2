# Three-pass review — 2026-10-26

## Pass 1 — implementation and measured audit

- The checkout was empty except for a one-line README. Restored the pinned public owner mirror of the numerical feature stack, mirrored sample and catalogue using Git blob and full-file hashes; the 419 MB raster remains ignored in `data/`, not in Git. Downloaded and reopened the nine named historical references plus the lattice and two parallel-site files for learning only.
- Reproduced the lattice capacity bound, historical raster lineage, sample/catalogue discrepancy and literal overlap failures in `evidence/registry_audit.json`. No new model, GeoTIFF, holdout score or contest upload was produced after the preflight stop.
- Created the fail-closed dashboard, nine individual site briefs, submission guide, ranked research hypotheses, source register, current-run card, and unchanged shared-template fetcher.

## Pass 2 — bug and edge-case review

- Found and fixed a validator defect: valid-looking finite zeros marked as NoData inside the footprint must fail, as must an incompatible reference CRS or pixel size. A finite numeric NoData value in the reference must be excluded from its footprint.
- Added an explicit incomplete-registry block, strictly inclusive Euclidean radius, constant-rank/empty-support errors, and rejection of candidate/registry masks inside the reference footprint. The H31 diagnostic stops before reading an intentionally missing final file.
- Added stale-on-error public feed behavior and a same-host redirect restriction so a GitHub token is not forwarded to a different host. Checked changed site refs without pretending new commits had been re-audited.
- Viewed the dashboard in headless Chromium at desktop and mobile widths. The table has nine rows, mobile body width matches the viewport, all three main pages open, and no browser script errors were observed. Added a mobile table-scroll cue.

## Pass 3 — request and evidence consistency

- Every historic row carries a pinned file, owner/user-claim label, unknown leaderboard estimate, literal uniqueness result and a do-not-submit decision; each has its own brief. Exact source hashes and directions are in the JSON audit. Static website data generation fails if its core numerical findings change without a narrative review.
- Verified local source/anchor links, null run-card fields, note length, lack of an approved download, score/receipt wording, and the preserved original prompt in the README. The public snapshot is not a per-file receipt. New input provenance, the authoritative template, full registry and private truth remain unresolved.
- Final local checks: 21 project unit/integration tests, 8 unchanged upstream shared-evaluator tests, Python compilation, JavaScript syntax, `git diff --check`, the real-raster audit and browser smoke checks. The local scientific HOLDOUT-DTI and canaries remain **not run**, not zero.
