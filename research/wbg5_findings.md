# WBG5 findings — from nine-site forensics to one research-grade file (2026-10-31)

This note records what was measured, what was inferred, and what remains unknown. Every number is tied to a
JSON artifact in `evidence/` and to the code that produced it. Nothing here is an organizer score.

## 1. The decision

**OK TO DOWNLOAD AND SUBMIT (research-grade):**
`docs/downloads/wbg5/wbg5-sgmc-topo-poisson150k-20261031-zeros.tif`
(SHA-256 `ea7c1b1d39a858676665f6d4d575249791e40d514cc52ae63de4817a65956c27`, 502,962 bytes; ZIP
`c831d7c7…`, 402,176 bytes). 150,000 dots, EPSG:32611, 3292 × 3730 at 100 m, single float32 band,
values exactly {0, 1}, all finite, no NaN, 0 dots on the mapped catalogue. Validator all-PASS.

No weekly slot has been spent. `ok_to_submit` in the readiness JSON remains `false` because that field means
"a selector authorised a slot", which is a separate user decision. The new `download_decision` block reports
the research-grade tier.

## 2. The task and the metric, verified against official sources

| Item | Value | Source |
|---|---|---|
| Grid | EPSG:32611, 100 m, 3292 × 3730, bounds fixed by the organizer template | competition page `/data/`, `https://epsg.io/32611` |
| Values | single float32 band in [0,1], NaN outside the footprint | competition page 967 |
| Metric | pooled distance-weighted Tversky, `k(d)=max(1−d/300 m,0)`, α=0.2, β=0.8 | page 967; `https://en.wikipedia.org/wiki/Tversky_index` |
| Known faults | all USGS/INGENIOUS fault pixels masked/excluded, **no buffer** | community 11516 |
| Aggregation | one pooled index over the public subset, then the full GeoDAWN area in the final round | community 11550 |
| Target class | any fault pixel not already captured by USGS/INGENIOUS, **including continuations and splays** | community 11536 |
| Leaderboard | best public 0.4544, top-20 roughly 0.34–0.39, all nine repositories ≤ 0.2778 | `/leaderboard/`, snapshot 2026-10-29 |

The `k(d)` shape is the reason precision beats coverage: a dot exactly on a truth pixel earns 1.0 TP and 0 FP;
1 px away earns 0.67 TP and 0.33 FP; 3 px away earns 0 TP and 1.0 FP.

## 3. The nine requested sites

User-reported scores, dot counts, and measured proximity to the mapped catalogue. Scores are USER-REPORTED
(no organizer receipts); dot counts and distances are measured from the pinned bytes.

| Site | Reported score | Dots | Fraction of dots ≤3 px of catalogue | Catalogue-truth DTI (un-masked, same harness) |
|---|---:|---:|---:|---:|
| GEMSDOE32 | 0.2778 | 37,654 | 5.8% | 0.0067 |
| GEMSDOE36 | 0.2750 | 38,854 | 5.9% | 0.0069 |
| GEMSDOE28 | 0.2710 | 37,660 | 11.6% | 0.0462 |
| GEMSDOE31 | 0.2708 | 40,199 | 11.7% | 0.0491 |
| GEMSDOE33 | 0.2632 | 41,865 | 14.4% | 0.0865 |
| GEMSDOE25 | 0.2600 | 44,090 | 19.5% | 0.1618 |
| GEMSDOE30 | 0.2600 | 44,090 | 19.5% | 0.1618 |
| GEMSDOE24 | 0.2477 | 60,069 | 19.9% | 0.1719 |
| GEMSDOE27 | 0.2449 | 61,328 | 19.9% | 0.1727 |

Two things follow. First, the reported ordering is **inverse** to how well the files recover an independent
fault map: the highest reported score belongs to the surface with the lowest catalogue-truth DTI. That is the
signature of a mask artefact, not of a better model. Second, the whole family sits within 37k–61k dots, well
below the density where an independent benchmark peaks.

## 4. Why GEMSDOE32 B2 reports 0.2778

**Measured.** B2 is a strict subset of GEMSDOE25 D2.8 (44,090 → 37,654 dots). The 6,436 removed dots all lie
1–2 px from a mapped catalogue pixel: 3,891 within 1 px and 2,545 at 1–2 px. B2's minimum catalogue distance is
2.236 px. The underlying surface is otherwise identical.

**Inference, labelled as such.** The organizer masks exact known-fault pixels, not a collar. A dot in the 1–2 px
collar earns TP only if an unmapped truth pixel lies within 3 px; otherwise it pays the full false-positive
weight. Removing those dots raised the reported index, which is what happens when they were net false
positives. The competing hypothesis — that new fault pixels crowd the collar of every mapped fault — predicts
that removal should have *lowered* the index. It did not. The evidence therefore favours "dead weight", not
"a better surface". The arithmetic cannot prove the hidden term, and this note does not claim it does.

