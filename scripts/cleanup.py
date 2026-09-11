#!/usr/bin/env python3
"""dotfiles のターミナル設定を退避し、アプリの既定値に戻す。標準ライブラリのみ。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid

FORMULAE = ('neovim', 'luarocks', 'lua', 'luajit', 'luv', 'lpeg',
            'tree-sitter', 'unibilium', 'bat', 'eza', 'fd', 'ripgrep',
            'starship', 'television', 'zoxide', 'zsh-autosuggestions',
            'zsh-syntax-highlighting', 'zsh')
CASKS = ('font-udev-gothic-nf', 'ghostty', 'cmux')
# JSONC の文字列を先に認識し、URL・文字列内の // や ,} を壊さない。
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/|\s+|.', re.S)


def read_jsonc(text):
    tokens = [t for t in TOKEN.findall(text)
              if not t.isspace() and not t.startswith(('//', '/*'))]
    return json.loads(''.join(t for i, t in enumerate(tokens)
                              if not (t == ',' and i + 1 < len(tokens)
                                      and tokens[i + 1] in ('}', ']'))))


def clean_editor(data):
    """VS Code 系のフォント、ターミナル、Vim、外観上書きだけ除く。"""
    removed = []
    for key in list(data):
        if (key.startswith(('terminal.integrated.', 'vim.', 'vscode-neovim.',
                            'editor.font', 'workbench.font', 'workbench.colorCustomizations'))
                or key in ('editor.lineHeight', 'editor.letterSpacing',
                           'editor.tokenColorCustomizations', 'workbench.colorTheme',
                           'workbench.iconTheme', 'workbench.productIconTheme')):
            removed.append(key)
            del data[key]
        elif key.startswith('[') and isinstance(data[key], dict):
            removed.extend(clean_editor(data[key]))
    return removed


class Cleanup:
    def __init__(self, home, apply=False):
        self.home = Path(home)
        self.apply = apply
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.backup = self.home / '.dotfiles-cleanup-backups' / (stamp + '-' + uuid.uuid4().hex[:8])
        self.warnings = []

    def warn(self, text):
        self.warnings.append(text)
        print('要確認: ' + text)

    def save(self, path):
        # 設定の秘密情報は表示しない。バックアップ全体は所有者のみアクセス可能。
        dest = self.backup / 'files' / path.relative_to(self.home)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            dest.symlink_to(os.readlink(path))
            if path.exists():
                resolved = dest.with_name(dest.name + '.resolved')
                if path.is_dir():
                    shutil.copytree(path, resolved, symlinks=True)
                else:
                    shutil.copy2(path, resolved)
        elif path.is_dir():
            shutil.copytree(path, dest, symlinks=True)
        else:
            shutil.copy2(path, dest)
        return dest

    def retire(self, path):
        path = Path(path)
        if not path.exists() and not path.is_symlink():
            return
        print('退避: ' + str(path))
        if self.apply:
            # move はリンク先を削除しない。キャッシュも削除せず退避する。
            dest = self.backup / 'files' / path.relative_to(self.home)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink():
                self.save(path)
                path.unlink()
            else:
                shutil.move(str(path), str(dest))

    def files(self):
        for name in ('.zshenv', '.zprofile', '.zshrc', '.zlogin', '.zlogout',
                     '.p10k.zsh', '.oh-my-zsh', '.config/zsh', '.config/nvim',
                     '.config/starship.toml', '.config/television', '.config/ghostty',
                     '.config/cmux', '.config/luarocks', '.luarocks', '.cache/luarocks',
                     '.cache/television', '.config/bat', '.config/eza', '.config/ripgrep',
                     '.config/zed/settings.json', '.config/zed/keymap.json',
                     '.local/share/nvim', '.local/state/nvim', '.cache/nvim',
                     '.local/share/zoxide', '.cache/starship', '.cache/starship-init.zsh',
                     '.cache/tv-init.zsh', '.cache/zoxide-init.zsh',
                     'Library/Application Support/com.mitchellh.ghostty'):
            self.retire(self.home / name)
        for pattern in ('.zcompdump*', '.cache/zcompdump*',
                        'Library/Fonts/*UDEV*', 'Library/Fonts/*udev*'):
            for path in sorted(self.home.glob(pattern)):
                self.retire(path)
        # .zsh_history / .zsh_sessions / .local/state/zsh/history は保持。

    def editors(self):
        for app in ('Code', 'Code - Insiders', 'Cursor', 'Windsurf'):
            user = self.home / 'Library/Application Support' / app / 'User'
            paths = [user / 'settings.json', *sorted(user.glob('profiles/*/settings.json'))]
            for path in paths:
                if not path.is_file():
                    continue
                try:
                    data = read_jsonc(path.read_text())
                    if not isinstance(data, dict):
                        raise ValueError('object required')
                    removed = clean_editor(data)
                except (ValueError, UnicodeError):
                    raise RuntimeError(f'設定の解析に失敗（内容は非表示）: {path}') from None
                if removed:
                    print('IDE設定を既定値へ: ' + str(path))
                    if self.apply:
                        self.save(path)
                        # 別の管理元にリンクされていてもリンク先を変更しない。
                        temp = path.with_name('.cleanup-' + uuid.uuid4().hex + '.json')
                        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
                        temp.chmod(0o600)
                        temp.replace(path)

    def git(self):
        # include先は書き換えず、ユーザー直下の設定ファイルだけを処理。
        for path in (self.home / '.gitconfig', self.home / '.config/git/config'):
            if not path.is_file():
                continue
            keys = []
            for key, binary in (('core.editor', 'nvim'), ('core.pager', 'bat')):
                result = subprocess.run(
                    ['/usr/bin/git', 'config', '--file', str(path), '--get-all', key],
                    capture_output=True, text=True)
                if result.returncode not in (0, 1):
                    raise RuntimeError('Git設定の確認に失敗: ' + str(path))
                if any(re.search(r'(^|[/\s])' + binary + r'(\s|$)', value)
                       for value in result.stdout.splitlines()):
                    keys.append((key, binary))
            if keys:
                print('Gitのエディタ・ページャ指定を解除: ' + str(path))
                if self.apply:
                    self.save(path)
                    if path.is_symlink():
                        content = path.read_bytes()
                        path.unlink()
                        path.write_bytes(content)
                    for key, binary in keys:
                        subprocess.run(['/usr/bin/git', 'config', '--file', str(path),
                                        '--unset-all', key,
                                        '(^|[/[:space:]])' + binary + '([[:space:]]|$)'],
                                       check=True)

    def terminal(self):
        print('Terminal.app: 設定ドメインを退避して既定値へ戻す')
        if not self.apply:
            return
        export = subprocess.run(['/usr/bin/defaults', 'export', 'com.apple.Terminal', '-'],
                                capture_output=True)
        if export.returncode:
            # ドメインが存在しないケースだけは正常な未設定として扱う。
            domains = subprocess.run(['/usr/bin/defaults', 'domains'], check=True,
                                     capture_output=True, text=True).stdout
            if 'com.apple.Terminal' in [d.strip() for d in domains.split(',')]:
                raise RuntimeError('Terminal設定のバックアップに失敗しました')
            return
        (self.backup / 'Terminal.plist').write_bytes(export.stdout)
        subprocess.run(['/usr/bin/defaults', 'delete', 'com.apple.Terminal'], check=True,
                       stdout=subprocess.DEVNULL)

    def shell(self):
        print('ログインシェル: /bin/zsh を使用')
        if self.apply:
            user = subprocess.check_output(['/usr/bin/id', '-un'], text=True).strip()
            current = subprocess.check_output(
                ['/usr/bin/dscl', '.', '-read', '/Users/' + user, 'UserShell'], text=True)
            (self.backup / 'login-shell.txt').write_text(current)
            if current.strip() != 'UserShell: /bin/zsh':
                subprocess.run(['/usr/bin/chsh', '-s', '/bin/zsh'], check=True)

    def packages(self):
        brew = next((p for p in ('/opt/homebrew/bin/brew', '/usr/local/bin/brew')
                     if Path(p).is_file()), None)
        if not brew:
            print('Homebrewなし: パッケージ処理をスキップ')
            return
        env = dict(os.environ, HOMEBREW_NO_AUTO_UPDATE='1', HOMEBREW_NO_AUTOREMOVE='1')
        def query(*args):
            return subprocess.check_output([brew, *args], env=env, text=True).splitlines()
        installed = query('list', '--formula')
        casks = query('list', '--cask')
        if self.apply:
            (self.backup / 'brew-formulae.txt').write_text('\n'.join(installed) + '\n')
            (self.backup / 'brew-casks.txt').write_text('\n'.join(casks) + '\n')
        pending = [p for p in FORMULAE if p in installed]
        for p in pending:
            print('Homebrew削除候補（他ツールの依存なら保持）: ' + p)
        # 依存元を先に除去し、対象内の依存順が変わっても再評価する。
        if self.apply:
            while pending:
                progress = False
                for p in pending[:]:
                    if query('uses', '--installed', p):
                        continue
                    subprocess.run([brew, 'uninstall', '--formula', p], env=env, check=True)
                    pending.remove(p)
                    progress = True
                if not progress:
                    for p in pending:
                        self.warn('他パッケージの依存として保持: ' + p)
                    break
        for p in CASKS:
            if p in casks:
                print('Homebrew cask 削除: ' + p)
                if self.apply:
                    subprocess.run([brew, 'uninstall', '--cask', p], env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description='引数なしは対象表示のみ。--apply で実行。')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if platform.system() != 'Darwin':
        parser.error('macOS 専用です')
    if os.geteuid() == 0:
        parser.error('sudo で実行しないでください')
    cleanup = Cleanup(Path.home(), args.apply)
    # 異なる XDG/ZDOTDIR は無断で広いパスを退避せず、対象の明示を求める。
    for key, default in (('ZDOTDIR', str(cleanup.home)),
                         ('XDG_CONFIG_HOME', str(cleanup.home / '.config')),
                         ('XDG_CACHE_HOME', str(cleanup.home / '.cache')),
                         ('XDG_DATA_HOME', str(cleanup.home / '.local/share')),
                         ('XDG_STATE_HOME', str(cleanup.home / '.local/state'))):
        if os.environ.get(key, default) != default:
            parser.error(key + ' が標準パスではありません。対象を確認してから実行してください')
    print('実行モード' if args.apply else 'プレビュー（変更なし）')
    if args.apply:
        # Terminal は実行元でもあるので終了させない。終了後にSSH/別アプリから実行。
        checks = [('Terminal', ['-x', 'Terminal']),
                  ('IDE・ターミナルアプリ', ['-f',
                   r'/(Visual Studio Code( - Insiders)?|Cursor|Windsurf|Zed|Ghostty|ghostty|cmux)\.app/Contents/MacOS/'])]
        for app, match in checks:
            result = subprocess.run(['/usr/bin/pgrep', *match], capture_output=True)
            if result.returncode == 0:
                parser.error(app + ' を終了してから、別アプリのシェルまたはSSHで実行してください')
            if result.returncode != 1:
                parser.error('起動中アプリの確認に失敗しました')
        os.umask(0o077)
        cleanup.backup.mkdir(parents=True, mode=0o700)
        print('バックアップ: ' + str(cleanup.backup))
    # パースエラーを変更前に検出する。
    preview = Cleanup(cleanup.home)
    preview.editors()
    cleanup.shell()
    cleanup.git()
    cleanup.editors()
    cleanup.files()
    cleanup.terminal()
    cleanup.packages()
    if args.apply:
        print('設定退避が完了しました。アプリを再起動して確認してください。')
        print('復元方法は README.md を参照。バックアップ: ' + str(cleanup.backup))
    return 2 if cleanup.warnings else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('中断: ' + str(exc), file=sys.stderr)
        sys.exit(1)
