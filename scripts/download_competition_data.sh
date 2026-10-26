#!/usr/bin/env bash
# Restores the pinned public owner mirror; not an authenticated official download.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" "$ROOT/scripts/prepare_data.py" --fetch "$@"
