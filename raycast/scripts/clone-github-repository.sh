#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Clone GitHub Repository
# @raycast.mode compact

# Optional parameters:
# @raycast.packageName Developer Tools
# @raycast.description Clone a GitHub repository to ~/dev and open it in Zed
# @raycast.argument1 { "type": "text", "placeholder": "owner/repository or GitHub URL" }

set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

REPO="$1"
ROOT="$HOME/dev"

NAME="${REPO##*/}"
NAME="${NAME%.git}"
DEST="$ROOT/$NAME"

mkdir -p "$ROOT"

if [[ -e "$DEST" ]]; then
  echo "Already exists. Opening in Zed."
  zed "$DEST"
  exit 0
fi

gh repo clone "$REPO" "$DEST"
zed "$DEST"

echo "Cloned and opened: $REPO"