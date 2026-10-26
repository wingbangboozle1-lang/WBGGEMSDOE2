#!/usr/bin/env python3
"""Refresh public source observations for the static site; failures stay stale.

This never logs in, reads submission receipts, or makes competition uploads.
Leaderboards can change. A failed/ambiguous parse must not become a new score.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = self.row = self.cell = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.depth += 1
            if self.depth == 1:
                self.table = []
        elif self.depth == 1 and tag == 'tr':
            self.row = []
        elif self.depth == 1 and self.row is not None and tag in ('td', 'th'):
            self.cell = []
        elif self.depth == 1 and self.cell is not None and tag == 'br':
            self.cell.append(' ')

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if self.depth == 1 and tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif self.depth == 1 and tag == 'tr' and self.row is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.depth:
            if self.depth == 1 and self.table is not None:
                self.tables.append(self.table)
                self.table = self.row = self.cell = None
            self.depth -= 1


def parse_leaderboard(text: str) -> dict:
    parser = TableParser()
    parser.feed(text)
    candidates = []
    for table in parser.tables:
        if not table:
            continue
        header = ' '.join(table[0]).lower()
        if 'rank' not in header or 'tversky' not in header:
            continue
        for row in table[1:]:
            if not row or not re.fullmatch(r'#?\s*1', row[0].strip()):
                continue
            scores = [c for c in row[1:] if re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)', c)]
            if len(scores) != 1:
                raise ValueError('ambiguous top-rank score')
            candidates.append({'top_score': scores[0], 'rank': 1})
    if len(candidates) != 1:
        raise ValueError('no unique recognizable rank-1 Tversky leaderboard row')
    return candidates[0]


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent':'WBGGEMSDOE2-research/1.0', 'Accept':'text/html'})
    with urllib.request.urlopen(req, timeout=20) as response:
        if not response.geturl().startswith('https://www.drivendata.org/'):
            raise ValueError('unexpected redirect from official leaderboard')
        body = response.read(4_000_001)
        if len(body) > 4_000_000:
            raise ValueError('leaderboard response exceeds limit')
        return body.decode('utf-8', errors='replace')


def refresh(base: dict, fetch=get) -> dict:
    result = dict(base)
    now = datetime.now(timezone.utc).isoformat()
    result['last_attempt_utc'] = now
    try:
        parsed = parse_leaderboard(fetch(URL))
        result.update(parsed)
        result.update(status='fresh', observed_at_utc=now, observed_date_utc=now[:10],
                      source=URL, top_participant=None, last_error=None)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        result.update(status='stale', last_error=f'{type(exc).__name__}: {str(exc)[:180]}')
    result['kind'] = 'OFFICIAL PUBLIC LEADERBOARD SNAPSHOT — not a submission receipt'
    return result


def check_refs(config: dict) -> list[dict]:
    """Compare current main refs with the archival file commits, not with audit time."""
    rows = []
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    for site in config['sites']:
        url = f"https://api.github.com/repos/{config['owner']}/{site['site']}/commits/main"
        headers = {'User-Agent':'WBGGEMSDOE2-research/1.0', 'Accept':'application/vnd.github+json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=20) as r:
                if not r.geturl().startswith('https://api.github.com/'):
                    raise ValueError('unexpected GitHub API redirect')
                payload = r.read(1_000_001)
                if len(payload) > 1_000_000:
                    raise ValueError('GitHub API response exceeds limit')
                current = json.loads(payload)['sha']
                if not re.fullmatch('[0-9a-f]{40}', current):
                    raise ValueError('invalid GitHub commit SHA')
            status = 'same_as_archival_file_ref' if current == site['ref'] else 'different_from_archival_file_ref'
            rows.append({'site':site['site'], 'archival_file_ref':site['ref'], 'current_ref':current, 'status':status})
        except (ValueError, OSError, KeyError, json.JSONDecodeError, urllib.error.URLError) as exc:
            rows.append({'site':site['site'], 'archival_file_ref':site['ref'], 'current_ref':None,
                         'status':'unavailable', 'error_type':type(exc).__name__})
    return rows


def main():
    dst = ROOT / 'docs/data/feed.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        base = json.loads(dst.read_text()) if dst.exists() else json.loads((ROOT / 'data/leaderboard_snapshot.json').read_text())
    except (OSError, json.JSONDecodeError):
        base = json.loads((ROOT / 'data/leaderboard_snapshot.json').read_text())
    result = refresh(base)
    result['site_refs'] = check_refs(json.loads((ROOT / 'data/focus_sources.json').read_text()))
    result['site_refs_checked_at_utc'] = datetime.now(timezone.utc).isoformat()
    dst.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Leaderboard feed:', result['status'], 'at', result['last_attempt_utc'])
    if result['status'] != 'fresh':
        print('Last known value retained; no upload status changed.')


if __name__ == '__main__':
    main()
