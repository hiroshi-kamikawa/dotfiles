#!/bin/bash
set -euo pipefail

MANAGED_SOURCE="${1:?Codex managed link source is required}"
MANAGED_DESTINATION="${2:?Codex managed link destination is required}"

if [[ ! -e "$MANAGED_SOURCE" ]]; then
  echo "Codex managed link source does not exist: $MANAGED_SOURCE" >&2
  exit 1
fi

DESTINATION_DIR="$(dirname "$MANAGED_DESTINATION")"
mkdir -p "$DESTINATION_DIR"

SOURCE_PATH="$(cd "$(dirname "$MANAGED_SOURCE")" && printf '%s/%s' "$(pwd -P)" "$(basename "$MANAGED_SOURCE")")"
DESTINATION_PATH="$(cd "$DESTINATION_DIR" && printf '%s/%s' "$(pwd -P)" "$(basename "$MANAGED_DESTINATION")")"

if [[ "$SOURCE_PATH" == "$DESTINATION_PATH" ]]; then
  echo "Refusing to link a Codex managed path to itself: $SOURCE_PATH" >&2
  exit 1
fi

if [[ -d "$MANAGED_SOURCE" ]]; then
  case "$DESTINATION_PATH/" in
    "$SOURCE_PATH/"*)
      echo "Refusing to create a Codex managed link inside its source: $MANAGED_DESTINATION" >&2
      exit 1
      ;;
  esac

  case "$SOURCE_PATH/" in
    "$DESTINATION_PATH/"*)
      echo "Refusing to replace a directory that contains the Codex managed source: $MANAGED_DESTINATION" >&2
      exit 1
      ;;
  esac
fi

if [[ -L "$MANAGED_DESTINATION" && "$(readlink "$MANAGED_DESTINATION")" == "$MANAGED_SOURCE" ]]; then
  echo "Already linked: $MANAGED_DESTINATION"
  exit 0
fi

BACKUP_PATH=""
if [[ -e "$MANAGED_DESTINATION" || -L "$MANAGED_DESTINATION" ]]; then
  BACKUP_PATH="$(mktemp -d "$DESTINATION_DIR/.codex-replaced.XXXXXX")"
  rmdir "$BACKUP_PATH"
  mv "$MANAGED_DESTINATION" "$BACKUP_PATH"
fi

if ! ln -s "$MANAGED_SOURCE" "$MANAGED_DESTINATION"; then
  if [[ -n "$BACKUP_PATH" && -e "$BACKUP_PATH" ]]; then
    mv "$BACKUP_PATH" "$MANAGED_DESTINATION"
  fi
  exit 1
fi

if [[ -n "$BACKUP_PATH" ]]; then
  rm -rf -- "$BACKUP_PATH"
fi

echo "Overwrote Codex managed link: $MANAGED_DESTINATION -> $MANAGED_SOURCE"
