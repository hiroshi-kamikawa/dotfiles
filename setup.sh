#!/bin/bash
set -euo pipefail

dotfiles_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
zshrc="${ZDOTDIR:-$HOME}/.zshrc"

if ! command -v brew >/dev/null 2>&1; then
  for brew_bin in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$brew_bin" ]]; then
      eval "$("$brew_bin" shellenv)"
      break
    fi
  done
fi
if ! command -v brew >/dev/null 2>&1; then
  printf '先にHomebrewをインストールしてください: https://brew.sh/ja/\n' >&2
  exit 1
fi

# インストールに失敗した場合は、シェル設定を変更しない。
brew bundle install --file="$dotfiles_dir/Brewfile" --no-upgrade

# 再実行時も既定・起動時プロファイルへ適用する。文字サイズは維持する。
if osascript <<'APPLESCRIPT'
tell application "Terminal"
  set nerdFont to "MesloLGSNF-Regular"
  set font name of default settings to nerdFont
  set font name of startup settings to nerdFont
  if (font name of default settings is not nerdFont) or (font name of startup settings is not nerdFont) then
    error "フォント設定を反映できませんでした。"
  end if
end tell
APPLESCRIPT
then
  printf '標準ターミナルのフォントを MesloLGS Nerd Font に設定しました。\n'
else
  printf 'フォントの自動設定に失敗しました。ターミナルの設定で MesloLGS Nerd Font を選択してください。\n' >&2
fi

printf -v source_line 'source %q' "$dotfiles_dir/zsh/zshrc"
if [[ -f "$zshrc" ]] && grep -Fqx -- "$source_line" "$zshrc"; then
  printf '設定済みです: %s\n' "$zshrc"
  exit 0
fi
if [[ -L "$zshrc" && ! -e "$zshrc" ]] || [[ -e "$zshrc" && ! -f "$zshrc" ]]; then
  printf '通常の設定ファイルとして読み込めません: %s\n' "$zshrc" >&2
  exit 1
fi

mkdir -p -- "$(dirname -- "$zshrc")"
temporary_rc="$(mktemp "${zshrc}.tmp.XXXXXX")"
trap 'rm -f -- "$temporary_rc"' EXIT
if [[ -f "$zshrc" ]]; then
  backup="$(mktemp "${zshrc}.backup.XXXXXX")"
  cp -pL -- "$zshrc" "$backup"
  cp -pL -- "$zshrc" "$temporary_rc"
  printf '既存設定のバックアップ: %s\n' "$backup"
fi
printf '\n# Terminal settings managed by dotfiles\n%s\n' "$source_line" >> "$temporary_rc"
# 既存のシンボリックリンク先は変更せず、読み込んだ内容を引き継ぐ。
mv -f -- "$temporary_rc" "$zshrc"
printf '設定しました: %s\n新しいターミナルを開いてください。\n' "$zshrc"
