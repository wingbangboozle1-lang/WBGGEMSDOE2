#!/usr/bin/env python3
"""Fetch a read-only official public-leaderboard snapshot for the static site.

The snapshot is not a submission-page receipt, a candidate score, or a forecast.
Failures replace the output with an explicit unavailable state rather than retaining
an old value as if it were current. No authentication or submission is attempted.
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
MAX_BYTES = 4_000_000


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table is None:
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def parse_top(html: str) -> str:
    parser = TableParser()
    parser.feed(html)
    candidates = []
    for table in parser.tables:
        if len(table) < 2:
            continue
        header = " ".join(table[0]).lower()
        if "rank" not in header or "public" not in header or "tversky" not in header:
            continue
        for row in table[1:]:
            if row and re.fullmatch(r"\s*#?\s*1\s*", row[0]):
                # Require a single unambiguous cell that is a decimal in [0, 1].
                matches = [cell.strip() for cell in row[1:]
                           if re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", cell.strip())]
                if len(matches) == 1:
                    candidates.append(matches[0])
                break
    if len(candidates) != 1:
        raise ValueError("No unique rank-one public Tversky observation found")
    return candidates[0]


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "WBGGEMSDOE2-public-snapshot/1.0", "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=30) as response:
        final = urlsplit(response.geturl())
        original = urlsplit(URL)
        if (final.scheme, final.netloc, final.path) != (original.scheme, original.netloc, original.path):
            raise ValueError("Unexpected redirect; public leaderboard not available")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Unexpectedly large response")
        return data.decode("utf-8", errors="strict")


def snapshot(html: str | None = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    try:
        value = parse_top(fetch() if html is None else html)
        return {"schema": "wbggems.public-leaderboard.v1", "checked_utc": now, "source": URL,
                "status": "ok", "top_public_dti": value,
                "evidence_class": "Official public leaderboard observation, not a submission-page receipt or candidate score"}
    except (OSError, UnicodeError, ValueError, http.client.HTTPException) as exc:
        return {"schema": "wbggems.public-leaderboard.v1", "checked_utc": now, "source": URL,
                "status": "unavailable", "top_public_dti": None, "error": str(exc)[:240],
                "evidence_class": "No verified current observation"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/data/leaderboard.json"))
    args = parser.parse_args()
    result = snapshot()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "ok":
        print("Refresh unavailable; the site will show an unavailable status.", file=sys.stderr)
    # An unavailable feed must not prevent deploying the fail-closed site.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
