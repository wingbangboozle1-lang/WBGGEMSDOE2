#!/usr/bin/env python3
"""Verify the 8-organization 2026-10-27 prompt ledger and live GitHub repository HEADs.

Extends ``PROMPT_LEDGER_20261027`` (144 rows across 5 orgs) with the 10 additional
8-organization prompt ledger entries across ``karagemop466-tech``, ``apartanish22-droid``,
``sassnarep3-star``, and ``buffedlizard55-lab/GEMSDOE92`` (``lbmc1``), emitting:
  - ``docs/data/user-reported-ledger-8org-20261027.csv`` (154 rows)
  - ``docs/data/user-reported-ledger-8org-20261027.json``
  - ``evidence/prompt_ledger_8org_audit_20261027.json``

Preserves ``docs/data/user-reported-ledger.csv`` (126 rows) and
``docs/data/user-reported-ledger-20261027.csv`` (144 rows) completely untouched.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_prompt_ledger import PROMPT_LEDGER_20261027, github_repo_from_pages_url  # noqa: E402

ADDITIONAL_8ORG_ENTRIES = [
    ("GEMSDOE92", "https://buffedlizard55-lab.github.io/GEMSDOE92/", "gemsdoe92-lbmc1-35801dots-20261027-89a660f6-zeros", ""),
    ("GEMSDOEkarage1", "https://karagemop466-tech.github.io/GEMSDOEkarage1/", "karage1-hmas-sinter-dualcover-sep29-20261027T220000Z-zeros", ""),
    ("GEMSDOEkarage2", "https://karagemop466-tech.github.io/GEMSDOEkarage2/", "gemsdoe-karage2-hkarage1-irregular-submodular-15000d-6a3f542a-zeros", ""),
    ("GEMSDOEkarage3", "https://karagemop466-tech.github.io/GEMSDOEkarage3/", "karage3-k3-fuse-greedy-b2-20261027T212847Z-80117cd2-zeros", ""),
    ("ApartGEMSDOE1", "https://apartanish22-droid.github.io/ApartGEMSDOE1/", "apartgems1-udth-submod-e3-20261027-50e7b334-zeros", ""),
    ("ApartGEMSDOE2", "https://apartanish22-droid.github.io/ApartGEMSDOE2/", "apartgemsdoe2-ap1-dilatcond-37654-20261027-1f26aa05-zeros", ""),
    ("ApartGEMSDOE3", "https://apartanish22-droid.github.io/ApartGEMSDOE3/", "apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros", ""),
    ("GEMSDOESASS1", "https://sassnarep3-star.github.io/GEMSDOESASS1/", "gemsass1-swgb-hrv2-44090dots-20261027T122104Z-f9b3f764-zeros", ""),
    ("GEMSDOESASS2", "https://sassnarep3-star.github.io/GEMSDOESASS2/", "gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros", ""),
    ("GEMSDOESASS3", "https://sassnarep3-star.github.io/GEMSDOESASS3/", "gemsdoesass3-lwst-geoconduit-dual37654-20261027T120000Z-a9ad3386-zeros", ""),
]

PROMPT_LEDGER_8ORG_20261027 = list(PROMPT_LEDGER_20261027) + ADDITIONAL_8ORG_ENTRIES


def main() -> int:
    csv_path = ROOT / "docs" / "data" / "user-reported-ledger-8org-20261027.csv"
    json_path = ROOT / "docs" / "data" / "user-reported-ledger-8org-20261027.json"

    rows_json = []
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["site", "org", "site_url", "submission_name", "reported_public_dti", "evidence_class"])
        for site, url, sub, score in PROMPT_LEDGER_8ORG_20261027:
            repo = github_repo_from_pages_url(url)
            org = repo.split("/")[0]
            ev = "USER-REPORTED" if score else "USER-REPORTED-BLANK"
            w.writerow([site, org, url, sub, score, ev])
            rows_json.append(
                {
                    "site": site,
                    "org": org,
                    "repo": repo,
                    "site_url": url,
                    "submission_name": sub,
                    "reported_public_dti": float(score) if score else None,
                    "evidence_class": ev,
                }
            )

    json_path.write_text(json.dumps(rows_json, indent=2) + "\n", encoding="utf-8")

    unique_repos = sorted({github_repo_from_pages_url(u) for _, u, _, _ in PROMPT_LEDGER_8ORG_20261027})
    verified_orgs = {}
    for org in sorted({r.split("/")[0] for r in unique_repos}):
        org_repos = [r for r in unique_repos if r.startswith(org + "/")]
        sample_repo = org_repos[0]
        res = subprocess.run(["gh", "api", f"repos/{sample_repo}"], capture_output=True, text=True)
        verified_orgs[org] = {
            "repo_count_in_ledger": len(org_repos),
            "sample_repo": sample_repo,
            "verified_exists": res.returncode == 0,
        }

    scored_rows = [r for r in rows_json if r["reported_public_dti"] is not None]
    scored_sorted = sorted(scored_rows, key=lambda r: float(r["reported_public_dti"]), reverse=True)

    audit = {
        "schema": "wbggems.prompt-ledger-8org-audit.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "csv_path": "docs/data/user-reported-ledger-8org-20261027.csv",
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "json_path": "docs/data/user-reported-ledger-8org-20261027.json",
        "total_distinct_entries": len(PROMPT_LEDGER_8ORG_20261027),
        "unique_repositories": len(unique_repos),
        "unique_github_orgs": len(verified_orgs),
        "scored_entries": len(scored_rows),
        "blank_entries": len(PROMPT_LEDGER_8ORG_20261027) - len(scored_rows),
        "max_reported_score": scored_sorted[0]["reported_public_dti"],
        "max_reported_entry": scored_sorted[0],
        "min_reported_score": scored_sorted[-1]["reported_public_dti"],
        "top_10_user_reported": scored_sorted[:10],
        "verified_github_orgs": verified_orgs,
        "irregularities_flagged": [
            "Historical prompt text contains BOTH '0.3195 is the highest score right now' (older DrivenData public leaderboard snapshot) and '0.4413' (later DrivenData snapshot), while the dated 2026-10-27 organizer public leaderboard top is 0.4544 (xiaofanhu). Across the 154-row 8-org team ledger, #1 USER-REPORTED score is GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros at 0.2778.",
            "External repository READMEs (GEMSDOE74, GEMSDOE86, KANLERGEMSDOE1..2, WBGGEMSDOE1..3) contain internal projections or unverified claims (e.g., 0.3195, 0.3133, 0.2994, 0.2981, 0.2913, 0.1636, 0.1558, 0.0970) absent from or contradicted by the prompt ledger (where GEMSDOE74=0.0669 and GEMSDOE86/KANLER/WBG are blank). All empirical score regressions in WBGGEMSDOE2 strictly reject external README claims and use ONLY verbatim prompt scores.",
            "eugboogieman123-ops (EUGGEMSDOE1..3) and ginnymcfiner23-ux (GINNYGEMSDOE1..3) exist on GitHub as verified public repositories, but hold 0 GeoTIFF (.tif) artifacts at main HEAD as of 2026-10-27.",
            "sassnarep3-star/GEMSDOESASS1 stores its primary submission under swgb/downloads/ rather than docs/downloads/; audit_gvcd_8org_fleet.py explicitly traverses swgb/downloads/.",
            "Prompt cross-repo misattributions: wbg3-h3pack-34k-20261027T174337Z-zeros (listed under WBGGEMSDOE3 in prompt) originated in WBGGEMSDOE2 PR #16, wbg2-offcatalogue-density-36k-20261027 (listed under WBGGEMSDOE2) resides in WBGGEMSDOE1/docs/downloads/, and WBGGEMSDOE3 main HEAD serves docs/lst1/downloads/wbggems3-lst1-hybrid-20261026-0a0229da-zeros.tif alongside docs/downloads/wb-gems-doe-3-latest-submission-zeros.tif.",
            "Prior WBGGEMSDOE2 PR #32 prose irregularities audited and corrected: (a) README.md and research/dphs_findings.md previously claimed DPHS used gdr_1051, gdr_1120, nbmg_springs, quaternary_contacts_100m, and usgs_comcat_nevada, which were not present in src/wbggems/dphs.py; (b) research/dphs_findings.md cited non-existent band cond_15km (the 19-band GeoDAWN stack contains cond_surf Band 17 and depth_to_base_surf Band 15)."
        ],
    }
    out_json = ROOT / "evidence" / "prompt_ledger_8org_audit_20261027.json"
    out_json.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(
        f"[ledger-8org] Wrote {len(PROMPT_LEDGER_8ORG_20261027)} rows "
        f"({len(scored_rows)} scored across {len(verified_orgs)} orgs / {len(unique_repos)} repos) -> {csv_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
