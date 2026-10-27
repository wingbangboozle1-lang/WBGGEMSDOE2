#!/usr/bin/env python3
"""Mirror the reviewed historical MSPTCD evidence without inventing new results."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = ROOT / "evidence/RUN_CARD_MSPTCD.json"
    card = json.loads(p.read_text())
    if (card.get("ok_to_submit") is not False or card.get("verdict") != "negative"
            or card.get("post_review", {}).get("promotion_evidence_valid") is not False):
        raise ValueError("Historical campaign cannot authorize release")
    for name in ("RUN_CARD_MSPTCD.json", "wbg2_msptcd_results.json", "wbg2_msptcd_canaries.json", "wbg2_msptcd_cross_lane_audit.json"):
        for folder in (ROOT / "docs/data", ROOT / "site/data"):
            shutil.copyfile(ROOT / "evidence" / name, folder / name)
    print("Mirrored reviewed historical receipts; no experiment or promotion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
