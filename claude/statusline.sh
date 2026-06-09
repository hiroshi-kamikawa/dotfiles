#!/bin/bash

input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir' | sed "s|$HOME|~|g")
model=$(echo "$input" | jq -r '.model.display_name')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
transcript=$(echo "$input" | jq -r '.transcript_path')
todo_count=$([ -f "$transcript" ] && grep -c '"type":"todo"' "$transcript" 2>/dev/null || echo 0)
time_now=$(date +%H:%M)

# Truncate directory to last 2 segments
seg_count=$(echo "$cwd" | tr '/' '\n' | wc -l | tr -d ' ')
if [ "$seg_count" -gt 2 ]; then
  cwd=".../"$(echo "$cwd" | rev | cut -d'/' -f1-2 | rev)
fi

# Git info
cd "$(echo "$input" | jq -r '.workspace.current_dir')" 2>/dev/null
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')
git_status_str=''
if [ -n "$branch" ]; then
  porcelain=$(git status --porcelain 2>/dev/null)
  if [ -n "$porcelain" ]; then
    local modified=0 staged=0 untracked=0
    while IFS= read -r line; do
      case "${line:0:2}" in
        '??') untracked=$((untracked + 1)) ;;
        ' M'|'MM'|' D') modified=$((modified + 1)) ;;
        'M '|'A '|'D '|'R ') staged=$((staged + 1)) ;;
      esac
    done <<< "$porcelain"
    [ "$staged" -gt 0 ] && git_status_str="${git_status_str} +${staged}"
    [ "$modified" -gt 0 ] && git_status_str="${git_status_str} ~${modified}"
    [ "$untracked" -gt 0 ] && git_status_str="${git_status_str} ?${untracked}"
  fi
fi

# Format: directory  git_branch git_status | model ctx time todos
printf "%s" "$cwd"
[ -n "$branch" ] && printf " %s" "$branch"
[ -n "$git_status_str" ] && printf " %s" "${git_status_str# }"
printf " %s" "$model"
[ -n "$remaining" ] && printf " ctx:%s%%" "$remaining"
printf " %s" "$time_now"
[ "$todo_count" -gt 0 ] && printf " todos:%s" "$todo_count"
echo
