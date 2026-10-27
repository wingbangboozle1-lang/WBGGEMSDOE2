"""Fail-closed status for a competition upload.

A research run card is not a slot selection. A file is eligible to be presented as
submission-ready only when the canonical run card is positive *and* a separate,
byte-bound selector record exists. This module never uploads or edits a raster.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD_REL = Path("evidence/run_card.json")
RELEASE_REL = Path("evidence/submission_release.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _current_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
    if age < -timedelta(minutes=5) or age > timedelta(hours=24):
        return None
    return parsed


def _official_quota_source(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"drivendata.org", "www.drivendata.org"}
        and parsed.username is None and parsed.password is None
        and port in (None, 443)
        and parsed.path.startswith("/competitions/306/competition-doe-gems/")
    )


def load_submission_status(root: Path | str = ROOT) -> dict[str, Any]:
    """Return the current upload decision; missing, stale, or incomplete evidence blocks.

    The selector record is intentionally separate from the method-lane run card so
    a research-lane ``verdict: promote`` cannot by itself authorize a weekly slot.
    Required release fields are documented in ``docs/PROJECT_CHARTER.md``.
    """
    root = Path(root).resolve()
    card_path = root / RUN_CARD_REL
    if not card_path.is_file():
        return {
            "approved": False,
            "reason": "Canonical run card is missing; no file is authorized.",
            "card": None,
            "release": None,
        }

    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "approved": False,
            "reason": f"Canonical run card is unreadable ({exc}); no file is authorized.",
            "card": None,
            "release": None,
        }

    if not isinstance(card, dict):
        return {
            "approved": False,
            "reason": "Canonical run card is not a JSON object; no file is authorized.",
            "card": None,
            "release": None,
        }

    reasons: list[str] = []
    if card.get("verdict") != "promote":
        reasons.append("the canonical run card is not promoted")
    if card.get("ok_to_submit") is not True or card.get("ok_to_download_new_tif") is not True:
        reasons.append("the canonical run card does not authorize download and submission")
    candidate_sha = card.get("raster_sha256")
    submission_name = card.get("submission_name")
    submission_note = card.get("submission_note")
    if not isinstance(candidate_sha, str) or re.fullmatch(r"[0-9a-f]{64}", candidate_sha) is None:
        reasons.append("the canonical run card has no valid candidate SHA-256")
    if not isinstance(submission_name, str) or not submission_name.strip():
        reasons.append("the canonical run card has no submission name")
    if not isinstance(submission_note, str) or not submission_note.strip() or len(submission_note) > 140:
        reasons.append("the canonical run card has no valid submission note (1–140 characters)")

    try:
        current_card_sha = _sha256(card_path)
    except OSError:
        current_card_sha = None
        reasons.append("the canonical run-card bytes could not be hashed")

    release_path = root / RELEASE_REL
    release = None
    if not release_path.is_file():
        reasons.append("the separate weekly-slot selector record is absent")
    else:
        try:
            release = json.loads(release_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            reasons.append(f"the selector record is unreadable ({exc})")
            release = None
        if release is not None and not isinstance(release, dict):
            reasons.append("the selector record is not a JSON object")
            release = None

    if release is not None:
        if release.get("schema") != "wbggems.submission-release.v1":
            reasons.append("the selector record has an unsupported schema")
        if release.get("decision") != "promote":
            reasons.append("the weekly-slot selector did not promote this file")
        if current_card_sha is None or release.get("run_card_sha256") != current_card_sha:
            reasons.append("the selector record does not bind to the current run-card bytes")
        if release.get("candidate_sha256") != candidate_sha:
            reasons.append("the selector record candidate hash differs from the run card")
        if release.get("submission_name") != submission_name:
            reasons.append("the selector record name differs from the run card")
        if release.get("submission_note") != submission_note:
            reasons.append("the selector record note differs from the run card")
        if release.get("weekly_quota_checked") is not True:
            reasons.append("the current weekly quota was not confirmed by the selector")
        if _current_utc_timestamp(release.get("weekly_quota_checked_at_utc")) is None:
            reasons.append("the weekly-quota check timestamp is missing, stale, or not UTC")
        if not _official_quota_source(release.get("weekly_quota_source_url")):
            reasons.append("the weekly-quota check is not linked to the official competition page")
        remaining = release.get("remaining_weekly_slots")
        if isinstance(remaining, bool) or not isinstance(remaining, int) or not 1 <= remaining <= 3:
            reasons.append("the selector did not confirm a remaining weekly slot within the current three-slot cap")

        candidate_rel = release.get("candidate_path")
        if not isinstance(candidate_rel, str) or not candidate_rel:
            reasons.append("the selector record has no candidate path")
        else:
            try:
                candidate_path = (root / candidate_rel).resolve()
                inside_repo = root in candidate_path.parents
                exists = inside_repo and candidate_path.is_file()
            except (OSError, RuntimeError, ValueError):
                candidate_path = None
                exists = False
            if not exists or candidate_path is None:
                reasons.append("the selected candidate path is missing or outside the repository")
            elif isinstance(candidate_sha, str) and re.fullmatch(r"[0-9a-f]{64}", candidate_sha):
                try:
                    candidate_matches = _sha256(candidate_path) == candidate_sha
                except OSError:
                    candidate_matches = False
                if not candidate_matches:
                    reasons.append("the saved candidate bytes do not match the run-card SHA-256")

    # A positive run card is still insufficient unless the science, novelty, and
    # byte gates are explicit. This prevents a stale boolean from unlocking a link.
    if not isinstance(card.get("mechanism"), str) or not card["mechanism"].strip():
        reasons.append("the run card has no stated physical mechanism")
    if not isinstance(card.get("named_non_fault_mimic"), str) or not card["named_non_fault_mimic"].strip():
        reasons.append("the run card has no named non-fault mimic")

    holdout = card.get("holdout_dti")
    if not isinstance(holdout, dict):
        holdout = {}
    if holdout.get("evidence_class") != "HOLDOUT-DTI" or holdout.get("status") != "COMPLETED":
        reasons.append("a completed HOLDOUT-DTI result is not recorded")
    if not isinstance(holdout.get("evaluator_version"), str) or not holdout["evaluator_version"].strip():
        reasons.append("the HOLDOUT-DTI evaluator version is missing")
    withheld = holdout.get("withheld_positives")
    if (isinstance(withheld, bool) or not isinstance(withheld, int)
            or not 1 <= withheld <= 2**63 - 1):
        reasons.append("the HOLDOUT-DTI withheld-positive count is missing or invalid")
    value = holdout.get("value")
    value_valid = _finite_number(value) and 0 <= value <= 1
    if not value_valid:
        reasons.append("the HOLDOUT-DTI value is missing or outside [0,1]")
    ci = holdout.get("ci95")
    ci_valid = (
        isinstance(ci, list) and len(ci) == 2
        and all(_finite_number(x) for x in ci)
        and 0 <= ci[0] <= ci[1] <= 1
        and value_valid and ci[0] <= value <= ci[1]
    )
    if not ci_valid:
        reasons.append("the HOLDOUT-DTI 95% confidence interval is missing or invalid")

    validator = card.get("validator")
    if not isinstance(validator, dict):
        validator = {}
    if validator.get("status") != "PASS":
        reasons.append("the byte-read-back validator has no PASS status")
    if validator.get("validated_raster_sha256") != candidate_sha:
        reasons.append("the validator receipt is not bound to the candidate SHA-256")
    for key in ("no_nan_inside_footprint", "values_in_0_1", "crs_shape_transform_match"):
        if validator.get(key) is not True:
            reasons.append(f"the validator does not pass {key}")

    registry = card.get("registry")
    if not isinstance(registry, dict):
        registry = {}
    if registry.get("all_current_registry_rasters_checked") is not True:
        reasons.append("the complete current registry has not been checked")
    registry_manifest = registry.get("registry_manifest_sha256")
    if not isinstance(registry_manifest, str) or re.fullmatch(r"[0-9a-f]{64}", registry_manifest) is None:
        reasons.append("the full-registry manifest hash is missing")
    uniqueness = card.get("uniqueness")
    if not isinstance(uniqueness, dict):
        uniqueness = {}
    surface_corr = uniqueness.get("preplacement_surface_max_abs_correlation")
    if not _finite_number(surface_corr) or not 0 <= surface_corr <= 0.90:
        reasons.append("the pre-placement surface correlation is missing or exceeds 0.90")
    final_overlap = uniqueness.get("final_dot_max_overlap_3px")
    if not _finite_number(final_overlap) or not 0 <= final_overlap <= 0.70:
        reasons.append("the final-dot 3-pixel overlap is missing or exceeds 70%")

    return {
        "approved": not reasons,
        "reason": "Submission gates and selector record pass." if not reasons else "; ".join(reasons) + ".",
        "card": card,
        "release": release,
    }


if __name__ == "__main__":
    status = load_submission_status()
    print(json.dumps({key: value for key, value in status.items() if key != "card"}, indent=2))
    raise SystemExit(0 if status["approved"] else 1)
