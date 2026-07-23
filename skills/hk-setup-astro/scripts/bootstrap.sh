#!/usr/bin/env bash

set -euo pipefail

usage() {
  printf '%s\n' \
    "Usage: bootstrap.sh <empty-project-directory>" \
    "" \
    "Scaffold the standard Astro starter and install its integrations." \
    "The target must be empty. Configuration is completed by the agent after this script."
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "$#" -ne 1 ]]; then
  usage >&2
  exit 2
fi

target=$1
mkdir -p "$target"

if [[ -n "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  printf 'Refusing to scaffold into a non-empty directory: %s\n' "$target" >&2
  exit 1
fi

command -v pnpm >/dev/null 2>&1 || {
  printf 'pnpm is required.\n' >&2
  exit 1
}

target=$(cd "$target" && pwd)
pnpm create astro@latest "$target" --template minimal --install --no-git --yes

if ! git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$target" init
fi

(
  cd "$target"
  pnpm exec astro add tailwind --yes
  pnpm add daisyui@latest
  pnpm exec astro add partytown sitemap --yes
)

printf 'Bootstrap complete: %s\n' "$target"
printf 'Complete project configuration, then run astro_starter.py audit and verify.\n'
