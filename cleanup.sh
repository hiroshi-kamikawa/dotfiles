#!/bin/bash
# シェル初期化ファイルを読み込まずに実行する。
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Error: python3 が必要です（このスクリプトは自動インストールしません）。' >&2
  exit 1
fi
exec python3 "$SCRIPT_DIR/scripts/cleanup.py" "$@"
