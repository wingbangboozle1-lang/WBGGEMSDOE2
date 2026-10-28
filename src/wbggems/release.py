"""Fail-closed publication policy, separate from format tests and slot selection.

The current repository has no authorized method lane or complete registry. This
module deliberately cannot promote a submission. Do not substitute a normalized
novelty diagnostic or a filename/hash change for the user's literal stop rule.
"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile

RELEASE_SCHEMA = "wbggems.release-audit.v1"
CANONICAL_RUN_CARDS = (
    'evidence/run_card.json', 'docs/data/run-card.json', 'docs/data/run_card.json',
    'site/data/run_card.json', 'data_public/run_card.json', 'docs/RUN_CARD.json',
    'docs/data/run-card-current.json', 'evidence/RUN_CARD_FINAL.json',
    'docs/data/RUN_CARD_FINAL.json',
)
NEGATIVE_RESEARCH_CARDS = (
    'evidence/RUN_CARD_CBS.json', 'docs/data/RUN_CARD_CBS.json',
    'evidence/RUN_CARD_H3.json', 'docs/data/RUN_CARD_H3.json',
    'evidence/RUN_CARD_MSPTCD.json', 'docs/data/RUN_CARD_MSPTCD.json',
    'evidence/RUN_CARD_DPHS.json', 'docs/data/run-card-dphs.json',
    'evidence/RUN_CARD_GVCD.json', 'docs/data/run-card-gvcd.json',
    'evidence/RUN_CARD_DISTAL.json', 'docs/data/RUN_CARD_DISTAL.json',
    'evidence/wbg2_distal_candidate.json', 'data_public/final_audit.json',
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


CANDIDATE_REGISTER = Path("config/release_register.json")


def registered_release_assets(root: Path) -> dict:
    """Validate and return every historically registered release artifact.

    Registration binds bytes and evidence for audit purposes; it is *not* selector
    authorization. Keep registered TIFFs out of the older forensic inventory while
    separately requiring an explicit selector flag and receipt before exposing any
    file as an eligible submission.
    """
    path = root / CANDIDATE_REGISTER
    if not path.exists():
        return {}
    data = read_json(path)
    out = {}
    for rec in data.get("candidates", []):
        required = ("path", "sha256", "run_card", "holdout_evidence", "uniqueness_evidence")
        missing = [k for k in required if not rec.get(k)]
        if missing:
            raise ValueError(f"Candidate register entry missing {missing}: {rec.get('path')}")
        artifact = root / rec["path"]
        if not artifact.is_file() or artifact.is_symlink():
            raise ValueError(f"Registered candidate is not a regular file: {rec['path']}")
        if digest(artifact) != rec["sha256"]:
            raise ValueError(f"Registered candidate bytes changed: {rec['path']}")
        for key in ("run_card", "holdout_evidence", "uniqueness_evidence"):
            if not (root / rec[key]).is_file():
                raise ValueError(f"Registered candidate evidence missing: {rec[key]}")
        out[rec["path"]] = rec
        if rec.get("zip"):
            z = root / rec["zip"]
            if not z.is_file() or z.is_symlink():
                raise ValueError(f"Registered candidate archive missing: {rec['zip']}")
            if rec.get("zip_sha256") and digest(z) != rec["zip_sha256"]:
                raise ValueError(f"Registered candidate archive bytes changed: {rec['zip']}")
            out[rec["zip"]] = rec
    return out


def approved_candidates(root: Path) -> dict:
    """Return only artifacts explicitly promoted by a separate selector receipt.

    Candidate creation, registration, format validation, uniqueness evidence and
    holdout evidence do not themselves grant permission to spend a competition
    slot. The selector must set ``selector_authorized`` and attach a nonempty
    organizer/slot receipt reference; no current register entry does so.
    """
    assets = registered_release_assets(root)
    approved = {}
    records = {rec["path"]: rec for rec in assets.values()}
    for rel, rec in records.items():
        receipt = rec.get("selector_receipt")
        if rec.get("selector_authorized") is not True or not isinstance(receipt, dict):
            continue
        receipt_path = receipt.get("path")
        receipt_hash = receipt.get("sha256")
        if not isinstance(receipt_path, str) or not isinstance(receipt_hash, str):
            continue
        receipt_rel = Path(receipt_path)
        receipt_file = root / receipt_rel
        try:
            receipt_inside_root = receipt_file.resolve().is_relative_to(root.resolve())
        except (OSError, RuntimeError):
            receipt_inside_root = False
        if (receipt_rel.is_absolute() or not receipt_inside_root or not receipt_file.is_file()
                or receipt_file.is_symlink() or digest(receipt_file) != receipt_hash):
            raise ValueError(f"Selector receipt missing or hash-mismatched: {receipt_path}")
        record = read_json(receipt_file)
        if (record.get("schema") != "wbggems.selector-receipt.v1"
                or record.get("decision") != "PROMOTE"
                or record.get("candidate_path") != rel
                or record.get("candidate_sha256") != rec.get("sha256")
                or type(record.get("weekly_slots_remaining")) is not int
                or record["weekly_slots_remaining"] < 1):
            raise ValueError(f"Selector receipt does not authorize this file and available slot: {receipt_path}")
        approved[rel] = rec
        if rec.get("zip"):
            approved[rec["zip"]] = rec
    return approved


def research_inventory(root: Path, suffixes: tuple[str, ...]) -> set[str]:
    """Include published assets and reject symlink paths that can hide inventory."""
    def fail_walk(error):
        raise ValueError(f'Could not enumerate research inventory: {error.filename}') from error

    paths = set()
    folders = (root / 'docs', root / 'site', root / 'downloads', root / 'candidate')
    for folder in folders:
        if folder.is_symlink():
            raise ValueError(f'Research inventory root must not be a symlink: {folder.relative_to(root)}')
        if not folder.exists():
            continue
        for current, directories, files in os.walk(
                folder, topdown=True, onerror=fail_walk, followlinks=False):
            base = Path(current)
            linked_directories = [name for name in directories if (base / name).is_symlink()]
            if linked_directories:
                raise ValueError(
                    f'Research inventory must not contain symlink directories: {base.relative_to(root)}')
            for name in files:
                path = base / name
                if path.is_symlink() and path.suffix.lower() in suffixes:
                    raise ValueError(f'Research asset must not be a symlink: {path.relative_to(root)}')
                if path.is_file() and path.suffix.lower() in suffixes:
                    paths.add(path.relative_to(root).as_posix())
    # Registered release bytes have their own hash-bound records and are not part
    # of the legacy negative witness inventory, whether or not a selector has
    # authorized them. Registration is not an upload approval.
    registered = set(registered_release_assets(root))
    return paths - registered


def read_json(path: Path):
    def reject(value):
        raise ValueError(f"Non-standard JSON constant {value} in {path}")

    def unique_pairs(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"Duplicate JSON key {key} in {path}")
            out[key] = value
        return out

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject, object_pairs_hook=unique_pairs)


def require_experiment_lane(lane_id: str, root: Path) -> None:
    """A ranked proposal is not a lane assignment; do not launch an old campaign."""
    lane = read_json(root / "config/research_hypotheses.json").get("method_lane", {})
    if lane.get("status") != "ASSIGNED" or lane.get("lane_id") != lane_id:
        raise RuntimeError(
            "STOP: no explicit method-lane assignment. Existing campaigns are historical; "
            "do not construct features, select dots, or overwrite their evidence."
        )
    # Assignment alone is not permission to bypass the all-registry preflight.
    raise RuntimeError("STOP: complete current registry and reviewed pre-placement launcher required")


def _research_path(root: Path, relative: str) -> Path:
    p = root / relative
    resolved = p.resolve()
    if (p.is_symlink() or not p.is_file()
            or not any(resolved.is_relative_to(root / folder) for folder in ('docs/downloads', 'downloads', 'candidate'))):
        raise ValueError(f"Artifact path outside the regular-file research inventory: {relative}")
    return p


def load_negative_release(root: Path) -> dict:
    """Check portable forensic receipts against committed TIFF/ZIP bytes on builds.

    No large input download or scientific dependencies are needed in Pages CI.
    A changed/new artifact, altered witness hash, invalid receipt or attempted
    promotion stops publication. This verifies an existing negative disposition,
    NOT a fresh exhaustive-registry pass or a new scientific/organizer validation.
    """
    root = Path(root).resolve()
    report = read_json(root / 'evidence/release_audit.json')
    if (report.get('schema') != RELEASE_SCHEMA or report.get('verdict') != 'negative'
            or report.get('ok_to_submit') is not False or report.get('approved_submission') is not None
            or report.get('leaderboard_score_estimate') is not None):
        raise ValueError('Release renderer only accepts the byte-bound negative disposition')
    policy = report.get('policy', {})
    if (policy.get('witness_exemptions') != [] or policy.get('radius_px') != 3
            or policy.get('overlap_stop_strictly_greater_than') != .70
            or policy.get('absolute_rank_stop_strictly_greater_than') != .90):
        raise ValueError('Literal registry policy changed; no implicit exemptions or calibration allowed')
    scope = report.get('scope', {})
    manifest_path = root / 'config/registry_inputs.json'
    if (scope.get('all_current_registry_rasters_checked') is not False
            or type(scope.get('new_candidate_experiments')) is not int or scope['new_candidate_experiments'] != 0
            or type(scope.get('weekly_slots_used')) is not int or scope['weekly_slots_used'] != 0
            or scope.get('registry_manifest_sha256') != digest(manifest_path)):
        raise ValueError('Release audit scope changed; rerun the independent forensic audit')
    inputs = read_json(manifest_path)['inputs']
    pins = {r['id']: r for r in inputs}
    if (len(pins) != len(inputs) or scope.get('registry_rasters_opened') != len(pins)
            or not {'13GEMSDOE', '17GEMSDOE_dense_prior'} <= set(pins)):
        raise ValueError('Pinned witness count or required references changed')
    recheck_path = root / 'evidence/release_independent_review_20261027.json'
    if recheck_path.exists():
        recheck = read_json(recheck_path)
        without_time = lambda value: {k: v for k, v in value.items() if k != 'generated_utc'}
        if without_time(recheck) != without_time(report):
            raise ValueError('Independent recheck changed a measurement; decisive witness mismatch')
    rows = report.get('artifacts', [])
    if not rows or len({r['sha256'] for r in rows}) != len(rows):
        raise ValueError('Empty or repeated release inventory')
    paths = set()
    for row in rows:
        if (row.get('ok_to_submit') is not False or row.get('verdict') != 'negative'
                or row.get('surface_rank_correlation') is not None or row.get('final_rank_correlation') is not None
                or row.get('leaderboard_score_estimate') is not None or row.get('organizer_receipt') is not None):
            raise ValueError('Research artifact cannot inherit an approval, score, or unmeasured rank check')
        comparisons = row.get('comparisons', [])
        if len(comparisons) != len(pins) or {r['registry_id'] for r in comparisons} != set(pins):
            raise ValueError('Incomplete or repeated pinned-witness comparisons')
        for c in comparisons:
            pin = pins[c['registry_id']]
            overlap = c.get('overlap_3px')
            if (type(overlap) not in (int, float) or not math.isfinite(overlap) or not 0 <= overlap <= 1
                    or c.get('sha256') != pin['sha256'] or c.get('source') != pin['url']
                    or c.get('support_type') != pin.get('support_type', 'binary_dots')
                    or c.get('duplicate_stop') is not (overlap > .70)):
                raise ValueError('Witness measurement not bound to its immutable pin or literal threshold')
        witnesses = {r['registry_id'] for r in comparisons if r['overlap_3px'] > .70}
        # The lattice is measured for every file but need not reject a small
        # raster. Under the current literal finite-positive rule the dense prior
        # must still be a decisive witness; its interpretation is not silently exempted.
        if '17GEMSDOE_dense_prior' not in witnesses:
            raise ValueError('Missing decisive literal-rule witness; no release clearance inferred')
        if set(row.get('duplicate_witnesses', [])) != witnesses:
            raise ValueError('Duplicate witness list disagrees with measurements')
        lattice = next(c['overlap_3px'] for c in comparisons if c['registry_id'] == '13GEMSDOE')
        if row.get('lattice_overlap_3px') != lattice or row.get('maximum_overlap_3px') != max(c['overlap_3px'] for c in comparisons):
            raise ValueError('Displayed overlap summary disagrees with the witness table')
        aliases = row.get('aliases', [])
        if row.get('path') not in aliases:
            raise ValueError('Primary research file absent from aliases')
        for rel in aliases:
            p = _research_path(root, rel)
            if rel in paths or digest(p) != row.get('sha256') or p.stat().st_size != row.get('bytes'):
                raise ValueError(f'Changed or multiply-listed research artifact: {rel}')
            paths.add(rel)
        for key in ('validator', 'strict_all_finite_validator'):
            validator = row.get(key, {})
            if (validator.get('sha256') != row['sha256'] or validator.get('submission_approval') is not False
                    or validator.get('reference_sha256') != report['reference']['sha256']):
                raise ValueError('Validator not bound to the audited raster/reference bytes or claims approval')
    current = research_inventory(root, ('.tif', '.tiff'))
    if paths != current or scope.get('owned_tif_paths') != len(current) or scope.get('distinct_tif_sha256') != len(rows):
        raise ValueError('Changed research TIFF inventory; audit new bytes before publishing')
    zip_paths = set()
    for row in report.get('zip_archives', []):
        p = _research_path(root, row['path'])
        if row['path'] in zip_paths or row.get('ok_to_submit') is not False or digest(p) != row['sha256']:
            raise ValueError('Changed, repeated or approved research ZIP')
        if row['member_sha256'] not in {r['sha256'] for r in rows}:
            raise ValueError('ZIP is not bound to an audited research TIFF')
        with zipfile.ZipFile(p) as z:
            if z.namelist() != [row['member']] or Path(row['member']).name != row['member'] or Path(row['member']).suffix.lower() not in ('.tif', '.tiff'):
                raise ValueError('ZIP must contain exactly its single named TIFF')
            h = hashlib.sha256()
            with z.open(row['member']) as member:
                for block in iter(lambda: member.read(1 << 20), b''):
                    h.update(block)
            if h.hexdigest() != row['member_sha256']:
                raise ValueError('ZIP member digest differs from the recorded TIFF')
        zip_paths.add(row['path'])
    if research_inventory(root, ('.zip',)) != zip_paths:
        raise ValueError('Changed ZIP inventory; rerun the forensic audit')
    # An incoming lane or a stale current-card alias cannot independently grant
    # permission. Portable receipt-only fixtures may omit cards; actual builders
    # separately require the canonical card and regenerate all of its aliases.
    card_paths = [root / relative for relative in (*CANONICAL_RUN_CARDS, *NEGATIVE_RESEARCH_CARDS)]
    card_paths.extend((root / 'candidate').rglob('*.json'))
    for path in card_paths:
        if path.exists():
            card = read_json(path)
            if card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False:
                raise ValueError(f'negative-only dashboard refuses to publish conflicting card: {path.relative_to(root)}')
    return report


def validate_negative_html(root: Path) -> None:
    """Portable pre-deploy copy guard, also used outside the numerical test suite.

    This is a negative-only publisher, not a general parser of future approvals.
    Check unchanged legacy HTML as well as pages produced by the current build.
    """
    class Copy(HTMLParser):
        def __init__(self):
            super().__init__()
            self.anchor = self.heading = None
            self.anchors, self.headings, self.words = [], [], []

        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                self.anchor = [dict(attrs).get('href') or '', '']
            if tag in ('h1', 'h2', 'h3'):
                self.heading = ['']

        def handle_data(self, text):
            self.words.append(text)
            if self.anchor is not None:
                self.anchor[1] += text
            if self.heading is not None:
                self.heading[0] += text

        def handle_endtag(self, tag):
            if tag == 'a' and self.anchor is not None:
                self.anchors.append(self.anchor)
                self.anchor = None
            if tag in ('h1', 'h2', 'h3') and self.heading is not None:
                self.headings.append(self.heading[0])
                self.heading = None

    for page in [root / 'index.html', *(root / 'docs').rglob('*.html'), *(root / 'site').rglob('*.html')]:
        if not page.exists():
            continue
        if page.is_symlink():
            raise ValueError(f'Public HTML must be a regular file: {page}')
        parsed = Copy()
        parsed.feed(page.read_text(encoding='utf-8'))
        promoted_pages_hrefs = set()
        allowed = set()
        for rel in approved_candidates(root):
            allowed.add(rel); allowed.add(str(Path(rel).with_suffix('.zip')))
        page_links_promoted = False
        for href, _label in parsed.anchors:
            parts = urlsplit(href)
            rel = Path(parts.path).as_posix().lstrip('./')
            rel = rel.split('downloads/', 1)[-1]
            if any(rel.endswith(Path(a).name) for a in allowed):
                page_links_promoted = True
        for heading in parsed.headings:
            normalized = ' '.join(heading.lower().split())
            if (normalized in ('download and submit', 'submit this file', 'cleared for submission')
                    or 'ok to download and submit' in normalized):
                if page_links_promoted:
                    continue
                raise ValueError(f'Stale positive submission heading: {page}')
        words = ' '.join(' '.join(parsed.words).lower().split())
        if 'cleared exactly one' in words or re.search(r'\b[1-9]\d* files? cleared\b', words):
            raise ValueError(f'Stale positive submission badge: {page}')
        # These verbatim legacy claims materially overstated score causality,
        # masking, leakage, or portal acceptance. This is deliberately a narrow
        # negative-only copy guard, not a general scientific truth classifier.
        unsafe = ('exact path past', 'why 0.2778 won', 'portal-safe',
                  'proven empirically', 'zero-leakage holdout',
                  'zero-leakage verification')
        if any(phrase in words for phrase in unsafe):
            raise ValueError(f'Unsupported legacy campaign claim in public HTML: {page}')
        for href, label in parsed.anchors:
            parts = urlsplit(href)
            if Path(parts.path).suffix.lower() not in ('.tif', '.tiff', '.zip'):
                continue
            owned = not parts.scheme and not parts.netloc
            owned |= '/wingbangboozle1-lang/wbggemsdoe2/' in parts.path.lower()
            if not owned:
                continue
            if any(Path(a).name and Path(a).name in parts.path for a in allowed):
                continue  # registered, hash-pinned submission candidate
            if 'research' not in label.lower() or 'DO NOT SUBMIT' not in label:
                raise ValueError(f'Unqualified owned research download: {page}: {href}')
