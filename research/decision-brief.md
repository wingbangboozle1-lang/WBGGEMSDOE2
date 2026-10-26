# Decision brief and verification ledger

## Verdict: negative; no new TIFF, no slot selected

The proposed **Ridge-Break Continuity** lane was preregistered in [preregistration.md](preregistration.md) before implementation. A literal registry preflight proved the planned 37,654-dot design cannot meet the requested 70% maximum directional overlap against an existing registry entry. The run stopped before generating a feature surface, canary, holdout, final raster, or submission. No model or scientific experiment was run, and no leaderboard score or improvement is claimed. [Machine-readable run card](../docs/data/run-card.json).

The user's phrase “single method paragraph below” does not designate a method. RBC and the three alternatives are research ideas only, not an assigned or authorized experimental lane; the parallel project charter also requires a real assignment before implementation. We did not change the budget or select boundary pixels to work around the mathematical stop. The user requires the literal rule against **any** registry raster; silently exempting the lattice would contradict that rule. A non-failing bound at a lower budget would not establish uniqueness or scientific value.

## Independently measured witness and exact bound

Source data are hash-pinned **owner mirrors**, not authenticated copies from DrivenData. [Input manifest](../data/focus-inputs.json) and [full measurement](../docs/data/focus-audit.json). The registered witness is `registry-039` in the pinned [GEMSDOE24 priority registry](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/7ab1c8f77f0b4b8644e3929403a0dab65838b008/registry/priority_rasters.json), whose value hash and file hash both match the mirrored `13GEMSDOE` lattice. We reopened the template and the witness; both are single-band on the same 3730×3292 grid, CRS EPSG:32611 and transform `(100, 0, 243350, 0, -100, 4508550)`.

The reference lattice is within an inclusive Euclidean 3-pixel radius of 5,160,724 of 5,167,373 footprint cells; U = 6,649 are uncovered. For K distinct candidate cells, at most U can avoid the lattice, so the directional overlap is at least `max(0, K - U) / K`. For K = 37,654, this is 31,005 / 37,654 = **82.3418%**, strictly greater than 70%. This is an exact lower bound, **not** an observed candidate overlap or a score. The first dot count for which this witness alone forces failure is 22,164. Equality at 70% is not treated as failure. This witness proves failure at the chosen budget, not infeasibility for every nonempty raster; all other registry checks would still be needed at a smaller budget.

