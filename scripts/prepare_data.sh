#!/usr/bin/env bash
# Restore the published mirror using the shared, pinned preparation tool.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"$ROOT/scripts/bootstrap_template.sh"
PYTHON=${PYTHON:-"$ROOT/.venv/bin/python"}
if [[ ! -x "$PYTHON" ]]; then
  echo "Python environment not found: $PYTHON. See README setup." >&2
  exit 1
fi
cd "$ROOT/.cache/template"
"$PYTHON" scripts/prepare_data.py --fetch --cache-bands
echo 'Data are in .cache/template; this is a hash-verified third-party mirror, not an official download receipt.'
