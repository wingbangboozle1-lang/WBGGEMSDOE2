> **Historical parallel-session notes, superseded.** The described TIFF fails the literal registry rule and masks footprint cells. The holdout used a private evaluator, its confidence interval was not reproduced by the committed script, and the single-fold canary cannot establish all-fold safety. Treat the narrative below as unverified, not a submission recommendation. See the [independent review](data/parallel_review.json) and [current findings](../research/findings.md).

# Candidate hypotheses not previously implemented as a standalone lane in this repo

This repo started empty (only `README.md`, verified 2026-10-26), so every item
below is new *to this repo*. Cross-site claims are limited to what the nine
focus sites publish. Ranked by expected HOLDOUT-DTI gain / implementation cost.

| # | Hypothesis (layers + transform) | Why it should catch a catalogue-missing fault | Mimic (non-fault process) | Cost | Rank |
|---|---|---|---|---|---|
| H1 ✅ LANE | **GeoDAWN TMI_up150 + Th/K gradient-step × lidar cross-slope asymmetry** (`cross_max`, `|downface-upface|`): gradient magnitude of TMI and ThK multiplied by lidar asymmetry bands, plus parent bands, HistGBM | A buried normal fault may lack a continuous scarp *and* lack an isolated magnetic step, but fault juxtaposition of basement plus piedmont tilting makes the two steps coincide on one line. Catalogue faults are already mapped where the scarp alone is obvious; the coincidence targets the buried remainder | Lithologic contact with an erosional escarpment; basalt flow edge over tilted alluvium | Low (bands already in public sibling repos) | 1 |
| H2 | **Up-dip advection of the TMI horizontal-gradient ridge**: shift gradient maxima 150–300 m (1.5–3 px) toward the down-thrown side inferred from lidar relief sign, for 45–60° dips, before emission | The magnetic source edge is offset from the surface trace; unshifted ridges fall outside the 300 m kernel of the true (hidden) trace | Contact dipping the opposite way; remanent magnetisation shifting the anomaly | Medium | 2 |
| H3 | **Hydrothermal Th/K-low corridor**: lows in ThK/UK radiometrics (clay alteration leaching) intersected with scarp-strike continuation beyond catalogue segment tips | Blind geothermal upflow alters rock along faults with no surface rupture; alteration follows the fault past its mapped tip | Lake-bed / playa clay flats (also Th/K-low, flat) | Low–Med | 3 |
| H4 | **Stepover relay closure**: orientation-coherent gap-filling between catalogue segment tips (tip azimuth agreement + collinearity ≤ 2 km gaps) using only fold-visible tips | Segmented normal-fault arrays link through relay ramps that are themselves unmapped fault | Aligned but unrelated lineaments (roads, drainages) | Medium | 4 |
| H5 | **2 m-temperature / spring-snail proximity annulus**: INGENIOUS 2 m probe + GDR spring points, annulus (not disk) around thermal anomalies, crossed with H1 surface | Direct geothermal surface expression can sit off the mapped trace on the upflow fault | Irrigated fields / shallow groundwater unrelated to faults | High — needs GDR 1391 download; obtainable free at https://gdr.openei.org/submissions/1391 (checked: page exists; file fetch not attempted from this sandbox) | 5 |

## Why 0.2778 won among the nine focus sites (evidence-bounded)
All nine focus-site bests (0.2449–0.2778, OWNER-REPORTED, no organizer
receipts in any repo) belong to one lineage: dotted/Poisson-disk re-emission of
the H19-5/H27-4 off-catalogue network at ~2.8–3.0 px spacing and 37–49k dots.
The score ordering inside the family tracks *emission thinning + pruning near
known catalogue faults*, not new geology: raw ribbons score ~0.19, dotted
re-emissions 0.2449–0.2778. The 0.2778 file (37,654 binary dots) is the most
thinned, catalogue-masked member. Beating it therefore requires either
(a) finding real off-network truth (hard: GEMSDOE32's unique H47 projected
0.240–0.248, below the champion), or (b) a surface whose off-network dots are
right more often — exactly what H1's holdout tests. Leaderboard top is stated
as 0.4413 in one part of the brief and 0.3195 in another (IRREGULARITY IR-1);
neither is organizer-verified here.

## Named mimic for the lane (protocol item)
H1's mimic is a **lithologic contact with an erosional escarpment** (e.g. a
basalt-flow edge): it produces a magnetic step and a slope asymmetry with no
fault. The holdout cannot fully exclude it; the radiometric Th/K step term is
the partial discriminator (flow edges usually lack the Th/K juxtaposition).
