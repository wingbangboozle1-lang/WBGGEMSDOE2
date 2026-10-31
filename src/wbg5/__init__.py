"""WBG5 campaign: prior-surface screening, density calibration and submission emission.

Every number produced by this package is either

* ``HOLDOUT-DTI`` — a distance-weighted Tversky index computed on withheld
  catalogue segments (not a leaderboard score), or
* ``SGMC-PROXY-DTI`` — the same arithmetic against the independent USGS State
  Geologic Map Compilation fault raster restricted to pixels >300 m from the
  public catalogue (again not a leaderboard score).

No leaderboard projection is written as a score.
"""
