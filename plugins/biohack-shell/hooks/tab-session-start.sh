#!/bin/bash
# Session starting — Claude is about to show prompt, set tab to orange (waiting)
if [[ -n "${WEZTERM_PANE:-}" ]]; then
    mkdir -p ~/.claude/tab-status
    echo "waiting" > ~/.claude/tab-status/"${WEZTERM_PANE}"
fi
