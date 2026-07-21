#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETUP_SCRIPT="$ROOT_DIR/codex/setup-config.sh"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

assert_regular_file() {
  local path="$1"
  [[ -f "$path" && ! -L "$path" ]] || {
    echo "Expected a regular file: $path" >&2
    return 1
  }
}

assert_content() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(<"$path")"
  [[ "$actual" == "$expected" ]] || {
    echo "Unexpected content in: $path" >&2
    return 1
  }
}

TEMPLATE="$TEST_DIR/config.toml"
printf '%s\n' 'approval_policy = "on-request"' >"$TEMPLATE"

# 未作成なら、共有ひな型から端末ローカルの実ファイルを作る。
MISSING_DEST="$TEST_DIR/missing/config.toml"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$MISSING_DEST"
assert_regular_file "$MISSING_DEST"
assert_content 'approval_policy = "on-request"' "$MISSING_DEST"
[[ "$(stat -f '%Lp' "$MISSING_DEST")" == "600" ]]

# 既存の端末ローカル設定は上書きしない。
EXISTING_DEST="$TEST_DIR/existing/config.toml"
mkdir -p "$(dirname "$EXISTING_DEST")"
printf '%s\n' 'local = true' >"$EXISTING_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$EXISTING_DEST"
assert_regular_file "$EXISTING_DEST"
assert_content 'local = true' "$EXISTING_DEST"

# 旧方式の管理対象リンクは、内容を保った実ファイルへ移行する。
MANAGED_DEST="$TEST_DIR/managed/config.toml"
mkdir -p "$(dirname "$MANAGED_DEST")"
ln -s "$TEMPLATE" "$MANAGED_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$MANAGED_DEST"
assert_regular_file "$MANAGED_DEST"
assert_content 'approval_policy = "on-request"' "$MANAGED_DEST"

# 管理外のリンクは変更しない。
OTHER_TARGET="$TEST_DIR/other.toml"
OTHER_DEST="$TEST_DIR/other/config.toml"
printf '%s\n' 'other = true' >"$OTHER_TARGET"
mkdir -p "$(dirname "$OTHER_DEST")"
ln -s "$OTHER_TARGET" "$OTHER_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$OTHER_DEST"
[[ -L "$OTHER_DEST" ]]
[[ "$(readlink "$OTHER_DEST")" == "$OTHER_TARGET" ]]

echo "Codex config setup tests passed."
