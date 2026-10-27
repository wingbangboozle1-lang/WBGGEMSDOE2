# Release reconciliation — 27 October 2026

> **Historical concurrent review:** this record describes a separate review that merged into main. Its marker-patch shortlist was later superseded by the current [ranked proposals](hypotheses.md); the current five-file release triage and status are in [the present review](../evidence/review.md). No approval is implied.

## Outcome

**Negative; no new TIFF, experiment, or weekly slot.** The priority was continuing prior-session work:
reconcile contradictory approvals, reopen the exact files, and repair automated publication so a
failed duplicate cannot become a green submission button. The user's required single method paragraph
still does not assign a lane; this review does not invent one.

## Pass 1 — evidence and implementation

- Re-fetched and hash-verified the nine historical focus rasters plus binary/continuous witnesses and two
  additional historical files. [New byte audit](../evidence/registry_recheck_20261027.json) confirms B2's
  pruning lineage. These are pinned historical bytes, not the latest best result of each site.
- Reopened DZ-16 and H3-PACK, verified their SHA-256s, compared grid, range and masks against the owner
  mirror, and measured lattice overlap: **99.9797% / 99.8618% — REGISTRY-MEASUREMENTS**. The 70% stop
  fails both. A byte hash or nine-site-only pass cannot establish full-registry uniqueness.
- Withdrew their approvals in current JSON, README, download notices and generated pages. Kept original
  reports in `evidence/release_archive/` as explicitly historical `.txt` records. Replaced both obsolete
  page builders with the same fail-closed renderer; retired already-rejected generator entrypoints.
- Restored the 418,912,844-byte owner-mirrored feature TIFF and 19 raw cached bands through the pinned
  shared preparation script. Hash `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`.
  This completes accessible mirror placement, not organizer authentication or the derived feature bank.
  [Restoration receipt](../evidence/data_preparation.json). No label-derived full-catalogue cache was used.
- Refreshed nine GitHub head observations; all differ from their audited pins. This is a freshness warning,
  not a new complete-raster registry. The old index cannot prove global uniqueness.

## Pass 2 — defects and scientific assumptions

- Found the former novelty test explicitly ignored literal failures in favor of normalized enrichment;
  disabled that approval path. Smoothed Pearson is not the required surface Spearman. Final-only
  measurements cannot be retrospectively labeled pre-placement checks.
- Found a tautological nearest-dot test: `maximum_filter(support) * support` necessarily includes each
  dot itself. Replaced it with the nearest **other** point distance using `cKDTree`.
- Found prior H1/H2 proposals already implemented in `src/wbggems/msptcd.py`. Replaced them with
  paired marker-patch registration and competing gravity forward-model/null tests. Retained untested
  drainage-deflection and flight-line repeatability ideas, explicitly blocked on external binary access.
  [Four ranked hypotheses](hypotheses.md) include layers, signatures, confounders and cost. These are
  research proposals, not literature-established predictors or verified fleet-wide novelties.
- Corrected the claim that hidden organizer truth is required for a holdout: visible-catalogue segments
  can be withheld for a legitimate proxy. But full-visible-catalogue agreement is not hide-and-recover.
- Restored shared code unmodified. Retried filing the existing mask-validation defect upstream;
  GitHub returned `Resource not accessible by integration (createIssue)`. No upstream issue or fix was
  created. The [reproducer](shared-template-format-report.md) and independent supplemental rejection
  remain. This is a repository-permission limitation, not a request for credentials.
- Reviewed the [official reference repository at a pinned revision](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b).
  Its README supports CPU-only training. The notebook uses an ordinary Tversky training loss with
  alpha 0.2 and beta 0.8; that alone does not verify the competition's distance-weighted metric.
  [Source hashes and scope](../evidence/official_repository_recheck_20261027.json).
- Historical MSPTCD results remain source-reported, not newly replicated. Passing feature-alone canaries
  does not prove zero leakage; banners now say so. No old result is a new session's HOLDOUT-DTI.
- The exact rejected upload is absent. Local diagnostics cannot establish which portal check failed;
  H3-PACK's `zeros` filename actually encodes NaN outside the footprint. No encoding was silently changed.

## Pass 3 — full-request checks

The final test and browser results are recorded below after verification. The revised builders run in
scheduled Pages and before CI tests. Existing artifact hashes are checked before release-review rendering;
changing approval booleans, a hash or witness failure stops publication. No automatic score projection or
submission selection is introduced.

### Remaining blockers, not solved claims

- Explicit lane assignment and resolution of continuous-support interpretation; binary witness failures
  still apply regardless of that interpretation. Do not move dots to footprint edges just to pass.
- Complete current registry, including newer parallel runs; exact official sample authentication;
  shared derived feature cache; upstream masked-footprint fix.
- A compliant whole-segment buffered hide-and-recover experiment, all-fold feature canaries and a
  same-fold incumbent comparison before any release. The new top proposal has **no HOLDOUT-DTI**, no
  positives count, no CI and no leaderboard estimate. This is a blocked review, not a measured negative
  model score.
- DrivenData, Dropbox, USGS, GDR and rules-PDF hosts are outside this sandbox's allowed outbound hosts.
  No renewed official-page/literature verification, live quota, receipt or external dataset availability
  is claimed. All external-source URLs are offered for traceability, not as proof they were opened here.
- The leaderboard values in the prompt conflict. The previously recorded public observation is stale,
  not a current verified leader or a file-specific organizer receipt.

The full original prompt is retained in README. Maximize P(Win) means saving slots when the evidence
fails; Own the Outcome means correcting the false green button, not manufacturing a new raster.

### Final verification results

- **173 automated tests passed** locally after restoration; no tests skipped. Rasterio emitted 34
  upstream affine-operation deprecation warnings, not failures.
- **60 browser page checks passed**: 30 routes at 1440×960 and 390×844, including all nine new
  per-site executive pages, both dashboard families, release summary and submission guide. Fixed
  mobile banner overflow found on the first browser pass. No HTTP/JavaScript errors or horizontal
  page overflow remained. [UI check record](../evidence/release_ui_checks_20261027.json).
- The browser initially lacked `libnspr4`/NSS; extracted the bundled Chromium libraries into ignored
  scratch storage and reran successfully. No browser binaries or large restored data are committed.
- `git diff --check` passed. CI rebuilds the site before running regression tests. Archived original
  approvals are labeled historical; no current card authorizes a file.

### Concurrent merge reconciliation

PR #21 merged a related fail-closed UI fix while this review was running. Merged `origin/main`
into this session branch without switching branches. Preserved its no-download section and tests;
updated the tests' URL expectations for the newly hash-bound negative release page. Rebuilt all
conflicted generated HTML rather than retaining conflict markers or an obsolete approval renderer.
