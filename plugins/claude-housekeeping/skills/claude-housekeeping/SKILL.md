---
name: claude-housekeeping
description: Scan all Claude Code project artifacts (memories, hooks, commands, plans, settings) across global ~/.claude and every project in ~/.claude/projects.json. Produce a numbered list of drift recommendations plus an executable command list, state-visualization table, and mermaid graphs. Never auto-applies — user must approve recommendations explicitly. Use when the user says "housekeeping", "/claude-housekeeping", "audit my claude config", "find drift", or wants a daily/weekly snapshot of their Claude setup health.
version: 1.4.1
---

# Housekeeping

User-invoked drift detector + cleanup helper for the user's Claude Code artifacts.

## Operating principle (hard rule — never relax)

1. **User-invoked.** Nothing schedules this skill automatically on Stop/SessionStart/Notification. The one exception: after the user explicitly approves and the model applies recommendations, the skill self-schedules a follow-up run 24 hours out (see [Post-apply scheduling](#post-apply-scheduling)). That schedule is a direct result of user-approved work, not background automation.
2. **Scans and reports.** Produces a numbered recommendation list. Does not apply any change on its own.
3. **Only acts on items the user explicitly approves** — "do #1, #3" or "all" or "skip". The user can also say "modify #3 to do X instead" and the skill respects that.
4. **After approved actions, report what was done + offer a follow-up scan** to confirm the items cleared.

If invoked via `/schedule` for an unattended cron run, the skill MUST stop after producing the report — surfaces a notification for the user to review on their next prompt. **No unattended execution of recommendations, ever.**

## Invocation modes

```
/claude-housekeeping                           # interactive: scan, show report, prompt for approvals, apply
/claude-housekeeping --report-only             # scan only, write report file, no prompts
/claude-housekeeping --report-only --quiet     # report only, no notification if zero recommendations
/claude-housekeeping --diff before=X after=Y   # generate delta report comparing two prior snapshots
/claude-housekeeping --threshold-days=N        # tune the "orphan plans older than N days" cutoff (default 1)
/claude-housekeeping --include-dormant         # scan dormant projects too (default: skip)
/claude-housekeeping --emit-commands=3,7,12    # output only the specified recommendations' command blocks
/claude-housekeeping --report-only --auto-reschedule  # report only + reschedule next run 24 h out (used by self-scheduled runs)
```

## How to invoke from the model

When the user types `/claude-housekeeping` (with any args), run the scanner directly — there is no wrapper script:

```bash
python3 $HOME/.claude/skills/claude-housekeeping/scanner.py --report-only [args]
```

The scanner writes a markdown report to `~/.claude/housekeeping/reports/YYYY-MM-DD-HHMM.md` and prints the path on stdout. The model should `Read` the report file and surface a summary + numbered recommendations to the user.

**Interactive flow** (after reading the report):
1. Surface the recommendation list to the user.
2. Wait for approval input ("do 1,3,7" / "all" / "skip" / "1-5" / "modify 3").
3. Execute approved recommendations one-by-one using the **Executable command list** section of the report (each block has backup → pre-check → action → post-check).
4. Report the result of each.
5. **Post-apply scheduling** — after all approved actions are complete, schedule the next run (see [Post-apply scheduling](#post-apply-scheduling)).

**Plan mode compatibility:** `--report-only` is safe to run in plan mode — it only writes an audit-output file under `~/.claude/housekeeping/reports/`, not actual state changes. Defer applying recommendations until plan mode exits.

## Post-apply scheduling

After the user approves and the model applies one or more recommendations, the model **must** create or reset a 24-hour one-shot follow-up run. This is the only scheduling that happens; it does not fire on `--report-only` runs that were not triggered by the scheduler itself.

State file: `~/.claude/housekeeping/scheduled-run.json`
```json
{ "job_id": "<CronCreate id>", "scheduled_for": "<ISO UTC>", "created_at": "<ISO UTC>" }
```

### Steps (run after step 4 of the interactive flow)

1. **Read state file.** If `~/.claude/housekeeping/scheduled-run.json` exists, extract `job_id`.
2. **Cancel old job.** Call `CronDelete(id)` — ignore errors (job may have already fired and auto-deleted).
3. **Compute target time.** Run via Bash:
   ```bash
   date -d '+24 hours' '+%M %H %d %m *'
   ```
   This produces the local-time cron expression (e.g. `"27 14 22 5 *"`).
4. **Create new job.** Call `CronCreate` with:
   - `cron`: the value from step 3
   - `recurring`: `false` (one-shot; auto-deletes after firing)
   - `durable`: `true` (persists across session restarts)
   - `prompt`: `"/claude-housekeeping --report-only --auto-reschedule"`
5. **Save state.** Write the returned job ID and timestamps to `~/.claude/housekeeping/scheduled-run.json`:
   ```bash
   SCHED_FOR=$(date -d '+24 hours' -u +%Y-%m-%dT%H:%M:%SZ)
   NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   printf '{"job_id":"%s","scheduled_for":"%s","created_at":"%s"}\n' \
     "$NEW_JOB_ID" "$SCHED_FOR" "$NOW" \
     > ~/.claude/housekeeping/scheduled-run.json
   ```
6. **Inform the user.** One line: `"Next housekeeping run scheduled for <human-readable local time>."` (e.g. "Thu 22 May 14:27").

### `--auto-reschedule` flow (self-scheduled unattended run)

When invoked as `/claude-housekeeping --report-only --auto-reschedule` (i.e., fired by the scheduler):

1. Run the scanner and write the report as normal.
2. Surface the report summary via notification (even if zero recommendations — confirms the run fired).
3. The one-shot job auto-deleted on firing, so skip step 2 (CronDelete) above. Run steps 3–6 to schedule the next 24-hour run.
4. **Never apply recommendations** — `--report-only` takes precedence. The user reviews the report on their next prompt.

## What it scans for

1. **Orphan plans** in `~/.claude/plans/*.md` older than `--threshold-days` (default 1).
   - Skip `screenshots/`.
   - Recommend: route to a likely project's `docs/plans/` (content-sniffing for project signals), or delete if trivially-small / shipped-duplicate.
   - **Caution — most orphans are already-migrated working copies.** Plan-mode plans get auto-migrated into a project's `docs/plans/` under a dated slug; the file left in `~/.claude/plans/` is the orphaned original. **Before routing, check the target project's `docs/plans/` for an existing canonical** (same H1 / topic, possibly a different slug or date). If one exists, **delete the orphan** — routing it creates a near-duplicate. Only genuinely-unmigrated plans should be routed.

2. **Duplicate memories** — same-filename `feedback_*.md` across ≥3 projects.
   - Recommend: promote to `~/.claude/memory/<name>.md` (create global index if absent), delete per-project copies. Show content diff if copies aren't identical.

3. **Duplicate commands** — `*.md` in `~/.claude/commands/` that also appear in `*/.claude/commands/`.
   - Recommend: delete the per-project copy. Excludes `.worktrees/` paths.

4. **Config drift** — per-project `settings.json` hook lines that are now covered globally.
   - Recommend: remove duplicate lines (or remove whole settings.json if empty after).

5. **Missing global hooks** — sanity check `~/.claude/settings.json` matches the expected baseline.

6. **Uncommitted/untracked `.claude/` changes** — modified or untracked artifacts (skills, commands, memory, hooks, `settings.json`, `CLAUDE.md`) in either the homedir repo (covers global `~/.claude/`) or any project repo (covers `~/SRC/<project>/.claude/`). Skips ephemeral subdirs (sessions, cache, daemon, telemetry, backups, etc.) and `.bak`/`~`/`.tmp`/`.swp` files. Catches in-flight skill development, untracked auto-memory files, and config edits that never got committed.

7. **Missing global memory cascade (scope-aware)** — Claude's auto-memory loader is cwd-siloed: only `~/.claude/projects/{slug}/memory/` loads, so the global memories at `~/.claude/memory/` never reach project sessions. But **not every global memory belongs in every project** — most are situational (a `bangkok_cost_estimates` memory is noise in a C++ engine; `wayland_keybindings` is noise in a web project). So the cascade is **scoped**, not blanket:
   - Each global memory declares **`applies-to: [tag, …]`** in its frontmatter (`universal` / `web` / `legacy-cpp` / `desktop` / `bkk` / …). Absent → treated as `universal` (back-compat).
   - Each project declares **`tags: [...]`** in `projects.json`. A memory cascades into a project iff it's `universal` **or** its `applies-to` intersects the project's `tags`. Untagged project → `universal` memories only (safe default).
   - This scan detects, per active project: **qualifying** global memories not yet symlinked in (to add), symlinks to memories that **no longer qualify** for the project's scope (to prune), stale symlinks (target deleted), and real-file collisions (project has a same-named local memory).
   - Recommend: run the `apply-cascade.py` helper, which symlinks only qualifying memories, **prunes out-of-scope ones**, merges the global `MEMORY.md` sections into the project's `MEMORY.md` between auto-managed markers, and updates `.gitignore`. Collisions are surfaced but never overwritten.
   - **Project-specific memories don't belong in global.** A memory that names one project (e.g. *"In ~/SRC/trip, …"*) should live as a real file in that project's `.claude/memory/`, not in the global dir (see scan #8).

8. **Hook checksum drift** — entries in `~/.claude/hook-checksums.json` whose recorded sha256 no longer matches the live `~/SRC/python-tui-lib/hooks/*.sh`. Happens when a shared hook changes (an uncommitted edit, or a `git pull` in python-tui-lib) without the manifest being regenerated; `hook-runner.sh` then refuses to run the drifted hook (warn, not block), so it silently stops firing (e.g. `md-preview.sh` no longer auto-renders edited `.md`).
   - Recommend: **audit the python-tui-lib diff first** (the regen trusts whatever is on disk), then `regen-hook-checksums.sh --global`, then verify live==recorded. Full steps in [`runbooks/hook-checksum-remediation.md`](runbooks/hook-checksum-remediation.md). Pairs with scan #5 (broken-hook-paths) as the two halves of hook integrity.

9. **Installed skill ≠ git source** — a skill under `~/.claude/skills/` that differs from its git-tracked plugin source under `~/SRC/biohack-claude/plugins/*/skills/`. The live copy was edited in place, or the published plugin is a stale snapshot — the two rot apart.
   - Recommend: pick the canonical side (usually the live, more-evolved copy), sync the other, and commit the source.

10. **Broken shared-library references** — a `python-tui-lib/scripts/` or `/hooks/` `.sh` referenced from a `settings.json` hook command (global + per-project) **or** a `cmds:` entry in `~/Taskfile.yml` / `~/SRC/*/Taskfile.yml`, that no longer exists on disk. Catches drift after a shared script is renamed/removed without updating its callers — e.g. `md-to-pdf.sh` → `md-to-html.sh` leaving `task md` dead with `exit 127`. Scoped to `python-tui-lib/{scripts,hooks}/` paths (resolving `{{.ROOT_DIR}}` / relative / `~` / `$VAR` forms) so it stays quiet on project-local scripts and remote `/opt/…` references.
    - Recommend: repoint the caller at the current file — the scan fuzzy-matches the missing basename against the live `python-tui-lib` listing to suggest the rename (e.g. `md-to-pdf.sh` → `md-to-html.sh`) — or delete the dead caller. Manifest-routed hooks then need `hook-checksums.json` regenerated.

## Report file format

Reports land at `~/.claude/housekeeping/reports/YYYY-MM-DD-HHMM[-before|-after|-diff].md`.

Structure (in order):

```
# Housekeeping report — YYYY-MM-DD HH:MM

## Summary

<sentence: N recommendations across K categories>

## Recommendations

### 1. <category> — <one-line title>
<details>

### 2. ...
[etc.]

## Executable command list

<prelude>

# Recommendation #1
<backup + pre-check + action + post-check + rollback hint>

# Recommendation #2
...

<end summary>

## State visualization

<Unicode-box table — one row per project, columns for artifact types>

## Mermaid graphs

<dependency map, recent migrations (if any), recommendation category pie>
```

For `--diff` mode, the structure differs (see "Diff mode" below).

## Diff mode (`--diff before=X after=Y`)

Generates a comparison report:

```
# Housekeeping diff — <before-timestamp> → <after-timestamp>

## Summary

- Resolved: N recommendations
- New: M recommendations (regressions or new drift)
- Unchanged: K recommendations (deferred / dormant)
- Net change: -<N-M>

## Resolved recommendations
<list — these got fixed>

## New recommendations
<list — investigate before declaring success>

## Unchanged recommendations
<list — skipped/dormant>

## State table diff
<side-by-side — what changed per project>

<details>
<summary>Full before report</summary>
<embedded report #1>
</details>

<details>
<summary>Full after report</summary>
<embedded report #2>
</details>
```

## Safety contract for recommendation execution

Every recommendation's command block follows this pattern:

1. **Backup** — `cp -a` originals into `/tmp/housekeeping-backup-<timestamp>/recommendation-N/`.
2. **Pre-check** — `sha256sum` / `diff` to confirm the file is in the expected pre-state.
3. **Action** — the actual change (`mv`, `rm`, etc.).
4. **Post-check** — verify the new state matches expectations.
5. **Rollback hint** — exact reverse commands in a comment.

**Hash-pinning**: the command block embeds sha256s of source files in pre-checks, so a deferred apply (hours later, state shifted) fails fast rather than overwriting unexpected state.

## Canonical project list

The skill reads `~/.claude/projects.json` for the list of projects to scan. Each entry has `name`, `path`, `status` (active/dormant), optional `notes`. Dormants skipped by default; `--include-dormant` includes them.

## Related plan

This skill was specified in `~/SRC/docs/plans/2026-05-19-globalize-hooks-housekeeping-skill.md` (Part B). Refer there for design rationale.
