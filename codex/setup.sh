#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${1:-$SCRIPT_DIR}"
DESTINATION_DIR="${2:-${CODEX_HOME:-$HOME/.codex}}"

if [[ ! -f "$SOURCE_DIR/review.config.toml" ]]; then
  echo "Codex managed file does not exist: $SOURCE_DIR/review.config.toml" >&2
  exit 1
fi

for managed_link in AGENTS.md hooks.json hooks rules; do
  if [[ ! -e "$SOURCE_DIR/$managed_link" ]]; then
    echo "Codex managed link does not exist: $SOURCE_DIR/$managed_link" >&2
    exit 1
  fi
done

mkdir -p "$DESTINATION_DIR"

bash "$SCRIPT_DIR/setup-config.sh" \
  "$SOURCE_DIR/review.config.toml" \
  "$DESTINATION_DIR/review.config.toml"

for managed_link in AGENTS.md hooks.json hooks rules; do
  bash "$SCRIPT_DIR/setup-link.sh" \
    "$SOURCE_DIR/$managed_link" \
    "$DESTINATION_DIR/$managed_link"
done
