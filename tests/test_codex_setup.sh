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
printf '%s\n' 'old instructions' >"$DESTINATION_DIR/AGENTS.md"
mkdir -p "$DESTINATION_DIR/hooks"
printf '%s\n' 'old hook' >"$DESTINATION_DIR/hooks/old.py"

bash "$SETUP_SCRIPT" \
  "$ROOT_DIR/codex" \
  "$DESTINATION_DIR"

[[ -f "$DESTINATION_DIR/config.toml" && ! -L "$DESTINATION_DIR/config.toml" ]]
[[ "$(<"$DESTINATION_DIR/config.toml")" == "old config" ]]

cmp -s "$ROOT_DIR/codex/review.config.toml" "$DESTINATION_DIR/review.config.toml"
[[ -f "$DESTINATION_DIR/review.config.toml" && ! -L "$DESTINATION_DIR/review.config.toml" ]]
[[ "$(stat -f '%Lp' "$DESTINATION_DIR/review.config.toml")" == "600" ]]

for managed_link in AGENTS.md hooks.json hooks rules; do
  [[ -L "$DESTINATION_DIR/$managed_link" ]]
  [[ "$(readlink "$DESTINATION_DIR/$managed_link")" == "$ROOT_DIR/codex/$managed_link" ]]
done

[[ "$(<"$DESTINATION_DIR/auth.json")" == "preserve" ]]
[[ "$(<"$DESTINATION_DIR/sessions/session.jsonl")" == "preserve" ]]
[[ -d "$AGENT_SKILLS_DIR" && ! -L "$AGENT_SKILLS_DIR" ]]
[[ "$(<"$AGENT_SKILLS_DIR/codex-only/SKILL.md")" == "preserve" ]]

echo "Codex setup integration test passed."
