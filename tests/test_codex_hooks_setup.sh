#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETUP_SCRIPT="$ROOT_DIR/codex/setup-hooks.sh"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

assert_link_to() {
  local expected="$1"
  local path="$2"

  [[ -L "$path" ]] || {
    echo "Expected a symbolic link: $path" >&2
    return 1
  }
  [[ "$(readlink "$path")" == "$expected" ]] || {
    echo "Unexpected link target: $path" >&2
    return 1
  }
}

SOURCE="$TEST_DIR/source/hooks.json"
mkdir -p "$(dirname "$SOURCE")"
printf '%s\n' '{"hooks":{}}' >"$SOURCE"

# 未作成なら、管理対象ファイルへのリンクを作る。
MISSING_DEST="$TEST_DIR/missing/hooks.json"
bash "$SETUP_SCRIPT" "$SOURCE" "$MISSING_DEST"
assert_link_to "$SOURCE" "$MISSING_DEST"

# 既に正しいリンクなら、そのまま維持する。
bash "$SETUP_SCRIPT" "$SOURCE" "$MISSING_DEST"
assert_link_to "$SOURCE" "$MISSING_DEST"

# 同じ内容の既存ファイルは、安全に管理対象リンクへ移行する。
MATCHING_DEST="$TEST_DIR/matching/hooks.json"
mkdir -p "$(dirname "$MATCHING_DEST")"
cp "$SOURCE" "$MATCHING_DEST"
bash "$SETUP_SCRIPT" "$SOURCE" "$MATCHING_DEST"
assert_link_to "$SOURCE" "$MATCHING_DEST"

# 内容の異なる既存ファイルは上書きしない。
CONFLICT_DEST="$TEST_DIR/conflict/hooks.json"
mkdir -p "$(dirname "$CONFLICT_DEST")"
printf '%s\n' '{"hooks":{"Stop":[]}}' >"$CONFLICT_DEST"
if bash "$SETUP_SCRIPT" "$SOURCE" "$CONFLICT_DEST"; then
  echo "Expected conflicting hooks setup to fail" >&2
  exit 1
fi
[[ ! -L "$CONFLICT_DEST" ]]
[[ "$(<"$CONFLICT_DEST")" == '{"hooks":{"Stop":[]}}' ]]

# 管理外のシンボリックリンクも上書きしない。
OTHER_TARGET="$TEST_DIR/other-hooks.json"
OTHER_DEST="$TEST_DIR/other/hooks.json"
printf '%s\n' '{"hooks":{"SessionStart":[]}}' >"$OTHER_TARGET"
mkdir -p "$(dirname "$OTHER_DEST")"
ln -s "$OTHER_TARGET" "$OTHER_DEST"
if bash "$SETUP_SCRIPT" "$SOURCE" "$OTHER_DEST"; then
  echo "Expected unmanaged hooks link setup to fail" >&2
  exit 1
fi
assert_link_to "$OTHER_TARGET" "$OTHER_DEST"

# hookスクリプトのディレクトリも同じ安全規則でリンクする。
SCRIPTS_SOURCE="$TEST_DIR/source/hooks"
SCRIPTS_DEST="$TEST_DIR/scripts/hooks"
mkdir -p "$SCRIPTS_SOURCE"
printf '%s\n' '#!/bin/sh' >"$SCRIPTS_SOURCE/example.sh"
bash "$SETUP_SCRIPT" "$SCRIPTS_SOURCE" "$SCRIPTS_DEST"
assert_link_to "$SCRIPTS_SOURCE" "$SCRIPTS_DEST"

echo "Codex hooks setup tests passed."
