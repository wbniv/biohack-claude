# Config-root migration + making housekeeping detect it

**Date:** 2026-07-14
**Status:** done — all five steps landed; see [Outcome](#outcome)
**Trigger:** Will asked "have we fully migrated the memory system to this new computer?" — the answer turned out to be no, and the gap was far wider than memory.

---

## The finding

Claude Code 2.1.209 resolves its global config from `$CLAUDE_CONFIG_DIR`, which on this
machine is set to `/home/will/.config/claude/will`. Everything under `~/.claude/` is
therefore **ignored**. This machine was set up 2026-07-11; Claude Code appears to have
generated a fresh minimal `settings.json` at the new root, and the rest of the config
never came across.

Will's own read, unprompted: *"that's exactly what it feels like to me"* — the diagnosis
matches the lived experience of the machine, which is the strongest signal it's right.

### What is and isn't live

| Global artifact | Old root `~/.claude` | Live root `~/.config/claude/will` |
|---|---|---|
| Hooks | 16 in the chain | **1** (context-mode only) |
| Skills | 13 | **0** |
| Commands | 3 | **0** |
| `settings.json` | 5555 b — `env`, `permissions`, `statusLine`, `theme`, `tui`, `autoMode` | 614 b — `model`, `hooks`, `enabledPlugins`, `extraKnownMarketplaces`, `effortLevel` |
| Global memory | 27 | 27 — reachable via the symlink farm at `projects/-home-will/memory/` |
| Project memory | — | 158 unreachable across 16 repos |

Dead hooks of note: `git-add-guard.sh` (enforces the scoped-`git add` rule),
`commit-checklist.sh`, `plan-first.sh`, `plan-migrate.sh`, `md-preview.sh` (the `task md`
automation described by the `feedback_run_task_md` memory), `transcript-logger.sh`,
`todo-reminder.sh`, `tf-blocker.sh`.

### The fault line

Project-scoped `.claude/` still loads **from the repo** — which is why
`gustos-colores/.claude/commands/create-cobrand.md` works fine. Only **global**
artifacts resolve through `CLAUDE_CONFIG_DIR`. That asymmetry is why the breakage was
invisible: the things Will touches most (project commands, CLAUDE.md, plugins) kept
working.

### Why memory looked "orphaned" but isn't

The scanner already encodes the intended two-tier design:

- per-repo `~/<proj>/.claude/memory/` is **canonical and version-controlled**
- the loader dir `<root>/projects/<slug>/memory` should be a **symlink** to it
- generic memories cascade in as symlinks to the `~/.claude/memory` masters

So the 459 per-repo memories are not junk — they're the intended home. They're
unreachable only because the loader dir moved to the new root and nothing re-pointed it.
Three loader dirs are real directories today (gustos-colores 8, monetization-platform 5,
wald3n.com 5); the rest of each repo's store is invisible to the session.

## Why housekeeping didn't catch it

The skill exists to catch exactly this class of drift. It's dead three ways:

1. **It crashes on startup.** `load_projects()` does `expanduser(entry["path"])`; 26 of
   64 `projects.json` entries are idea-stage with `path: null` → `TypeError` before any
   scan runs. A run scheduled for 2026-07-12 silently produced nothing; the only report
   on disk is 2026-07-11.
2. **Every root is hardcoded to the old world.** `GLOBAL_CLAUDE = HOME/".claude"` is the
   only global root it knows, so the new loader dirs are invisible. `skill-install-drift`
   points at `~/SRC/biohack-claude`, which does not exist (the marketplace checkout lives
   under `<root>/plugins/marketplaces/biohack-claude`).
3. **The fix already existed, stranded.** `~/.claude/skills/claude-housekeeping/` is
   *newer* than the git-tracked plugin source and already carries the null-path fix and
   `code.tags` namespacing — but it sits in the orphaned root, so it never runs. The
   stale, crashing plugin copy is the live one. This is precisely the `skill-install-drift`
   the scanner is supposed to report, undetectable because that scan's own path is wrong.

## Pivot: who moved the root, and why "port into the live root" is wrong

Two facts found mid-implementation invert the obvious fix.

**1. Claude Code moved the root itself.** `CLAUDE_CONFIG_DIR` is *not* set by any shell
profile — a clean `env -i bash -lc` login shell has it unset. Claude Code 2.1.209 exports
it to child processes. So this is Claude Code's own XDG migration
(`~/.claude` → `~/.config/claude/<account>/`), and it was partial: plugins, plans,
projects, and CLAUDE.md came across; skills, commands, the hook chain, permissions, and
the memory master did not. Nobody did this on purpose — which is exactly why nobody
noticed. (Corroborating: `~/.local/bin/claude-status` reads the account name from
`CLAUDE_CONFIG_DIR`, commented "set by claude-account wrapper" — a wrapper that does not
exist on this machine. The statusline is itself one of the dropped settings, so it isn't
running either.)

**2. The live root is gitignored; the old root is version-controlled.** `$HOME` *is* the
`wbniv/homedir` git repo. `~/.claude/` has **317 tracked files** (skills 108, projects
172, memory 26, hooks 5, commands 3, settings.json). `~/.config/claude/` matches the
`.config/*` ignore-all rule and has **0 tracked files**.

> Porting the artifacts *into* the live root — the plan's original step 3 — would move
> Will's entire config from version-controlled to untracked, days before a machine swap.
> That is the precise opposite of the goal.

**Revised approach — canonical stays `~/.claude`, the live root points at it:**

- `<live>/skills`, `<live>/commands`, `<live>/memory` become **symlinks** to the tracked
  `~/.claude/*` originals. This extends a pattern already proven on this machine: the
  memory symlink farm at `<live>/projects/-home-will/memory/` (created 2026-07-11 13:03)
  does exactly this, file by file.
- **Hook scripts need no move at all** — `settings.json` already references them by
  absolute path (`/home/will/.claude/hooks/…`, `$HOME/SRC/python-tui-lib/hooks/…`). Only
  the hook *chain* in `settings.json` has to be restored.
- `settings.json` can't be a symlink (Claude Code rewrites it), so the dropped keys get
  **merged** into the live file, and a targeted `!` opt-in in `~/.gitignore` puts it —
  and the new symlinks — under version control so the swap carries them.

Rejected: relocating the 317 tracked files into the live root and re-tracking there.
It's arguably where Claude Code is heading, but it's a large migration to run days before
a hardware swap, and it can be done later from a clean state.

## Plan

1. **Reconcile scanner copies.** Port the stranded null-path + `code.tags` fixes from the
   installed copy into the git-tracked plugin source. Unblocks everything else.
2. **Make the scanner root-aware.**
   - Resolve the live root from `$CLAUDE_CONFIG_DIR`, falling back to `~/.claude`.
   - Loader dir = `<live_root>/projects/<slug>/memory`.
   - Fix `skill-install-drift`'s marketplace path.
   - **New scan — `legacy-config-root`:** diff the legacy root against the live root
     generically (skills / commands / hooks / memory / settings keys) and report anything
     present in the former and absent from the latter. Root-agnostic on purpose: the next
     machine move gets caught by `/claude-housekeeping` instead of by hand.
3. **Reconnect the global artifacts** (Will's call: as-is, not reviewed) — per the pivot
   above: symlink `<live>/{skills,commands,memory}` → the tracked `~/.claude/*`; merge the
   16-hook chain and the dropped `settings.json` keys (`env`, `permissions`, `statusLine`,
   `theme`, `tui`, `autoMode`, …) into the live `settings.json` **without** clobbering the
   live context-mode hook or the keys Claude Code wrote (`model`, `enabledPlugins`,
   `extraKnownMarketplaces`, `effortLevel`); add `~/.gitignore` opt-ins so the result is
   tracked.
4. **Consolidate memory** onto the intended design: merge each real loader dir into its
   repo store, symlink loader → repo, verify nothing is lost.
5. **Verify + push.** Scanner runs clean; `legacy-config-root` and `unmirrored-memory`
   report zero. Commit to `wbniv/biohack-claude` so the fix travels to the next machine
   via the marketplace rather than living only on this disk.

## Constraint

Will replaces this machine in a few days. The point is not to tidy this box — it's that
whatever is copied forward is what survives. Consolidating *before* the swap means one
clean store gets copied; the scanner change is what makes the *next* swap self-checking.

## Verification

- `scanner.py --report-only` completes (today: `TypeError`).
- `legacy-root` reports the drifted artifacts before the port, zero after.
- `unmirrored-memory` reports 3 before consolidation, zero after.
- Memory file count is conserved across the consolidation (no store loses a file).
- A fresh session sees the restored skills/commands and the per-project memory.

## Outcome

All verification gates met.

| Scan | Before | After |
|---|---|---|
| scanner runs at all | `TypeError` | 70 recommendations ✅ |
| `legacy-root` | 68 stranded artifacts | **0** ✅ |
| `unmirrored-memory` | 3 projects | **0** ✅ |
| `global-hooks` | 8 of 8 baseline missing | **0** ✅ |

Reconnected: 13 skills, 3 commands, 28-file memory master; `settings.json`
614 b → 5934 b (17 hooks, 14 keys, 13 permission rules, 14 plugins — the move had
silently disabled 10 of 13).

Memory consolidated with **nothing lost** — verified file-by-file against a backup,
including content equality and index-entry preservation:

| Project | Reachable before | After |
|---|---|---|
| gustos-colores | 10 | **46** |
| monetization-platform | 6 | **24** |
| wald3n.com | 7 | **28** |

**Live confirmation mid-session:** the 13 skills and both commands reappeared in the
session's skill list immediately after symlinking — Claude Code picked them up without a
restart.

### Bugs found along the way (each fixed)

- `cmd_block_mirror_memory()` would have **clobbered each repo's `MEMORY.md`** with the
  loader's shorter one, silently dropping every cascade entry. Caught by checking for
  collisions before copying rather than trusting the generated block.
- `_project_dir_slug()` slugged the unresolved path, so `~/SRC/<name>` compat symlinks
  yielded `-home-will-SRC-foo` — matching no loader dir and reporting a **clean zero**.
  This single bug hid all 3 unmirrored-memory findings.
- `_repo_tracks_memory()` grepped for a literal `!.claude/memory/` instead of asking git;
  repos that simply never ignore `.claude` were told to "add" a line they don't need.
- Five copies of this skill exist on disk. I edited the wrong one first (the legacy-root
  marketplace checkout); canonical is `~/biohack-claude`, and the *executing* copy is the
  commit-keyed plugin cache.

### Follow-ups (not done — deliberately out of scope)

- **Restart Claude Code.** Hooks, permissions and statusLine are read at session start;
  the plugin cache is keyed by commit (`6b49abca38f1` = pre-fix) and rebuilds on restart.
  Until then the plugin still runs the stale scanner — the synced `~/.claude/skills/` copy
  is current.
- **`missing-cascade`: 33** — pre-existing, untouched. Global memories not yet symlinked
  into each project.
- **`~/.claude/skills/` duplicates ~8 plugins** (`billing-tags`≈`aws-billing-tags`,
  `package`, `iam-bootstrap`, …). Both now load, as they did on the old machine. Worth a
  deliberate pick-one pass, but that's a strategy call, not drift.
- **`projects.json`** still declares `~/SRC/<name>` paths and
  `global_artifacts_root: ~/.claude`. Both work (the SRC symlinks resolve; the scanner now
  resolves paths itself), but they're stale declarations.
- **Relocating the 317 tracked files into the live root** and retiring `~/.claude` — likely
  where Claude Code is heading, but a large migration to run days before a hardware swap.