Reproduce from clean public mirrors (about 25 MB; GitHub access required):

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/audit_registry.py --restore --output .work/reproduced-audit.json
.venv/bin/python scripts/check_shared_template.py --restore --output .work/template-diagnostic.json
.venv/bin/pytest -q
python scripts/build_site.py
```

The scripts fail on missing or hash-mismatched inputs, nonmatching grids, missing witness identity or invalid values. They use no hidden labels and do not emit a TIFF.

## Nine-site evidence and the B2 question

We restored each of the nine specifically requested historical leaders at an immutable GitHub commit, checked its byte SHA-256 and in-footprint value SHA-256, and reopened the arrays. Each historical leader has more than 70% of its dots within 3 pixels of at least one **other** focus-site leader; GEMSDOE25 and GEMSDOE30 have identical in-footprint values. This is a measured overlap test, not a surface-rank test or a complete search of every previous submission. All old files are learning references, not new candidates.

The user-provided historical numbers are **USER-REPORTED claims without an authenticated organizer submission-page receipt**, not verified performance measurements or estimated scores. Of those claims, GEMSDOE32 B2 is largest. What is verifiable is the raster lineage: GEMSDOE30 D2.8 has 44,090 dots; GEMSDOE31 R1 is its exact 40,199-dot subset (3,891 dots removed, each at most 1 pixel from the mirrored catalogue); GEMSDOE32 B2 is R1's exact 37,654-dot subset (2,545 further dots removed, each at most 2 pixels from the catalogue). GEMSDOE36's named raster is B2 plus 1,200 dots. These comparisons are reproducible from the pinned bytes; they do not prove the files were the actual uploaded bytes.

The [organizer's published DTI](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) rewards proximity with a triangular kernel extending 300 m, and weights false positives and false negatives differently. Removing low-yield dots *can* improve the index if the decrease in false-positive cost is worth the lost true-positive credit. That mechanism is consistent with the reported sequence but not proven: the private fault labels, per-submission TP/FP/FN and authenticated receipts are unavailable. A mapped fault's exact pixels are excluded from scoring, while nearby predictions are not automatically exempt; [organizer clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4). We cannot predict that a new method will exceed any reported score or the public leader.

## Shared-template defect: reported, not forked

A synthetic, byte-pinned test of [GEMSDOE24 `novelty.py` at fc2bc6f](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/src/gems/novelty.py) shows that `compare_registry` checks raster shape and value hash but does not receive/check the expected CRS and transform; a same-shaped EPSG:4326 file with an unrelated transform returned `passed: true`. See [diagnostic](../docs/data/template-diagnostic.json), `scripts/check_shared_template.py`, and [upstream issue #59](https://github.com/buffedlizard55-lab/GEMSDOE24/issues/59). Our preflight independently validated the witness/template CRS, shape, transform and band count before computing the bound. We have no write permission to that repository and did not keep a modified private copy. A fix and regression test belong in the shared template before a future campaign relies on the full registry comparison.

The template supports an optional mode that reports calibration-separated results; its default is the literal rule. Do not use a calibration exemption for this request without explicit authorization. The shared writer's zero-outside mode and official null-outside wording require care: its own diagnostic distinguishes a local format check from official-text compliance. We could not inspect the previously rejected file or authenticate against the portal, so the cause of the user's range error is unknown. The original [competition format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format) calls for float32, values in `[0,1]` and null/NaN outside the bounds; zero-filling the exterior does not by itself establish compliance or acceptance.

## Inputs, source rights and irregularities

| Source | Verified statement | Constraint |
| --- | --- | --- |
| [DrivenData problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fault presence is the target, not proof of a geothermal vent; metric and submission requirements are published. | Hidden test faults, portal receipt and actual competition files are inaccessible here. [Data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) redirected the page reader to login. |
| [USGS GeoDAWN data release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Magnetic and radiometric survey products include GeoTIFFs; USGS page marks the release CC0. | Survey flight height and acquisition artifacts are plausible confounders. Sandbox shell cannot reach USGS data hosts. |
| [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) | 3DEP products are free without use restrictions. | Project-specific tile coverage, quality and availability were not independently downloaded here. |
| [DOE GDR 1391](https://gdr.openei.org/submissions/1391) | Public INGENIOUS data include 2-m probes, wells, springs, fault maps, and geophysics; the record is CC BY 4.0. | Coverage, sampling effort, license of each linked product, and label leakage require checks before use. |
| [USGS Surprise Valley](https://www.usgs.gov/publications/influence-pre-existing-structures-geothermal-springs-inferences-potential-field) | Springs occur near local breaks and bends in an inferred magnetic high in that case study. | Motivation only; it neither verifies RBC features nor proves any predicted vent. |
| [Pinned shared-template provenance](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/f7ad7e61cf03842c6e6410a96ee5ee6cbbc6a08a/registry/template_pins.json) | Identifies the GEMSDOE24 shared evaluator/writer and byte hashes. | The actual prepared feature cache was absent here. A [manifest](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/f7ad7e61cf03842c6e6410a96ee5ee6cbbc6a08a/registry/data_manifest.json) identifies a large split owner mirror of raw training features; integrity is not organizer authentication. |

Additional irregularity: the mirrored “sample submission” has 60,988 positive cells, all coincident with the mirrored label positives, whereas the organizer's problem description calls its sample a fault-absence prediction. This is a mismatch in provenance/description, not a conclusion about organizer data. It was used **only for the grid and footprint**, never as a feature or holdout prediction. Resolve by comparing authenticated original bytes before training.

The public [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) is dynamic. The site contains a timestamped snapshot with explicit freshness and an official live link; it does not authenticate any of our submissions. The GitHub Actions workflow attempts a read-only scheduled refresh on the hosting infrastructure, but automatic deployment is not yet demonstrated: Pages currently publishes from the main branch and a request to switch its source returned HTTP 403 for this integration. The sandbox shell is restricted to GitHub and package hosts; failures display “unavailable” rather than stale values.
