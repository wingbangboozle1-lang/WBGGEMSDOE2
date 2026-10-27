# Nine-site README recheck — 27 October 2026

We fetched README text at the nine commit IDs in the [machine-readable receipt](../evidence/focus_readme_review_20261027.json) at approximately **19:12 UTC**. These commits were identified by the earlier HEAD check; HEADs can move again. This is a **documentation-only scan** of each README, not a review of all source files, a fresh raster-byte audit, a validation of the sibling numerical results, a complete registry inventory, or an organizer receipt. Every finding below is **SOURCE-REPORTED**, not independently reproduced here. The historical score table remains the user-supplied comparison, not a verified current best.

| Focus site and pinned source | Selected current-readme observation |
|---|---|
| [GEMSDOE24](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/4ac957757f8494439e2dc51b58ca62c380550e44/README.md) | Feasibility review stops the usual dot budgets; TMCG is research-only and its source reports lattice duplication. |
| [GEMSDOE25](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/3a1d548c6a187d50899095e29f5c022101edefc5/README.md) | H78 remains DO NOT SUBMIT; its earlier 0.2785 forecast was reported as hard-coded and withdrawn. |
| [GEMSDOE27](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/59246f662cd6492976599597cd754a7c730d92f0/README.md) | H33-BSS is a research artifact with a source-reported negative holdout; DO NOT SUBMIT. |
| [GEMSDOE28](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/91e8d24b87a5cfb3e0562249ae32ae78fe9183b4/README.md) | S22C is stopped under the lattice rule; texture-covariance and drainage ideas appear as proposals. |
| [GEMSDOE30](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/d21ddd9502f3c3911e8d77b8f1e6abfaadffc876/README.md) | CSR-1 and two later artifacts are stopped; the README flags full-catalogue leakage in the latter holdouts. |
| [GEMSDOE31](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/88ec212955353f7590e94b8ef2a9763ffa035d45/README.md) | H31-AA is research-only; its source reports a lower holdout than its incumbent and states no artifact is approved. |
| [GEMSDOE32](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/6a28a39a2bca6bbb49cd8a56292c78d474c9ef91/README.md) | ARENA49-PCG phase congruency is a reported prior implementation; latest decisions say DO NOT SUBMIT. |
| [GEMSDOE33](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/844f514819041c7be9efd345a24cf5cd70263f00/README.md) | R5 is reported as failing holdout; its uniqueness claim covers 21 comparators, not a complete registry. |
| [GEMSDOE36](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/6306b61ba11339d534e9356c5b8ec78b65ac4d3a/README.md) | KPL is reported duplicate and DO NOT SUBMIT; a file-linked score conflicts with this repository ledger. |

## Corrections prompted by this scan

- **Prior work:** GEMSDOE32 reports an ARENA49-PCG phase-congruency implementation; GEMSDOE36 reports a negative K/Th alteration experiment. GEMSDOE28 already proposed two-sided texture covariance and drainage deflection, and GEMSDOE24 reports a D8-knickpoint experiment. We withdrew phase congruency, K/Th alteration, and the earlier generic drainage idea from the local prospective shortlist, and explicitly distinguish the remaining matched-texture idea from those proposals. We did not reproduce or reinterpret the sibling holdouts.
- **Conflicting user-reported KPL values:** [GEMSDOE36 README](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/6306b61ba11339d534e9356c5b8ec78b65ac4d3a/README.md) reports **0.1647** for `gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros`, while our [user-reported ledger](../docs/data/user-reported-ledger-20261027.csv) lists **0.2314** for the same filename. Neither is supported by an organizer receipt in this review. Do not resolve the discrepancy by guessing or use either number as a new score.
- **Reported uniqueness is comparator-dependent:** GEMSDOE33 reports its R5 file unique against 21 rasters. We did not open that newer file, and this is not a pass against the full registry. The independent lattice counting bound remains applicable only if the reported support is distinct and in the same verified footprint; it does not substitute for inspecting its bytes.

The revised [four ranked desk proposals](hypotheses.md) have not been run in this lane, are not asserted to be globally novel and do not assign a method. External ComCat and groundwater records were not fetched; official access documentation does not establish target coverage or successful binary/API access.
