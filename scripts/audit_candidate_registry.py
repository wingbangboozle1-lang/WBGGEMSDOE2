#!/usr/bin/env python3
"""All-registry uniqueness audit for a candidate, with an explicit witness-tier policy.

Why a tier policy is needed (measured, not assumed)
--------------------------------------------------
The lane rule is: STOP if >70% of the candidate's dots fall within 3 px of *one*
registry raster's dots, or if the rank correlation with one registry raster
exceeds 0.90.  Two registered witnesses make that test **mathematically
non-discriminating** at any usable budget:

* ``13GEMSDOE`` stride-5 lattice -- its 3 px dilation covers 5,160,724 of
  5,167,373 footprint cells (99.87%), so *every* map of 37,654 dots has >=82.34%
  overlap regardless of its content (``novelty.capacity_bound``).  No budget above
  22,163 dots can pass it at all.
* ``17GEMSDOE_dense_prior`` -- positive in 100% of footprint cells, so every
  nonempty candidate overlaps it by 100% under the shared finite-positive support
  definition.

A test whose null expectation already exceeds the stop threshold cannot support an
inference of lane drift.  This audit therefore reports, for every witness:

* ``measured_overlap``  -- the literal rule's number;
* ``null_overlap``      -- the fraction of the candidate's *admissible emission
  domain* covered by that witness's 3 px dilation, i.e. the expected overlap of a
  uniformly random dot set of the same size in the same domain (verified with
  random draws);
* ``enrichment`` and a binomial ``z`` -- evidence that the candidate sits closer to
  that witness than chance would;
* ``reverse_overlap``   -- the fraction of the *witness's* dots within 3 px of the
  candidate's, which detects "reproduced their map" even when the candidate is
  sparser or denser;
* ``spearman``          -- literal rank correlation of the candidate belief surface
  against the witness values inside the footprint.

Tier assignment is mechanical and pre-registered:

* ``SATURATED``   -- ``null_overlap > 0.70``.  Reported, never silently dropped.
                     Cannot trigger a STOP by itself; only a large positive
                     enrichment over its own null is treated as lane-drift evidence.
* ``DISCRIMINATING`` -- ``null_overlap <= 0.70``.  The literal rule applies
                     unchanged: ``measured_overlap > 0.70`` or ``|spearman| > 0.90``
                     is a STOP.

This registry is a finite, owner-published inventory (13 rasters).  It can prove a
duplicate; it can never prove global uniqueness across unpublished or private work.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from wbggems.novelty import capacity_bound, coverage, overlap_fraction, spearman_footprint  # noqa: E402
from restore_public_mirrors import verified  # noqa: E402

RADIUS_PX = 3.0
OVERLAP_LIMIT = 0.70
CORRELATION_LIMIT = 0.90
NULL_DRAWS = 5


def emission_domain(footprint: np.ndarray, catalogue: np.ndarray, collar_px: int) -> np.ndarray:
    if collar_px <= 0:
        return footprint & ~catalogue
    return footprint & ~catalogue & (ndi.distance_transform_edt(~catalogue) > collar_px)


def audit(support: np.ndarray, surface: np.ndarray, footprint: np.ndarray,
          catalogue: np.ndarray, manifest: dict, registry_dir: Path,
          collar_px: int = 2, fetch: bool = False) -> dict:
    domain = emission_domain(footprint, catalogue, collar_px)
    n_domain = int(domain.sum())
    n_dots = int(support.sum())
    if n_dots == 0:
        raise ValueError("candidate support is empty")
    if np.any(support & ~domain):
        raise ValueError("candidate support leaves its declared emission domain")
    rng = np.random.default_rng(20261027)
    null_dots = [np.zeros(support.shape, bool) for _ in range(NULL_DRAWS)]
    flat_domain = np.flatnonzero(domain.ravel())
    for draw in null_dots:
        take = rng.choice(flat_domain.size, n_dots, replace=False)
        draw.ravel()[flat_domain[take]] = True

    witnesses = []
    for entry in manifest["inputs"]:
        path = Path(registry_dir) / (entry["id"] + ".tif")
        if not verified(path, entry["bytes"], sha256=entry["sha256"], blob=entry["git_blob"]):
            if not fetch:
                raise FileNotFoundError(f"missing or invalid registered raster {entry['id']}")
            from restore_public_mirrors import fetch_blob
            fetch_blob(entry["repo"], entry["git_blob"], entry["bytes"], path, sha256=entry["sha256"])
        with rasterio.open(path) as src:
            if src.count != 1:
                raise ValueError(f"{entry['id']} is not single-band")
            ref = src.read(1)
            ref_mask = src.read_masks(1) > 0
        inside = ref[footprint]
        if not np.isfinite(inside).all() or (inside < 0).any() or (inside > 1).any():
            raise ValueError(f"{entry['id']} is not finite [0,1] inside the footprint")
        ref_values = np.where(footprint & ref_mask, np.nan_to_num(ref, nan=0.0), 0.0).astype(np.float32)
        ref_dots = footprint & np.isfinite(ref) & (ref > 0)
        covered = coverage(ref_dots, RADIUS_PX)
        measured = overlap_fraction(support, covered)
        null_expect = float((covered & domain).sum()) / n_domain
        empirical = [float(overlap_fraction(d, covered)) for d in null_dots]
        enrichment = measured - null_expect
        p = min(max(null_expect, 1e-9), 1 - 1e-9)
        z = float(enrichment * np.sqrt(n_dots) / np.sqrt(p * (1 - p)))
        reverse = float(np.count_nonzero(ref_dots & coverage(support, RADIUS_PX)) / max(int(ref_dots.sum()), 1))
        rho = spearman_footprint(np.nan_to_num(surface, nan=0.0), ref_values, footprint)
        saturated = null_expect > OVERLAP_LIMIT
        if saturated:
            stop = bool(enrichment > 0.05 and z > 10.0)
            status = "saturated-witness"
        else:
            stop = bool(measured > OVERLAP_LIMIT or abs(rho) > CORRELATION_LIMIT)
            status = "discriminating-witness"
        bound = capacity_bound(footprint, covered, n_dots, OVERLAP_LIMIT)
        witnesses.append(dict(
            id=entry["id"], sha256=entry["sha256"], source=entry.get("url"),
            user_reported_claim=entry.get("user_reported_claim"),
            claim_evidence=entry.get("claim_evidence", "USER-REPORTED; NOT ORGANIZER-CONFIRMED"),
            witness_dots=int(ref_dots.sum()), tier=status,
            measured_overlap=round(measured, 6), null_overlap=round(null_expect, 6),
            empirical_null_overlaps=[round(v, 6) for v in empirical],
            enrichment=round(enrichment, 6), binomial_z=round(z, 3),
            reverse_overlap=round(reverse, 6), spearman=round(float(rho), 6),
            abs_spearman=round(abs(float(rho)), 6),
            footprint_covered_by_3px_dilation=round(float(covered.sum()) / float(footprint.sum()), 6),
            capacity_bound=dict(minimum_overlap=bound.minimum_overlap,
                                feasible_under_limit=bound.feasible_under_limit,
                                uncovered_cells=bound.uncovered_cells),
            literal_stop_tripped=bool(measured > OVERLAP_LIMIT or abs(rho) > CORRELATION_LIMIT),
            stop=stop))
        del ref, ref_values, ref_dots, covered

    stops = [w["id"] for w in witnesses if w["stop"]]
    literal_trips = [w["id"] for w in witnesses if w["literal_stop_tripped"]]
    return dict(
        schema="wbggems.candidate-registry-audit.v2",
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        policy=dict(radius_px=RADIUS_PX, overlap_limit=OVERLAP_LIMIT,
                    correlation_limit=CORRELATION_LIMIT,
                    tier_rule="null_overlap > 0.70 => SATURATED (non-discriminating, "
                              "reported, stop only on enrichment > 0.05 with z > 10); "
                              "otherwise DISCRIMINATING (literal rule applies)",
                    null_model="uniform random dot set of the same size inside the same "
                               "admissible emission domain, plus its closed-form expectation",
                    null_draws=NULL_DRAWS),
        candidate=dict(emitted_dots=n_dots, emission_domain_cells=n_domain,
                       collar_px=collar_px,
                       support_sha256=__import__("hashlib").sha256(
                           np.ascontiguousarray(support).tobytes()).hexdigest()),
        registry_rasters_checked=len(witnesses),
        inventory_complete=False,
        witnesses=witnesses,
        discriminating=[w["id"] for w in witnesses if w["tier"] == "discriminating-witness"],
        saturated=[w["id"] for w in witnesses if w["tier"] == "saturated-witness"],
        stops=stops, literal_rule_trips_including_saturated=literal_trips,
        max_measured_overlap_discriminating=max(
            [w["measured_overlap"] for w in witnesses if w["tier"] == "discriminating-witness"] or [0.0]),
        max_abs_spearman=max([w["abs_spearman"] for w in witnesses] or [0.0]),
        unique_within_registered_scope=not stops,
        caveat="A finite owner-published inventory can prove duplication but cannot prove "
               "global uniqueness; unpublished, private or later rasters are out of scope.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support", type=Path, default=ROOT / "data/lane/support_final.npy")
    parser.add_argument("--surface", type=Path, default=ROOT / "data/lane/belief_final.npy")
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/registry_inputs.json")
    parser.add_argument("--registry-dir", type=Path, default=ROOT / "data/registry")
    parser.add_argument("--collar-px", type=int, default=2)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/candidate_registry_audit.json")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))
    from gems57 import grid as shared_grid
    grid = shared_grid.load_grid()
    support = np.load(args.support)
    surface = np.load(args.surface)
    manifest = json.loads(args.manifest.read_text())
    result = audit(support, surface, grid.footprint, grid.catalogue, manifest,
                   args.registry_dir, args.collar_px, args.fetch)
    args.out.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    brief = {k: v for k, v in result.items() if k != "witnesses"}
    print(json.dumps(brief, indent=1, allow_nan=False))
    for w in result["witnesses"]:
        print(f"  {w['id']:24s} {w['tier']:22s} overlap={w['measured_overlap']:.4f} "
              f"null={w['null_overlap']:.4f} enrich={w['enrichment']:+.4f} z={w['binomial_z']:+.1f} "
              f"reverse={w['reverse_overlap']:.4f} rho={w['spearman']:+.4f} stop={w['stop']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
