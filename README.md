# dotfiles

macOS + zsh向けのターミナル設定です。Homebrewで必要なツールをまとめて導入します。

## セットアップ

先に[Homebrew](https://brew.sh/ja/)をインストールし、このリポジトリ内で実行してください。

```sh
bash setup.sh
```

インストール後、新しいターミナルを開いてください。標準ターミナルの既定・起動時プロファイルには **MesloLGS Nerd Font** を自動設定し、文字サイズは維持します。macOSからターミナルの操作許可を求められた場合は許可してください。再実行時もフォント設定を適用します。

自動設定に失敗した場合や、ほかのターミナルアプリ・プロファイルを使う場合は、アプリのフォント設定で **MesloLGS Nerd Font** を選択してください。

既存の `.zshrc` は同じディレクトリの `.zshrc.backup.XXXXXX` に保存し、内容を維持したまま設定を読み込む行を末尾に追加します。`ZDOTDIR` を使う場合は、その値を環境変数として渡して実行してください。既存ファイルがシンボリックリンクなら、リンク先の内容を引き継いだ通常ファイルに置き換え、リンク先は変更しません。

同じ場所から再実行しても読み込み行は重複しません。インストール済みツールを一括更新する処理は行いません。リポジトリを移動した場合は `.zshrc` の `source` 行のパスを修正してください。

## 機能と使い方

| 機能 | 操作 |
| --- | --- |
| Starship | 現在のディレクトリ、Gitブランチ・変更状態、時間のかかったコマンドの実行時間を表示 |
| eza | `ls`：色分け・アイコン・ディレクトリ優先 |
| eza | `ll`：サイズ・日時・Git状態を含む詳細表示 |
| eza | `la`：隠しファイルを含む詳細表示 |
| eza | `lt`：2階層のツリー表示 |
| fzf | `Ctrl + R`：履歴検索、`Ctrl + T`：ファイル選択 |
| zsh-autosuggestions | 履歴から続きを提案。カーソルが行末にあるとき右矢印で採用 |
| zsh-syntax-highlighting | 入力中のコマンドや引数を色分け |
| zoxide | 一度 `cd` した場所へ `z ディレクトリ名の一部` で移動。`zi` で対話的に選択 |
| bat | `bat ファイル名`：行番号・構文の色分け付きで表示 |
| zshの履歴 | 最大10万件を保存し、別タブでも共有 |
| zshの補完 | `Tab` でコマンドやパスなどを補完 |

`ls` の元の動作が必要な場合は `command ls` を使用できます。アイコン不要の場合は `eza --icons=never` を使用してください。

## 設定ファイル

- `Brewfile`：ツール7種類とNerd Font
- `zsh/zshrc`：履歴、補完、エイリアス、各ツールの初期化
- `starship.toml`：プロンプトの表示設定（`STARSHIP_CONFIG` で指定）

設定変更後は新しいターミナルで反映を確認してください。既存のプロンプトや同名エイリアスがある場合は、この設定が優先されます。既存のプラグイン管理設定で同じツールを読み込んでいる場合は重複を整理してください。

## 元に戻す

`.zshrc` の `# Terminal settings managed by dotfiles` と直後の `source` 行を削除し、新しいターミナルを開いてください。変更前の内容はセットアップ時に表示したバックアップにも残ります。インストールしたツール・フォントとコマンド履歴は残ります。

## 参考

- [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)
- [Starship](https://starship.rs/guide/)
- [fzf](https://github.com/junegunn/fzf)
- [eza](https://github.com/eza-community/eza)
- [zoxide](https://github.com/ajeetdsouza/zoxide)
- [bat](https://github.com/sharkdp/bat)
- [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions)
- [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting)
