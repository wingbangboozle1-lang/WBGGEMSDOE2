#!/usr/bin/env bash
# Restore the hash-pinned competition mirrors and build the local band cache.
#
# This fetches *public owner-mirror bytes* through the GitHub API and verifies
# every file against a pinned SHA-256.  It is NOT an authenticated DrivenData
# download: the official data page requires login and no credentials are read or
# stored here.  Large files land in data/ and .cache/, both of which are ignored
# by Git.
#
# Usage:  bash scripts/get_data.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --quiet -r requirements.txt

python scripts/prepare_data.py --fetch --cache-bands

# Flatten the 19-band stack into a memory-mapped float32 bank used by the
# generator (933 MB, ignored by Git).  Band statistics are recorded alongside so
# the robust z-score is reproducible.
python scripts/build_feature_bank.py

echo "[ok] data restored and feature bank built"
