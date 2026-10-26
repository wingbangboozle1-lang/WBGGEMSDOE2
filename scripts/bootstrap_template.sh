#!/usr/bin/env bash
# Fetch the shared upstream template at an immutable commit. No source forks.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REF=822a0ce5546c7b6749cdd82eb145b6b3e616603d
TEMPLATE="$ROOT/.cache/template"
if [[ ! -f "$TEMPLATE/src/gems57/evaluate_holdout.py" ]]; then
  mkdir -p "$ROOT/.cache"
  work=$(mktemp -d "$ROOT/.cache/template-restore.XXXXXX")
  trap 'rm -rf "$work"' EXIT
  curl --fail --location --silent --show-error --retry 2 \
    "https://codeload.github.com/buffedlizard55-lab/57GEMSDOE/tar.gz/$REF" \
    -o "$work/template.tar.gz"
  mkdir "$work/unpacked"
  tar -xzf "$work/template.tar.gz" -C "$work/unpacked" --strip-components=1
  (cd "$work/unpacked" && sha256sum --check --status "$ROOT/site-data/template-sha256.txt") || {
    echo 'Shared template verification failed; refusing to use it.' >&2; exit 1;
  }
  if [[ -e "$TEMPLATE" ]]; then
    echo 'Incomplete template directory exists; remove only .cache/template and retry.' >&2
    exit 1
  fi
  mv "$work/unpacked" "$TEMPLATE"
fi
(cd "$TEMPLATE" && sha256sum --check --status "$ROOT/site-data/template-sha256.txt") || {
  echo 'Shared template has changed; refusing to use a private fork.' >&2; exit 1;
}
echo "Shared template verified at $REF (read-only source)."
