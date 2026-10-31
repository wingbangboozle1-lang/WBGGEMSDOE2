#!/usr/bin/env python3
"""Restore the hash-pinned external-layer mirrors into .cache/external/.

Every file is fetched from the exact repo+ref recorded in
``evidence/external_layers_provenance.json`` and verified against the SHA-256
recorded there.  This is a public owner-mirror transport (same trust level as
``scripts/prepare_data.py``): it is NOT an authenticated organizer or USGS
download.  Nothing here writes to Git-tracked paths.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "evidence" / "external_layers_provenance.json"
DEST = ROOT / ".cache" / "external"

# dem10 channels consumed by src/wbggems/dphs.py (DEM10_SCARP_NAMES + code)
DEM10_NEEDED = {
    "dem10_slope_max", "dem10_steep_ratio_max", "dem10_hgm20_max",
    "dem10_hgm50_max", "dem10_curv_absmax", "dem10_onesided3",
    "dem10_slope_mean", "dem10_valid_frac",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(repo: str, ref: str, remote: str, size: int, target: Path, expected: str) -> None:
    if target.is_file() and target.stat().st_size == size and digest(target) == expected:
        print(f"[ok] cached {target.relative_to(ROOT)}", flush=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    partial.unlink(missing_ok=True)
    print(f"[fetch] {repo}@{ref[:8]}:{remote} ({size:,} B)", flush=True)
    with partial.open("wb") as out:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{remote}?ref={ref}",
             "-H", "Accept: application/vnd.github.raw+json"],
            stdout=out, stderr=subprocess.PIPE, timeout=900, check=False)
    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"fetch failed: {remote}: {result.stderr.decode(errors='replace')[:200]}")
    got = digest(partial)
    if got != expected or partial.stat().st_size != size:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"hash mismatch for {remote}: got {got} want {expected}")
    partial.replace(target)
    print(f"[ok] verified {target.relative_to(ROOT)}", flush=True)


# provenance records the audit-copy path for the Tiger road raster
REMOTE_PATH_OVERRIDE = {
    "tiger_road_distance_m.tif": "data/external/audit_sources/tiger_road_distance_m.tif",
}


def main() -> int:
    prov = json.loads(PROV.read_text())
    dem10 = prov["dem10_seamless_3dep"]
    n = 0
    for f in prov["files"]:
        name = f["name"]
        remote = REMOTE_PATH_OVERRIDE.get(name, f"data/external/{name}")
        fetch(f["mirror_repo"], f["mirror_ref"], remote,
              f["bytes"], DEST / name, f["sha256"])
        n += 1
    for ch in dem10["channels"]:
        if ch["channel"] not in DEM10_NEEDED:
            continue
        fetch(dem10["mirror_repo"], dem10["mirror_tag"],
              f"{ch['channel']}.f32.npy", ch["bytes"],
              DEST / "dem10" / f"{ch['channel']}.f32.npy", ch["sha256"])
        n += 1
    print(f"[done] {n} external mirror files verified under .cache/external/", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
