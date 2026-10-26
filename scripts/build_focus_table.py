#!/usr/bin/env python3
"""Render the nine research-only rows from the pinned audit report."""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- BEGIN FOCUS TABLE -->'
END = '<!-- END FOCUS TABLE -->'


def main() -> None:
    pins = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    audit = json.loads((ROOT / 'reports/focus-review.json').read_text())
    rows = {r['site']: r for r in audit['rows']}
    if set(rows) != {p['site'] for p in pins['focus_sites']}:
        raise ValueError('focus audit does not cover every pinned focus site')
    rendered = []
    for p in sorted(pins['focus_sites'], key=lambda x: -x['claimed_value']):
        r = rows[p['site']]
        if p['sha256'] != r['sha256'] or p['claimed_value'] != r['user_reported_claim']:
            raise ValueError('focus report and pins disagree')
        safe = html.escape
        unique = 'YES' if r['unique_vs_nine_under_literal_rule'] else 'NO'
        detail = f"{r['max_forward_overlap_3px']:.1%} vs {safe(r['worst_focus_site'])}"
        rendered.append(
            f'<tr><th scope="row"><span class="table-site">{safe(p["site"])}</span>'
            f'<a class="table-file" href="{safe(p["research_download"], quote=True)}">{safe(p["filename"])} ↗</a></th>'
            f'<td><span class="claim">{p["claimed_value"]:.4f}</span><span class="sub-label">USER-REPORTED</span></td>'
            f'<td>Unavailable</td><td><span class="no-badge">{unique}</span>'
            f'<span class="overlap-detail">{detail}</span></td><td><span class="table-status">DO NOT SUBMIT</span></td></tr>')
    path = ROOT / 'executive-summary.html'
    contents = path.read_text(encoding='utf-8')
    if contents.count(BEGIN) != 1 or contents.count(END) != 1:
        raise ValueError('focus table markers are missing or ambiguous')
    prefix, rest = contents.split(BEGIN)
    _, suffix = rest.split(END)
    path.write_text(prefix + BEGIN + '\n  ' + '\n  '.join(rendered) + '\n  ' + END + suffix, encoding='utf-8')


if __name__ == '__main__':
    main()
