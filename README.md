# WBGGEMSDOE2 — DOE GEMS evidence-first research

> **Read this brief before every project change.** This repository starts from an empty codebase; it does not contain competition rasters, cached features, training labels, evaluator, submission writer, or prior implementation. No model score or TIF can be truthfully claimed from this checkout yet.

## Mission and decision standard

Build an auditable, reproducible system for discovering previously unmapped faults relevant to the DOE GEMS challenge. Optimize for evidence and the probability of winning—not for generating a file at any cost. Own the full outcome: data provenance, spatial validation, duplicate checks, format checks, run cards, and an unambiguous submit / do-not-submit decision. A valid GeoTIFF is not proof of a useful model, uniqueness, leaderboard performance, or portal acceptance.

The operator's priority sites are GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. Historical names and values supplied in the project request are preserved as **unverified owner/page reports**, not organizer receipts or forecasts. Do not copy prior submissions; they may be studied for educational error analysis only. Do not claim uniqueness without comparing the actual raster bytes and spatial supports against a complete, dated registry.

## Non-negotiable run protocol

1. **One lane only.** Do not start a candidate until its permitted method paragraph/lane is explicitly recorded. Check rank-correlation against every registry surface and 3-pixel dot overlap before placement and on the final dots. Stop and record a duplicate if absolute rank-correlation exceeds 0.90 or more than 70% of candidate dots lie within 3 pixels of any one registry raster. Do not evade the gate by renaming, jittering, or re-encoding a duplicate.
2. **Reuse shared tools.** Use the template's cached feature stack, shared `evaluate_holdout.py`, and shared `submission_writer.py`. Hold out whole fault segments with a buffer; derive catalogue features only from visible segments; mask those visible segments pixel-exactly; compute pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular distance kernel. Fix a shared-tool defect in its shared source, not in a private fork. If those tools are absent, stop and report the blocker; do not make substitutes appear equivalent.
3. **Leakage canaries first.** Evaluate each feature alone on the spatial holdout. AUC > 0.90 is leakage until explained and independently cleared.
4. **Evidence labels.** A metric is either `HOLDOUT-DTI` (include evaluator version, number of withheld positives, and 95% CI) or `ORGANIZER-CONFIRMED` (copy from a submission-page receipt). A projection is never a score. Never present an owner-reported value as organizer-confirmed.
5. **Run card.** Every experiment ends with a JSON card: hypothesis; mechanism; named non-fault mimic; HOLDOUT-DTI and CI; correlation/overlap versus registry; raster SHA-256; validator result (no NaN inside footprint, values in [0,1], CRS/shape/transform match); submission name and <=140-character note; verdict `promote` or `negative`. A negative experiment is a deliverable.
6. **Budget and slot discipline.** Stop at three experiments or two hours, whichever comes first. Do not select or spend a weekly competition slot in the experiment lane; promotion is a separate selector action and subject to the live portal cap.
7. **Fail closed.** Do not publish a submission download as approved unless the actual saved TIFF passes the format validator, the registry check is complete, all leakage canaries pass, and the preregistered holdout gate beats the current same-evaluator best. State `OK TO SUBMIT: NO` whenever any gate or required evidence is missing.

## Executive summary — historical focus-site results

The table below transcribes the values in the project request. They are historical page/owner-reported values; this checkout cannot authenticate portal receipts or connect a score to the exact downloaded bytes. **No leaderboard estimate is defensible from this repository.** “Unique” means unique against the other eight actual rasters, not merely a different name; no raster bytes are present here, so uniqueness is not verified. Public sibling pages themselves report clone/alias concerns, including a shared D2.8 / H19-5 lineage. Treat every historical file as research-only and do not re-upload it.

| Site | Highest result reported in request | Reported value (unverified) | File available in this checkout? | Unique vs the other focus sites? | OK to download and submit from this repo? |
|---|---|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 (page-reported) | No | Not verified; lineage overlap reported | **No** |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 (page-reported) | No | Not verified; lineage overlap reported | **No** |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 (page-reported) | No | Not verified | **No** |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 (page-reported) | No | Not verified; related entries appear across sites | **No** |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 (page-reported) | No | Not verified; D2.8 family overlap reported | **No** |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 (page-reported) | No | Not verified; exact/near aliases reported | **No** |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 (page-reported) | No | Not verified; page reports a shared lineage | **No** |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 (page-reported) | No | Not verified; page reports a shared lineage | **No** |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 (page-reported) | No | Not verified; page reports a shared lineage | **No** |

