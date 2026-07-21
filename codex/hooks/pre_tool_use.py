#!/usr/bin/env python3
import shlex
from typing import Optional

from hook_utils import added_patch_lines, contains_secret, deny_tool, read_payload


PROTECTED_GIT_COMMANDS = {"am", "cherry-pick", "commit", "merge", "push", "rebase"}


def shell_segments(command: str) -> tuple[tuple[str, ...], ...]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
        lexer.commenters = ""
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = tuple(lexer)
    except ValueError:
        return ()

    segments: list[tuple[str, ...]] = []
    current: list[str] = []
    for token in tokens:
        if token and all(char in ";&|\n" for char in token):
            if current:
                segments.append(tuple(current))
                current = []
        else:
            current.append(token)
    if current:
        segments.append(tuple(current))
    return tuple(segments)


def executable_arguments(segment: tuple[str, ...], executable: str) -> Optional[tuple[str, ...]]:
    for index, token in enumerate(segment):
        if token.rsplit("/", 1)[-1] != executable:
            continue
        prefixes = segment[:index]
        if any(item not in {"command", "env", "sudo"} and "=" not in item for item in prefixes):
            return None
        return segment[index + 1 :]
    return None


def git_subcommand(arguments: tuple[str, ...]) -> Optional[str]:
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "-c":
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None


def nested_shell_command(segment: tuple[str, ...]) -> Optional[str]:
    for executable in ("bash", "sh", "zsh"):
        arguments = executable_arguments(segment, executable)
        if arguments is None:
            continue
        for index, token in enumerate(arguments):
            if token.startswith("-") and "c" in token[1:] and index + 1 < len(arguments):
                return arguments[index + 1]
    return None


def destructive_git_reason(command: str, depth: int = 0) -> Optional[str]:
    if depth > 2:
        return None

    for segment in shell_segments(command):
        nested_command = nested_shell_command(segment)
        if nested_command:
            nested_reason = destructive_git_reason(nested_command, depth + 1)
            if nested_reason:
                return nested_reason

        arguments = executable_arguments(segment, "git")
        if arguments is None:
            continue

        lowered = tuple(token.lower() for token in arguments)
        lowered_segment = tuple(token.lower() for token in segment)
        if any("core.hookspath" in token for token in lowered_segment):
            return "Git hooks の無効化は許可されていません。"

        subcommand = git_subcommand(lowered)
        if subcommand in PROTECTED_GIT_COMMANDS and "--no-verify" in lowered:
            return "--no-verify による Git hooks の回避は許可されていません。"
        force_option = any(
            token.startswith("--force") or (token.startswith("-") and not token.startswith("--") and "f" in token[1:])
            for token in lowered
        )
        force_refspec = any(token.startswith("+") for token in arguments)
        if subcommand == "push" and (force_option or force_refspec):
            return "force push は禁止されています。通常の push を使用してください。"
        if subcommand == "reset" and "--hard" in lowered:
            return "git reset --hard は破壊的なため禁止されています。"
        forced_clean = any(
            token == "--force" or (token.startswith("-") and not token.startswith("--") and "f" in token[1:])
            for token in lowered
        )
        if subcommand == "clean" and forced_clean:
            return "git clean の強制実行は未追跡ファイルを削除するため禁止されています。"
    return None


def main() -> int:
    payload = read_payload()
    if payload is None:
        deny_tool("安全性検査の入力を解析できなかったため、ツール実行を停止しました。")
        return 0

    tool_name = payload.get("tool_name")
    if tool_name not in {"Bash", "apply_patch"}:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        deny_tool("安全性検査に必要な tool_input がないため、ツール実行を停止しました。")
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str):
        deny_tool("安全性検査に必要な command がないため、ツール実行を停止しました。")
        return 0

    if tool_name == "Bash":
        reason = destructive_git_reason(command)
        if reason:
            deny_tool(reason)
    elif tool_name == "apply_patch" and contains_secret("\n".join(added_patch_lines(command))):
        deny_tool("高確度の秘密情報らしき文字列を検出したため、ファイル編集を停止しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
