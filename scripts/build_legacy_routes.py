#!/usr/bin/env python3
"""Replace previously unsafe legacy download routes with fail-closed redirects.

URLs remain reachable, but a browser with refresh disabled also sees the stop.
The canonical dashboard and all nine historical briefs remain available.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITES = ('GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27', 'GEMSDOE28',
         'GEMSDOE30', 'GEMSDOE31', 'GEMSDOE32', 'GEMSDOE33', 'GEMSDOE36')


def redirect(target: str) -> str:
    href = escape(target, quote=True)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMS research — no file cleared</title>
<meta http-equiv="refresh" content="0; url={href}"></head><body><main>
<h1>DO NOT SUBMIT — no file is cleared</h1><p>Earlier H3-PACK and DZ-16 approvals were revoked after the literal duplicate audit.
This route points to the current evidence dashboard, not a submission download.</p>
<p><a href="{href}">Continue to the current evidence</a> if you are not redirected.</p>
</main></body></html>\n'''


def main() -> int:
    routes = {
        'index.html': './docs/index.html',
        'docs/submit/index.html': '../executive-summary.html',
        'docs/submission/index.html': '../executive-summary.html',
        'docs/submission/executive-summary.html': '../executive-summary.html',
        'docs/submission/methodology.html': '../research.html',
        'docs/submission/sources.html': '../sources.html',
        'docs/submission/parallel-lanes.html': '../executive-summary.html',
        'docs/methodology.html': 'research.html',
        'docs/executive-summary/index.html': '../executive-summary.html',
    }
    for site in SITES:
        routes[f'docs/sites/{site}.html'] = f'../../site/sites/{site}.html'
        routes[f'docs/submission/sites/{site}.html'] = f'../../../site/sites/{site}.html'
    for rel, target in routes.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(redirect(target), encoding='utf-8')
    print(f'Wrote {len(routes)} fail-closed legacy routes; no TIFF was generated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
