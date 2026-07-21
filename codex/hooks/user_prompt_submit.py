#!/usr/bin/env python3
from hook_utils import block_prompt, contains_secret, read_payload


def main() -> int:
    payload = read_payload()
    if payload is None:
        block_prompt("秘密情報検査の入力を解析できませんでした。新しいセッションで再試行してください。")
        return 0

    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        block_prompt("秘密情報検査に必要なプロンプトを取得できませんでした。")
    elif contains_secret(prompt):
        block_prompt("高確度の秘密情報らしき文字列を検出しました。値を削除または伏字にして再送してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
