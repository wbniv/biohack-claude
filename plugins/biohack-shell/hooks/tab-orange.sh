#!/bin/bash
# Claude stopped — waiting for user input
# Writes a marker file that WezTerm's format-tab-title reads to color the tab.
# Uses ~/.claude/tab-status/ because WezTerm Flatpak can read $HOME but not /tmp.
#
# Marker values:
#   "question" — Claude asked a question (AskUserQuestion) → blue tab
#   "waiting"  — Claude finished responding → orange tab
if [[ -n "${WEZTERM_PANE:-}" ]]; then
    mkdir -p ~/.claude/tab-status
    # Synchronous Stop hook receives JSON on stdin with last_assistant_message.
    # Read all of stdin, check for AskUserQuestion tool usage.
    status="waiting"
    input=$(cat)
    # Check if the last tool use was AskUserQuestion (structured JSON check).
    # The stop_hook_active field or last_assistant_message contains tool_use
    # blocks with "name": "AskUserQuestion". Plain text mentioning the tool
    # name won't match this jq query.
    if echo "$input" | jq -e '
      .last_assistant_message // [] | map(select(.type == "tool_use")) |
      last | .name == "AskUserQuestion"
    ' >/dev/null 2>&1; then
        status="question"
    fi
    echo "$status" > ~/.claude/tab-status/"${WEZTERM_PANE}"
fi
