import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('cleanup', Path(__file__).parents[1] / 'scripts/cleanup.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CleanupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def put(self, name, data='keep'):
        p = self.home / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)
        return p

    def test_preview_changes_nothing(self):
        p = self.put('.zshrc')
        c = module.Cleanup(self.home)
        c.files()
        self.assertEqual(p.read_text(), 'keep')
        self.assertFalse(c.backup.exists())

    def test_move_and_repeat_preserves_history_and_other_data(self):
        rc = self.put('.zshrc')
        cache = self.put('.local/share/nvim/lazy/plugin/file')
        protected = [self.put(p) for p in ('.zsh_history', '.local/state/zsh/history',
                     'Downloads/file', '.codex/config.toml', 'project/file',
                     'Library/Fonts/Other.ttf')]
        c = module.Cleanup(self.home, True)
        c.files()
        self.assertFalse(rc.exists())
        self.assertFalse(cache.exists())
        self.assertEqual((c.backup / 'files/.zshrc').read_text(), 'keep')
        c.files()
        for p in protected:
            self.assertEqual(p.read_text(), 'keep')

    def test_links_do_not_remove_source_and_dangling_links_are_retired(self):
        source = self.put('source/settings', 'original')
        link = self.home / '.zshrc'
        link.symlink_to(source)
        missing = self.home / '.zprofile'
        missing.symlink_to(self.home / 'missing')
        c = module.Cleanup(self.home, True)
        c.files()
        self.assertEqual(source.read_text(), 'original')
        self.assertFalse(link.is_symlink())
        self.assertFalse(missing.is_symlink())
        self.assertEqual((c.backup / 'files/.zshrc.resolved').read_text(), 'original')
        self.assertTrue((c.backup / 'files/.zprofile').is_symlink())

    def test_jsonc_preserves_strings_and_non_target_settings(self):
        data = module.read_jsonc('''{// comment
          "url": "https://example.com/a,}", /* block */
          "editor.fontFamily": "custom",
          "[python]": {"editor.fontSize": 20, "editor.tabSize": 4,},
          "values": ["x,]",], "escaped": "a\\\"//b",
        }''')
        module.clean_editor(data)
        self.assertEqual(data['url'], 'https://example.com/a,}')
        self.assertEqual(data['escaped'], 'a"//b')
        self.assertEqual(data['values'], ['x,]'])
        self.assertEqual(data['[python]'], {'editor.tabSize': 4})
        self.assertNotIn('editor.fontFamily', data)

    def test_editor_symlink_detached_and_profiles_handled(self):
        source = self.put('source.json', '{"editor.fontSize": 30, "keep": true}')
        p = self.home / 'Library/Application Support/Cursor/User/settings.json'
        p.parent.mkdir(parents=True)
        p.symlink_to(source)
        profile = self.put('Library/Application Support/Code/User/profiles/abc/settings.json',
                           '{"terminal.integrated.fontFamily":"custom", "keep": 1}')
        c = module.Cleanup(self.home, True)
        c.editors()
        self.assertFalse(p.is_symlink())
        self.assertEqual(json.loads(p.read_text()), {'keep': True})
        self.assertIn('editor.fontSize', source.read_text())
        self.assertEqual(json.loads(profile.read_text()), {'keep': 1})
        c.editors()

    def test_invalid_editor_is_not_changed(self):
        p = self.put('Library/Application Support/Code/User/settings.json', '{broken')
        with self.assertRaises(RuntimeError):
            module.Cleanup(self.home, True).editors()
        self.assertEqual(p.read_text(), '{broken')

    def test_brew_dependency_is_not_forced_and_dependency_order_retries(self):
        installed = {'lua', 'neovim', 'ripgrep'}
        calls = []
        def output(cmd, **kw):
            if cmd[1:] == ['list', '--formula']:
                return '\n'.join(installed)
            if cmd[1:] == ['list', '--cask']:
                return ''
            if cmd[1:3] == ['uses', '--installed']:
                return 'other-app' if cmd[-1] == 'ripgrep' else ('neovim' if cmd[-1] == 'lua' and 'neovim' in installed else '')
            self.fail(cmd)
        def run(cmd, **kw):
            calls.append(cmd)
            installed.remove(cmd[-1])
            return Mock(returncode=0)
        c = module.Cleanup(self.home, True)
        c.backup.mkdir(parents=True)
        with patch.object(module.Path, 'is_file', return_value=True), \
             patch.object(module.subprocess, 'check_output', side_effect=output), \
             patch.object(module.subprocess, 'run', side_effect=run):
            c.packages()
        self.assertEqual(installed, {'ripgrep'})
        self.assertTrue(c.warnings)
        self.assertTrue(all(cmd[1:3] == ['uninstall', '--formula'] for cmd in calls))

    def test_git_keeps_identity_and_other_values(self):
        p = self.put('.gitconfig', '[user]\n name = Example\n[core]\n editor = nvim\n pager = bat --plain\n')
        c = module.Cleanup(self.home, True)
        c.git()
        self.assertIn('name = Example', p.read_text())
        self.assertNotIn('nvim', p.read_text())
        self.assertNotIn('bat', p.read_text())
        c.git()

    def test_terminal_export_failure_does_not_delete_domain(self):
        c = module.Cleanup(self.home, True)
        c.backup.mkdir(parents=True)
        with patch.object(module.subprocess, 'run', side_effect=[
            Mock(returncode=1), Mock(stdout='com.apple.Terminal, other')]) as run:
            with self.assertRaises(RuntimeError):
                c.terminal()
        self.assertEqual(run.call_count, 2)


if __name__ == '__main__':
    unittest.main()
