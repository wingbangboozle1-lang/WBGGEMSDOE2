# Three-pass review — 2026-10-26

## Pass 1 — implementation and measured audit

- The checkout was empty except for a one-line README. Restored the pinned public owner mirror of the numerical feature stack, mirrored sample and catalogue using Git blob and full-file hashes; the 419 MB raster remains ignored in `data/`, not in Git. Downloaded and reopened the nine named historical references plus the lattice and two parallel-site files for learning only.
- Reproduced the lattice capacity bound, historical raster lineage, sample/catalogue discrepancy and literal overlap failures in `evidence/registry_audit.json`. This review lane produced no model, GeoTIFF, holdout score or contest upload after the preflight stop.
- Created the fail-closed dashboard, nine individual site briefs, submission guide, ranked research hypotheses, source register, current-run card, and unchanged shared-template fetcher.

## Pass 2 — bug and edge-case review

- Found and fixed a defect in our independent validator: valid-looking finite zeros marked as NoData inside the footprint must fail, as must an incompatible reference CRS or pixel size. A finite numeric NoData value in the reference must be excluded from its footprint.
- Added an explicit incomplete-registry block, strictly inclusive Euclidean radius, constant-rank/empty-support errors, and rejection of candidate/registry masks inside the reference footprint. The H31 diagnostic stops before reading an intentionally missing final file.
- Added stale-on-error public feed behavior and a same-host redirect restriction so a GitHub token is not forwarded to a different host. Checked changed site refs without pretending new commits had been re-audited.
- Viewed the dashboard in headless Chromium at desktop and mobile widths. The table has nine rows, mobile body width matches the viewport, all main pages open, and no browser script errors were observed. Added a mobile table-scroll cue; a later long-hash overflow on the individual briefs was found and fixed.

## Pass 3 — request and evidence consistency

- Every historic row carries a pinned file, owner/user-claim label, unknown leaderboard estimate, literal uniqueness result and a do-not-submit decision; each has its own brief. Exact source hashes and directions are in the JSON audit. Static website data generation fails if its core numerical findings change without a narrative review.
- Verified local source/anchor links, null run-card fields, note length, lack of an approved download, score/receipt wording, and the preserved original prompt in the README. The public snapshot is not a per-file receipt. New input provenance, the authoritative template, full registry and private truth remain unresolved.
- After reconciling the concurrent dashboards, local checks: the combined project/unit/integration tests plus 8 unchanged upstream shared-evaluator tests, Python compilation, JavaScript syntax, `git diff --check`, the real-raster audit and browser smoke checks. The local scientific HOLDOUT-DTI and canaries remain **not run**, not zero.

## Concurrent integration review

- Preserved the concurrently merged `docs/` evidence, charter, tests and dashboard while adding fieldnotes and nine individually linked site briefs. Both site trees now publish exact copies of the same canonical negative run card. The independent second audit agrees on the lattice bound and confirmed the fully positive registered 17GEMSDOE continuous prior; its policy interpretation is explicit.
- Rebuilt the unchanged shared label-free cache for all 19 raw bands. Official descriptions identify the depth layer as a conductive base, while the owner mirror says basement; the scientific narrative now notes the disagreement rather than assuming equivalence.
- Found a second issue in the pinned shared format gate: finite zeros marked NoData inside the footprint can pass. An additive check now rejects that case and a fixture reproduces the upstream gap; the shared implementation is unchanged and still needs an upstream fix. The shared metric documentation's false `delta_T <= k` bound is also documented for upstream correction.
- The merged dashboards and all nine briefs were checked in Chromium at 390 px. Both main overview tables show nine rows; no local page overflows or script errors were observed after the fix.

## Concurrent experimental TIFF recheck

A later merged parallel session reported three experiments and generated one TIFF. Reopened the exact SHA-256-pinned TIFF and independently measured 99.3838% overlap with the binary lattice, and 100% against the continuous prior under the shared finite-positive support definition. The TIFF uses `nodata=0` and masks 5,132,809 of 5,167,373 in-footprint cells. The shared gate by itself returned `ok=true`; the additional read-back correctly rejected it. The original nine-file-only overlap test does not satisfy the any-registry instruction, and the pre-placement surface was not replayed. The reported holdout and interval remain unreplicated and use a private evaluator with only fold-0 canaries. No organizer receipt was found.

Preserved the other session's original code and claims as explicitly superseded research archives, disabled its failing partial gate/private writer/generator to prevent an accidental rerun, and made both dashboards and the previously published executive path say **DO NOT SUBMIT**. The TIFF is retained only as a clearly marked research reference. This review lane did not use a weekly slot.

## Corroborating concurrent audit and public-feed fix

A second independent merged audit computed the same 34,351/34,564 binary-lattice overlap, 100% literal continuous-prior overlap and 5,132,809 masked footprint cells. Its receipt is retained alongside this review. Its public-feed fix identifies DrivenData's same-origin HTMX leaderboard fragment and supports the fragment's implicit table header; both dashboard feeds now use that parser, and any network or parsing failure remains visibly stale.

## Separate parallel conduit artifact

The later parallel conduit candidate has SHA-256 `95458ad456a01733d1e95e537557bd410b82543985cb22b9174429cffc2fa9ad`. Its ≥0.5 threshold selects 5,094,374 cells; 5,087,882 (99.8725653%) are within three pixels of the registered lattice. Both it and its ZIP were byte-checked. The format-only check passed against the mirror, but the original 58-file audit omitted both key witnesses. No holdout or organizer receipt exists. The generator uses synthetic geometric trends/noise, not the named features, and the private evaluator did not implement required buffered, pixel-exact pooled scoring. Original records are archived and unsafe entry points disabled. This review performed no additional experiment.
