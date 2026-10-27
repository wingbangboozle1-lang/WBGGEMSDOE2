#!/usr/bin/env python3
"""Rebuild the historical MSPTCD pages from corrected, negative-only evidence.

The previous renderer presented unproven zero-leakage/band-identity claims and
invalid arithmetic. Its source is preserved in evidence/retired_20261027.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "msptcd"


def render_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # HTML pages use <base href="../"> (docs/). Point evidence links to the
    # copies staged by build_site.py, not to repository paths absent on Pages.
    text = text.replace("](../evidence/", "](data/")
    text = text.replace("](hypotheses.md)", "](research.html)")
    text = text.replace("](msptcd_sources.md)", "](msptcd/sources.html)")
    text = text.replace("](msptcd_findings.md)", "](msptcd/index.html)")
    text = text.replace("](shared-template-format-report.md)",
                        "](https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/research/shared-template-format-report.md)")
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def page(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><base href="../"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Corrected historical MSPTCD campaign evidence; no submission approved."><title>{escape(title)} · GEMS Research</title><link rel="stylesheet" href="styles.css"></head><body><header class="topbar"><div class="shell"><a class="brand" href="index.html">GEMS <small>RESEARCH</small></a><nav class="nav" aria-label="Main navigation"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a><a href="research.html">Research</a><a href="sources.html">Sources</a></nav></div></header><main id="main" class="shell main"><section class="banner"><div class="banner-copy"><p class="banner-label">Historical campaign · NEGATIVE</p><h2>No file is approved for submission.</h2><p>DO NOT SUBMIT. The TIFF failed the literal duplicate stop. These are exploratory proxy results, not organizer scores or proof of no leakage.</p></div><div class="actions"><button class="button" disabled>No submission file</button><a class="text-link" href="data/RUN_CARD_FINAL.json">Current negative run card →</a></div></section><nav aria-label="MSPTCD research"><a href="msptcd/index.html">Findings</a> · <a href="msptcd/executive-summary.html">B2 explanation</a> · <a href="msptcd/research.html">Hypotheses</a> · <a href="msptcd/sources.html">Sources</a></nav><article class="card guide-card research-prose">{body}</article></main><footer class="footer"><div class="shell"><strong>GEMS RESEARCH · Evidence before submission</strong><a href="data/release_triage_20261027.json">Release triage</a></div></footer></body></html>'''


def main() -> None:
    card = json.loads((ROOT / "evidence/RUN_CARD_MSPTCD.json").read_text(encoding="utf-8"))
    final = json.loads((ROOT / "evidence/RUN_CARD_FINAL.json").read_text(encoding="utf-8"))
    if (card.get("verdict") != "negative" or card.get("ok_to_submit") is not False
            or final.get("ok_to_submit") is not False or final.get("raster_sha256") is not None):
        raise SystemExit("STOP: this renderer only publishes the negative historical campaign.")
    findings = render_markdown(ROOT / "research/msptcd_findings.md")
    hypotheses = render_markdown(ROOT / "research/msptcd_hypotheses.md")
    sources = render_markdown(ROOT / "research/msptcd_sources.md")
    b2 = render_markdown(DOCS / "research/why-b2-scored-2778.md")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, title, body in (
        ("index.html", "Corrected MSPTCD findings", findings),
        ("executive-summary.html", "B2 lineage and metric", b2),
        ("research.html", "Historical and future hypotheses", hypotheses),
        ("sources.html", "Sources and access", sources),
    ):
        (OUT / name).write_text(page(title, body), encoding="utf-8")
        print("built", OUT / name)


if __name__ == "__main__":
    main()
