#!/usr/bin/env python3
"""Render docs/EXECUTIVE_SUMMARY_NINE_SITES_20261028.md to a GitHub-Pages HTML page.

Output: docs/nine-site-executive-summary.html (regenerated, never hand-edited).
Requires the pinned `Markdown` package from requirements.txt.
"""
from __future__ import annotations

from pathlib import Path

import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "EXECUTIVE_SUMMARY_NINE_SITES_20261028.md"
OUT = ROOT / "docs" / "nine-site-executive-summary.html"
# Files outside docs/ are not staged for GitHub Pages; link them to the repository.
REPO_BLOB = "https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GEMSDOE nine-site executive summary (2026-10-28)</title>
<link rel="stylesheet" href="styles.css">
<style>
body{{max-width:1100px;margin:2rem auto;padding:0 1rem;font-family:system-ui,sans-serif;line-height:1.5;color:#1b1b1b}}
table{{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92rem}}
th,td{{border:1px solid #ccc;padding:.4rem .5rem;vertical-align:top;text-align:left}}
th{{background:#f1f3f6}}
blockquote{{border-left:5px solid #c0392b;background:#fdf2f0;margin:1rem 0;padding:.6rem 1rem}}
code{{font-size:.88em;word-break:break-all}}
a{{color:#0b57d0}}
</style></head>
<body>
<p><a href="index.html">&larr; Site home</a></p>
{body}
</body></html>
"""


def main() -> int:
    body = markdown.markdown(SRC.read_text(encoding="utf-8"),
                             extensions=["tables", "toc", "fenced_code"])
    body = re.sub(r'href="\.\./([^"]+)"', lambda m: f'href="{REPO_BLOB}{m.group(1)}"', body)
    OUT.write_text(PAGE.format(body=body), encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