**Best historical reported value in that table:** GEMSDOE32's 0.2778. It is not a current validated best, not an organizer-confirmed score, and not evidence that a distinct new submission can beat it. The prompt separately gives two purported current leaderboard highs, 0.3195 and 0.4413; these conflict and have no dated capture or receipt attached. A read of the official public leaderboard on 2026-10-26 showed a leading entry above both, so both prompt values are stale or otherwise inconsistent. Because this is a page observation rather than a saved submission-page receipt, it is not entered as an `ORGANIZER-CONFIRMED` score in the experiment record. Re-check the linked leaderboard immediately before any selector decision. No candidate or submission TIF is generated in this checkout. No experiment was run: the repository has none of the required inputs, shared evaluator/writer, registry rasters, or declared method lane. The run budget therefore remains unused. The machine-readable blocked/no-experiment decision is recorded in [docs/run-card-current.json](docs/run-card-current.json); it deliberately contains no fabricated HOLDOUT-DTI, uniqueness measurement, or raster hash.

### Why the GEMSDOE32 result may be high — and what is not proven

The challenge's scoring is distance-weighted Tversky, with alpha 0.2 and beta 0.8 and a 300 m (three 100 m pixels) triangular tolerance. That makes near-misses around labelled faults receive partial credit and weights false negatives more heavily than false positives. A dense set of predictions around known/catalogue-adjacent fault traces can therefore score well on a spatial recovery proxy, especially if the evaluation labels include continuations or offsets of those structures. This is a plausible mechanism, **not a verified causal explanation** of the reported 0.2778: the private evaluation labels, exact uploaded bytes, receipt, and same-protocol ablation are not present here. A high historical score is not proof of geothermal discovery or novelty.

## Hypothesis shortlist — proposals only, not experiments

These are distinct test designs against the feature stack described on the official challenge page. Their novelty relative to all sibling repositories is **unverified**; do not describe them as never tried until actual code and rasters from the complete registry have been audited. No scores are projected.

