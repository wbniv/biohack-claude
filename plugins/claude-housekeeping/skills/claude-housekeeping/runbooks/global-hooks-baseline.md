# Runbook: Install the baseline global hook chain

This runbook adds the missing hooks to `~/.claude/settings.json` so every
Claude Code session in any working directory gets the standard chain:
plan-first reminder, plan-migrate auto-copy, transcript logging, etc.

**Pre-state:** `~/.claude/settings.json` may already exist with the
tab-color hooks (`tab-session-start.sh`, `tab-orange.sh`,
`tab-reset.sh`). Don't replace those — **merge** the additions below
into the existing `hooks` block.

**Post-state:** The hooks block contains every entry in the
[Expected hook table](#expected-hook-table). Other top-level keys
(`permissions`, `statusLine`, `enabledPlugins`, `autoMode`, etc.) are
unchanged.

## Expected hook table

| Event              | Matcher           | Hooks (in order)                                                                       |
| ------------------ | ----------------- | -------------------------------------------------------------------------------------- |
| SessionStart       | —                 | tab-session-start.sh, session-clear-md-flags.sh                                        |
| UserPromptSubmit   | —                 | tab-reset.sh, transcript-logger.sh                                                     |
| PreToolUse         | Bash              | commit-checklist.sh, tf-blocker.sh, sleep-blocker.sh, git-add-guard.sh                 |
| PreToolUse         | Write\|Edit       | plan-first.sh                                                                          |
| **PostToolUse**    | **ExitPlanMode**  | **plan-migrate.sh** ← required for Plan-mode → docs/plans/ auto-copy                   |
| PostToolUse        | Write\|Edit       | md-preview.sh                                                                          |
| PostToolUse        | Write\|Edit\|MultiEdit | py-syntax.sh, shell-strict.sh                                                     |
| Stop               | —                 | tab-orange.sh, todo-reminder.sh, transcript-stop.sh                                    |

## Hook command form

All hook commands take the form:

```
bash $HOME/.claude/hook-runner.sh <name>.sh
```

The `hook-runner.sh` wrapper verifies the SHA-256 of `<name>.sh` against
`$HOME/.claude/hook-checksums.json` before exec'ing it (defence against
upstream tamper). If the runner isn't installed yet, fall back to direct
`bash ${SRC_ROOT:-$HOME/SRC}/python-tui-lib/hooks/<name>.sh` — also
absolute-path-resolved so subdir/worktree cwd doesn't break resolution.

## JSON snippet to merge

Paste this into `~/.claude/settings.json` inside the existing top-level
`hooks` key (don't overwrite — merge each event array). If your editor
supports JSON merge / patch, that's easier than hand-merging.

```json
"UserPromptSubmit": [
  {
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh transcript-logger.sh", "timeout": 5 }
    ]
  }
],
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh commit-checklist.sh", "timeout": 5 },
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh tf-blocker.sh", "timeout": 5 },
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh sleep-blocker.sh", "timeout": 5 },
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh git-add-guard.sh", "timeout": 5 }
    ]
  },
  {
    "matcher": "Write|Edit",
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh plan-first.sh", "timeout": 5 }
    ]
  }
],
"PostToolUse": [
  {
    "matcher": "ExitPlanMode",
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh plan-migrate.sh", "timeout": 10 }
    ]
  },
  {
    "matcher": "Write|Edit",
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh md-preview.sh", "timeout": 30 }
    ]
  },
  {
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh py-syntax.sh", "timeout": 10 },
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh shell-strict.sh", "timeout": 5 }
    ]
  }
],
"Stop": [
  {
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh todo-reminder.sh", "timeout": 5 }
    ]
  },
  {
    "hooks": [
      { "type": "command", "command": "bash $HOME/.claude/hook-runner.sh transcript-stop.sh", "timeout": 5 }
    ]
  }
]
```

The existing `SessionStart` and `Stop` blocks already have tab-color
hooks. **Append** `session-clear-md-flags.sh` to `SessionStart` and
`todo-reminder.sh` + `transcript-stop.sh` to `Stop` rather than replacing.

## Steps

1. **Backup:**
   ```bash
   cp -a $HOME/.claude/settings.json /tmp/settings.json.bak-$(date +%Y%m%d-%H%M)
   ```

2. **Edit:**
   ```bash
   ${EDITOR:-vi} $HOME/.claude/settings.json
   ```
   Merge the JSON snippet above into the existing `hooks` block.
   Preserve all other top-level keys.

3. **Validate JSON:**
   ```bash
   jq . $HOME/.claude/settings.json > /dev/null && echo "valid JSON"
   ```

4. **Sanity-check hooks load:** Start a fresh Claude Code session,
   send any prompt, watch for hook errors in stderr. None expected.

5. **Verify with the scanner:**
   ```bash
   /claude-housekeeping --report-only
   ```
   The `global-hooks` category should drop to 0 recommendations.

## Rollback

```bash
cp -a /tmp/settings.json.bak-<timestamp> $HOME/.claude/settings.json
```

## See also

- [Plan: 2026-05-19-globalize-hooks-housekeeping-skill.md](~/SRC/docs/plans/2026-05-19-globalize-hooks-housekeeping-skill.md) (Part A: hook + global wiring; Part E: hook-runner.sh)
- [Audit: 2026-05-19-housekeeping-report-audit.md](~/SRC/docs/investigations/2026-05-19-housekeeping-report-audit.md) (why the report was reshaped)
