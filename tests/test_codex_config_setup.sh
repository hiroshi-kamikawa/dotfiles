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

# 既存の端末ローカル設定は共有設定で上書きする。
EXISTING_DEST="$TEST_DIR/existing/config.toml"
mkdir -p "$(dirname "$EXISTING_DEST")"
printf '%s\n' 'local = true' >"$EXISTING_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$EXISTING_DEST"
assert_regular_file "$EXISTING_DEST"
assert_content 'approval_policy = "on-request"' "$EXISTING_DEST"
[[ "$(stat -f '%Lp' "$EXISTING_DEST")" == "600" ]]

# 旧方式の管理対象リンクも、現在の共有設定で実ファイルへ置き換える。
MANAGED_DEST="$TEST_DIR/managed/config.toml"
mkdir -p "$(dirname "$MANAGED_DEST")"
printf '%s\n' 'approval_policy = "never"' >"$TEMPLATE"
ln -s "$TEMPLATE" "$MANAGED_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$MANAGED_DEST"
assert_regular_file "$MANAGED_DEST"
assert_content 'approval_policy = "never"' "$MANAGED_DEST"

# 管理外のリンクも共有設定の実ファイルへ置き換える。
OTHER_TARGET="$TEST_DIR/other.toml"
OTHER_DEST="$TEST_DIR/other/config.toml"
printf '%s\n' 'other = true' >"$OTHER_TARGET"
mkdir -p "$(dirname "$OTHER_DEST")"
ln -s "$OTHER_TARGET" "$OTHER_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$OTHER_DEST"
assert_regular_file "$OTHER_DEST"
assert_content 'approval_policy = "never"' "$OTHER_DEST"
assert_content 'other = true' "$OTHER_TARGET"

# 壊れたリンクも共有設定の実ファイルへ置き換える。
BROKEN_DEST="$TEST_DIR/broken/config.toml"
mkdir -p "$(dirname "$BROKEN_DEST")"
ln -s "$TEST_DIR/missing-target.toml" "$BROKEN_DEST"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$BROKEN_DEST"
assert_regular_file "$BROKEN_DEST"
assert_content 'approval_policy = "never"' "$BROKEN_DEST"

# 再実行時も更新された共有設定で上書きする。
printf '%s\n' 'approval_policy = "untrusted"' >"$TEMPLATE"
bash "$SETUP_SCRIPT" "$TEMPLATE" "$EXISTING_DEST"
assert_content 'approval_policy = "untrusted"' "$EXISTING_DEST"

# 宛先がディレクトリの場合は、予期しない削除を避けて拒否する。
DIRECTORY_DEST="$TEST_DIR/directory/config.toml"
mkdir -p "$DIRECTORY_DEST"
printf '%s\n' 'old' >"$DIRECTORY_DEST/old.toml"
if bash "$SETUP_SCRIPT" "$TEMPLATE" "$DIRECTORY_DEST"; then
  echo "Expected directory config destination to fail" >&2
  exit 1
fi
[[ "$(<"$DIRECTORY_DEST/old.toml")" == "old" ]]

# 管理元がない場合は失敗し、既存の適用先を保持する。
MISSING_SOURCE_DEST="$TEST_DIR/missing-source/config.toml"
mkdir -p "$(dirname "$MISSING_SOURCE_DEST")"
printf '%s\n' 'local = true' >"$MISSING_SOURCE_DEST"
if bash "$SETUP_SCRIPT" "$TEST_DIR/does-not-exist.toml" "$MISSING_SOURCE_DEST"; then
  echo "Expected missing config source to fail" >&2
  exit 1
fi
assert_content 'local = true' "$MISSING_SOURCE_DEST"

# 管理元と適用先が同一の場合は、破壊を避けるため拒否する。
if bash "$SETUP_SCRIPT" "$TEMPLATE" "$TEMPLATE"; then
  echo "Expected identical config paths to fail" >&2
  exit 1
fi
assert_content 'approval_policy = "untrusted"' "$TEMPLATE"

if find "$TEST_DIR" -name '.codex-managed.*' -o -name '.codex-replaced.*' | grep -q .; then
  echo "Expected no temporary setup files" >&2
  exit 1
fi

echo "Codex config setup tests passed."
