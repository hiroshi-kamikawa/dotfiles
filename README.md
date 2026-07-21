# dotfiles

```bash
cd ~/dotfiles
bash setup.sh
```

## Codex hooks

Codex のユーザー共通 hooks は `codex/hooks.json` と `codex/hooks/` で管理し、
`setup.sh` が `~/.codex/hooks.json` と `~/.codex/hooks` へシンボリックリンクを
作成する。

現在の構成では、高確度の秘密情報、force push、`git reset --hard`、
`--no-verify` や `core.hooksPath` による Git hooks の回避を実行前に防ぐ。
ファイル編集後は追加されたデバッグ用コードを警告する。フォーマッターや
テストはリポジトリごとに異なるため、グローバル hooks からは実行しない。
これらは補助的なガードであり、完全なセキュリティ境界ではない。保護ブランチ、
Git hooks、CI、専用の秘密情報スキャナーを主な防御として併用する。

既存の `~/.codex/hooks.json` と管理元の内容が異なる場合や、管理外の
シンボリックリンクがある場合は、上書きせずにセットアップを停止する。
リンク後に hooks を変更した場合は、Codex CLI の `/hooks` で内容を確認して
再度信頼する。

## 自動アップデート

`setup.sh` を実行すると、Homebrew と Claude Code を毎日 12:00 に自動更新する
LaunchAgent (`com.shoirhi.dotfiles.autoupdate`) がインストールされる。

- 更新内容: `brew update` / `brew upgrade` / `brew cleanup` / `claude update`
- 実行時刻にスリープ・電源オフでも、次回起動・復帰時に一度だけ実行される
- ログ: `~/.local/state/dotfiles/auto-update.log`
- 完了時は macOS の通知センターに結果を表示（正常完了 / 失敗したステップ一覧）

### 手動実行・管理

```bash
# 手動で今すぐ更新
bash ~/dotfiles/scripts/auto-update.sh

# 即時実行（launchd経由で起動）
launchctl start com.shoirhi.dotfiles.autoupdate

# 登録状態の確認
launchctl list | grep autoupdate

# 一時停止 / 再開
launchctl unload ~/Library/LaunchAgents/com.shoirhi.dotfiles.autoupdate.plist
launchctl load   ~/Library/LaunchAgents/com.shoirhi.dotfiles.autoupdate.plist

# ログ確認
tail -f ~/.local/state/dotfiles/auto-update.log
```
