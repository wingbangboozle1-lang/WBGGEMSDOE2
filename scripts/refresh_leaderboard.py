#!/usr/bin/env python3
"""Refresh a public leaderboard snapshot; preserve and mark stale on failure.

This retrieves no credentials and cannot identify the TIFF behind a public row.
It only accepts a table headed Rank and public DW-Tversky with a valid rank-1
row; a login page, an altered schema, bad values, or an outage cannot replace the
last good observation. The optional cache is used only by the Pages workflow.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

URL = 'https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'
MAX_BYTES = 5 * 1024 * 1024


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = self.row = self.cell = None
        self.in_anchor = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and self.table is None:
            self.table = []
        elif tag == 'tr' and self.table is not None and self.row is None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None and self.cell is None:
            self.cell = {'text': [], 'links': [], 'tag': tag}
        elif tag == 'a' and self.cell is not None:
            self.in_anchor = True
            self.cell['links'].append([])
        elif tag == 'br' and self.cell is not None:
            self.cell['text'].append(' ')

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'].append(data)
            if self.in_anchor and self.cell['links']:
                self.cell['links'][-1].append(data)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.in_anchor = False
        elif tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = ' '.join(''.join(self.cell['text']).split())
            self.cell['links'] = [' '.join(''.join(a).split()) for a in self.cell['links']]
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = self.row = self.cell = None


def parse_leaderboard(html: str) -> dict:
    parser = Tables()
    parser.feed(html)
    matches = []
    for table in parser.tables:
        header_index = None
        for index, row in enumerate(table):
            names = [c['text'].lower() for c in row]
            if any(n.strip() == 'rank' for n in names) and any('tversky' in n and 'public' in n for n in names):
                header_index = index
                break
        if header_index is None:
            continue
        names = [c['text'].lower() for c in table[header_index]]
        rank_col = next(i for i, n in enumerate(names) if n.strip() == 'rank')
        score_col = next(i for i, n in enumerate(names) if 'tversky' in n and 'public' in n)
        participant_cols = [i for i, n in enumerate(names) if 'participant' in n]
        if not participant_cols:
            continue
        participant_col = participant_cols[0]
        for row in table[header_index + 1:]:
            if len(row) <= max(rank_col, score_col, participant_col):
                continue
            if not re.fullmatch(r'#?\s*1', row[rank_col]['text']):
                continue
            raw = row[score_col]['text'].strip()
            if not re.fullmatch(r'(?:0(?:\.\d+)?|1(?:\.0+)?)', raw):
                raise ValueError('rank-1 score is not a probability-like decimal')
            score = float(raw)
            if not 0 <= score <= 1:
                raise ValueError('rank-1 score out of range')
            cell = row[participant_col]
            participant = next((s for s in cell['links'] if s), cell['text'])
            if not participant or len(participant) > 120:
                raise ValueError('invalid rank-1 participant')
            matches.append({'participant': participant, 'score': score})
    if len(matches) != 1:
        raise ValueError('expected exactly one rank-1 public DW-Tversky row')
    return matches[0]


def fetch(url: str = URL) -> str:
    request = Request(url, headers={'User-Agent': 'WBGGEMSDOE2-public-audit/1.0', 'Accept': 'text/html'})
    with urlopen(request, timeout=30) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError('leaderboard page exceeds size limit')
        if not response.geturl().startswith('https://www.drivendata.org/competitions/306/'):
            raise ValueError('redirected away from the public competition page')
    return body.decode('utf-8', errors='replace')


def update_snapshot(previous: dict, html: str | None, timestamp: str, error: str | None = None) -> dict:
    result = dict(previous)
    result['last_attempt_at_utc'] = timestamp
    if html is not None:
        try:
            record = parse_leaderboard(html)
        except ValueError as exc:
            error = str(exc)
        else:
            result.update(record, observed_at_utc=timestamp,
                          observation_method='Public leaderboard HTML; rank-1 row.',
                          last_attempt_result='success')
            return result
    result['last_attempt_result'] = 'failed: ' + (error or 'unavailable')[:200]
    return result


def load_previous(output: Path, cache: Path | None = None) -> dict:
    # A corrupt optional Actions cache must not prevent deployment or invent a
    # result. Fall back to the checked-in observation and validate its source.
    paths = ([cache] if cache is not None else []) + [output]
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            score = data['score']
            if isinstance(score, bool) or not isinstance(score, (float, int)) or not 0 <= score <= 1:
                raise ValueError('invalid cached score')
            observed = data['observed_at_utc']
            if not isinstance(observed, str):
                raise ValueError('invalid observation timestamp')
            parsed = datetime.fromisoformat(observed.replace('Z', '+00:00'))
            if parsed.tzinfo is None or not isinstance(data['participant'], str) or not data['participant'].strip():
                raise ValueError('invalid cached observation')
            if data['source_url'] != URL or data['evidence_class'] != 'PUBLIC-LEADERBOARD-OBSERVATION':
                raise ValueError('untrusted cached source')
            return data
        except (ValueError, KeyError, TypeError, OSError):
            continue
    raise ValueError('no valid previous leaderboard observation available')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('site-data/leaderboard.json'))
    parser.add_argument('--cache', type=Path, help='optional last-successful deployment snapshot')
    args = parser.parse_args()
    previous = load_previous(args.output, args.cache)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    try:
        html = fetch()
        updated = update_snapshot(previous, html, now)
    except Exception as exc:  # network/HTML outages must not masquerade as fresh data
        updated = update_snapshot(previous, None, now, f'{type(exc).__name__}: {exc}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(updated, indent=2, allow_nan=False) + '\n'
    args.output.write_text(text, encoding='utf-8')
    if args.cache:
        args.cache.parent.mkdir(parents=True, exist_ok=True)
        args.cache.write_text(text, encoding='utf-8')
    print(f"Leaderboard refresh: {updated['last_attempt_result']}; last observation {updated['observed_at_utc']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
