#!/usr/bin/env python3
"""Preserve the last public leaderboard observation across Pages builds.

The Actions cache is only a dated fallback, not a source of organizer receipts.
A restored snapshot is explicitly stale until the official endpoint is fetched
again. Invalid, future-dated, older, and contradictory cache entries are ignored.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path

from refresh_leaderboard import PARTIAL_URL, ROOT, URL

EVIDENCE = "OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT"
DEFAULT_CACHE = ROOT / ".cache/feed-state/leaderboard.json"
DEFAULT_OUTPUT = ROOT / "docs/data/leaderboard.json"
MAX_BYTES = 1_000_000


def validate_observation(data: dict, *, now: dt.datetime | None = None) -> dt.datetime:
    """Return the UTC capture time, or reject an untrustworthy snapshot shape."""
    if not isinstance(data, dict) or data.get("evidence_class") != EVIDENCE or data.get("source_url") != URL:
        raise ValueError("not a project official-public leaderboard snapshot")
    if data.get("data_url", PARTIAL_URL) != PARTIAL_URL:
        raise ValueError("unexpected leaderboard data URL")
    if data.get("status") not in ("fresh", "stale"):
        raise ValueError("invalid observation status")
    value = data.get("top_public_dti")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("invalid public leaderboard value")
    stamp = data.get("captured_utc")
    if not isinstance(stamp, str):
        raise ValueError("missing capture timestamp")
    try:
        captured = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid capture timestamp") from exc
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("capture timestamp must include a timezone")
    captured = captured.astimezone(dt.timezone.utc)
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("current time must include a timezone")
    if captured > current.astimezone(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ValueError("capture timestamp is in the future")
    return captured


def read_observation(path: Path, *, now: dt.datetime | None = None) -> tuple[dict, dt.datetime] | None:
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data, validate_observation(data, now=now)
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        return None


def write_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def restore(cache: Path, output: Path, *, now: dt.datetime | None = None) -> bool:
    """Restore a strictly newer valid cache as STALE; never rewrite an older one."""
    previous = read_observation(cache, now=now)
    if previous is None:
        return False
    current = read_observation(output, now=now)
    if current is not None and previous[1] <= current[1]:
        return False
    snapshot = dict(previous[0])
    snapshot.update(status="stale",
                    note="Restored prior public snapshot; stale until this build refreshes the official page.")
    write_atomic(output, snapshot)
    return True


def save(output: Path, cache: Path, *, now: dt.datetime | None = None) -> bool:
    """Cache a valid observation unless a newer or contradictory one is present."""
    current = read_observation(output, now=now)
    if current is None:
        return False
    previous = read_observation(cache, now=now)
    if previous is not None:
        if previous[1] > current[1]:
            return False
        if previous[1] == current[1] and previous[0]["top_public_dti"] != current[0]["top_public_dti"]:
            return False
    write_atomic(cache, current[0])
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("restore", "save"))
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    changed = (restore(args.cache, args.output) if args.operation == "restore"
               else save(args.output, args.cache))
    print(f"Leaderboard cache {args.operation}: {'updated' if changed else 'no usable newer state'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
