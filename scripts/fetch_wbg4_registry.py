"""Fetch the registry rasters named in ``data_public/raster_fetch_manifest.json``.

Only public GitHub repositories are read (``api.github.com`` raw media type).
Every downloaded byte is hashed; nothing is written into Git (``data/`` is
ignored).  Used for two purposes only: (1) the duplicate/novelty audit of the
new candidate, (2) a matched-incumbent holdout baseline.  No registry raster is
ever used as an input feature.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "registry"
MANIFEST = ROOT / "data_public" / "raster_fetch_manifest.json"


def fetch(repo: str, path: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with open(tmp, "wb") as fh:
        r = subprocess.run(
            ["gh", "api", f"/repos/{repo}/contents/{path}",
             "-H", "Accept: application/vnd.github.raw"],
            stdout=fh, stderr=subprocess.PIPE,
        )
    if r.returncode != 0 or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        return False
    tmp.rename(dest)
    return True


def main(limit: int | None = None) -> int:
    entries = json.loads(MANIFEST.read_text())
    if limit:
        entries = entries[:limit]
    index, misses = [], []
    for i, e in enumerate(entries, 1):
        dest = OUT / f"{e['site']}__{Path(e['path']).name}"
        ok = fetch(e["repo"], e["path"], dest)
        if not ok:
            misses.append(e)
            continue
        index.append({
            "site": e["site"], "repo": e["repo"], "path": e["path"],
            "local": str(dest.relative_to(ROOT)),
            "bytes": dest.stat().st_size,
            "reported_score": e.get("reported_score"),
            "score_evidence": "USER-REPORTED; not an organizer receipt",
        })
        if i % 10 == 0:
            print(f"{i}/{len(entries)} fetched", flush=True)
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    (OUT / "misses.json").write_text(json.dumps(misses, indent=2) + "\n")
    print(f"ok {len(index)}  miss {len(misses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
