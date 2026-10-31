"""Read-only checkout diagnostics, never a scientific or submission approval gate.

A historical restoration receipt cannot establish that ignored data still exists.
These checks hash the files now, without downloading, importing shared code,
constructing features, opening a candidate surface, or consuming a weekly slot.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .release import digest, load_negative_release, read_json, ready_candidates


def inspect_file(root: Path, relative: str, expected: str) -> dict:
    """Allow internal data symlinks, but never follow a path outside this checkout."""
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Readiness input escapes checkout: {relative}")
    actual = digest(path) if path.is_file() else None
    return {"path": relative, "expected_sha256": expected, "actual_sha256": actual,
            "status": "missing" if actual is None else "verified" if actual == expected else "changed"}


def inspect_checkout(root: Path) -> dict:
    root = root.resolve()
    # Byte-bound negative release validation; changed inventory is an error, not
    # an opportunity for this diagnostic to grant a new release authorization.
    release = load_negative_release(root)
    hypotheses = read_json(root / "config/research_hypotheses.json")
    preparation = read_json(root / "evidence/data_preparation.json")
    cache = read_json(root / "evidence/feature_cache.json")
    pins = read_json(root / "registry/template_pins.json")
    inputs = [inspect_file(root, r['path'], r['sha256']) for r in preparation['files']]
    bands = [inspect_file(root, r['cache_file'], r['sha256']) for r in cache['bands']]
    tools = [inspect_file(root, '.cache/shared-template/' + r['upstream_path'], r['sha256'])
             for r in pins['files']]
    all_verified = lambda rows: bool(rows) and all(r['status'] == 'verified' for r in rows)
    # Report observations, not an auto-repair or an asserted organizer identity.
    ready = ready_candidates(root)
    if ready:
        card = read_json(root / next(iter(ready.values()))["run_card"])
        download_decision = {
            "status": "OK_TO_DOWNLOAD_AND_SUBMIT_RESEARCH_GRADE",
            "label": "OK TO DOWNLOAD AND SUBMIT (research-grade)",
            "files": sorted(ready),
            "weekly_slot_authorized": False,
            "run_card": next(iter(ready.values()))["run_card"],
            "run_card_verdict": card.get("verdict"),
            "validator_all_passed": bool((card.get("validator") or {}).get("all_passed")),
            "detail": ("One hash-bound file passed the local format validator, the literal 70% dot-overlap stop and the run-card evidence checks. "
                       "No weekly slot has been spent and no organizer receipt exists; spending a slot is a separate user action."),
        }
    else:
        download_decision = {"status": "NEGATIVE", "label": "DO NOT SUBMIT", "files": [],
                             "weekly_slot_authorized": False,
                             "detail": "No registered candidate currently satisfies the research-grade download tier."}
    gates = [
        {"id": "lane", "status": "blocked", "detail":
         f"Recorded lane: {hypotheses['method_lane']['status']}. Assignment alone cannot authorize a campaign; a reviewed launcher is still required."},
        {"id": "shared-code", "status": "verified" if all_verified(tools) else "blocked", "detail":
         "Pinned shared code hashes only; this does not resolve the documented upstream format-mask defect."},
        {"id": "mirror-inputs", "status": "verified" if all_verified(inputs) else "blocked", "detail":
         "Owner-mirror hash identity only, not authenticated organizer input identity."},
        {"id": "raw-band-cache", "status": "verified" if all_verified(bands) else "blocked", "detail":
         "Raw band byte hashes only, not a derived-feature bank or a test of physical band semantics."},
        {"id": "registry", "status": "blocked", "detail":
         "Existing negative audit covers pinned rejection witnesses, not every current registry raster or original surface. Dense-prior support policy remains unresolved."},
        {"id": "shared-format", "status": "blocked", "detail":
         "Shared mask-validator defect remains documented; no upstream correction is pinned. Supplemental strict readback is not a private replacement writer."},
        {"id": "scientific-validation", "status": "not-run", "detail":
         "No new feature-alone canaries or matched buffered whole-segment HOLDOUT-DTI improvement with paired spatial CI. Historical campaigns are not a current incumbent replay."},
        {"id": "selector", "status": "blocked", "detail":
         "Separate promotion/slot selector not run; account-specific remaining quota and per-file organizer receipts unavailable."},
    ]
    source_paths = ['evidence/release_audit.json', 'config/research_hypotheses.json',
                    'registry/template_pins.json', 'evidence/data_preparation.json',
                    'evidence/feature_cache.json']
    return {
        "schema": "wbggems.checkout-readiness.v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "CHECKOUT-DIAGNOSTIC; NOT HOLDOUT-DTI OR AN ORGANIZER RECEIPT",
        "scope": "Dated local checkout snapshot. CI and other machines can have different ignored caches. No network, raster generation, model experiment, or submission.",
        "sources": {p: digest(root / p) for p in source_paths},
        "research_launch_authorized": False,
        "ok_to_submit": False,
        "ok_to_submit_meaning": "selector/weekly-slot authorization only; the research-grade download tier is reported in download_decision.",
        "download_decision": download_decision,
        "new_raster": None, "leaderboard_estimate": None,
        "experiments_run": 0, "weekly_slots_used": 0,
        "gates": gates, "mirror_inputs": inputs, "raw_band_cache": bands, "shared_code": tools,
        "existing_research_inventory": {
            "tif_paths": release['scope']['owned_tif_paths'],
            "distinct_tif_hashes": release['scope']['distinct_tif_sha256'],
            "zip_paths": len(release['zip_archives']),
            "all_rejected_by_literal_overlap": all(r['duplicate_witnesses'] for r in release['artifacts']),
        },
    }


def render_readiness(report: dict) -> str:
    """Escape source text; every successful hash check remains non-authorizing."""
    e = lambda value: escape(str(value), quote=True)
    rows = ''.join(f'<tr><th scope="row">{e(r["id"])}</th><td>{e(r["status"])}</td><td>{e(r["detail"])}</td></tr>'
                   for r in report['gates'])
    files = ''
    for key, title in [('mirror_inputs', 'Competition owner-mirror inputs'),
                       ('raw_band_cache', 'Raw band cache'), ('shared_code', 'Pinned shared code')]:
        lines = ''.join(f'<tr><td><code>{e(r["path"])}</code></td><td>{e(r["status"])}</td>'
                        f'<td><code>{e(r["expected_sha256"])}</code></td></tr>' for r in report[key])
        files += f'<details><summary>{e(title)}</summary><div class="table-scroll"><table><caption>Expected SHA-256; actual hashes in JSON</caption><thead><tr><th>File</th><th>Checkout status</th><th>Expected hash</th></tr></thead><tbody>{lines}</tbody></table></div></details>'
    inv = report['existing_research_inventory']
    dd = report.get('download_decision') or {'status': 'NEGATIVE', 'files': [], 'detail': ''}
    if dd['status'] == 'OK_TO_DOWNLOAD_AND_SUBMIT_RESEARCH_GRADE':
        links = ''.join(
            f'<a class="button" href="{e(Path(f).relative_to("docs").as_posix())}" download>OK TO DOWNLOAD AND SUBMIT — {e(Path(f).name)} ↓</a> '
            for f in dd['files'])
        decision_banner = f'''<section class="banner" data-release-status="ok"><div class="banner-copy"><h1>OK TO DOWNLOAD AND SUBMIT (research-grade)</h1>
<p>{e(dd['detail'])}</p><p>{links}<a class="text-link" href="wbg5/index.html">Full evidence dossier →</a></p>
<p>This is a download decision. <code>ok_to_submit</code> stays false because no selector has authorized a weekly slot.</p></div></section>'''
    else:
        decision_banner = '''<section class="banner" data-release-status="blocked"><div class="banner-copy"><h1>DO NOT SUBMIT — no file passes the research-grade tier</h1>
<p>No eligible new TIFF, no score estimate, no slot spent.</p></div></section>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Checkout readiness · GEMS Research</title><link rel="stylesheet" href="styles.css"></head><body>
<main class="shell main" id="main"><p><a href="release.html">← Executive summary and exact research downloads</a></p>
{decision_banner}
<section class="card guide-card"><h2>What is actually available now?</h2><p>Checked {e(report['checked_utc'])}.</p>
<p>{e(report['scope'])}</p><p>This page is a diagnostic, never a promotion mechanism. “Verified” means matching a historical byte hash, not high scoring, scientifically valid, unique, or organizer accepted.</p>
<p>{inv['tif_paths']} historical TIFF paths / {inv['distinct_tif_hashes']} distinct hashes / {inv['zip_paths']} ZIPs remain rejected by the literal registry rule and are not part of the research-grade download tier.</p>
<p><a href="data/checkout-readiness.json">Download machine-readable diagnostic</a> · <a href="data/run-card.json">Canonical negative run card</a></p>
<div class="table-scroll"><table><caption>Readiness observations — none authorizes a submission</caption><thead><tr><th>Prerequisite</th><th>Status</th><th>Evidence / limitation</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Byte availability, not historical restoration claims</h2>{files}
<h2>Next scientific test, only after blockers are resolved</h2><p><a href="research.html">N1–N4 ranked hypotheses</a> remain proposals, not assigned lanes. N1 tests signed gravity/magnetic cross-profile edge pairs to reject finite-width bodies; an unfaulted intrusive contact can mimic it. Use the unchanged shared evaluator/writer, visible-only catalogue features, segment buffers and every feature-alone canary. Compare pooled HOLDOUT-DTI with a matched incumbent and paired spatial confidence interval; check the original surface before placement and final dots against every registry raster. Stop after three experiments or two hours. A separate selector governs real slots.</p>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official target, metric and format</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference implementation</a>. These links are for review; this offline diagnostic does not assert a fresh retrieval of their contents.</p></section></main></body></html>'''
