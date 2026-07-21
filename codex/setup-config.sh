#!/bin/bash
set -euo pipefail

CONFIG_SOURCE="${1:?Codex config source is required}"
CONFIG_DESTINATION="${2:?Codex config destination is required}"

mkdir -p "$(dirname "$CONFIG_DESTINATION")"

if [[ -L "$CONFIG_DESTINATION" ]]; then
  LINK_TARGET="$(readlink "$CONFIG_DESTINATION")"

  if [[ "$LINK_TARGET" != "$CONFIG_SOURCE" ]]; then
    echo "Kept unmanaged Codex config link: $CONFIG_DESTINATION -> $LINK_TARGET"
    exit 0
  fi

  TEMP_CONFIG="$(mktemp "$(dirname "$CONFIG_DESTINATION")/.config.toml.XXXXXX")"
  cp "$CONFIG_DESTINATION" "$TEMP_CONFIG"
  chmod 600 "$TEMP_CONFIG"
  rm "$CONFIG_DESTINATION"
  mv "$TEMP_CONFIG" "$CONFIG_DESTINATION"
  echo "Migrated Codex config link to a local file: $CONFIG_DESTINATION"
  exit 0
fi

if [[ -e "$CONFIG_DESTINATION" ]]; then
  echo "Kept local Codex config: $CONFIG_DESTINATION"
  exit 0
fi

cp "$CONFIG_SOURCE" "$CONFIG_DESTINATION"
chmod 600 "$CONFIG_DESTINATION"
echo "Created local Codex config: $CONFIG_DESTINATION"
