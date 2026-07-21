#!/bin/bash
set -euo pipefail

SOURCE_DIR="${1:?Shared skills source is required}"
DESTINATION_DIR="${2:?Agent skills destination is required}"
LINK_SCRIPT="${3:?Managed link setup script is required}"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Shared skills directory does not exist: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$DESTINATION_DIR"

for skill_dir in "$SOURCE_DIR"/*; do
  [[ -d "$skill_dir" ]] || continue
  bash "$LINK_SCRIPT" \
    "$skill_dir" \
    "$DESTINATION_DIR/$(basename "$skill_dir")"
done
