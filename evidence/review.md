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

## Final integrated checks

After both parallel artifacts and the leaderboard-fragment work were integrated: 84 project tests and 8 unchanged pinned shared-evaluator tests passed; Python compilation and both JavaScript syntax checks passed. Headless Chromium loaded both dashboards and 17 mobile pages at 390 px without overflow or browser errors. All three static run-card copies were rebuilt. These checks establish the described local evidence, not scientific promotion or organizer acceptance.

---

# Three-pass review — 2026-10-27 (`WBG2-MSPTCD` campaign & updated fleet audit)

## Pass 1 — implementation and zero-leakage experiment execution

- Addressed previous-session next steps first: verified the live DrivenData public leaderboard (`0.4544` by `xiaofanhu` on 2026-10-27 UTC), updated the fleet ledger (`docs/data/user-reported-ledger.csv`, 144 rows including 17 new 2026-10-26/27 entries across `GEMSDOE28/33/36/91/92` and `KANLER/EUG/WBG/GINNY`), and empirically audited all 19 cached GeoDAWN bands—discovering from raw pixel quantiles (`q01=7.637, median=18.490, q99=29.020`, `0` negative cells) that Band 6 (`tc`) is positive airborne gamma-ray total counts rather than a `[-\pi/2, \pi/2]` magnetic tilt angle.
- Formulated and ranked 5 physical hypotheses (`research/hypotheses.md`), implemented 12 label-free geophysical operators in `src/wbggems/msptcd.py`, ran 124 fold-local single-feature leakage canaries (`31` features × `4` buffered spatial folds, max two-sided ROC-AUC `0.6131 <= 0.90`), and executed 3 preregistered zero-leakage experiments (`EXP-1`, `EXP-2`, `EXP-3` vs `CTRL-19B`) on the unmodified shared `gems57.evaluate_holdout` (`gems57-pooled-hide-v2`, `60,988` withheld positives, `8.0 km` buffer, 1,000 paired 20 km cluster bootstrap draws).
- `EXP-1` improved pooled `HOLDOUT-DTI` from `0.023409` (`CTRL-19B`) to `0.034975` (`+49.4%`, paired 95% CI `[+0.005424, +0.018644]`, winning all 4 quadrants), and `EXP-3` (`greedy_allocate`) reached `0.042554` (`+81.8%`, paired 95% CI `[+0.010977, +0.028755]`) plus `0.030799` vs `0.016915` (`+82.1%`) on detached splays (`>= 400 m` from visible faults).
- Emitted the cross-fitted research GeoTIFF + ZIP (`docs/downloads/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.{tif,zip}`, SHA-256 `fb11891a3a2e6c9400daa7c19f34bbb149f1ef853b3578f457c0efd1cec53614`) via unmodified `gems57.submission_writer`, verified `64.45%–68.06% <= 70%` novelty against all 9 priority focus champions, and stopped fail-closed (`verdict="negative"`, `ok_to_submit=false`, `0` slots used) due to literal all-registry witnesses (`13GEMSDOE` lattice `100.00%`, `17GEMSDOE`/`WBGGEMSDOE1` continuous priors `100.00%`, `GEMSDOE27_H31` `78.34%`).

## Pass 2 — bug, boundary, CI, and edge-case fixes

- Fixed three edge cases in `src/wbggems/msptcd.py`: replaced `h - 1.001` boundary clamping in `_bilinear_sample` with exact `[0, h-1]` / `min(floor, h-2)` bilinear indexing (eliminating `0.001` px bias on bottom-row footprint pixels and rejecting `<2x2` grids cleanly), avoided `[::16]` decimation on small footprints (`<= 65,536` cells) in `_robust_scale`, and added explicit shape and required-band validation (`ValueError` on missing bands, mismatched shapes, or constant zero-variance inputs).
- Rebuilt `.cache/msptcd_features/` from scratch and re-ran the full campaign end-to-end to confirm deterministic bit-identical GeoTIFF/ZIP SHA-256 hashes and receipts.
- Fixed the shared-template pytest command in `README.md` (`data/shared_template/tests/test_evaluate_holdout.py`), updated `docs/executive-summary/index.html` with the `0.0725` user-reported post-upload outcome of the rejected parallel `stepxasym` file, and simulated the `.github/workflows/pages.yml` build in an isolated `/usr/bin/python3` stdlib-only copy without `.venv`, `.cache/`, or `/data/`.

## Pass 3 — line-by-line verification against original request

- Re-checked every requirement in the prompt and `AGENTS.md`: 9 priority focus sites + 2026-10-26/27 sibling updates audited with clear downloadable links and `DO NOT SUBMIT` vs research-only status; `GEMSDOE32` `0.2778` mathematical lineage explained; 5 ranked hypotheses documented with official verified links; single-lane 3-experiment budget honored (`306.3 s <= 2 h`, `0` slots used); automated `[0, 1]` and interior-mask byte validation verified; canonical `run_card.json` synced identically across all 4 locations; full test suite (`89` repo tests + `8` upstream shared-evaluator tests = `97` passed), link checks, `git diff --check`, and snapshot size check verified before opening and merging the PR onto `main`.
