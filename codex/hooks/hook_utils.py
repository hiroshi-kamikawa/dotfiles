#!/usr/bin/env python3
import json
import re
import sys
from typing import Any, Optional


MAX_INPUT_BYTES = 1024 * 1024
SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def read_payload() -> Optional[dict[str, Any]]:
    raw_bytes = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw_bytes) > MAX_INPUT_BYTES:
        return None

    try:
        raw = raw_bytes.decode("utf-8")
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError):
        return None

    return value if isinstance(value, dict) else None


def contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def added_patch_lines(patch: str) -> tuple[str, ...]:
    return tuple(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))


def write_json(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")


def deny_tool(reason: str) -> None:
    write_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def block_prompt(reason: str) -> None:
    write_json({"decision": "block", "reason": reason})
