---
name: home_src_layout
description: "Post-reformat, projects moved from ~/SRC/<name> to ~/<name>; what still assumes the old ~/SRC path and how it was patched"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9425f245-1b60-4bcf-91a7-279db284a72c
---

After the May 2026 machine reformat, project working copies live **directly at `~/<name>`** (e.g. `~/python-tui-lib`, `~/biohack.net`), **not** at `~/SRC/<name>`. `~/SRC/` now holds only `CLAUDE.md`, `docs/`, `free-services.md`. The old homedir is preserved at `~/homedir-old/`.

Things that still hardcode the old `~/SRC/<name>` layout:
- **`~/.claude/projects.json`** — every `path` is `~/SRC/<name>`. Stale, and also lists 9 active projects not checked out on this machine (bumper2bumper, finding-your-way, foundrylinux.org, gustos-colores, pcs, rapid-raccoon-site, RedGreenV2, WorldFoundry-wbniv, worldfoundry.org). **User chose to leave it as-is** — so [[claude-housekeeping]] scans will keep reporting those 9 as "missing memory cascade" false positives. Skip them.
- **`~/.claude/hook-runner.sh`** — defaults `SRC_ROOT` to `$HOME/SRC` and resolves all 12 dispatched hooks from `$SRC_ROOT/python-tui-lib/hooks/`. This broke the whole wrapper hook chain (transcript-logger, plan-first, md-preview, etc.).

**Fix applied (2026-05-25):** symlink `~/SRC/python-tui-lib -> ~/python-tui-lib` (user picked this over editing settings.json `env`). hook-runner now resolves + passes checksum. Note: editing `~/.claude/settings.json` is blocked by the auto-mode self-modification classifier — needs explicit user approval.

**Why:** the scanner can't see inside `hook-runner.sh`, so broken wrapper-dispatched hooks don't show up as drift — only the runtime "hook-runner: missing hook" error does.

**How to apply:** when a hook or scanner result references `~/SRC/<name>`, the real path is `~/<name>`. Don't recreate `~/SRC/<name>` dirs or fabricate cascades for absent projects.

## Stale clones reconciled (2026-05-25)

Three clones were far behind their remotes (newer work pushed from another machine post-reformat) and have since been reconciled:
- **`~/WorldFoundry.2026-new-level`** (`2026-new-level`): had 4 real local commits + was behind 14 → **merged** remote in. Now ahead 6, **unpushed** (push when ready).
- **`~/biohack.net`** (`master`, was behind 89) & **`~/indri.studio`** (`main`, was behind 30): the stale-based cascade commit was dropped, fast-forwarded to remote tip, then cascade re-run on the fresh tree. Both at remote tip with **uncommitted** memory changes (biohack: MEMORY.md only — it gitignores the symlinks; indri: 16 files — its remote had the cascade but with the broken 4-deep target, now retargeted to 3-deep).

The other commits (homedir, claude-usage, python-tui-lib, parking-space, wf-games, party-games) pushed cleanly.

**Why it mattered:** force-push would have deleted real remote commits; blind merge conflicted because both sides touched `.claude/memory/`. **How to apply:** when local is far behind with only a regenerable cascade commit on top, drop it + fast-forward + re-cascade rather than merging.
