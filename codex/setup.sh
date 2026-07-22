#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${1:-$SCRIPT_DIR}"
DESTINATION_DIR="${2:-${CODEX_HOME:-$HOME/.codex}}"
SHARED_SKILLS_DIR="${3:-$(cd "$SCRIPT_DIR/.." && pwd)/skills}"
AGENT_SKILLS_DIR="${4:-${AGENTS_HOME:-$HOME/.agents}/skills}"

for managed_file in config.toml AGENTS.md review.config.toml; do
  if [[ ! -f "$SOURCE_DIR/$managed_file" ]]; then
    echo "Codex managed file does not exist: $SOURCE_DIR/$managed_file" >&2
    exit 1
  fi
done

for managed_link in hooks.json hooks rules; do
  if [[ ! -e "$SOURCE_DIR/$managed_link" ]]; then
    echo "Codex managed link does not exist: $SOURCE_DIR/$managed_link" >&2
    exit 1
  fi
done

bash "$SCRIPT_DIR/setup-link.sh" \
  "$SHARED_SKILLS_DIR" \
  "$AGENT_SKILLS_DIR"

mkdir -p "$DESTINATION_DIR"

for managed_file in config.toml AGENTS.md review.config.toml; do
  bash "$SCRIPT_DIR/setup-config.sh" \
    "$SOURCE_DIR/$managed_file" \
    "$DESTINATION_DIR/$managed_file"
done

for managed_link in hooks.json hooks rules; do
  bash "$SCRIPT_DIR/setup-link.sh" \
    "$SOURCE_DIR/$managed_link" \
    "$DESTINATION_DIR/$managed_link"
done
