#!/usr/bin/env python3
import sys

from hook_utils import added_patch_lines, read_payload, write_json


def main() -> int:
    payload = read_payload()
    if payload is None:
        print("Codex hook input を解析できなかったため、検査をスキップしました。", file=sys.stderr)
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    additions = added_patch_lines(command)
    if any("console.log(" in line or "debugger" in line for line in additions):
        write_json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "追加行にデバッグ用コードが残っています。意図的でなければ削除し、関連テストを確認してください。",
                }
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
