#!/bin/sh

set -eu

repository=${1:-.}

if ! repository=$(cd "$repository" 2>/dev/null && pwd); then
  echo "check-hook-conflicts: repository directory does not exist" >&2
  exit 1
fi

found=0

if [ -d "$repository/.husky" ]; then
  echo "husky: .husky directory detected"
  found=$((found + 1))
fi

if [ -f "$repository/lefthook.yml" ] || [ -f "$repository/lefthook.yaml" ]; then
  echo "lefthook: configuration detected"
  found=$((found + 1))
fi

if [ -f "$repository/.pre-commit-config.yaml" ] || [ -f "$repository/.pre-commit-config.yml" ]; then
  echo "pre-commit: configuration detected"
  found=$((found + 1))
fi

if [ -d "$repository/.githooks" ]; then
  echo "custom: .githooks directory detected"
  found=$((found + 1))
fi

hooks_path=$(git -C "$repository" config --local --get core.hooksPath 2>/dev/null || true)
if [ -n "$hooks_path" ]; then
  echo "core.hooksPath: $hooks_path"
  case "$hooks_path" in
    .husky/_|.husky/_/)
      if [ ! -d "$repository/.husky" ]; then
        found=$((found + 1))
      fi
      ;;
    *) found=$((found + 1)) ;;
  esac
fi

if [ "$found" -eq 0 ]; then
  echo "hook-managers: none detected"
elif [ "$found" -gt 1 ]; then
  echo "conflict: multiple hook-management signals require manual review"
else
  echo "conflict: none detected"
fi
