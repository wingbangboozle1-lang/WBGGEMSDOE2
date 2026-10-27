# Five ranked geological hypotheses — distal blind-fault program 2026-10-27

**Evidence class:** `PROPOSED-HYPOTHESIS` — qualitative prior, not measured HOLDOUT-DTI. All layers below are from the hash-pinned 19-band owner-mirrored stack (`data/official/training_features.tif` SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`) plus Census TIGER and GDR sources. No new external binary is required. Mirror origin is not organizer-authenticated; ignored caches must be re-verified before any holdout run. The official depth layer is `depth to conductive base` (not authenticated basement depth).

**Fleet observation that motivates the ranking:** The 95-scored-raster empirical model (LOSO R² 0.4303, Spearman 0.6488) shows top scorers (GEMSDOE32 0.2778, GEMSDOE70 0.3133 USER-REPORTED) place 34–37% of mass >32 px distal vs 3.6% for range-front-concentrated DPHS-EXP3. B2's gain likely came from removing 6,436 near-catalogue dots (44,090→37,654) that were paying FP cost without adding distal T. The next gain should come from *re-allocating* that budget to distal piedmont, not from more range-front density.

| Rank | ID | Title | Expected HOLDOUT-DTI gain (qualitative, untested) | Cost | Layers | Status |
|-----:|----|-------|---------------------------------------------------|------|--------|--------|
| 1 | **N5 — Distal piedmont blind-fault allocation outside 30 px** | **Highest** — directly targets the 30–40% of fleet variance explained by distal placement; lowest FP overlap with known faults | **Low** (~90 LOC; EDT + masked submodular, no new sensor) | `existing_faults` distance (EDT), `depth_to_base_surf` (Band 15 proxy), `det_elev` (Band 12) + TIGER road de-confound | **Implemented as research candidate** `wbg2-distal-blind-piedmont-6000dots-20261027T120000Z-7a3f9c1d-zeros` — see run card |
| 2 | **N1 — Signed edge-pair body veto** | High qualitative — discriminates finite-width intrusives from monotonic steps | Medium (profile sampling at 200/400/800 m) | `rtp` (B2), `iso_grav_anom` (B13), `depth_to_base_surf` (B15) | Proposal only; distinct from MSPTCD unsigned gradients |
| 3 | **N2 — Radiometric-quiet magnetic transfer under cover** | Moderate — targets cover bias | Medium (matched strata sampling) | `tc` (B6), `rtp` (B2), `depth_to_base_surf` (B15), `cond_surf` (B17) | Proposal only |
| 4 | **N3 — Catalogue-free orientation transport at junctions** | Exploratory — high cost, non-unique | High (graph) | `iso_grav_anom` (B13), `rtp` (B2), `det_elev` (B12) | Proposal only |
| 5 | **N4 — Survey-axis notch stability veto** | Low direct — artefact control only | Low–Medium (local FFT) | `mag_anom` (B1), `rtp` (B2), `tc` (B6) + USGS GeoDAWN flight-line docs | Proposal only |

## N5 — Distal piedmont blind-fault allocation (implemented)

- **Specific layers:** `existing_faults.tif` Euclidean distance transform (EDT) >30 px (=3,000 m) mask; `depth_to_base_surf` (Band 15, conductive-base depth proxy) for piedmont vs playa stratification; `det_elev` (Band 12) for relief context; Census TIGER `tiger_road_distance_m` for road de-confounder (250 m buffer). No new binary needed.
- **Physical signature:** Basin-and-Range normal faults produce 0.5–8 m piedmont scarps with asymmetric topographic steps and 100 m-scale linear coherence. Beyond 3 km from range fronts, Holocene/Late-Pleistocene scarps are systematically omitted from 1:100k compilations (Faulds & Hinz 2015). Require distal EDT mask + road-suppressed scarp contrast, sampled only on fold-visible training folds.
- **Why it catches uncatalogued vs known:** Known faults are range-front master strands with >10 m throws and clear bedrock scarps; they dominate the training catalogue. Blind intrabasin faults have <3 m throws under thin Quaternary fill, lack bedrock exposure, and are invisible to pre-3DEP mapping. By masking `d_vis ≤2.05 px` and decoding only `d_vis >30 px` via submodular cover, we *exclude* near-catalogue FP waste and *re-allocate* to distal hypothesis space where hidden truth density is higher (fleet model: distal fraction explains +0.12 DTI).
- **Difference from repo:** DZ-16 used isotropic `d≤32 px` truncation (distal starvation: 3.6% distal). MSPTCD was zero-catalogue. DPHS-H2 used Voronoi relay bridges (2.5–26 px) — a *near-catalogue* linker, not a distal allocator. H3-PACK was uniform lattice packing. None used an explicit **30 px distal mask** with road/shoreline de-confounded 10 m DEM + 1 m LiDAR (when available) as a *budget allocator*. Our candidate's uncovered-edge priority is a *registry-uniqueness* strategy, not geology; the distal mask is the geology.
- **Non-fault mimic:** Pleistocene Lake Lahontan shoreline benches (1,315–1,348 m), highway causeways (<250 m from TIGER), and symmetric arroyo incision can mimic piedmont steps. Mitigated by Lahontan elevation notch (1332±15 m) and road-weight `clip(dist/250,0.15,1)`.
- **External data:** None required. All layers are in the restored 19-band mirror. For LiDAR gap (24.7% un-flown), fallback is seamless 10 m 3DEP DEM (already in DPHS cache). No free external source needed; if pursued, USGS 3DEP 1 m LiDAR via https://apps.nationalmap.gov/downloader/ (official, CC0) is obtainable.
- **Cost & validation:** Low — EDT is O(n), greedy placement is O(N log N). **Holdout:** Not yet run on `gems57-pooled-hide-v2` (requires full 19-band cache re-verification and 2 h). Leakage canary is trivial (distance is catalogue-derived but strictly fold-visible; AUC must be tested per-fold). Empirical fleet-model projection for this geometry (median 45.5 px, frac_within 3.2%, 6,000 dots) is `EMPIRICAL-ESTIMATE 0.18–0.30, 95% PI [0.00,0.35]` (RMSE 0.094, not a HOLDOUT-DTI or organizer receipt). Weekly slot not spent.

## N1–N4 — carried forward, not implemented here

See `research/hypotheses.md` for full N1–N4 specifications with sources. Ranking here reflects new fleet evidence: distal allocation outranks body-veto because fleet variance is dominated by *where* mass is placed, not just *what* is vetoed. N1 remains the top *feature* proposal; N5 is the top *placement* proposal.

## How B2 achieved 0.2778 (PhD-level forensic)

**DTI mechanism:** `DTI = TP_w / (0.2·TP_w + 0.2·FP_w + 0.8·N + ε)` with `FN_w = N − TP_w` and 300 m triangular kernel `K(r)=max(0,1−r/3)`. For a change `ΔT, ΔF` from an ancestor at score `s`, `ΔDTI>0 ⇔ [1−0.8s]·ΔT > 0.2·s·ΔF`. B2 deletes 6,436 dots near catalogue (within 2 px). Upper bound `ΔF ≤6,436` and `ΔT ≤6,436`, but `TP_w` is kernel-weighted: a dot near a masked known fault contributes ~0.0 to `FP_w` if its kernel mass falls on visible faults? Actually organizer masks exact known-fault pixels *only* (not a 2-px collar), so B2's 2-px exclusion is *stricter* than official masking. Its reported +0.0178 (0.2600→0.2778) is plausible if those dots were FP-heavy (e.g., on footwall granite) and TP-light, but without hidden labels per-dot contributions are unmeasurable. GEMSDOE36 adds 1,200 dots to B2 and scores *lower* (0.2750), consistent with FP-cost hypothesis but not proof. All are USER-REPORTED, no receipt, public-set overfitting possible.

**Why others trail:** GEMSDOE25/30 (44,090 dots) are identical predictions (different TIFF bytes). Their higher N pays `β=0.8·N` penalty without proportional `TP_w` gain. GEMSDOE24/27 (60k+ dots) pay even higher `β·N`. The optimum balances covering hidden distal faults (`ΔT`) against paying `0.2·FP_w+0.8·N`. Lattice packing (13GEMSDOE) maximizes coverage but maximizes `FP_w`.

**Can we beat 0.2778?** Unknown. Fleet model predicts 6k distal placement at `0.18–0.30` (wide PI); B2's empirical projection is `0.25` ±0.09. Only a buffered hide-and-recover holdout (visible-only features, 60,988 withheld positives, paired CI) can rank N5 vs B2. No HOLDOUT-DTI was measured here; no weekly slot was spent.

## Sources (verified 2026-10-27)

- Official competition, metric, features, format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Masking clarification: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516
- GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- Argenta Rise multi-physics: https://pubs.usgs.gov/publication/70271418
- Blind geothermal synthesis: https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and
- GDR INGENIOUS 1391: https://gdr.openei.org/submissions/1391
- 3DEP: https://www.usgs.gov/3d-elevation-program/about-3dep-products-services
- TIGER/Line: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Tversky/DTI: https://en.wikipedia.org/wiki/Tversky_index
- EPSG:32611: https://epsg.io/32611

Evidence note: All hypothesis layers were reverified via `.cache` on 2026-10-27; owner-mirrored stack is hash-pinned, not organizer-authenticated. No holdout, leakage canary, or organizer receipt was produced in this session for N5–N1 beyond the file-format/uniqueness checks above.
