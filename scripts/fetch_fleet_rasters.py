#!/usr/bin/env python3
"""Fetch the fleet (owner-mirror) rasters named in the requester's score list.

Provenance: the (site, file, score) rows come from the requester's message
(data_public/fleet_score_claims.csv). Scores are USER-REPORTED: there is no
authenticated organizer submission-page receipt for any of them.

Files are downloaded through the GitHub API (authenticated `gh` session) into
data_public/rasters/. They are research inputs only; they are NOT approved for
submission and they are git-ignored.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_public" / "rasters"
CACHE = ROOT / "data_public" / "_listing_cache"
OWNER = "buffedlizard55-lab"

# requester's site label -> owner repo name
REPO = {
    "GEMSDOE": "GEMSDOE", "GEMSDOE2": "GEMSDOE2", "GEMSDOE3": "GEMSDOE3",
    "GEMSDOE4": "GEMSDOE4", "GEMSDOE7": "7GEMSDOE", "GEMSDOE9": "GEMSDOE9",
    "GEMSDOE10": "GEMSDOE10", "GEMSDOE12": "12GEMSDOE", "GEMSDOE13": "13GEMSDOE",
    "GEMSDOE16": "16GEMSDOE", "GEMSDOE17": "17GEMSDOE", "GEMSDOE18": "18GEMSDOE",
    "GEMSDOE19": "19GEMSDOE", "GEMSDOE20": "20GEMSDOE", "GEMSDOE21": "GEMSDOE21",
    "GEMSDOE22": "GEMSDOE22", "GEMSDOE23": "GEMSDOE23", "GEMSDOE24": "GEMSDOE24",
    "GEMSDOE25": "GEMSDOE25", "GEMSDOE26": "GEMSDOE26", "GEMSDOE27": "GEMSDOE27",
    "GEMSDOE28": "GEMSDOE28", "GEMSDOE28b": "GEMSDOE28", "GEMSDOE29": "GEMSDOE29",
    "GEMSDOE30": "GEMSDOE30", "GEMSDOE31": "GEMSDOE31", "GEMSDOE32": "GEMSDOE32",
    "GEMSDOE33": "GEMSDOE33", "GEMSDOE34": "GEMSDOE34", "GEMSDOE35": "GEMSDOE35",
    "GEMSDOE36": "GEMSDOE36", "GEMSDOE37": "GEMSDOE37", "GEMSDOE38": "GEMSDOE38",
    "GEMSDOE39": "GEMSDOE39", "GEMSDOE40": "GEMSDOE40", "GEMSDOE41": "GEMSDOE41",
    "GEMSDOE42": "42GEMSDOE", "GEMSDOE43": "GEMSDOE43", "GEMSDOE44": "GEMSDOE44",
    "GEMSDOE45": "GEMSDOE45", "GEMSDOE46": "GEMSDOE46", "GEMSDOE47": "GEMSDOE47",
    "GEMSDOE48": "GEMSDOE48", "GEMSDOE49": "GEMSDOE49", "GEMSDOE50": "GEMSDOE50",
    "GEMSDOE51": "GEMSDOE51", "GEMSDOE52": "GEMSDOE52", "GEMSDOE53": "GEMSDOE53",
    "GEMSDOE56": "56GEMSDOE", "GEMSDOE58": "58GEMSDOE", "GEMSDOE59": "59GEMSDOE",
    "GEMSDOE61": "61GEMSDOE", "GEMSDOE62": "62GEMSDOE", "GEMSDOE63": "GEMSDOE63",
    "GEMSDOE64": "GEMSDOE64", "GEMSDOE65": "GEMSDOE65", "GEMSDOE66": "GEMSDOE66",
    "GEMSDOE67": "GEMSDOE67", "GEMSDOE68": "GEMSDOE68", "GEMSDOE69": "GEMSDOE69",
    "GEMSDOE70": "GEMSDOE70", "GEMSDOE71": "GEMSDOE71", "GEMSDOE72": "GEMSDOE72",
    "GEMSDOE73": "GEMSDOE73", "GEMSDOE74": "GEMSDOE74", "GEMSDOE75": "GEMSDOE75",
    "GEMSDOE76": "GEMSDOE76", "GEMSDOE77": "GEMSDOE77", "GEMSDOE78": "GEMSDOE78",
    "GEMSDOE79": "GEMSDOE79", "GEMSDOE80": "GEMSDOE80", "GEMSDOE83": "GEMSDOE83",
    "GEMSDOE85": "GEMSDOE85", "GEMSDOE87": "GEMSDOE87", "GEMSDOE90": "GEMSDOE90",
    "GEMSDOE91": "GEMSDOE91",
}


def gh_api(path: str, raw: bool = False) -> bytes:
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github.raw", path] if raw else ["gh", "api", path]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode()[:400])
    return res.stdout


def listing(repo: str) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{repo}.json"
    if f.exists():
        return json.loads(f.read_text())
    try:
        data = json.loads(gh_api(f"repos/{OWNER}/{repo}/contents/docs/downloads"))
    except RuntimeError:
        data = []
    if isinstance(data, dict):
        data = []
    rows = [{"name": d["name"], "path": d["path"], "size": d["size"]} for d in data]
    f.write_text(json.dumps(rows))
    return rows


def _hash_token(stem: str) -> str | None:
    toks = [t for t in re.split(r"[-_.]", stem) if re.fullmatch(r"[0-9a-f]{8,14}", t)]
    return toks[-1] if toks else None


def pick(rows: list[dict], stem: str) -> dict | None:
    """Match a requester-supplied file stem to a real docs/downloads entry.

    Variants of the same surface (-nan / -zeros / -allfinite / -nanoutside)
    share in-footprint geometry, so any variant is acceptable for statistics.
    Preference order favours portal-legal -zeros, then plain, then others.
    """
    tifs = [r for r in rows if r["name"].lower().endswith(".tif")]
    def base(n: str) -> str:
        return n.rsplit(".", 1)[0]
    def preference(r):
        n = r["name"]
        return (0 if n.endswith("-zeros.tif") else 1 if "-nan" not in n and "-allfinite" not in n else 2,
                len(n))
    tok = _hash_token(stem)
    cands: list[dict] = []
    if tok:
        cands = [r for r in tifs if tok in r["name"]]
    if not cands:
        cands = [r for r in tifs if base(r["name"]) == stem]
    if not cands:
        core = stem
        for suf in ("-zeros", "-nan", "-allfinite", "-nanoutside", "-zero", "-hard", "-candidate"):
            if core.endswith(suf):
                core = core[: -len(suf)]
        cands = [r for r in tifs if core in base(r["name"]) or base(r["name"]) in core]
    if not cands:
        key = stem[:24]
        cands = [r for r in tifs if key in r["name"]]
    return sorted(cands, key=preference)[0] if cands else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / "data_public" / "fleet_score_claims.csv").open()))
    manifest, misses = [], []
    for row in rows:
        site, stem, score = row["site"], row["file_stem"], row["reported_score"]
        if not score:
            continue
        repo = REPO.get(site)
        if repo is None:
            misses.append({"site": site, "file_stem": stem, "reason": "no repo mapping"})
            continue
        try:
            rows_ = listing(repo)
        except RuntimeError as exc:  # pragma: no cover
            misses.append({"site": site, "file_stem": stem, "reason": f"listing failed: {exc}"})
            continue
        hit = pick(rows_, stem)
        if hit is None:
            misses.append({"site": site, "file_stem": stem, "reason": "not found in docs/downloads"})
            continue
        dest = OUT / f"{site}__{hit['name']}"
        if not dest.exists() or dest.stat().st_size != hit["size"]:
            try:
                blob = gh_api(f"repos/{OWNER}/{repo}/contents/{hit['path']}", raw=True)
            except RuntimeError as exc:  # pragma: no cover
                misses.append({"site": site, "file_stem": stem, "reason": f"fetch failed: {exc}"})
                continue
            dest.write_bytes(blob)
        manifest.append({
            "site": site, "repo": f"{OWNER}/{repo}", "path": hit["path"],
            "local": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size,
            "file_stem_requested": stem, "reported_score": float(score),
            "score_evidence": "USER-REPORTED; no organizer receipt",
        })
        print(f"{site:12s} {hit['name'][:70]:70s} {score}", flush=True)
    (ROOT / "data_public" / "raster_fetch_manifest.json").write_text(json.dumps(manifest, indent=1))
    (ROOT / "data_public" / "raster_fetch_misses.json").write_text(json.dumps(misses, indent=1))
    print(f"\nfetched {len(manifest)}  missed {len(misses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
