#!/bin/bash
set -euo pipefail

CONFIG_SOURCE="${1:?Codex managed file source is required}"
CONFIG_DESTINATION="${2:?Codex managed file destination is required}"

if [[ ! -f "$CONFIG_SOURCE" ]]; then
  echo "Codex managed file source does not exist: $CONFIG_SOURCE" >&2
  exit 1
fi

DESTINATION_DIR="$(dirname "$CONFIG_DESTINATION")"
mkdir -p "$DESTINATION_DIR"

SOURCE_PATH="$(cd "$(dirname "$CONFIG_SOURCE")" && printf '%s/%s' "$(pwd -P)" "$(basename "$CONFIG_SOURCE")")"
DESTINATION_PATH="$(cd "$DESTINATION_DIR" && printf '%s/%s' "$(pwd -P)" "$(basename "$CONFIG_DESTINATION")")"

if [[ "$SOURCE_PATH" == "$DESTINATION_PATH" ]]; then
  echo "Refusing to overwrite a Codex managed file with itself: $SOURCE_PATH" >&2
  exit 1
fi

case "$SOURCE_PATH/" in
  "$DESTINATION_PATH/"*)
    echo "Refusing to replace a directory that contains the Codex managed source: $CONFIG_DESTINATION" >&2
    exit 1
    ;;
esac

if [[ -d "$CONFIG_DESTINATION" && ! -L "$CONFIG_DESTINATION" ]]; then
  echo "Refusing to replace a directory with a Codex managed file: $CONFIG_DESTINATION" >&2
  exit 1
fi

TEMP_CONFIG="$(mktemp "$DESTINATION_DIR/.codex-managed.XXXXXX")"
trap 'rm -f "$TEMP_CONFIG"' EXIT
cp "$CONFIG_SOURCE" "$TEMP_CONFIG"
chmod 600 "$TEMP_CONFIG"

BACKUP_PATH=""
if [[ -e "$CONFIG_DESTINATION" || -L "$CONFIG_DESTINATION" ]]; then
  BACKUP_PATH="$(mktemp -d "$DESTINATION_DIR/.codex-replaced.XXXXXX")"
  rmdir "$BACKUP_PATH"
  mv "$CONFIG_DESTINATION" "$BACKUP_PATH"
fi

if ! mv "$TEMP_CONFIG" "$CONFIG_DESTINATION"; then
  if [[ -n "$BACKUP_PATH" && -e "$BACKUP_PATH" ]]; then
    mv "$BACKUP_PATH" "$CONFIG_DESTINATION"
  fi
  exit 1
fi

trap - EXIT

if [[ -n "$BACKUP_PATH" ]]; then
  rm -rf -- "$BACKUP_PATH"
fi

echo "Overwrote Codex managed file: $CONFIG_DESTINATION"
