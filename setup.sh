#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$HOME/dotfiles"

# シンボリックリンクを作成（既に正しいリンクなら何もしない）
# ファイル・ディレクトリ両対応
link_file() {
  local src="$1"
  local dest="$2"
  if [[ -L "$dest" && "$(readlink "$dest")" == "$src" ]]; then
    echo "Already linked: $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  ln -sfn "$src" "$dest"
  echo "Linked: $dest -> $src"
}

# Homebrewインストール
if ! command -v brew &>/dev/null; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "Homebrew is already installed."
fi

# Apple Silicon対応: HomebrewのPATH設定
if [[ -f /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -f /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

# Brewfileでパッケージインストール（インストール済みはスキップ、アップグレードしない）
# 一部のcaskがインストールエラーになっても他のパッケージは継続する
echo "Installing packages from Brewfile..."
if ! brew bundle --file="$DOTFILES_DIR/Brewfile" --no-upgrade 2>&1; then
  echo "Warning: Some packages failed to install (see above). Continuing..."
fi
echo "Done."

# Claude Codeインストール
if ! command -v claude &>/dev/null; then
  echo "Installing Claude Code..."
  npm install -g @anthropic-ai/claude-code
else
  echo "Claude Code is already installed."
fi

# Playwrightインストール
# npx は未インストール時に確認プロンプトを出して入力待ちでハングするため、
# --no-install を付けて「ローカル/グローバルに存在するか」だけを判定する
if ! npx --no-install playwright --version &>/dev/null; then
  echo "Installing Playwright..."
  npm install -g playwright
  npx playwright install --with-deps chromium
else
  echo "Playwright is already installed."
fi

# Wrangler（Cloudflare CLI）インストール
if ! command -v wrangler &>/dev/null; then
  echo "Installing Wrangler..."
  npm install -g wrangler@latest
else
  echo "Wrangler is already installed."
fi

# macOS設定
echo "Applying macOS settings..."
bash "$DOTFILES_DIR/macos.sh"
echo "Done."

# Git設定
link_file "$DOTFILES_DIR/git/config" "$HOME/.config/git/config"
link_file "$DOTFILES_DIR/git/ignore" "$HOME/.config/git/ignore"

# Neovim設定（ディレクトリごとリンク）
link_file "$DOTFILES_DIR/nvim" "$HOME/.config/nvim"

# Zed設定
link_file "$DOTFILES_DIR/zed/settings.json" "$HOME/.config/zed/settings.json"

# Zsh設定
link_file "$DOTFILES_DIR/zsh/.zshrc" "$HOME/.zshrc"
link_file "$DOTFILES_DIR/zsh" "$HOME/.config/zsh"

# Claude Code設定
mkdir -p "$HOME/.claude"
link_file "$DOTFILES_DIR/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
link_file "$DOTFILES_DIR/claude/settings.json" "$HOME/.claude/settings.json"
link_file "$DOTFILES_DIR/claude/statusline.sh" "$HOME/.claude/statusline.sh"
link_file "$DOTFILES_DIR/claude/rules" "$HOME/.claude/rules"
link_file "$DOTFILES_DIR/claude/skills" "$HOME/.claude/skills"
link_file "$DOTFILES_DIR/claude/agents" "$HOME/.claude/agents"

# Codex設定
# config.tomlには端末固有の状態も追記されるため、共有ひな型から初回だけ実ファイルを作る
# 旧方式で作成した管理対象シンボリックリンクは、現在の内容を保った実ファイルへ移行する
bash "$DOTFILES_DIR/codex/setup-config.sh" \
  "$DOTFILES_DIR/codex/config.toml" \
  "$HOME/.codex/config.toml"
bash "$DOTFILES_DIR/codex/setup-hooks.sh" \
  "$DOTFILES_DIR/codex/hooks.json" \
  "$HOME/.codex/hooks.json"
bash "$DOTFILES_DIR/codex/setup-hooks.sh" \
  "$DOTFILES_DIR/codex/hooks" \
  "$HOME/.codex/hooks"

# 自動アップデート用 LaunchAgent（毎日12時に brew/claude を更新）
echo "Setting up auto-update LaunchAgent..."
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_LABEL="com.shoirhi.dotfiles.autoupdate"
PLIST_SRC="$DOTFILES_DIR/launchd/$PLIST_LABEL.plist"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_LABEL.plist"
mkdir -p "$LAUNCH_AGENTS_DIR"
# plist は絶対パスが必要なため、テンプレートの __HOME__ を展開して配置する
sed "s|__HOME__|$HOME|g" "$PLIST_SRC" >"$PLIST_DEST"
# 既存のジョブがあれば一度アンロードしてから再ロード（設定変更を反映）
launchctl unload "$PLIST_DEST" 2>/dev/null || true
if launchctl load "$PLIST_DEST"; then
  echo "Loaded LaunchAgent: $PLIST_LABEL"
else
  echo "Warning: Failed to load LaunchAgent: $PLIST_LABEL"
fi

echo "Setup complete!"
