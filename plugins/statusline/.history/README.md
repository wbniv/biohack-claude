| Date | Change |
|------|--------|
| [2026-06-24](https://github.com/wbniv/biohack-claude/commit/a9ca22c) | feat(statusline): publish the two-line status line as a marketplace plugin |

<!--history-meta v1
a9ca22c	author	Will Norris
a9ca22c	added	44
a9ca22c	deleted	0
a9ca22c	files	1
a9ca22c	body	Ship ~/.local/bin/claude-status (account · model · effort · cwd/branch on\nline 1; context, 5h/7d rate-limit bars, reset countdown, cost on line 2) as\na `statusline` plugin so it can be installed from the biohack-claude\nmarketplace.\n\nA plugin can't set the user-scoped `statusLine` key itself, so a one-shot\n/install-statusline command does it: copies the script to the stable\n~/.local/bin/claude-status (the plugin dir is versioned and changes on every\nupdate), patches ~/.claude/settings.json with an absolute path via jq after\nbacking it up, verifies the render, then self-uninstalls — same pattern as\ninstall-gnome-usage.\n\nRegenerated marketplace.json (statusline [personal]) and added the README row.\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SishYPqHvuMnHP3JAGdUxQ
-->
