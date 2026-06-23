# 2026-06-24 — Rewrite the /claude/ page generator to emit claude.astro cards

## Problem

`scripts/gen-biohack-skills-page.sh` wrote a standalone, unstyled
`~/SRC/biohack.net/claude/index.html`. That path is **dead**: the live
`https://www.biohack.net/claude/` page is the hand-authored, styled Astro page
`src/pages/claude.astro` in the `biohack.net` repo. The generator never touched
the real page, so it was useless and silently stale.

## Goal

Rewrite the generator to update the **plugin-card sections** of the real
`src/pages/claude.astro`, from this marketplace's plugin metadata, while leaving
all hand-authored chrome (styles, header, featured card + screenshot, footer)
intact.

## Design

- **Marker-delimited region.** The generator rewrites only the text between
  `<!-- @generated:plugin-cards start … -->` and `<!-- @generated:plugin-cards end -->`
  in `claude.astro`. Everything else is hand-authored and never touched.
- **Source set.** Iterate registered plugins in `marketplace.json`; keep only
  **local** ones (`source` starts with `./plugins/`) — vendored/external are
  excluded. Read each plugin's `plugin.json` for description/category/featured.
- **Featured exclusion.** Plugins with `"featured": true` in their `plugin.json`
  are skipped — they live in the hand-authored featured section (currently
  `install-gnome-usage`, which has a bespoke screenshot + source link).
- **Source link rule.** `skills/<name>/SKILL.md` exists → link the blob;
  otherwise → link the plugin tree. This reproduces every current card link
  (skill plugins → SKILL.md; `biohack-shell`, `statusline` → tree).
- **Order preservation.** Within a category, cards keep the existing curated
  order parsed from the current page (`plugin-name">NAME<`); new plugins are
  appended alphabetically. Category order: techops, design, meta, personal;
  unknown categories appended alphabetically. Glyphs: ⚒ ✦ ⬡ ◆.
- **Single source of truth = `plugin.json`.** Two live cards had copy that
  diverged from metadata (`new-installer`, `statusline`); fold that copy back
  into their `plugin.json` so regeneration reproduces the page exactly, and
  regen `marketplace.json` to match.

## Touch list

- `biohack-claude`: rewrite `scripts/gen-biohack-skills-page.sh`; `+featured` on
  `install-gnome-usage`; reconcile `new-installer` + `statusline` descriptions;
  `task gen-marketplace`; update `Taskfile.yml` `publish-site`; README mention.
- `biohack.net`: add the two markers around the category `<section>` blocks in
  `src/pages/claude.astro`.

## Verification

1. `bash scripts/gen-biohack-skills-page.sh` → updates claude.astro; `git diff`
   shows only the expected region (no chrome changes, curated order kept).
2. `cd ~/SRC/biohack.net && task check-source-links` → all links 200.
3. `pnpm build` → `/claude/index.html` built; `statusline` + all cards present.
4. Re-run the generator → "already up to date" (idempotent).
