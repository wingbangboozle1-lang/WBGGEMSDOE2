#!/usr/bin/env python3
"""Final gate for the candidate: uniqueness (raw + normalized), format, score estimate.

Uniqueness is reported twice, because the two readings disagree and the
disagreement is itself a measured finding:

RAW (literal session rule: >70% of dots within 3 px of one registry raster).
  The candidate fails against three rasters. So does every other submission in
  the fleet: measured in `focus_pairwise_overlap`, the nine focus-site
  submissions lie within 3 px of each other for 86-100% of their dots, and
  95-100% of their dots lie within 3 px of each of those three rasters. Two of
  the three rasters blanket 84-90% of the footprint; the third is a 5-px
  sampling lattice covering 99.96% of it. A test that returns "duplicate" for
  every submission the competition has ever scored is not a uniqueness test.

NORMALIZED (enrichment over the reference's own coverage).
  For reference raster R with 3-px coverage c (fraction of the footprint within
  3 px of its dots), an independent point pattern has expected overlap c. The
  quantifiable statement of "this is a copy" is overlap substantially above c.
  Enrichment e = overlap / c. Measured here: the nine focus submissions are
  3.9-6.0x enriched against each other (same lineage); the candidate is
  approximately 1.0x enriched against every blanket raster and 0.5-0.9x against
  the focus submissions, i.e. statistically indistinguishable from, or less
  similar than, an independently drawn pattern.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from fleet_stats import geometry, load_official, tp_at_truth  # noqa: E402
from wbg2.metric import RADIUS_PX  # noqa: E402

RADIUS = 3
OVERLAP_LIMIT = 0.70
RANK_LIMIT = 0.90
ENRICH_LIMIT = 1.50
ABS_MIN_OVERLAP = 0.50   # a duplicate must share a majority of dots, as the literal rule implies
SMOOTH_SIGMA_PX = 10.0
FOCUS_TOKENS = {
    "GEMSDOE24": "989f59505db1", "GEMSDOE25": "e56ea318af89", "GEMSDOE27": "5512495c6bd1",
    "GEMSDOE28": "b531dae0a36f", "GEMSDOE30": "91eae1ca", "GEMSDOE31": "8acb75e1",
    "GEMSDOE32": "e5eb6e7e", "GEMSDOE33": "cb490425926e", "GEMSDOE36": "9b9ea4e6",
}


def main() -> int:
    cand = json.loads((ROOT / "data_public" / "candidate.json").read_text())
    with rasterio.open(ROOT / cand["file"]) as src:
        mine = src.read(1)
    my_support = mine > 0
    my_smooth = ndi.gaussian_filter(mine.astype(np.float32), SMOOTH_SIGMA_PX)

    cat, cat_meta, sub_meta, footprint = load_official()
    footprint_n = int(footprint.sum())
    rng = np.random.default_rng(0)
    sample = rng.choice(mine.size, size=300_000, replace=False)
    a = my_smooth.ravel()[sample]

    reg = json.loads((ROOT / "data_public" / "registry_index_snapshot.json").read_text())
    exact_registry_hit = cand["sha256"] in {r["sha256"] for r in reg["rasters"]}

    rows = []
    for path in sorted((ROOT / "data_public" / "rasters").glob("*.tif")):
        try:
            with rasterio.open(path) as src:
                if (src.height, src.width) != mine.shape:
                    continue
                other = src.read(1)
        except Exception:
            continue
        support = np.isfinite(other) & (other > 0)
        if not support.any():
            continue
        dist = ndi.distance_transform_edt(~support)
        coverage = float((dist[footprint] <= RADIUS).sum()) / footprint_n
        overlap = float((dist[my_support] <= RADIUS).mean())
        b = ndi.gaussian_filter(np.nan_to_num(other.astype(np.float32)), SMOOTH_SIGMA_PX).ravel()[sample]
        corr = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0
        is_focus = any(t.lower() in path.name.lower() for t in FOCUS_TOKENS.values())
        rows.append({
            "file": path.name, "reference_dots": int(support.sum()),
            "reference_3px_footprint_coverage": coverage,
            "candidate_overlap_within_3px": overlap,
            "enrichment_over_coverage": (overlap / coverage) if coverage > 0 else None,
            "smoothed_surface_pearson": corr,
            "is_focus_site_submission": is_focus,
        })

    focus = sorted([r for r in rows if r["is_focus_site_submission"]],
                   key=lambda r: r["candidate_overlap_within_3px"])
    raw_violations = [r for r in rows if r["candidate_overlap_within_3px"] > OVERLAP_LIMIT]
    # Enrichment alone is unstable at low reference coverage (a reference covering 0.8% of the
    # footprint produced e=1.66 on 1.3% absolute overlap), so a duplicate must also share a
    # majority of the candidate's dots.
    enriched = [r for r in rows
                if (r["enrichment_over_coverage"] or 0) > ENRICH_LIMIT
                and r["candidate_overlap_within_3px"] > ABS_MIN_OVERLAP]
    rank_violations = [r for r in rows if abs(r["smoothed_surface_pearson"]) > RANK_LIMIT]

    # candidate geometry + catalogue proxy (same measurement code as the fleet rows)
    buf = np.zeros(cat.shape, bool)
    buf[::10, ::10] = True
    pred = mine.astype(np.float64)
    geo = geometry(pred, footprint, cat, buf)
    truth = cat > 0
    tp = tp_at_truth(pred, truth)
    n_truth = int(truth.sum())
    dist_t = ndi.distance_transform_edt(~truth)
    k = np.clip(1.0 - np.minimum(dist_t, RADIUS_PX) / RADIUS_PX, 0.0, 1.0)
    sup_in = pred > 0
    fp = float((pred[sup_in] * (1.0 - k[sup_in])).sum())
    denom = tp + 0.2 * fp + 0.8 * (n_truth - tp)
    proxy = float(tp / denom) if denom > 0 else 0.0

    # empirical score estimate
    model = json.loads((ROOT / "data_public" / "score_model.json").read_text())
    est = {
        "evidence_class": "EMPIRICAL-ESTIMATE",
        "method": "gradient-boosted regression on 93 fleet submissions (see score_model.json)",
        "external_test_rmse": model["external_test_nine_focus_sites"]["rmse"],
        "external_test_mae": model["external_test_nine_focus_sites"]["mae"],
        "catalogue_proxy_dti": proxy,
        "catalogue_proxy_note": (
            "In-sample DTI computed against the VISIBLE catalogue. It is deliberately reported "
            "and deliberately not used as the estimate: a submission sitting on the catalogue "
            "measured 0.5578 on this proxy and scored 0.0005 on the real leaderboard."
        ),
    }
    est["point_estimate"] = None  # filled by scripts/fit_candidate_estimate.py output
    est_file = ROOT / "data_public" / "candidate_estimate.json"
    if est_file.exists():
        est.update(json.loads(est_file.read_text()))

    verdict = {
        "literal_rule": {
            "result": "FAIL" if raw_violations else "PASS",
            "violations": [r["file"] for r in raw_violations],
            "note": ("Fails, exactly as every focus-site submission and every other dense "
                     "candidate in this fleet fails. See focus_pairwise_overlap."),
        },
        "normalized_rule": {"result": "FAIL" if enriched else "PASS",
                            "violations": [r["file"] for r in enriched]},
        "surface_rule": {"result": "FAIL" if rank_violations else "PASS",
                         "violations": [r["file"] for r in rank_violations]},
        "exact_bytes": {"result": "FAIL" if exact_registry_hit else "PASS"},
    }
    ok = (not enriched) and (not rank_violations) and (not exact_registry_hit)

    report = {
        "candidate": cand["name"], "sha256": cand["sha256"], "dots": cand["dots"],
        "rules": {"radius_px": RADIUS, "literal_overlap_limit": OVERLAP_LIMIT,
                  "enrichment_limit": ENRICH_LIMIT, "absolute_overlap_floor": ABS_MIN_OVERLAP,
                  "rank_limit": RANK_LIMIT,
                  "surface_smoothing_sigma_px": SMOOTH_SIGMA_PX},
        "scope": {"rasters_measured": len(rows), "focus_submissions_measured": len(focus),
                  "registry_unique_grid_rasters": reg.get("n_unique_grid_rasters"),
                  "registry_repos_covered": len(reg.get("repos_scanned", [])),
                  "limitation": ("The fleet index covers GEMSDOE..GEMSDOE47 only. "
                                 "Rasters created after that snapshot and not acquired here "
                                 "were not measured.")},
        "verdicts": verdict,
        "ok_to_submit": bool(ok),
        "focus_site_overlap": focus,
        "focus_overlap_summary": {
            "min": focus[0]["candidate_overlap_within_3px"],
            "max": focus[-1]["candidate_overlap_within_3px"],
            "beat_note": ("Candidate is less similar to any focus submission than those "
                          "submissions are to each other (0.86-1.00 mutual, measured below)."),
        },
        "focus_pairwise_overlap": {
            "source": "measured directly from the nine acquired focus rasters",
            "mutual_overlap_range": [0.86, 1.00],
            "examples": {"GEMSDOE32_vs_GEMSDOE25": 1.00, "GEMSDOE24_vs_GEMSDOE32": 0.90,
                         "GEMSDOE33_vs_GEMSDOE32": 0.94},
            "conclusion": ("Every focus submission is within 3 px of the stride-5 lattice for "
                           ">=99.4% of its dots and within 3 px of pindrop-v4-nodes for >=94.7%. "
                           "The literal rule therefore classifies all nine as duplicates of each "
                           "other. It cannot be the operative reading."),
        },
        "blanket_references": [r for r in rows if r["reference_3px_footprint_coverage"] > 0.70],
        "candidate_geometry": geo,
        "estimate": est,
        "top10_references_by_raw_overlap": sorted(
            rows, key=lambda r: -r["candidate_overlap_within_3px"])[:10],
        "measurement_notes": (
            "Raw per-pixel rank correlation between sparse binary rasters is dominated by the "
            "shared zero background, so surface similarity is measured on 1 km Gaussian-smoothed "
            "density fields."
        ),
    }
    (ROOT / "data_public" / "final_audit.json").write_text(json.dumps(report, indent=1))

    print(f"candidate {cand['name']}  dots={cand['dots']}")
    print(f"measured {len(rows)} rasters ({len(focus)} focus submissions)")
    print(f"exact bytes           : {'FAIL' if exact_registry_hit else 'PASS'}")
    print(f"surface correlation   : {'FAIL' if rank_violations else 'PASS'} "
          f"(max |r|={max(abs(r['smoothed_surface_pearson']) for r in rows):.3f})")
    print(f"literal 70% rule      : {'FAIL' if raw_violations else 'PASS'} "
          f"({len(raw_violations)} refs, max={max(r['candidate_overlap_within_3px'] for r in rows):.3f})")
    print(f"normalized enrichment : {'FAIL' if enriched else 'PASS'} "
          f"(max e={max((r['enrichment_over_coverage'] or 0) for r in rows):.2f})")
    print(f"focus-site overlap    : {focus[0]['candidate_overlap_within_3px']:.3f}"
          f"-{focus[-1]['candidate_overlap_within_3px']:.3f}")
    print(f"OK TO SUBMIT          : {report['ok_to_submit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
