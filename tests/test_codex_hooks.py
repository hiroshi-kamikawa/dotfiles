#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = ROOT / "codex" / "hooks"


def run_hook(name: str, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/python3", str(HOOKS_DIR / name)],
        input=json.dumps(payload),
        capture_output=True,
        check=False,
        text=True,
    )


class PreToolUseTests(unittest.TestCase):
    def test_allows_normal_git_push(self) -> None:
        result = run_hook(
            "pre_tool_use.py",
            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_force_push(self) -> None:
        for command in (
            "git push --force origin main",
            "git push -uf origin main",
            "git push origin +main",
            "git -C repo push --force origin main",
            "/usr/bin/git push --force origin main",
            "sh -c 'git push --force origin main'",
            "echo ready\ngit push --force origin main",
        ):
            with self.subTest(command=command):
                result = run_hook(
                    "pre_tool_use.py",
                    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}},
                )

                self.assertEqual(result.returncode, 0)
                output = json.loads(result.stdout)
                self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("force push", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_blocks_hard_reset(self) -> None:
        result = run_hook(
            "pre_tool_use.py",
            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD~1"}},
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_forced_git_clean(self) -> None:
        result = run_hook(
            "pre_tool_use.py",
            {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git clean -xfd"}},
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_git_hook_bypass(self) -> None:
        for command in (
            "git commit --no-verify -m 'skip checks'",
            "git -c core.hooksPath=/dev/null commit -m 'skip hooks'",
            "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m 'skip hooks'",
        ):
            with self.subTest(command=command):
                result = run_hook(
                    "pre_tool_use.py",
                    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}},
                )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_high_confidence_secret_in_patch(self) -> None:
        result = run_hook(
            "pre_tool_use.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n+token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'\n*** End Patch"},
            },
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("秘密情報", json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_removing_a_secret_from_a_patch(self) -> None:
        result = run_hook(
            "pre_tool_use.py",
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "command": "*** Begin Patch\n-token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'\n+token = os.environ['TOKEN']\n*** End Patch"
                },
            },
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_malformed_input_fails_closed_without_echoing_input(self) -> None:
        result = subprocess.run(
            ["/usr/bin/python3", str(HOOKS_DIR / "pre_tool_use.py")],
            input="not-json",
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn("not-json", result.stderr)


class UserPromptSubmitTests(unittest.TestCase):
    def test_blocks_high_confidence_secret(self) -> None:
        for secret in (
            "sk-proj-abcdefghijklmnopqrstuvwxyz123456",
            "github_pat_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
            "glpat-abcdefghijklmnopqrstuvwxyz",
        ):
            with self.subTest(secret_type=secret.split("-", 1)[0]):
                result = run_hook(
                    "user_prompt_submit.py",
                    {"hook_event_name": "UserPromptSubmit", "prompt": f"このキーを使って: {secret}"},
                )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_allows_normal_prompt(self) -> None:
        result = run_hook(
            "user_prompt_submit.py",
            {"hook_event_name": "UserPromptSubmit", "prompt": "認証処理のテストを書いて"},
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


class PostToolUseTests(unittest.TestCase):
    def test_warns_about_added_debug_statement(self) -> None:
        result = run_hook(
            "post_tool_use.py",
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n+console.log('debug')\n*** End Patch"},
                "tool_response": {},
            },
        )

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn("デバッグ", output["hookSpecificOutput"]["additionalContext"])

    def test_ignores_removed_debug_statement(self) -> None:
        result = run_hook(
            "post_tool_use.py",
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n-console.log('debug')\n+return value\n*** End Patch"},
                "tool_response": {},
            },
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


class HooksConfigTests(unittest.TestCase):
    def test_config_uses_codex_scripts(self) -> None:
        config = json.loads((ROOT / "codex" / "hooks.json").read_text())
        serialized = json.dumps(config)

        self.assertNotIn("CLAUDE_", serialized)
        self.assertIn("pre_tool_use.py", serialized)
        self.assertIn("user_prompt_submit.py", serialized)
        self.assertIn("post_tool_use.py", serialized)


if __name__ == "__main__":
    unittest.main()
