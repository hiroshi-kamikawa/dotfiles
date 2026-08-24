#!/bin/bash

input=$(cat)
model=$(echo "$input" | jq -r '.model.display_name')
ctx_remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

ctx_str="Left ctx:?"
[ -n "$ctx_remaining" ] && ctx_str="Left ctx:$(printf '%.0f' "$ctx_remaining")%"

printf "%s・%s\n" "$model" "$ctx_str"
