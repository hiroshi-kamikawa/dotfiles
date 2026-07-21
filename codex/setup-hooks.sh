#!/bin/bash
set -euo pipefail

HOOKS_SOURCE="${1:?Codex hooks source is required}"
HOOKS_DESTINATION="${2:?Codex hooks destination is required}"

if [[ ! -e "$HOOKS_SOURCE" ]]; then
  echo "Codex hooks source does not exist: $HOOKS_SOURCE" >&2
  exit 1
fi

mkdir -p "$(dirname "$HOOKS_DESTINATION")"

if [[ -L "$HOOKS_DESTINATION" ]]; then
  LINK_TARGET="$(readlink "$HOOKS_DESTINATION")"

  if [[ "$LINK_TARGET" == "$HOOKS_SOURCE" ]]; then
    echo "Already linked: $HOOKS_DESTINATION"
    exit 0
  fi

  echo "Refusing to replace unmanaged Codex hooks link: $HOOKS_DESTINATION -> $LINK_TARGET" >&2
  exit 1
fi

if [[ -e "$HOOKS_DESTINATION" ]]; then
  if [[ -d "$HOOKS_SOURCE" || -d "$HOOKS_DESTINATION" ]]; then
    echo "Refusing to replace existing Codex hooks path: $HOOKS_DESTINATION" >&2
    exit 1
  fi

  if ! cmp -s "$HOOKS_SOURCE" "$HOOKS_DESTINATION"; then
    echo "Refusing to replace different Codex hooks: $HOOKS_DESTINATION" >&2
    exit 1
  fi

  rm "$HOOKS_DESTINATION"
fi

ln -s "$HOOKS_SOURCE" "$HOOKS_DESTINATION"
echo "Linked: $HOOKS_DESTINATION -> $HOOKS_SOURCE"
