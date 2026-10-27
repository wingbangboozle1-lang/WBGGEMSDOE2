WHICH FILE TO SUBMIT
====================

OK TO DOWNLOAD AND SUBMIT (ONLY THIS ONE FILE):
  * wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.tif
    sha256: 2262aa7e543690c27a307efdd3a0bd15357cd917bac265da32b8a3cf792c4080
    (single-TIFF zip mirror: hvgf/wbg2-hvgf-vent-relay-submod-37654d-20261027T194500Z-543811e3-zeros.zip,
     zip sha256: dce3f3728c67ea23a780c312561bf998a2773596b9a0fbc66fe3fbabf54acc9e)
    Optional DrivenData note (<=140 chars, 116 chars):
      WBG2-HVGF E3: OOF hydrothermal vent back-proj + K/Th-demag + 1m/10m scarp/chi + 2-host relay submod (37654d, 0 NaN).

DO NOT SUBMIT ANY OF THE LEGACY / SUPERSEDED / REJECTED FILES RETAINED FOR AUDIT PROVENANCE:
  * wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif
    -- DO NOT SUBMIT: superseded catalogue-only DZ-16 baseline (no geophysics/hydrothermal stack;
       outscored on Piedmont SGMC 0.0407 -> 0.0528 by WBG2-HVGF).
  * h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif
    -- DO NOT SUBMIT: contains 7,111,787 NaN pixels outside footprint (nodata=nan), which triggers
       DrivenData portal rejection "Predicted values must be in range [0, 1]".
  * msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif
    -- DO NOT SUBMIT: superseded 19-band MSPTCD research raster (0.0426 vs 0.1156 HOLDOUT-DTI on
       8 km spatial quadrant holdout; halted fail-closed on literal registry).
  * wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif
    -- DO NOT SUBMIT: rejected (masked interior cells, 99.4% lattice duplication, no validated holdout).
  * ../../downloads/wbg-h1-blind-conduit-breach-20261026T220000Z-a1b2c3d4-zeros.tif
    -- DO NOT SUBMIT: rejected continuous-prior research surface (5,167,373 positive pixels).

Historical binaries are retained strictly because existing audit receipts bind to their SHA-256 hashes.
