#!/usr/bin/env python3
"""Render the reviewed hypothesis shortlist from its structured source of truth."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config/research_hypotheses.json"
OUTPUT = ROOT / "research/hypotheses.md"


def render(data: dict) -> str:
    hypotheses = data.get("hypotheses")
    if not isinstance(hypotheses, list) or not 3 <= len(hypotheses) <= 5:
        raise ValueError("The shortlist must contain between three and five hypotheses")
    ranks = [row.get("potential_rank") for row in hypotheses]
    if sorted(ranks) != list(range(1, len(hypotheses) + 1)):
        raise ValueError("Hypothesis potential ranks must be unique and contiguous")
    lane = data.get("method_lane", {})
    if lane.get("status") != "UNASSIGNED":
        raise ValueError("This review must not self-assign the missing parallel method lane")
    if lane.get("experiments_run_in_this_review_lane") != 0:
        raise ValueError("This documentation-only review has no experiment run")

    lines = [
        "# Ranked research hypotheses — none cleared for implementation",
        "",
        f"**Editorial review:** {data['reviewed_utc']} UTC. These are proposals, not results.",
        "",
        f"**Method lane: UNASSIGNED.** {lane['reason']}",
        "",
        "No experiment was run in this review lane. The qualitative ranking below is a judgment about relative potential to improve spatially blocked HOLDOUT-DTI and implementation cost—not a score, a DTI delta, a probability of winning, or a leaderboard forecast. No candidate is selected for a weekly slot.",
        "",
        data["novelty_scope"],
        "",
        "The supplied feature-layer names are from the hash-checked owner-mirrored 19-band manifest, not an authenticated DrivenData download. The local cache and derived shared feature bank are absent in this checkout. The official feature description and owner-mirror band metadata disagree about the depth layer; retain the official term ‘depth to conductive base’ unless original metadata resolves it.",
        "",
        "## Qualitative ranking",
        "",
        "| Potential rank | Proposal | Expected HOLDOUT-DTI potential (qualitative, untested) | Implementation cost | Status |",
        "|---:|---|---|---|---|",
    ]
    for h in sorted(hypotheses, key=lambda row: row["potential_rank"]):
        lines.append(
            f"| {h['potential_rank']} | **{h['id']} — {h['title']}** | "
            f"{h['potential_label']} | {h['implementation_cost']} | Proposal only; not run |"
        )
    lines.extend(["", "## Candidate mechanisms and disconfirming alternatives", ""])
    for h in sorted(hypotheses, key=lambda row: row["potential_rank"]):
        lines.extend([
            f"### {h['id']} — {h['title']}",
            "",
            f"- **Layers:** {'; '.join(h['layers'])}.",
            f"- **Physical signature:** {h['signature']}",
            f"- **Why it might find an uncatalogued fault:** {h['why_uncatalogued']}",
            f"- **Difference from reviewed methods:** {h['difference_from_reviewed_methods']}",
            f"- **Named non-fault mimic:** {h['non_fault_mimic']}",
            f"- **Data/access status:** {h['data_status']}",
        ])
        external = h.get("external_data")
        if external:
            lines.append(
                f"- **Specific official external source:** [{external['source']}]({external['url']}). "
                f"{external['access_check']}"
            )
        if h.get("sources"):
            sources = " · ".join(f"[{url}]({url})" for url in h["sources"])
            lines.append(f"- **Source links for manual review:** {sources}")
        lines.append("")

    lines.extend([
        "## Why no candidate was validated",
        "",
        "The requested literal registry gate is fail-closed. The registered stride-5 binary lattice forces more than 70% three-pixel overlap for the standard 37,654-distinct-dot budget. Separately, a registered continuous prior is positive throughout the footprint; if the pinned shared finite-positive support definition applies to it, every nonempty candidate has 100% overlap. Whether a continuous field should count as ‘dots’ is unresolved, so no exemption is assumed. The inventory is incomplete and does not establish global uniqueness.",
        "",
        "The current checkout also lacks the competition rasters and derived feature cache. No spatial holdout, feature-alone leakage canary, matched incumbent comparison, or confidence interval can be reported. Do not substitute a projection or a previously reported parallel result for a protocol-valid HOLDOUT-DTI.",
        "",
        "## Gates before any experiment or slot selector",
        "",
        "1. Resolve the continuous-prior interpretation and restore an immutable, complete, fresh registry; do not move dots to exploit edge cells.",
        "2. Record the explicit assigned method lane. This shortlist does not assign one.",
        "3. Restore and authenticate the competition inputs and exact shared cached feature stack. Keep the pinned shared evaluator/writer unchanged; report any defect upstream.",
        "4. For each feature alone, compute the leakage canary on every spatially blocked fold. Treat AUC above 0.90 (or its inverse) as leakage until disproven. Derive all catalogue-based features only from visible faults, withhold whole segments plus a buffer, and mask visible faults pixel-exactly.",
        "5. Use the shared pooled DTI evaluator (alpha 0.2, beta 0.8, 300 m triangular kernel), compare against a matched incumbent on identical folds, and report evaluator version, withheld-positive count, and a spatial-block 95% CI.",
        "6. Stop at three experiments or two hours. A holdout result is not an organizer-confirmed score; a format pass is not uniqueness or promotion. Slot selection remains a separate, quota-aware action.",
        "",
        "## Official and scientific references",
        "",
        "- [DrivenData problem description and provided-feature inventory](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — faults are the prediction target; geothermal favorability is not itself a fault label.",
        "- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — magnetic/radiometric survey context and acquisition limitations.",
        "- [USGS Argenta Rise study](https://pubs.usgs.gov/publication/70271418) — independent multi-physics context; does not validate the proposed transforms.",
        "- [USGS blind geothermal play-fairway synthesis](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and) — geothermal context; not a direct submission-score result.",
        "- [DOE GDR INGENIOUS release 1391](https://gdr.openei.org/submissions/1391) — regional data compilation and license information; specific files were not fetched here.",
        "- [USGS 3DEP products and services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) — the official source named for H3; exact tiles/coverage remain unverified.",
        "",
        "**Evidence note:** Research/source pages were last checked in the repository's source register on 2026-10-26 UTC. This editorial review did not fetch the external non-GitHub hosts; see [`research/sources.md`](sources.md) for the recorded access status and limitations.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    text = render(data)
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Rendered {len(data['hypotheses'])} proposals; lane remains UNASSIGNED; no experiment performed.")


if __name__ == "__main__":
    main()