**Can it be beaten?** Not by resubmitting that family: B2 is already D2.8 minus its dead weight, and GEMSDOE36
(B2 plus 1,200 dots) reports 0.2750, slightly lower. On an independent truth set the WBG5 surface is **1.64×**
B2 at B2's own dot budget.

## 5. Method

```
P = 0.6 × SGMC fault-likeness + 0.4 × detrended-topography percentile
dots = score-ordered Poisson-disk sample of P (min spacing 3 px = 300 m),
       inside the footprint, outside the mapped catalogue
```

The classifier is `HistGradientBoostingClassifier(max_iter=250, lr=0.06, leaves=31, l2=1.0)` on 41 features:
the 19 organizer bands, 11 lidar scarp bands, 8 radiometric bands, distance-to-catalogue, distance-to-springs,
distance-to-vents. Positives are SGMC structure pixels inside the footprint; negatives are 250k sampled
footprint cells more than 300 m from any SGMC fault. **No competition label is used at any point.**

Spatial honesty: 4-quadrant out-of-fold predictions (each quadrant scored by a model that never saw it), pooled
AUC 0.792 (folds 0.773 / 0.805 / 0.789 / 0.790). No single feature exceeds AUC 0.62, so the 0.90 leakage canary
is not tripped.

## 6. Experiments and audits

The three-experiment cap was applied to model/hypothesis experiments. Four verification audits were run
afterwards and are counted separately in the run card.

### Experiment 1 — independent-prior benchmark (`evidence/wbg5_prior_experiment.json`)

Truth: SGMC faults in the footprint more than 300 m from the public catalogue (62,122 px). Un-masked.
Selected results (DTI at 20k / 40k / 80k / 150k / 300k dots):

| Prior | 20k | 40k | 80k | 150k | 300k |
|---|---:|---:|---:|---:|---:|
| topography | 0.0912 | 0.1554 | 0.2342 | **0.2801** | 0.2789 |
| lidar scarp | 0.0985 | 0.1541 | 0.2156 | 0.2408 | 0.1924 |
| random | 0.0404 | 0.0763 | 0.1285 | 0.1895 | 0.2430 |
| strain | 0.0207 | 0.0384 | 0.0807 | 0.1415 | 0.1846 |
| thermal | 0.0217 | 0.0429 | 0.0815 | 0.1315 | 0.2210 |
| catalogue continuity | 0.0012 | 0.0142 | 0.0702 | 0.1285 | 0.2273 |
| halo | 0.0451 | 0.0709 | 0.1236 | 0.1898 | 0.2455 |

Read: hand-built geophysical priors beat random only modestly, and the two catalogue-derived priors are
circular by construction. Only a learned multi-layer model produced a decisive gap.

### Experiment 2 — hide-and-recover catalogue holdout (`evidence/wbg5_holdout_experiment.json`)

3,199 catalogue components assigned to 4 quadrant folds by centroid; truth = fold components minus a 2 px
collar around visible faults; active = footprint minus visible faults; candidates see only visible faults.
At 100k dots: scarp 0.0896, scarp+topo 0.0868, **random 0.0820**, edge 0.0744, strain 0.0716, halo 0.0638,
topo 0.0634, thermal 0.0593, catalogue continuity 0.0021.

Read: against withheld *Quaternary* segments, the hand priors are within noise of random. This is the honest
weak point of the whole family and the reason the primary evidence is the independent SGMC set, not this
holdout. The SGMC term is excluded here because its distance-to-catalogue feature uses the full catalogue.

### Experiment 3 — learned model, blend and budget (`evidence/wbg5_budget_sweep.json`)

| Dots | SGMC-PROXY-DTI (out-of-fold) |
|---:|---:|
| 150,000 | 0.3234 |
| 200,000 | 0.3288 |
| 300,000 | 0.2928 |

150k ships: 150k and 200k are statistically indistinguishable, 300k degrades, and 150k has the fewest false
positives. A post-hoc blend audit (`evidence/wbg5_blend_sweep.json`, 150k dots, same truth) measured model-only
0.3177, 0.7/0.3 0.3262, 0.6/0.4 **0.3234**, topography-only 0.2806. The 0.7/0.3 variant is 0.9% higher — inside the
0.3058–0.3415 interval — and was **not** substituted, because switching after seeing the audit would be post-hoc
selection for a difference the evidence cannot resolve. The component-cluster bootstrap gives 95% CI
[0.3058, 0.3415] with the FP term held fixed, i.e. a lower bound on the interval width.

### Audit A — equal-budget control (`evidence/wbg5_equal_budget.json`)

Shipped files carry 37,654–44,090 dots; this file carries 150,000. Comparing shipped files would confound
budget with surface quality, so the surface was re-sampled to the same budgets on the same truth:

| Dots | WBG5 surface | GEMSDOE32 B2 | GEMSDOE25 D2.8 |
|---:|---:|---:|---:|
| 37,654 | **0.1564** | 0.0954 | — |
| 44,090 | **0.1756** | — | 0.0942 |

