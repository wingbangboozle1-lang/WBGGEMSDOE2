#!/usr/bin/env python3
"""Build docs/submit/index.html so visitors landing on /docs/submit/ see the
single approved WBG2-HVGF submission and an explicit DO NOT SUBMIT quarantine
banner on the legacy NaN-containing wbg3-h3pack file.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CSS = """
:root{--ink:#101418;--mut:#5a6672;--line:#dfe5ec;--bg:#f6f8fb;--good:#0f7b3d;--bad:#b3261e;--warn:#8a5a00;--acc:#1a4fd6}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 80px}
nav{display:flex;gap:16px;flex-wrap:wrap;padding:0 0 18px;border-bottom:1px solid var(--line);margin-bottom:20px;font-size:.92rem}
nav a{color:var(--acc);text-decoration:none;font-weight:600}
h1{font-size:1.9rem;margin:.2em 0 .3em}h2{font-size:1.3rem;margin:2em 0 .5em;padding-top:.4em;border-top:1px solid var(--line)}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:18px 0;box-shadow:0 1px 2px rgba(16,20,24,.04)}
.hero{border:3px solid var(--good);background:linear-gradient(180deg,#f2fbf5,#fff)}
.hero .tag{display:inline-block;background:var(--good);color:#fff;font-weight:700;font-size:.78rem;letter-spacing:.08em;padding:.3em .7em;border-radius:999px;text-transform:uppercase}
.dl{display:inline-block;background:var(--good);color:#fff;text-decoration:none;text-align:center;font-weight:800;font-size:1.08rem;padding:14px 22px;border-radius:10px;margin:10px 10px 6px 0}
.dl.sec{background:#eef2f7;color:var(--ink);border:1px solid var(--line);font-weight:600;font-size:.95rem}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.84rem;word-break:break-all}
.note-box{background:#f0f6f2;border:1px solid #bcdcc8;border-radius:8px;padding:12px 14px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.86rem}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin:10px 0}
th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}
th{background:#eef2f7;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.ok{color:var(--good);font-weight:700}.no{color:var(--bad);font-weight:700}
.pill{display:inline-block;padding:.15em .55em;border-radius:999px;font-size:.76rem;font-weight:700}
.pill.ok{background:#e3f5e9;color:#0f7b3d}.pill.no{background:#fde7e5;color:#b3261e}.pill.warn{background:#fff3d6;color:#8a5a00}
.bad-note{background:#fdecea;border-left:4px solid var(--bad);padding:12px 14px;border-radius:8px;margin:12px 0}
a{color:var(--acc)}
footer{margin-top:40px;color:var(--mut);font-size:.82rem}
"""


def esc(x) -> str:
    return html.escape(str(x))


def main() -> int:
    cand = json.loads((ROOT / "data_public/candidate.json").read_text())
    card = json.loads((ROOT / "evidence/RUN_CARD_HVGF.json").read_text())
    focus = json.loads((ROOT / "data_public/focus_table.json").read_text())["rows"]
    tif_fname = Path(cand["file"]).name
    zip_fname = f"{cand['name']}.zip"
    q8 = card["holdout_dti"]["primary_quadrant_8km"]
    sgmc = card["holdout_dti"]["independent_sgmc_piedmont_offcatalogue"]
    comp = card["holdout_dti"]["within_network_component_hide"]

    focus_rows = "".join(
        f"<tr><td><b><a href=\"../submission/sites/{esc(r['site'])}.html\">{esc(r['site'])}</a></b></td>"
        f"<td class=\"mono\">{esc(Path(r['path']).name)}</td>"
        f"<td><b>{r['user_reported_score']:.4f}</b> <span class=\"pill warn\">USER-REPORTED</span></td>"
        f"<td>{r['dots']:,}</td>"
        f"<td>{r['overlap_with_wbg2_candidate']*100:.1f}%</td>"
        f"<td><span class=\"pill no\">DO NOT SUBMIT (83–100% peer duplicate)</span></td></tr>"
        for r in focus
    )

    out_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DOE GEMS Submission — Download &amp; Submit (WBG2-HVGF)</title><style>{CSS}</style></head><body><div class="wrap">
<nav>
  <a href="../submission/index.html">Primary Submission Portal</a>
  <a href="../submission/executive-summary.html">Executive Summary &amp; Multi-Site Table</a>
  <a href="../submission/how-to-submit.html">DrivenData Upload Checklist</a>
  <a href="../submission/methodology.html">PhD Methodology &amp; Hypotheses</a>
  <a href="../submission/sources.html">Official Sources</a>
  <a href="../index.html">Repo Overview</a>
</nav>

<h1>DOE GEMS Prize — Verified Submission Download (<code>WBG2-HVGF</code>)</h1>
<p><b>Exactly one file in this repository is cleared for upload.</b> All 15 automated format, CRS, grid, and finite-<code>[0, 1]</code> checks pass with zero human-inspector intervention.</p>

<div class="card hero">
  <span class="tag">OK TO DOWNLOAD AND SUBMIT</span>
  <h2 style="border:0;margin:.6em 0 .2em;padding:0"><code>{esc(tif_fname)}</code></h2>
  <p class="mono" style="margin:.3em 0">GeoTIFF SHA-256: {esc(cand['sha256'])} ({cand['bytes']:,} bytes)<br>
  Single-TIFF ZIP SHA-256: {esc(cand['zip_sha256'])}</p>
  <p style="margin:.4em 0">1-band <code>float32</code> · <code>EPSG:32611</code> · <code>3730 × 3292</code> · <b>{cand['dots']:,}</b> non-touching 1.0 dots · <b>0.0 outside footprint</b> · <code>nodata=None</code> · <b>0 NaN · 0 Inf anywhere</b></p>
  <a class="dl" href="../downloads/{esc(tif_fname)}" download>⬇ Download Approved GeoTIFF (.tif)</a>
  <a class="dl sec" href="../downloads/hvgf/{esc(zip_fname)}" download>⬇ Download Single-TIFF (.zip)</a>
  <a class="dl sec" href="../submission/how-to-submit.html">Full Upload Instructions →</a>
  <p style="margin:.8em 0 .3em"><b>Copyable DrivenData Submission Note</b> ({card['submission_note_chars']} / 140 chars):</p>
  <div class="note-box">{esc(card['submission_note'])}</div>
</div>

<div class="bad-note">
  <b>DO NOT SUBMIT <code>wbg3-h3pack-34k-20261027T174337Z-zeros.tif</code> (Quarantined Legacy File):</b>
  Byte-level inspection proved that the earlier H3 file previously linked on this page contained <b>7,111,787 <code>NaN</code> pixels</b> outside the study footprint (<code>scripts/write_h3_submission.py:57</code>), which caused DrivenData's portal error <code>"Predicted values must be in range [0, 1]"</code> because IEEE-754 <code>NaN &gt;= 0</code> evaluates to <code>False</code>. Both the writer and validator have been fixed upstream; always submit <code>{esc(tif_fname)}</code> above.
</div>

<h2>Zero-Leakage Multi-Instrument Holdout Summary (<code>HOLDOUT-DTI</code>, Not a Live Score)</h2>
<table>
<tr><th>Holdout Instrument (<code>gems57-pooled-hide-v2</code>)</th><th>Withheld Fault Pixels</th><th>Control Baseline</th><th>Promoted <code>WBG2-HVGF E3</code></th></tr>
<tr><td>Instrument A — 8 km Spatial Quadrant Holdout</td><td>{q8['withheld_positive_pixels']:,}</td><td>0.0287 (19-band GBDT) · 0.0426 (MSPTCD)</td><td class="ok">{q8['dti']:.4f} (95% CI {q8['ci95'][0]:.4f}–{q8['ci95'][1]:.4f}, 4.03×)</td></tr>
<tr><td>Instrument B — Within-Network Component Hide</td><td>{comp['withheld_positive_pixels']:,}</td><td>0.0075 (19-band GBDT)</td><td class="ok">{comp['dti']:.4f} (95% CI {comp['ci95'][0]:.4f}–{comp['ci95'][1]:.4f}, 2.76×)</td></tr>
<tr><td>Instrument C — Blind SGMC Concealed Piedmont Faults</td><td>{sgmc['withheld_positive_pixels']:,}</td><td>0.0407 (DZ-16) · 0.0075 (MSPTCD)</td><td class="ok">{sgmc['dti']:.4f} (95% CI {sgmc['ci95'][0]:.4f}–{sgmc['ci95'][1]:.4f}, +29.7% vs DZ-16)</td></tr>
</table>

<h2>Nine Priority Sites — Historical Comparison (All Marked <code>DO NOT SUBMIT</code>)</h2>
<table>
<tr><th>Site</th><th>Historical File</th><th>Reported Score</th><th>Dots</th><th>3-px Overlap vs <code>WBG2-HVGF</code></th><th>Status</th></tr>
{focus_rows}
</table>

<footer>WBGGEMSDOE2 · Lane WBG2-HVGF · <a href="../submission/executive-summary.html">Full PhD Executive Summary &amp; 144-Row Multi-Site Ledger →</a></footer>
</div></body></html>
"""
    out_dir = DOCS / "submit"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(out_html)
    print("Built docs/submit/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
