---
name: home_src_layout
description: "The ~/SRC/<name> → ~/<name> flattening is complete; ~/SRC no longer exists and nothing should reference it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9425f245-1b60-4bcf-91a7-279db284a72c
---

**`~/SRC/` is gone.** The layout is flat: every project working copy lives **directly at `~/<name>`** (e.g. `~/python-tui-lib`, `~/biohack.net`), and the shared cascade docs are `~/CLAUDE.md`, `~/docs/`, `~/docs/free-services.md`. The homedir git repo *is* `~`. The old homedir is preserved at `~/homedir-old/`.

The migration finished on **2026-07-19**: `~/SRC/` and the interim `~/SRC/python-tui-lib -> ~/python-tui-lib` compat symlink were removed, which broke every hook wired as `$HOME/SRC/python-tui-lib/hooks/*.sh`. Fixed in the same pass — `~/.claude/settings.json` and `~/.config/claude/will/settings.json` hooks, `.gitconfig` `hooksPath`, `~/.config/workspace-default`, GTK bookmarks, the `claude-housekeeping` scanner, and the `project-bootstrap` / `snes-rom-page` skills all now use flat `$HOME/<name>` paths. `~/.claude/projects.json` was migrated to `~/<name>` paths separately.

Still true and unrelated to SRC: projects.json lists several active projects **not checked out on this machine** (parking-space, bumper2bumper, finding-your-way, …). Those are registry entries for another machine's clone — [[claude-housekeeping]] reports them as absent, which is expected, not drift. `~/bin/clone-projects` is what clones them, flat.

**Why:** a compat symlink made the old paths keep working, so the stale references survived far longer than the move itself. Once the symlink went, everything referencing `SRC` failed at once.

**How to apply:** treat any `~/SRC/...` path you encounter as `~/...` — in docs, hook commands, or scanner output. Never recreate `~/SRC/` or a compat symlink to revive an old path; fix the reference instead. Dated files under `docs/plans/` and `.history/` still say `~/SRC/` on purpose — they record the state at the time and were deliberately left unrewritten.

## Stale clones reconciled (2026-05-25)

Three clones were far behind their remotes (newer work pushed from another machine post-reformat) and have since been reconciled:
- **`~/WorldFoundry.2026-new-level`** (`2026-new-level`): had 4 real local commits + was behind 14 → **merged** remote in. Now ahead 6, **unpushed** (push when ready).
- **`~/biohack.net`** (`master`, was behind 89) & **`~/indri.studio`** (`main`, was behind 30): the stale-based cascade commit was dropped, fast-forwarded to remote tip, then cascade re-run on the fresh tree. Both at remote tip with **uncommitted** memory changes (biohack: MEMORY.md only — it gitignores the symlinks; indri: 16 files — its remote had the cascade but with the broken 4-deep target, now retargeted to 3-deep).

The other commits (homedir, claude-usage, python-tui-lib, parking-space, wf-games, party-games) pushed cleanly.

**Why it mattered:** force-push would have deleted real remote commits; blind merge conflicted because both sides touched `.claude/memory/`. **How to apply:** when local is far behind with only a regenerable cascade commit on top, drop it + fast-forward + re-cascade rather than merging.
