#!/usr/bin/env python3
"""Fetch every registry raster listed in data_public/registry_index_snapshot.json.

Resumable, hash-pinned (SHA-256 from the snapshot), stored under the
Git-ignored data_public/rasters/ tree.  This makes the duplicate-stop scan
approach a *complete accessible scan* of the pinned registry index instead of
the 95-raster subset audited on 2026-10-28.
"""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data_public" / "registry_index_snapshot.json"
OUT = ROOT / "data_public" / "rasters"
STATE = OUT / "_fetch_state.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_blob(repo: str, blob: str) -> bytes:
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/blobs/{blob}", "--jq", ".content"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300, check=False)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace")[:200])
    return base64.b64decode(r.stdout)


def main() -> int:
    snap = json.loads(SNAP.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.is_file() else {"done": {}}
    entries = snap["rasters"]
    t0 = time.time()
    fail = 0
    for i, e in enumerate(entries):
        key = e["sha256"][:16]
        if key in state["done"]:
            continue
        first = e.get("sources", [None])[0] or ""
        repo, _, path = first.partition(":")
        if not repo:
            state["done"][key] = {"status": "no_source"}
            continue
        if "/" not in repo:
            repo = f"buffedlizard55-lab/{repo}"
        try:
            data = fetch_blob(repo, e["blob"])
            if len(data) != e["bytes"] or sha(data) != e["sha256"]:
                raise RuntimeError("bytes/hash mismatch")
            (OUT / f"{key}.tif").write_bytes(data)
            state["done"][key] = {"status": "ok", "file": f"{key}.tif",
                                  "sources": e.get("sources", [])}
        except Exception as exc:  # noqa: BLE001 - log and continue
            fail += 1
            state["done"][key] = {"status": "error", "err": str(exc)[:120],
                                  "sources": e.get("sources", [])}
        if i % 25 == 0:
            STATE.write_text(json.dumps(state, indent=0))
            print(f"[{i+1}/{len(entries)}] ok={sum(1 for v in state['done'].values() if v['status']=='ok')} "
                  f"err={fail} elapsed={time.time()-t0:.0f}s", flush=True)
    STATE.write_text(json.dumps(state, indent=0))
    ok = sum(1 for v in state["done"].values() if v["status"] == "ok")
    print(f"[done] fetched={ok}/{len(entries)} errors={fail} elapsed={time.time()-t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
