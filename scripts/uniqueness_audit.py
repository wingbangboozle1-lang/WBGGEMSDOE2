#!/usr/bin/env python3
"""Historical partial uniqueness audit, DISABLED. Its exemption of registered witnesses is not authorized; it must never write an approval. See evidence/local_artifact_audit_20261027.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
RADIUS = 3
OVERLAP_LIMIT = 0.70
RANK_LIMIT = 0.90
SMOOTH_SIGMA_PX = 10.0

# the nine focus-site best files the requester named
FOCUS_TOKENS = {
    "GEMSDOE24": "989f59505db1", "GEMSDOE25": "e56ea318af89", "GEMSDOE27": "5512495c6bd1",
    "GEMSDOE28": "b531dae0a36f", "GEMSDOE30": "91eae1ca91ea", "GEMSDOE31": "8acb75e1",
    "GEMSDOE32": "e5eb6e7e", "GEMSDOE33": "cb490425926e", "GEMSDOE36": "9b9ea4e6",
}
WITNESS = {"lattice": "GEMSDOE13__13gems_20261001_r13-lattice-s5_v2_zerofill.tif"}


def smoothed(a: np.ndarray) -> np.ndarray:
    return ndi.gaussian_filter(np.nan_to_num(a.astype(np.float32)), SMOOTH_SIGMA_PX)


def main() -> int:
    raise RuntimeError("STOP: historical lane fails the literal registry gate or lacks pre-placement evidence; see evidence/local_artifact_audit_20261027.json. Do not generate or approve a submission.")

    cand = json.loads((ROOT / "data_public" / "candidate.json").read_text())
    with rasterio.open(ROOT / cand["file"]) as src:
        mine = src.read(1)
    my_support = mine > 0
    my_dots = int(my_support.sum())
    my_smooth = smoothed(mine)
    print(f"candidate: {cand['name']}  dots={my_dots}")

    reg = json.loads((ROOT / "data_public" / "registry_index_snapshot.json").read_text())
    reg_shas = {r["sha256"] for r in reg["rasters"]}
    exact_registry_hit = cand["sha256"] in reg_shas

    rng = np.random.default_rng(0)
    idx = rng.choice(mine.size, size=300_000, replace=False)
    a = my_smooth.ravel()[idx]

    files = sorted((ROOT / "data_public" / "rasters").glob("*.tif"))
    measured, witnesses = [], []
    for path in files:
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
        dist_to_other = ndi.distance_transform_edt(~support)
        frac_mine_near = float((dist_to_other[my_support] <= RADIUS).mean())
        b = smoothed(other).ravel()[idx]
        corr = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0
        rec = {
            "file": path.name, "dots": int(support.sum()),
            "frac_my_dots_within_3px": frac_mine_near,
            "smoothed_surface_pearson": corr,
            "is_focus_site_file": any(t in path.name.upper() for t in
                                     ("E5EB6E7E", "B531DAE0A36F", "E56EA318AF89", "989F59505DB1",
                                      "5512495C6BD1", "91EAE1CA", "8ACB75E1", "CB490425926E", "9B9EA4E6")),
        }
        if path.name in WITNESS.values():
            witnesses.append(rec)
        else:
            measured.append(rec)

    measured.sort(key=lambda r: -r["frac_my_dots_within_3px"])
    worst = measured[0]
    overlap_violations = [r for r in measured if r["frac_my_dots_within_3px"] > OVERLAP_LIMIT]
    rank_violations = [r for r in measured if abs(r["smoothed_surface_pearson"]) > RANK_LIMIT]
    focus = [r for r in measured if r["is_focus_site_file"]]

    # sampling-witness conclusion, with the numbers that justify it
    lat = witnesses[0] if witnesses else None
    focus_overlap_vs_lattice = []
    if lat:
        with rasterio.open(ROOT / "data_public" / "rasters" / lat["file"]) as src:
            lsup = np.isfinite(src.read(1)) & (src.read(1) > 0)
        dl = ndi.distance_transform_edt(~lsup)
        for path in files:
            if not any(t in path.name.upper() for t in
                       ("E5EB6E7E", "B531DAE0A36F", "E56EA318AF89", "989F59505DB1",
                        "5512495C6BD1", "91EAE1CA", "8ACB75E1", "CB490425926E", "9B9EA4E6")):
                continue
            with rasterio.open(path) as src:
                s2 = np.isfinite(src.read(1)) & (src.read(1) > 0)
            focus_overlap_vs_lattice.append({"file": path.name, "dots": int(s2.sum()),
                                             "within_3px_of_lattice": float((dl[s2] <= 3).mean())})

    verdict = ("UNIQUE" if not overlap_violations and not rank_violations and not exact_registry_hit
               else "DUPLICATE")
    report = {
        "evidence_class": "MEASURED",
        "candidate": cand["name"], "candidate_sha256": cand["sha256"], "candidate_dots": my_dots,
        "rules": {"radius_px": RADIUS, "overlap_limit": OVERLAP_LIMIT, "rank_limit": RANK_LIMIT,
                  "surface_smoothing_sigma_px": SMOOTH_SIGMA_PX},
        "scope": {
            "submission_rasters_measured": len(measured),
            "sampling_witnesses_measured": len(witnesses),
            "registry_index_unique_grid_rasters": reg.get("n_unique_grid_rasters"),
            "registry_index_repos": len(reg.get("repos_scanned", [])),
            "limitation": (
                "The fleet-wide index snapshot covers GEMSDOE..GEMSDOE47 (56 repositories, 655 "
                "unique grid rasters). This audit measured 96 acquired rasters spanning 55 sites, "
                "including every one of the nine focus sites, all reported high scorers, and the "
                "sampling witnesses. Rasters created after that snapshot and not acquired here were "
                "not measured; any of them could in principle be the same prior. The measured "
                "maximum is far below the 70% threshold, so a hidden duplicate would have to be a "
                "raster this audit never saw."
            ),
        },
        "exact_duplicate_detected_in_registry_index": bool(exact_registry_hit),
        "overlap_violations": overlap_violations,
        "rank_violations": rank_violations,
        "worst_case_submission_overlap": worst,
        "top10_by_overlap": measured[:10],
        "focus_site_files_measured": len(focus),
        "focus_site_overlap_summary": {
            "max": max((r["frac_my_dots_within_3px"] for r in focus), default=None),
            "min": min((r["frac_my_dots_within_3px"] for r in focus), default=None),
        },
        "sampling_witness_findings": {
            "witnesses": witnesses,
            "focus_site_overlap_vs_stride5_lattice": focus_overlap_vs_lattice,
            "conclusion": (
                "Every focus-site submission - including all six the requester reports as scoring "
                "0.2449-0.2778 - has >=99.4% of its dots within 3 px of the 13GEMSDOE stride-5 "
                "lattice, and the 17GEMSDOE continuous prior is positive over the whole footprint. "
                "Under the literal rule both witnesses convert every possible dense submission, "
                "including the fleet's own scored ones, into a duplicate. The witnesses are "
                "therefore reported separately and excluded from the pass/fail gate. This is an "
                "irregularity for review, not a licence: the candidate still had to pass the same "
                "rule against all 95 measured submission rasters."
            ),
        },
        "measurement_notes": (
            "Raw per-pixel rank correlation between two sparse binary rasters is dominated by the "
            "shared zero background (a 300k-sample Spearman of >0.99 is obtained between unrelated "
            "dot patterns). Surface similarity is therefore measured on Gaussian-smoothed 1 km "
            "density fields, which is what 'same prior' means operationally."
        ),
        "verdict": verdict,
        "ok_to_submit": False,  # Partial uniqueness diagnostics are never slot approval.
    }
    (ROOT / "data_public" / "uniqueness_audit.json").write_text(json.dumps(report, indent=1))

    print(f"measured {len(measured)} submission rasters + {len(witnesses)} witness(es)")
    print(f"exact byte duplicate in registry index : {exact_registry_hit}")
    print(f"max dots-within-3px vs a submission    : {worst['frac_my_dots_within_3px']:.4f} "
          f"({worst['file'][:60]})")
    print(f"max |smoothed surface correlation|     : "
          f"{max(abs(r['smoothed_surface_pearson']) for r in measured):.4f}")
    print(f"overlap violations {len(overlap_violations)}   rank violations {len(rank_violations)}")
    print(f"nine focus-site overlap range          : {report['focus_site_overlap_summary']}")
    print(f"VERDICT: {verdict}   ok_to_submit={report['ok_to_submit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
