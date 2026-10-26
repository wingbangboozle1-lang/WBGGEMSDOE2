#!/usr/bin/env python3
"""Fetch the official public leaderboard; keep and clearly mark a stale snapshot on failure."""
from __future__ import annotations
import argparse
import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = 0
        self.row = None
        self.cell = None
        self.rows = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if not self.in_table:
                self.rows = []
            self.in_table += 1
        if self.in_table and tag == "tr":
            self.row = []
        if self.row is not None and tag in ("td", "th"):
            self.cell = []
        if self.cell is not None and tag in ("br", "p", "div"):
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.cell is not None and tag in ("td", "th"):
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "table" and self.in_table:
            self.in_table -= 1
            if not self.in_table:
                self.tables.append(self.rows)


def parse_top(html: str) -> tuple[float, str | None]:
    parser = TableRows()
    parser.feed(html)
    candidates = []
    for table in parser.tables:
        if not table:
            continue
        headers = [cell.lower() for cell in table[0]]
        rank_columns = [i for i, cell in enumerate(headers) if 'rank' in cell]
        score_columns = [i for i, cell in enumerate(headers) if 'public' in cell and 'tversky' in cell]
        if len(rank_columns) != 1 or len(score_columns) != 1:
            continue
        rank_col, score_col = rank_columns[0], score_columns[0]
        for row in table[1:]:
            if len(row) <= max(rank_col, score_col) or not re.fullmatch(r"#?\s*1", row[rank_col].strip()):
                continue
            cell = row[score_col].strip()
            if re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", cell):
                # Do not infer a username from a layout that may change.
                candidates.append(float(cell))
    if len(candidates) == 1:
        return candidates[0], None
    raise ValueError("No unambiguous rank-one public DTI row found; page layout may have changed")


def load_previous(output: Path, cache: Path | None = None) -> dict:
    """Prefer a valid last-known observation; a corrupt cache cannot break publishing."""
    for path in (cache, output):
        if path is None:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            score = value.get("top_public_dti")
            captured = value.get("captured_utc")
            if (isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1
                    or not isinstance(captured, str) or not captured.strip()
                    or (value.get("source_url") is not None and value["source_url"] != URL)):
                continue
            parsed = dt.datetime.fromisoformat(captured.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                continue
            return value
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return {}


def refresh(output: Path, cache: Path | None = None) -> bool:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    previous = load_previous(output, cache)
    try:
        req = Request(URL, headers={"User-Agent": "WBGGEMSDOE2/1.0 public leaderboard monitor"})
        with urlopen(req, timeout=25) as response:
            parsed = urlparse(response.geturl())
            if parsed.scheme != "https" or parsed.hostname != "www.drivendata.org":
                raise ValueError("Leaderboard redirected outside the official host")
            body = response.read(4_000_001)
            if len(body) > 4_000_000:
                raise ValueError("Unexpectedly large leaderboard response")
            html = body.decode("utf-8", errors="strict")
        value, participant = parse_top(html)
        data = {"evidence_class": "OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT", "source_url": URL,
                "captured_utc": now, "last_attempt_utc": now, "status": "fresh",
                "top_public_dti": value, "top_participant": participant,
                "note": "Official public leaderboard; not a receipt for any project raster. Values can change."}
        ok = True
    except Exception as error:
        # Keep the last genuine observation, never relabel it as freshly observed.
        data = dict(previous)
        data.update(evidence_class="OFFICIAL-PUBLIC-LEADERBOARD-SNAPSHOT", source_url=URL,
                    last_attempt_utc=now, status="stale",
                    last_error=f"{type(error).__name__}: {str(error)[:240]}",
                    note="Refresh failed; showing the last successful observation if present, not a live value.")
        ok = False
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(output)
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache_temp = cache.with_suffix(cache.suffix + ".tmp")
        cache_temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        cache_temp.replace(cache)
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "docs/data/leaderboard.json")
    p.add_argument("--cache", type=Path, help="optional last-known observation across scheduled builds")
    args = p.parse_args()
    if refresh(args.output, args.cache):
        print("Official public leaderboard snapshot refreshed.")
    else:
        print("WARNING: leaderboard refresh failed; the snapshot is explicitly stale.", file=sys.stderr)
    # Stale data is still publishable as stale; it is never labeled live.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
