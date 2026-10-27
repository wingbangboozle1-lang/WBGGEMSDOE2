WHICH FILE TO SUBMIT (2026-10-27 AUDIT)
=======================================

1) NORMALIZED NON-BLANKET UNIQUENESS CLEARANCE ONLY (LOW EMPIRICAL SCORE ESTIMATE):
   wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif
   sha256 a9c46823cd6ef367726c1446581f0ccfc3d92456f8a242e521358ae84bd27912
   Status: OK TO DOWNLOAD AND SUBMIT under the normalized non-blanket uniqueness rule
   (0 exact matches, surface |r| <= 0.56, 16.1%..24.2% 3-px overlap vs 9 focus sites,
   0 enriched discrete duplicates across 467 fleet rasters; all 9 format/range checks PASS).
   CAVEAT: Fails literal blanket-inclusive overlap (vs 13GEMSDOE stride-5 lattice) and has
   EMPIRICAL-ESTIMATE = 0.088 (95% PI [0.006, 0.214]); do NOT spend a 3/week competitive
   DrivenData slot on DZ-16 if aiming to beat GEMSDOE32 (0.2778 USER-REPORTED).

2) DO NOT SUBMIT — RETAINED FOR RESEARCH / AUDIT BINDING ONLY:
   * dphs/wbg2-dphs-exp3-submod300m-20261027T194500Z-46a3a89a-zeros.tif
     sha256 31f3d8e61d195dd5ac09f380815cd08ea072d8812e2f5021d2c41fa423e6ccd9
     Status: DO NOT SUBMIT (Run Card status = negative). Passes all byte/format/[0,1] checks,
     leakage canary (max AUC 0.6179), surface Spearman (0.8608 <= 0.90), and 9-focus-site
     overlap (0.4268..0.5823 <= 0.70), and achieved repo-best HOLDOUT-DTI = 0.1735
     (95% CI [0.1525, 0.1944]) on gems57-pooled-hide-v2; STOPPED at the >70% final-dot
     registry duplicate gate (max 0.9587 vs GEMSDOE12 dem10-scarp; 45 discrete range-front
     rasters > 0.70; EMPIRICAL-ESTIMATE = 0.0713).
   * msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif
     Status: DO NOT SUBMIT (HOLDOUT-DTI = 0.0296; >70% overlap with 50 discrete + 48 blanket rasters).
   * h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif
     Status: DO NOT SUBMIT (uniform hexagonal lattice with zero geology; HOLDOUT-DTI = 0.0720;
     literal lattice duplicate).
   * wbg2-h1-stepxasym-e2-34564dots-20261027T014251Z-b5642264-zeros.tif
     Status: DO NOT SUBMIT (masked interior cells, 99.4% lattice duplication, unvalidated).
   * wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif
     Status: DO NOT SUBMIT (duplicate of registered lattice).
