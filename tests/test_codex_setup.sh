#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETUP_SCRIPT="$ROOT_DIR/codex/setup.sh"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

DESTINATION_DIR="$TEST_DIR/.codex"
AGENT_SKILLS_DIR="$TEST_DIR/.agents/skills"
mkdir -p "$DESTINATION_DIR/sessions"
mkdir -p "$AGENT_SKILLS_DIR/codex-only"
printf '%s\n' 'preserve' >"$AGENT_SKILLS_DIR/codex-only/SKILL.md"
printf '%s\n' 'preserve' >"$DESTINATION_DIR/auth.json"
printf '%s\n' 'preserve' >"$DESTINATION_DIR/sessions/session.jsonl"
printf '%s\n' 'old config' >"$DESTINATION_DIR/config.toml"
mkdir -p "$DESTINATION_DIR/hooks"
printf '%s\n' 'old hook' >"$DESTINATION_DIR/hooks/old.py"

bash "$SETUP_SCRIPT" \
  "$ROOT_DIR/codex" \
  "$DESTINATION_DIR"

[[ -f "$DESTINATION_DIR/config.toml" && ! -L "$DESTINATION_DIR/config.toml" ]]
[[ "$(<"$DESTINATION_DIR/config.toml")" == "old config" ]]

for managed_file in AGENTS.md review.config.toml; do
  cmp -s "$ROOT_DIR/codex/$managed_file" "$DESTINATION_DIR/$managed_file"
  [[ -f "$DESTINATION_DIR/$managed_file" && ! -L "$DESTINATION_DIR/$managed_file" ]]
  [[ "$(stat -f '%Lp' "$DESTINATION_DIR/$managed_file")" == "600" ]]
done

for managed_link in hooks.json hooks rules; do
  [[ -L "$DESTINATION_DIR/$managed_link" ]]
  [[ "$(readlink "$DESTINATION_DIR/$managed_link")" == "$ROOT_DIR/codex/$managed_link" ]]
done

[[ "$(<"$DESTINATION_DIR/auth.json")" == "preserve" ]]
[[ "$(<"$DESTINATION_DIR/sessions/session.jsonl")" == "preserve" ]]
[[ -d "$AGENT_SKILLS_DIR" && ! -L "$AGENT_SKILLS_DIR" ]]
[[ "$(<"$AGENT_SKILLS_DIR/codex-only/SKILL.md")" == "preserve" ]]

echo "Codex setup integration test passed."
