"""WBG4 — expected-DTI (EDTI) campaign.

A deliberately different lane from wbg2/wbg3:

* wbg2 and wbg3 select dots with a *max-cover* (CELF/submodular) objective over a
  hazard surface.  Max-cover maximises the amount of probability mass covered and
  has no explicit false-positive term.
* wbg4 optimises the competition metric itself.  The official metric is
  ``DTI = T / (T + 0.2*F + 0.8*N)`` with ``FN == N - T``, so an extra dot is only
  worth placing when its expected kernel-weighted hit probability exceeds a
  budget-dependent break-even value.  The placement step below maximises the
  *ratio* rather than the covered mass.

Nothing in this package authorises a competition submission; see
``docs/EDTI_EXECUTIVE_SUMMARY.md`` for the decision record.
"""
__all__ = ["features", "holdout", "placement", "writer", "algebra"]
