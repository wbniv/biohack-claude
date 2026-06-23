| Date | Change |
|------|--------|
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/f2d7607) | feat(new-installer): add skill to scaffold one-shot self-removing installers |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/90e9764) | feat(gnome): add install-gnome-usage one-shot installer plugin |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/7ddf24d) | feat: add GNOME extensions section (claude-usage indicator) |
| [2026-05-23](https://github.com/wbniv/biohack-claude/commit/46b2fff) | feat: initial biohack-claude marketplace |

<!--history-meta v1
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
