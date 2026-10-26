#!/usr/bin/env python3
"""Cache unchanged shared template code from an immutable public GitHub commit.

The result is a local, gitignored dependency, not a private evaluator fork.
The template's full-catalogue geometry cache must NOT be used in a holdout fold.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from restore_public_mirrors import fetch_blob

REPO = "buffedlizard55-lab/57GEMSDOE"
COMMIT = "822a0ce5546c7b6749cdd82eb145b6b3e616603d"


def restore(destination: Path):
    tree = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/git/trees/{COMMIT}?recursive=1"]))
    if tree.get("truncated") or "tree" not in tree:
        raise ValueError("upstream template inventory is incomplete")
    selected = [x for x in tree["tree"] if x["type"] == "blob" and
                (x["path"].startswith("src/gems57/") and x["path"].endswith(".py")
                 or x["path"] in {"tests/test_evaluate_holdout.py", "scripts/prep_feature_stack.py"})]
    required = {"src/gems57/evaluate_holdout.py", "src/gems57/submission_writer.py",
                "src/gems57/metric.py", "src/gems57/holdout.py"}
    if not required.issubset({x["path"] for x in selected}):
        raise ValueError("shared template is missing an essential module")
    for item in selected:
        p = PurePosixPath(item["path"])
        if p.is_absolute() or ".." in p.parts:
            raise ValueError("unsafe upstream path")
        fetch_blob(REPO, item["sha"], item["size"], destination.joinpath(*p.parts))
    print(f"Cached {len(selected)} unmodified shared files from {REPO}@{COMMIT}")
    print("The derived bank_u8.npy cache is NOT included in this public tree; no holdout was run.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("data/shared_template"))
    args = parser.parse_args()
    try:
        restore(args.destination)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Template restore failed: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
