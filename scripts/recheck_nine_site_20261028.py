#!/usr/bin/env python3
"""Independent recheck of the candidate TIFs against the nine focus GEMSDOE sites.

Why this exists: the earlier uniqueness numbers were produced from a temp folder
(/tmp/fleet) that no longer exists, so they could not be re-run. This script
re-fetches the nine pinned focus rasters from GitHub, refuses any file whose
SHA-256 differs from registry/focus_sites.json, and recomputes the duplicate
metrics with the same definitions as scripts/gemsdoe_novelty.py:

  R2  fraction of the candidate's positive cells (value > 0) within an inclusive
      3-px Euclidean halo of the site's positive cells (and the reverse);
  R3  Spearman correlation of 1-km (10-cell) uniform-smoothed surfaces on the
      template footprint.

Footprint: the pinned grid template data/official/sample_submission.tif
(5,167,373 finite cells), read exactly as scripts/validate_submission.py does.
Format: calls the shared validator run() unchanged.

Writes evidence/nine_site_recheck_20261028.json. Large downloads stay in the
gitignored data/ tree. Usage:
    python scripts/recheck_nine_site_20261028.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_submission import run as validate_run, SAMPLE_SHA  # noqa: E402

SAMPLE = ROOT / "data/official/sample_submission.tif"
CACHE = ROOT / "data/recheck"
OUT = ROOT / "evidence/nine_site_recheck_20261028.json"
CANDIDATES = [
    "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2-zerooutside.tif",
    "submissions/gems-wbg4-triphysics-ridge-38k-20261028T190000Z-b7c1e4a2.tif",
    "docs/downloads/distal_exp2/wbg2-distal2-natural_oof-38000dots-20261028T170304Z-062373ad-zeros.tif",
    "artifacts/wbg4/wbg4-mc40k-scarprad20-20261028-9f5dbc9b-zeros.tif",
    "docs/downloads/wbg4-sscc-blind-66383dots-20261028T170239Z.tif",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_sites() -> dict[str, Path]:
    pins = json.loads((ROOT / "registry/focus_sites.json").read_text())["sites"]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {}
    for s in pins:
        dest = CACHE / f"{s['site']}.tif"
        if not (dest.is_file() and sha256(dest) == s["sha256"]):
            body = subprocess.run(
                ["gh", "api", "-H", "Accept: application/vnd.github.raw",
                 f"repos/{s['repository']}/contents/{s['path']}?ref={s['ref']}"],
                capture_output=True, check=True).stdout
            dest.write_bytes(body)
        if sha256(dest) != s["sha256"]:
            raise SystemExit(f"STOP: {s['site']} SHA-256 mismatch against registry pin")
        out[s["site"]] = dest
    return out


def load_positive(path: Path, footprint: np.ndarray | None = None):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float32")
        meta = (str(ds.crs), tuple(ds.shape), tuple(ds.transform)[:6])
    a = np.where(np.isfinite(a), a, 0.0).astype("float32")
    a = np.clip(a, 0.0, 1.0)
    return a, meta


def footprint() -> np.ndarray:
    with rasterio.open(SAMPLE) as ds:
        return np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)


def main() -> int:
    if not SAMPLE.is_file() or sha256(SAMPLE) != SAMPLE_SHA:
        print("STOP: grid template missing or hash-mismatched; run scripts/prepare_data.py --fetch first")
        return 2
    fp = footprint()
    sites = fetch_sites()
    site_pos, site_halo, site_sm = {}, {}, {}
    for name, path in sites.items():
        a, _ = load_positive(path)
        pos = a > 0
        site_pos[name] = pos
        site_halo[name] = ndi.distance_transform_edt(~pos) <= 3
        site_sm[name] = ndi.uniform_filter(a, 10)

    # Pairwise: fraction of row-site's dots within 3 px of column-site's dots.
    names = list(sites)
    pairwise = {a: {b: float(site_halo[b][site_pos[a]].mean()) for b in names} for a in names}
    off = [pairwise[a][b] for a in names for b in names if a != b]

    results = []
    for rel in CANDIDATES:
        cand_path = ROOT / rel
        validator = validate_run(cand_path, SAMPLE)
        cand, meta = load_positive(cand_path)
        cpos = cand > 0
        chalo = ndi.distance_transform_edt(~cpos) <= 3
        crank = ndi.uniform_filter(cand, 10)[fp]
        per_site = {}
        for name in names:
            frac_mine = float(site_halo[name][cpos].mean())
            frac_theirs = float(chalo[site_pos[name]].mean())
            rho = float(spearmanr(crank, site_sm[name][fp]).statistic)
            per_site[name] = {"frac_my_dots_within_3px": round(frac_mine, 4),
                              "frac_their_dots_within_3px": round(frac_theirs, 4),
                              "smoothed_spearman": round(rho, 4)}
        worst_halo = max(names, key=lambda n: per_site[n]["frac_my_dots_within_3px"])
        worst_rho = max(names, key=lambda n: abs(per_site[n]["smoothed_spearman"]))
        results.append({
            "file": rel,
            "sha256": sha256(cand_path),
            "bytes": cand_path.stat().st_size,
            "dots": int(cpos.sum()),
            "grid": {"crs": meta[0], "shape": list(meta[1]), "transform": list(meta[2])},
            "validator_ok": bool(validator["ok"]),
            "validator_problems": validator.get("problems", []) + validator.get("supplemental_failures", []),
            "n_nan": int(validator.get("n_nan", -1)),
            "max_frac_my_dots_within_3px": per_site[worst_halo]["frac_my_dots_within_3px"],
            "max_frac_worst_site": worst_halo,
            "max_abs_smoothed_spearman": abs(per_site[worst_rho]["smoothed_spearman"]),
            "max_rho_worst_site": worst_rho,
            "halo_rule_limit": 0.70,
            "rank_rule_limit": 0.90,
            "passes_vs_nine_sites": bool(per_site[worst_halo]["frac_my_dots_within_3px"] <= 0.70
                                         and abs(per_site[worst_rho]["smoothed_spearman"]) <= 0.90),
            "per_site": per_site,
        })

    report = {
        "schema": "wbggems.nine-site-recheck.v1",
        "evidence_class": "MEASURED (re-fetched pinned rasters; sha256 verified against registry/focus_sites.json)",
        "sites": {n: {"sha256": sha256(p), "dots": int(site_pos[n].sum())} for n, p in sites.items()},
        "site_pairwise_fraction_in_3px_halo": pairwise,
        "site_pairwise_min_off_diagonal": round(min(off), 4),
        "site_pairwise_max_off_diagonal": round(max(off), 4),
        "candidates": results,
    }
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)),
                      "site_pairwise_min": report["site_pairwise_min_off_diagonal"],
                      "candidates": [(r["file"].split("/")[-1], r["validator_ok"],
                                      r["max_frac_my_dots_within_3px"], r["max_frac_worst_site"],
                                      r["max_abs_smoothed_spearman"], r["passes_vs_nine_sites"])
                                     for r in results]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
