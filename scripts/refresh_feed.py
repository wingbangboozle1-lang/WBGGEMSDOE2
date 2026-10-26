#!/usr/bin/env python3
"""Refresh public leaderboard and nine-site commit status for a Pages build.

A failed or unparseable fetch preserves the dated fallback, marks it stale, and
never publishes a fabricated value. It does not log or store GitHub tokens.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit
from refresh_leaderboard import PARTIAL_URL, parse_top

ROOT = Path(__file__).resolve().parents[1]
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
API_ROOT = "https://api.github.com"


def parse_leaderboard(html):
    # Reuse the official-fragment parser, including implicit <thead> headers and
    # rejection of multiple matching rank-one tables.
    return parse_top(html)[0]


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
    if not github and url == PARTIAL_URL:
        headers["HX-Request"] = "true"
    if github and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.build_opener(SameHostRedirect()).open(request, timeout=25) as response:
        if not github and response.geturl() != url:
            raise ValueError("official leaderboard fragment redirected unexpectedly")
        data = response.read(8_000_001)
        if len(data) > 8_000_000:
            raise ValueError("source exceeded the permitted size")
        return data.decode("utf-8")


def refresh(fallback, snapshots, *, fetch=get_url, now=None):
    now = (now or datetime.now(timezone.utc)).isoformat()
    old = fallback.get("leaderboard", {})
    lead = {"source": LEADERBOARD, "evidence": "ORGANIZER-PUBLISHED LEADERBOARD; NOT A SUBMISSION RECEIPT",
            "checked_at": now, "data_url": PARTIAL_URL}
    try:
        lead.update(status="fresh", value=parse_leaderboard(fetch(PARTIAL_URL)), observed_at=now)
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
            "site_ref_notice": "Changed refs are compared with an observed HEAD baseline, not the historic raster pins; they require review and are not an automatic audit.",
            "baseline_observed_at": snapshots.get("captured_at"),
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