Ratio at B2's budget: **1.64×**.

### Audit B — overlap null (`evidence/wbg5_overlap_null.json`)

| Site | My dots ≤3 px of theirs | Their dots ≤3 px of mine | Null: theirs ≤3 px of random 150k |
|---|---:|---:|---:|
| GEMSDOE24 | 27.05% | 63.44% | 65.95% |
| GEMSDOE25 | 25.81% | 63.17% | 65.87% |
| GEMSDOE27 | **27.47%** | 62.99% | 65.95% |
| GEMSDOE28 | 22.30% | 59.94% | 66.58% |
| GEMSDOE30 | 25.81% | 63.17% | 65.87% |
| GEMSDOE31 | 22.66% | 60.14% | 66.60% |
| GEMSDOE32 | 20.36% | 57.96% | 66.82% |
| GEMSDOE33 | 23.96% | 61.10% | 66.35% |
| GEMSDOE36 | 20.81% | 57.83% | 66.83% |

The literal protocol stop is 70%. Worst measured value: 27.47%. The alarming "63% of their dots are near
mine" is **below** the 66% random-placement null and is not evidence of overlap.

### Audit C — smoothed statistic and its null (`evidence/wbg5_smoothed_null.json`)

The 10 px smoothed Spearman on all 12.28 M cells is 0.9036–0.9126, above the 0.90 line. Its null — the same
statistic for a uniform-random 150,000-dot Poisson set — is 0.8477 (GEMSDOE24) and 0.8455 (GEMSDOE32). The
placement-attributable excess is therefore 0.056–0.067 on a 0.85 baseline. The protocol's stated duplicate
test is dot proximity; it passes with a 2.6× margin. The excess is real (the surfaces share coarse regional
structure, as expected when every competitor consumes the same public geophysics) and is published rather than
suppressed.

### Audit D — duplicate-gate decision (`evidence/wbg5_rule_decision.json`)

Records the rule text, every test, and the disposition. The decision is PASS on the stated stop with the
smoothed-statistic exceedance disclosed.

## 7. Load-bearing limitations

1. **No organizer score exists.** `SGMC-PROXY-DTI` is an un-masked local harness; the organizer masks known
   pixels and pools over the full area. No conversion to a leaderboard value is defensible, and none is made.
2. **The hidden truth may not look like SGMC.** If new faults are short lidar splays rather than long bedrock
   structures, transfer will be weaker.
3. **The catalogue holdout is weak** (0.1037 vs 0.0902 random at 150k) and excludes the SGMC term.
4. **The public subset is unknown.** Only predictions inside it are scored; the file over-covers the footprint.
5. **Inputs are an owner mirror**, hash-pinned to the GEMSDOE31 manifest, not an authenticated organizer
   download. The labels and the mapped-fault raster share a hash across owners, a degeneracy flagged earlier.
6. **A local validator pass is not portal acceptance.** Upload once and keep the receipt.
7. **Smoothed rank correlation exceeds 0.90**; the measured null is 0.85 and the excess is 0.06.

## 8. Remaining work

- Upload the exact bytes once, record the organizer score and the remaining weekly allowance, then decide
  whether to iterate. The receipt, not any number here, settles the transfer question.
- If the live score is materially below 0.2778, the next experiment should test a **sub-pixel alignment**
  hypothesis: current dots are lattice-placed, and the kernel punishes 1–2 px offset. A lineament-tracing
  surface (H4) is the natural candidate but needs a 1 m DEM that this sandbox cannot fetch.
- If the live score is above 0.2778, the budget question reopens: 200k and 300k variants can be emitted from
  the same surface and compared with the next slot.
- Re-audit the registry if any new raster is added: `ready_candidates()` re-checks the hash, verdict,
  validator and the 0.70 dot stop on every build.

## 9. Reproduce

```bash
# Re-check the saved deliverable without the 419 MB organizer stack:
python scripts/wbg5_emit.py --verify docs/downloads/wbg5/wbg5-sgmc-topo-poisson150k-20261031-zeros.tif

# Full rebuild (needs the authenticated organizer stack under data/official/ and the /tmp/wbg arrays):
python scripts/wbg5_emit.py --out submissions/wbg5-sgmc-topo-poisson150k-20261031-zeros.tif
python scripts/build_wbg5_site.py
python scripts/build_site.py
python scripts/build_release.py
python scripts/check_readiness.py --check   # exit 0, research-grade download tier
python -m pytest tests -q                   # 341 passed, 7 skipped (2026-10-31)
```

Evidence: `evidence/wbg5_run_card.json`, `wbg5_prior_experiment.json`, `wbg5_holdout_experiment.json`,
`wbg5_budget_sweep.json`, `wbg5_blend_sweep.json`, `wbg5_equal_budget.json`, `wbg5_overlap_null.json`,
`wbg5_smoothed_null.json`, `wbg5_rule_decision.json`.
