"""WBG4 — strike-conditioned structural-corridor lane (new, independently validated).

This package holds the eighth-round lane implemented 2026-10-28.  It is
deliberately separate from ``wbg2``/``wbg3``/``wbggems`` so that no earlier
approval or negative decision is inherited or silently reused.

Design summary (see ``research/wbg4_lane.md`` for the full argument):

* Inputs are the *official* competition grids (labels / sample submission,
  SHA-256 pinned in ``config/wbg4_lane.json``) plus public USGS-derived rasters
  whose provenance the sites documented (GeoDAWN radiometrics and their
  derivative extensions, lidar scarp morphology, the SGMC fault raster) and two
  public point layers (GDR well/spring chemistry, INGENIOUS 2 m temperature
  probes).  No other site's prediction raster is used as an input.
* The target is *unmapped* faults, so the model is fitted on whole fault
  components with a spatial block held out, and every catalogue-derived feature
  is rebuilt from the visible components only (hide-and-recover).
* The emitted raster is a dense structural corridor field thresholded at the
  DTI-optimal operating point, not a copy of, or a jitter of, any registry dot
  pattern.
"""

from __future__ import annotations

__all__ = ["lane", "emit"]

__version__ = "1.0.0"
