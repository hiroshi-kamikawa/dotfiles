# dotfiles

macOS の個人設定。ターミナル・Neovim・IDEのカスタマイズは管理対象から外し、
ルートの `setup.sh` を `cleanup.sh` に置き換えた。
Git、Codex、Raycast、Dock/Finderなどの `macos.sh` は残している。
`Brewfile` は残す開発ツール・アプリの一覧で、cleanup時にはインストールしない。

## クリーンアップ

Python 3 と macOS が必要。リポジトリの配置場所は任意。
まず変更対象を表示する（Macの設定は変更しない）。

```bash
bash cleanup.sh --dry-run
```

実際のクリーンアップは次のコマンドで行う。
Terminal.app、Zed、VS Code、Cursor、Windsurf、Ghostty、cmuxを終了し、
CodexのターミナルやSSHなど別のシェルから実行する。
アプリが設定を上書きし直すことを防ぐため、起動中は実行を中断する。
`sudo` は付けない。ログインシェルの変更が必要な場合だけ `chsh` が認証を求める。

```bash
bash cleanup.sh --apply
```

- Zshの起動設定5種（`.zshenv`、`.zprofile`、`.zshrc`、`.zlogin`、`.zlogout`）、
  aliases、補完、Oh My Zsh、Powerlevel10k設定を退避。独自のPATHや環境変数も無効になる。
- Neovimの設定、プラグイン、データ、キャッシュ、LuaRocks設定を退避。
- Starship、Television、Zoxide、bat、eza、ripgrep、Ghostty、cmuxの設定・関連キャッシュを退避。
- Zedのユーザー設定とキーマップは全体を退避し、アプリの既定値に戻す。
- VS Code / Insiders / Cursor / Windsurfのユーザー設定と名前付きプロファイルから、
  フォント、統合ターミナル、Vim/Neovim、テーマ・アイコンの上書きを除く。
  JSONCのコメントと書式は保存後に整形されるが、対象外の設定値は保持する。
- `~/.gitconfig` と `~/.config/git/config` に残るNeovimエディタ・batページャ指定を解除。
- Terminal.appの設定を丸ごと書き出してから削除し、標準プロファイル・フォントへ戻す。
  独自プロファイル、ショートカットなどもリセットする。
- HomebrewのNeovim、Lua関連、bat、eza、fd、ripgrep、Starship、Television、Zoxide、
  Zsh補助プラグイン、Homebrew版Zsh、過去に導入していたGhostty/cmux/UDEVフォントを削除。
  手動配置のUDEVフォントも退避する。macOSの `/bin/zsh` は残し、ログインシェルにする。
- 他パッケージが依存するformulaは保持し、終了コード `2` と「要確認」で報告する。
  強制削除・一括autoremove・Homebrew本体の削除は行わない。

履歴、プロジェクト、Downloads、Gitのユーザー情報、Codex設定、Node/pnpm/gh、
IDEアプリ本体、無関係なフォントは保持する。IDEの拡張機能やワークスペース設定、
JetBrains/iTerm2などこのdotfilesで管理していないアプリ設定は対象外。
標準と異なる `XDG_*` / `ZDOTDIR` が設定されている場合は中断する。
`/etc` 配下のシステム設定は変更しない。

起動設定を取り除くため、新しいシェルではHomebrewやCLI独自のPATHが使えなくなる場合がある。
Homebrewは `/opt/homebrew/bin/brew`（Apple Silicon）または `/usr/local/bin/brew`（Intel）から呼べる。
全Macの工場出荷状態への復元ではなく、上記のユーザー設定の初期化を行う。

## バックアップと復元

実行ごとに `~/.dotfiles-cleanup-backups/日時-ID/` を作成する（所有者のみアクセス可）。
途中で失敗した場合もバックアップは残る。復元する設定を選び、対象アプリを終了してから戻す。

- `files/` はホームからの相対パスと同じ構造。現在の同名ファイルを別途退避し、元の場所へ戻す。
- シンボリックリンクはリンク自体を保存し、読み取れるリンク先は隣の `.resolved` にも保存。
  dotfilesから削除済みのリンク先はGit履歴から復元する必要がある。
  例: `git restore --source=<削除前コミット> -- zsh nvim zed`。
  この操作はリポジトリの該当ファイルを上書きするので、現在の変更を確認してから使う。
- Terminal設定: `defaults import com.apple.Terminal "バックアップの絶対パス/Terminal.plist"`。
- `login-shell.txt` に元のログインシェル、`brew-formulae.txt` と `brew-casks.txt` に導入済み一覧を保存。
  パッケージ本体は保存しない。必要なものだけ `brew install` で再導入する（元の版の保証はない）。

再実行は可能。既に退避済みのファイル・未導入パッケージはスキップする。
アプリを再起動し、Terminalの新規ウィンドウ、通常の `ls` / `cat` / `cd`、IDEのフォントを確認する。
設定同期が有効なIDEでは、同期元からカスタマイズが戻る場合もある。

## 残した設定

`macos.sh`、`git/`、`codex/`、`raycast/` はそれぞれ独立して管理する。
cleanupはこれらのセットアップを実行しない。Git設定からNeovimとbatの指定は削除済み。
既存のCodex関連の変更はこのクリーンアップとは別のものとして維持している。

## 検証

Macの設定を変更せず、一時ディレクトリとモックでクリーンアップを検証する。

```bash
bash -n cleanup.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_cleanup.py'
bash cleanup.sh --dry-run
```
