#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETUP_SCRIPT="$ROOT_DIR/codex/setup-link.sh"
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

# 内容の異なる既存ファイルも管理対象リンクへ置き換える。
CONFLICT_DEST="$TEST_DIR/conflict/hooks.json"
mkdir -p "$(dirname "$CONFLICT_DEST")"
printf '%s\n' '{"hooks":{"Stop":[]}}' >"$CONFLICT_DEST"
bash "$SETUP_SCRIPT" "$SOURCE" "$CONFLICT_DEST"
assert_link_to "$SOURCE" "$CONFLICT_DEST"

# 管理外のシンボリックリンクも管理対象リンクへ置き換える。
OTHER_TARGET="$TEST_DIR/other-hooks.json"
OTHER_DEST="$TEST_DIR/other/hooks.json"
printf '%s\n' '{"hooks":{"SessionStart":[]}}' >"$OTHER_TARGET"
mkdir -p "$(dirname "$OTHER_DEST")"
ln -s "$OTHER_TARGET" "$OTHER_DEST"
bash "$SETUP_SCRIPT" "$SOURCE" "$OTHER_DEST"
assert_link_to "$SOURCE" "$OTHER_DEST"
[[ "$(<"$OTHER_TARGET")" == '{"hooks":{"SessionStart":[]}}' ]]

# 壊れたリンクも管理対象リンクへ置き換える。
BROKEN_DEST="$TEST_DIR/broken/hooks.json"
mkdir -p "$(dirname "$BROKEN_DEST")"
ln -s "$TEST_DIR/missing-hooks.json" "$BROKEN_DEST"
bash "$SETUP_SCRIPT" "$SOURCE" "$BROKEN_DEST"
assert_link_to "$SOURCE" "$BROKEN_DEST"

# hookスクリプトのディレクトリも同じ安全規則でリンクする。
SCRIPTS_SOURCE="$TEST_DIR/source/hooks"
SCRIPTS_DEST="$TEST_DIR/scripts/hooks"
mkdir -p "$SCRIPTS_SOURCE"
printf '%s\n' '#!/bin/sh' >"$SCRIPTS_SOURCE/example.sh"
bash "$SETUP_SCRIPT" "$SCRIPTS_SOURCE" "$SCRIPTS_DEST"
assert_link_to "$SCRIPTS_SOURCE" "$SCRIPTS_DEST"

# 既存ディレクトリも管理対象ディレクトリへのリンクへ置き換える。
EXISTING_SCRIPTS_DEST="$TEST_DIR/existing-scripts/hooks"
mkdir -p "$EXISTING_SCRIPTS_DEST"
printf '%s\n' '#!/bin/sh' >"$EXISTING_SCRIPTS_DEST/old.sh"
bash "$SETUP_SCRIPT" "$SCRIPTS_SOURCE" "$EXISTING_SCRIPTS_DEST"
assert_link_to "$SCRIPTS_SOURCE" "$EXISTING_SCRIPTS_DEST"

# 管理元と適用先が同一の場合は、自己参照リンク化を避けるため拒否する。
SELF_SOURCE="$TEST_DIR/source/self.json"
printf '%s\n' '{"hooks":{}}' >"$SELF_SOURCE"
if bash "$SETUP_SCRIPT" "$SELF_SOURCE" "$SELF_SOURCE"; then
  echo "Expected identical hooks paths to fail" >&2
  exit 1
fi
[[ -f "$SELF_SOURCE" && ! -L "$SELF_SOURCE" ]]

# 管理元がない場合は失敗し、既存の適用先を保持する。
MISSING_SOURCE_DEST="$TEST_DIR/missing-source/hooks.json"
mkdir -p "$(dirname "$MISSING_SOURCE_DEST")"
printf '%s\n' '{"local":true}' >"$MISSING_SOURCE_DEST"
if bash "$SETUP_SCRIPT" "$TEST_DIR/does-not-exist.json" "$MISSING_SOURCE_DEST"; then
  echo "Expected missing hooks source to fail" >&2
  exit 1
fi
[[ "$(<"$MISSING_SOURCE_DEST")" == '{"local":true}' ]]

if find "$TEST_DIR" -name '.codex-replaced.*' | grep -q .; then
  echo "Expected no temporary setup paths" >&2
  exit 1
fi

echo "Codex hooks setup tests passed."
