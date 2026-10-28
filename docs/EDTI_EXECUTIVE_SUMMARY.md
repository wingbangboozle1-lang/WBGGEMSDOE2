# WBG4 / EDTI executive summary

**Verdict: FORMAT-VALID AND UNIQUE — HOLD, NOT A LEADERBOARD PICK** — `artifacts/wbg4/wbg4-mc40k-scarprad20-20261028-9f5dbc9b-zeros.tif` (download: https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/artifacts/wbg4/wbg4-mc40k-scarprad20-20261028-9f5dbc9b-zeros.tif?raw=1)
(sha256 `9f5dbc9b820da220b6ce21bedab6a486ef33c702a71bec3bc1d2d9aa42b51ce1`).

| item | value |
|---|---|
| File to download | `wbg4-mc40k-scarprad20-20261028-9f5dbc9b-zeros.tif` |
| Estimated score | **PROJECTION 0.20–0.30** (not an organizer score) |
| Unique vs method-bearing registry rasters | YES — max 3 px overlap 0.5604 (limit 0.70), max |Spearman| 0.1665 (limit 0.90) |
| Format gate | PASS |
| Dots | 40,000 |
| Holdout | HOLDOUT-DTI 0.11714 (edti@32000), n=2 folds, no CI claimed |

## 1. Why 0.2778 happened

`DTI = c / (c + 0.8 + 0.2f)` where `c = T/N` is weighted coverage of hidden truth and `f = F/N` is
false-positive mass per truth cell, so `c = DTI(0.8 + 0.2f)/(1 - DTI)`.

| reported | implied coverage c (f in [0, 0.6]) |
|---|---|
| 0.2778 | 0.3077 – 0.3539 |
| 0.3195 | 0.3756 – 0.4319 |
| 0.4413 | 0.6319 – 0.7267 |
| 0.4544 | 0.6663 – 0.7662 |

## 2. The nine sites are one family

72 of 72 ordered pairs exceed the 0.70
duplicate stop; 64 exceed 0.90; the maximum is
1.0. GEMSDOE28 and GEMSDOE31 decode to the same 40,199 dots;
GEMSDOE25 and GEMSDOE30 to identical in-footprint arrays (44,090). None of the nine is a distinct
method.

## 3. Measured experiments

* EXP-1 (HOLDOUT-DTI, 2 folds): nms 0.1175 / maxcover 0.1169 / edti 0.1147 — selectors are
  indistinguishable. Negative result.
* EXP-2 (HOLDOUT-DTI, 2 folds): the same hazard field scores 0.0154 as a continuous map and
  0.1171 as edti@32000 dots — **binarisation is worth 7.6x**. Interior
  optimum at 32k–40k dots.
* EXP-3: final build, all format clauses PASS.

## 4. Limits

No organizer truth; `drivendata.org` unreachable; external data limited to GitHub/PyPI. No offline
method can demonstrate a score above 0.2778. See the HTML page §6 for the named unblock list.

Full page: `docs/edti/index.html`.
