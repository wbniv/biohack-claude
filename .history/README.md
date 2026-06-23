| Date | Change |
|------|--------|
| [2026-06-24](https://github.com/wbniv/biohack-claude/commit/a9ca22c) | feat(statusline): publish the two-line status line as a marketplace plugin |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/f2d7607) | feat(new-installer): add skill to scaffold one-shot self-removing installers |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/90e9764) | feat(gnome): add install-gnome-usage one-shot installer plugin |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/7ddf24d) | feat: add GNOME extensions section (claude-usage indicator) |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/46b2fff) | feat: initial biohack-claude marketplace |

<!--history-meta v1
a9ca22c	author	Will Norris
a9ca22c	added	6
a9ca22c	deleted	0
a9ca22c	files	1
a9ca22c	body	Ship ~/.local/bin/claude-status (account · model · effort · cwd/branch on\nline 1; context, 5h/7d rate-limit bars, reset countdown, cost on line 2) as\na `statusline` plugin so it can be installed from the biohack-claude\nmarketplace.\n\nA plugin can't set the user-scoped `statusLine` key itself, so a one-shot\n/install-statusline command does it: copies the script to the stable\n~/.local/bin/claude-status (the plugin dir is versioned and changes on every\nupdate), patches ~/.claude/settings.json with an absolute path via jq after\nbacking it up, verifies the render, then self-uninstalls — same pattern as\ninstall-gnome-usage.\n\nRegenerated marketplace.json (statusline [personal]) and added the README row.\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SishYPqHvuMnHP3JAGdUxQ
f2d7607	author	Will Norris
f2d7607	added	6
f2d7607	deleted	0
f2d7607	files	1
f2d7607	body	Generalizes the install-gnome-usage pattern into a reusable skill that\ngenerates the plugin dir, command, README entry, and site card.\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
90e9764	author	Will Norris
90e9764	added	3
90e9764	deleted	3
90e9764	files	1
90e9764	body	Self-removes after cloning wbniv/claude-usage, symlinking the GNOME\nextension, and enabling it — no residual token cost.\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
7ddf24d	author	Will Norris
7ddf24d	added	6
7ddf24d	deleted	0
7ddf24d	files	1
7ddf24d	body	gnome/extensions.json catalogs the Claude Usage Indicator extension\n(wbniv/claude-usage). gen-biohack-skills-page.sh renders a GNOME\nsection on biohack.net/claude/. README updated.\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
46b2fff	author	Will Norris
46b2fff	added	76
46b2fff	deleted	0
46b2fff	files	1
46b2fff	body	9 plugins (8 skills + biohack-shell), .claude-plugin/marketplace.json,\nvendor/ evaluation workflow, memories/ sync, plans/ curation scaffold.\n\nThree skill renames on migration:\n  cloudflare-static-site  → cf-static-site\n  cloudflare-domain-setup → cf-domain-setup\n  billing-tags            → aws-billing-tags\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
-->
