#!/usr/bin/env python3
"""Build a fail-closed status page for the former H3 download URL.

Historical lane receipts remain in evidence/, but this legacy page cannot turn
one into a current submission release. A positive run card requires a separate
selector record and a release-aware publication review before any file link is
added.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from submission_status import load_submission_status

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def main() -> int:
    status = load_submission_status(ROOT)
    if status["approved"]:
        raise SystemExit(
            "A positive selector release exists; review and replace this negative-only page before publishing."
        )
    card = status.get("card") or {}
    (DOCS / "submit").mkdir(parents=True, exist_ok=True)
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Submission status — DO NOT SUBMIT</title>
<style>
:root{{color-scheme:light;--ink:#17221d;--muted:#53625b;--line:#d5ded8;--red:#a22121;--pale:#fff2f0;--green:#164c3b}}
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f4;color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:900px;margin:48px auto;padding:0 22px}}article{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px;box-shadow:0 8px 28px #10251a12}}
.alert{{border:2px solid var(--red);background:var(--pale);border-radius:12px;padding:18px 20px;margin:22px 0}}
h1{{font-size:clamp(2rem,5vw,3.2rem);line-height:1.1;margin:.2em 0}}h2{{margin-top:1.6em}}.eyebrow{{color:var(--green);font-weight:800;letter-spacing:.12em;text-transform:uppercase}}
button{{font:inherit;background:#69736e;color:#fff;border:0;border-radius:8px;padding:12px 18px;font-weight:700;cursor:not-allowed}}
a{{color:#064f83}}code{{overflow-wrap:anywhere}}.muted{{color:var(--muted)}}footer{{margin-top:28px;border-top:1px solid var(--line);padding-top:16px;color:var(--muted);font-size:.9rem}}
</style></head><body><main><article>
<p class="eyebrow">DOE GEMS · current release gate</p>
<h1>DO NOT SUBMIT</h1>
<div class="alert" role="alert"><strong>No GeoTIFF is approved for download or competition upload.</strong>
<p>This page replaces a historical candidate-download page. Old “promote” labels refer to individual research lanes and are not current project authorization.</p>
<button type="button" disabled>No approved file</button></div>
<h2>Why the release is blocked</h2>
<p>The canonical run card is not a released candidate. There is no hash-bound candidate, completed HOLDOUT-DTI, passing validator receipt, complete current-registry pass, or confirmed slot selection. The machine-check detail is available below.</p>
<details><summary>Machine-check reasons</summary><p>{esc(status['reason'])}</p></details>
<ul><li>Canonical run-card verdict: <code>{esc(card.get('verdict', 'missing'))}</code>.</li>
<li>Method lane: unassigned; no experiment or candidate is authorized.</li>
<li>Current novelty status: incomplete registry plus literal lattice/continuous-prior witnesses; no global uniqueness pass.</li>
<li>Weekly slot selector: separate byte-bound release record is absent.</li></ul>
<h2>Historical files</h2>
<p>DZ-16, H3-PACK and MSPTCD TIFF/ZIP artifacts are retained for research and audit provenance only. Do not submit them, rename them, or treat their format checks, projections, lane verdicts, or local HOLDOUT-DTI results as organizer approval. The MSPTCD result is a local holdout result; it failed the literal all-registry gate.</p>
<p><a href="../downloads/README.txt">Read the research-only archive notice</a> · <a href="../data/run-card.json">Open the canonical run card</a> · <a href="../index.html">Open the evidence dashboard</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official competition description</a></p>
<footer>Evidence before submission · generated from the canonical run card and separate selector gate.</footer>
</article></main></body></html>"""
    (DOCS / "submit" / "index.html").write_text(html_doc, encoding="utf-8")
    print("wrote fail-closed status page: docs/submit/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