| Rank | Candidate hypothesis and layers | Physical signature / why it could find uncatalogued faults | Main non-fault mimic | Expected DTI improvement (qualitative only) | Cost / evidence needed |
|---:|---|---|---|---|---|
| 1 | **Cross-field edge concordance:** RTP/TMI magnetic horizontal/vertical gradients plus isostatic-gravity gradient and detrended-elevation slope. | A fault juxtaposing rocks or offsetting basin fill can produce coincident, directionally persistent potential-field boundaries; combine independent field edges, not raw anomaly amplitude. | Lithologic contacts, intrusive bodies, basin margins, flight-line artifacts. | Moderate, low-confidence; independent gradients may improve localization, but catalogue recovery is not discovery. | Medium; all layers are listed as challenge inputs. Must reproduce fold-local edge transforms and per-feature leakage canaries. |
| 2 | **Radiometric contact rejection / compositional transition:** K, eU, eTh (and ratios only if actual source bands exist) with magnetics. | Use radiometric transitions to identify exposed lithologic contacts, then down-weight magnetic edges that coincide with broad compositional boundaries; retain sharp cross-cutting edges as fault candidates. | Soil, surficial cover, drainage, vegetation, radon/weathering and flight-height variation. | Low-to-moderate, low-confidence; could reduce false positives more than add recall. | Medium-high; verify exact radiometric bands, masks, units and survey seam corrections in cached stack. The official [USGS GeoDAWN data release](https://doi.org/10.5066/P93LGLVQ) is listed by USGS with GeoTIFF deliverables and CC0 1.0 rights; re-check geographic coverage, product version, CRS and pixel grid before use. Prefer the official competition feature stack when it contains the required bands. |
| 3 | **Strain–structure change points:** dilatation, shear strain rate, second invariant, earthquake-density gradient, and magnetic edge orientation. | Seek local kinematic discontinuities coincident with structural edges rather than generic high strain; a fault may be expressed as a coherent change in deformation/earthquake density. | Seismic-network detection effort, transient swarms, interpolation boundaries, regional strain gradients. | Low-to-moderate, low-confidence; feature dependence and sparse labels may limit gain. | Medium; listed challenge layers suffice. Requires strict spatial blocking and a detection-effort canary. |
| 4 | **Conductive-basement boundary geometry:** surface conductivity and depth-to-conductive-base gradients with gravity and strain. | Fault-controlled fluid pathways or juxtaposed basin/basement blocks may create a narrow conductive-depth boundary corroborated by gravity/strain. | Clay-rich alteration, saline groundwater, basin-fill thickness, non-fault lithologic contacts. | Low, very low-confidence because conductivity is not fault-specific. | Medium; existing layers suffice if units/coverage are documented. Must test conductivity-only AUC and mask artifacts. |

The priority ordering is a design triage, not a measured ranking. The protocol says stay in one authorized lane; no lane paragraph is present in this checkout, so no experiment is authorized. Candidate 1 is the lowest-dependency proposal, but is **not** authorized for implementation until the shared template and current registry are made available.

## Data and blockers

The competition page describes a single-band float32 probability/confidence GeoTIFF, values in [0,1], in EPSG:32611 with a matching grid. Official page: [DOE GEMS challenge / submission and metric details](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The official challenge dataset is behind DrivenData authentication; no credentials are available in this workspace. The prompt's Dropbox links are not accessible from the repo runtime under the configured outbound-host restriction. There is no `data/` directory or raster in this clone.

The new [automated local TIFF format checker](scripts/validate_submission.py) compares a candidate to the provided reference grid, checks single-band float32 and the full-array finite [0,1] range (avoids the reported range-validation error), and emits a JSON receipt. It does **not** compute holdout DTI, canaries, registry similarity, or organizer acceptance. Because there is no trusted reference TIFF or registry in this clone, it has not been run on competition data and cannot authorize submission.

### Official / primary sources for manual review

- [DrivenData DOE GEMS challenge: overview, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — challenge host / competition authority.
- [DrivenData competition rules and overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) — official competition page.
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — a 2026-10-26 page read showed a leader above both values quoted in the request; page display is not a saved submission-page receipt.
- [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login required for the restricted training files.
- [DrivenData reference solution source](https://github.com/drivendataorg/gems-prize-reference-solution) — challenge-hosted reference implementation.
- [USGS GeoDAWN dataset landing page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [USGS ScienceBase catalog record](https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7) — official survey description and catalog metadata.
- [USGS GeoDAWN publication record](https://pubs.usgs.gov/publication/70261199) — peer-reviewed/official USGS publication record.
- [GBCGE INGENIOUS project](https://gbcge.org/current-projects/ingenious/) — project organization source; validate data provenance and licensing per dataset before use.
- [EPSG:32611](https://epsg.io/32611) — CRS definition (EPSG registry mirror).
- [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) — background only; the challenge's own metric definition is authoritative.
- [DOE GEMS Prize Official Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — official rules document, September 2026; fetched and reviewed. It specifies up to three predictions per week, one final submission across both rounds, and disclosure of any generative-AI use in the narrative. The rules govern prize conditions; the DrivenData page governs the metric and file-format description.

### What is needed to continue autonomously

1. Run the already-prescribed `bash scripts/download_competition_data.sh` on an authenticated/unrestricted machine into `data/`, then `python scripts/prepare_data.py`; those scripts are **not present** in this checkout and must come from the actual shared template, not be invented here.
2. Provide/restore the actual shared template, cached feature stack, `evaluate_holdout.py`, `submission_writer.py`, and current benchmark receipts. No GPU or training environment can help until these inputs and code exist.
3. Provide a dated, hash-addressed registry of the actual comparison TIFs and the single allowed lane paragraph. Without it, uniqueness and lane compliance cannot be assessed.
4. Run the official-format checker against the exact sample submission template and candidate bytes; then use the shared evaluator, feature-only canaries, surface/final registry checks, and separate selector. Keep no weekly slot spent until all scientific gates pass.
5. For portal submission, verify the live submission cap and retain the actual organizer receipt. The September 2026 official rules say predictions may be submitted up to three per week, but only one final submission is selected for scoring across both prize rounds; public leaderboard performance is not the private-set score. If generative AI is used, the rules require it to be disclosed in the submission narrative, including its extent and use. This repo cannot log in, submit, inspect private labels, or verify receipts.
6. There is no automated current leaderboard/registry feed in this repository. Adding one requires a source with a stable, public machine-readable endpoint and an update/failure audit trail; the current runtime cannot reach DrivenData directly from shell, and the prompt's competing leaderboard values are unresolved. Do not present a stale static value as current.

## Local validation

Install `rasterio` and `numpy` from `requirements-audit.txt`, then run:

```bash
python -m unittest discover -s tests -v
python scripts/validate_submission.py --candidate candidate.tif --reference sample_submission.tif --json-out validation.json
```

A passing format receipt is only a file-format pass. The output intentionally records `submission_authorized: false` because scientific and uniqueness gates are outside this checker.
