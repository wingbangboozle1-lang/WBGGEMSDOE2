# Historical parallel-run hypothesis notes

> **Superseded:** H1 was self-assigned, not an approved lane. Its candidate failed the registered binary-lattice overlap gate, and the parallel holdout was not protocol-valid. These are untested geological proposals, not proven geological conclusions or score projections. See the [current hypotheses](research/hypotheses.md) and [independent audit](data/parallel_candidate_audit.json).

This repo started empty (only `README.md`, verified 2026-10-26), so every item
below is new *to this repo*. Cross-site claims are limited to what the nine
focus sites publish. Ranked by expected HOLDOUT-DTI gain / implementation cost.

| # | Hypothesis (layers + transform) | Why it should catch a catalogue-missing fault | Mimic (non-fault process) | Cost | Rank |
|---|---|---|---|---|---|
| H1 — parallel, blocked | **GeoDAWN TMI_up150 + Th/K gradient-step × lidar cross-slope asymmetry** (`cross_max`, `|downface-upface|`): gradient magnitude of TMI and ThK multiplied by lidar asymmetry bands, plus parent bands, HistGBM | A buried normal fault may lack a continuous scarp *and* lack an isolated magnetic step, but fault juxtaposition of basement plus piedmont tilting makes the two steps coincide on one line. Catalogue faults are already mapped where the scarp alone is obvious; the coincidence targets the buried remainder | Lithologic contact with an erosional escarpment; basalt flow edge over tilted alluvium | Low (bands already in public sibling repos) | 1 |
| H2 | **Up-dip advection of the TMI horizontal-gradient ridge**: shift gradient maxima 150–300 m (1.5–3 px) toward the down-thrown side inferred from lidar relief sign, for 45–60° dips, before emission | The magnetic source edge is offset from the surface trace; unshifted ridges fall outside the 300 m kernel of the true (hidden) trace | Contact dipping the opposite way; remanent magnetisation shifting the anomaly | Medium | 2 |
| H3 | **Hydrothermal Th/K-low corridor**: lows in ThK/UK radiometrics (clay alteration leaching) intersected with scarp-strike continuation beyond catalogue segment tips | Blind geothermal upflow alters rock along faults with no surface rupture; alteration follows the fault past its mapped tip | Lake-bed / playa clay flats (also Th/K-low, flat) | Low–Med | 3 |
| H4 | **Stepover relay closure**: orientation-coherent gap-filling between catalogue segment tips (tip azimuth agreement + collinearity ≤ 2 km gaps) using only fold-visible tips | Segmented normal-fault arrays link through relay ramps that are themselves unmapped fault | Aligned but unrelated lineaments (roads, drainages) | Medium | 4 |
| H5 | **2 m-temperature / spring-snail proximity annulus**: INGENIOUS 2 m probe + GDR spring points, annulus (not disk) around thermal anomalies, crossed with H1 surface | Direct geothermal surface expression can sit off the mapped trace on the upflow fault | Irrigated fields / shallow groundwater unrelated to faults | High — needs GDR 1391 download; obtainable free at https://gdr.openei.org/submissions/1391 (checked: page exists; file fetch not attempted from this sandbox) | 5 |

## Historical B2 context

The 0.2778 figure is owner-reported and has no organizer receipt in this review. We independently found that B2 is D2.8 with dots within two pixels of the mirrored catalogue removed. Sparse emission and pruning are plausible explanations, not established causes. No reliable leaderboard forecast for a new candidate is available.

## Named mimic for the lane (protocol item)
H1's mimic is a **lithologic contact with an erosional escarpment** (e.g. a
basalt-flow edge): it produces a magnetic step and a slope asymmetry with no
fault. The parallel holdout cannot establish that it has excluded this mimic. Whether a radiometric Th/K step discriminates these processes requires independent validation.
