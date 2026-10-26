#!/usr/bin/env python3
"""Refresh public leaderboard and nine-site commit status for a Pages build.

A failed or unparseable fetch preserves the dated fallback, marks it stale, and
never publishes a fabricated value. It does not log or store GitHub tokens.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
API_ROOT = "https://api.github.com"


class Tables(HTMLParser):
    """Extract top-level table rows as text; no assumptions about CSS classes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
        elif self.depth == 1:
            if tag == "tr":
                self.row = []
            elif tag in ("td", "th") and self.row is not None:
                self.cell = []
            elif tag in ("br", "p", "div") and self.cell is not None:
                self.cell.append(" ")

    def handle_data(self, data):
        if self.depth == 1 and self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "table":
            if self.depth == 1 and self.table is not None:
                self.tables.append(self.table)
                self.table = None
            self.depth = max(0, self.depth - 1)
        elif self.depth == 1:
            if tag in ("td", "th") and self.cell is not None and self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
                self.cell = None
            elif tag == "tr" and self.row is not None:
                if self.row:
                    self.table.append(self.row)
                self.row = None


def parse_leaderboard(html):
    parser = Tables()
    parser.feed(html)
    for table in parser.tables:
        for header_i, row in enumerate(table):
            matches = [i for i, cell in enumerate(row)
                       if "tversky" in cell.lower() and "public" in cell.lower()]
            if len(matches) != 1:
                continue
            col = matches[0]
            for values in table[header_i + 1:]:
                if len(values) <= col or not values or not re.fullmatch(r"\s*#?1\s*", values[0]):
                    continue
                # Avoid extracting an arbitrary number from an unexpected layout.
                score_text = values[col].strip()
                if not re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", score_text):
                    raise ValueError("unexpected first-place score cell")
                value = float(score_text)
                if not 0 <= value <= 1:
                    raise ValueError("leaderboard value outside [0,1]")
                return value
    raise ValueError("official public Tversky table or first-ranked row not found")


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if new.scheme != "https" or new.hostname != old.hostname:
            raise ValueError("cross-host or insecure redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get_url(url, *, github=False):
    expected = "api.github.com" if github else "www.drivendata.org"
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != expected:
        raise ValueError("unexpected source host")
    headers = {"User-Agent": "WBGGEMSDOE2-evidence-feed/1.0", "Accept": "application/json" if github else "text/html"}
    if github and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.build_opener(SameHostRedirect()).open(request, timeout=25) as response:
        data = response.read(8_000_001)
        if len(data) > 8_000_000:
            raise ValueError("source exceeded the permitted size")
        return data.decode("utf-8")


def refresh(fallback, snapshots, *, fetch=get_url, now=None):
    now = (now or datetime.now(timezone.utc)).isoformat()
    old = fallback.get("leaderboard", {})
    lead = {"source": LEADERBOARD, "evidence": "ORGANIZER-PUBLISHED LEADERBOARD; NOT A SUBMISSION RECEIPT",
            "checked_at": now}
    try:
        lead.update(status="fresh", value=parse_leaderboard(fetch(LEADERBOARD)), observed_at=now)
    except (OSError, ValueError, UnicodeError):
        lead.update(status="stale", value=old.get("value"), observed_at=old.get("observed_at"),
                    notice="Official page could not be fetched or parsed; showing dated fallback if available.")

    def site_status(item):
        # These names come from a committed allowlisted config, not arbitrary URLs.
        if not re.fullmatch(r"GEMSDOE(?:24|25|27|28|30|31|32|33|36)", item["site"]):
            raise ValueError("unexpected site in snapshot")
        url = f"{API_ROOT}/repos/buffedlizard55-lab/{item['site']}/commits/main"
        result = {"site": item["site"], "baseline_sha": item["observed_main_sha"]}
        try:
            latest = json.loads(fetch(url, github=True))["sha"]
            if not re.fullmatch(r"[0-9a-f]{40}", latest):
                raise ValueError("invalid GitHub SHA")
            result.update(latest_sha=latest, status="unchanged" if latest == item["observed_main_sha"] else "changed")
        except (OSError, ValueError, KeyError, UnicodeError, TypeError):
            result.update(latest_sha=None, status="unknown")
        return result
    with ThreadPoolExecutor(max_workers=4) as executor:
        site_results = list(executor.map(site_status, snapshots["sites"]))
    return {"schema": "wbggems.public-feed.v1", "generated_at": now, "leaderboard": lead,
            "site_ref_notice": "Changed refs indicate a freshness review is needed, not an automatic audit of new files.",
            "sites": site_results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fallback", type=Path, default=ROOT / "site/data/leaderboard.json")
    parser.add_argument("--snapshots", type=Path, default=ROOT / "config/site_snapshots.json")
    parser.add_argument("--output", type=Path, default=ROOT / "site/data/leaderboard.json")
    args = parser.parse_args()
    old = json.loads(args.fallback.read_text()) if args.fallback.exists() else {}
    snapshots = json.loads(args.snapshots.read_text())
    result = refresh(old, snapshots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Leaderboard: {result['leaderboard']['status']}; site refs: " +
          ", ".join(f"{v['site']}={v['status']}" for v in result['sites']))

if __name__ == "__main__":
    main()
