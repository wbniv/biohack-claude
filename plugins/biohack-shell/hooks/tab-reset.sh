#!/bin/bash
# User submitted prompt — Claude is working
# Removes the marker file so WezTerm's format-tab-title resets tab color.
if [[ -n "${WEZTERM_PANE:-}" ]]; then
    rm -f ~/.claude/tab-status/"${WEZTERM_PANE}"
fi
