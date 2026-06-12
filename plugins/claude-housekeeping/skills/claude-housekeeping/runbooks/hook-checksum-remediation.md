# Runbook: Hook checksum drift remediation

`hook-runner.sh` verifies each shared hook's sha256 against the manifest at
`~/.claude/hook-checksums.json` before running it, and **refuses to run** (warn,
not block) any hook whose live content drifted. Drift happens when a hook in
`~/SRC/python-tui-lib/hooks/` changes — an uncommitted local edit, or a
`git pull` in python-tui-lib — without the manifest being regenerated.

**Symptom:** a PostToolUse/PreToolUse hook prints
`hook-runner: checksum mismatch for <name>.sh`, and that hook silently stops
firing (e.g. `md-preview.sh` no longer auto-renders edited `.md` files).

**Pre-state:** the manifest's recorded sha for `<name>.sh` ≠ the live file's sha.

**Post-state:** manifest sha == live sha for every hook; hook-runner runs them again.

> The regen **trusts whatever is on disk**. Never regenerate without first
> auditing the diff — a regen blesses a tampered hook just as readily as a
> legitimate one.

## Steps

### 1. Audit — what changed, and is it benign?

```bash
git -C "$HOME/SRC/python-tui-lib" status --short hooks/
git -C "$HOME/SRC/python-tui-lib" diff hooks/        # uncommitted edits
git -C "$HOME/SRC/python-tui-lib" log --oneline -3 -- hooks/   # or a recent pull
```

Read the actual diff. A one-line fallback-renderer swap or a path fix is benign;
a new `curl … | sh`, an added network call, or an obfuscated payload is **not** —
stop and investigate before regenerating.

### 2. (If the change should persist) commit it in python-tui-lib

So the manifest references a committed SHA, not a throwaway working-tree state:

```bash
git -C "$HOME/SRC/python-tui-lib" add hooks/<name>.sh
git -C "$HOME/SRC/python-tui-lib" commit -m "fix(hooks): <what changed>"
```

### 3. Regenerate the manifest

The manifest in use here is the **global** one (`~/.claude/hook-checksums.json`):

```bash
bash "$HOME/SRC/python-tui-lib/scripts/regen-hook-checksums.sh" --global
```

(Drop `--global`, or use `--target <project>`, for a project-local manifest.
`--all` refreshes the global manifest and every opted-in project at once.)

### 4. Verify live == recorded

```bash
name=<name>.sh
live=$(sha256sum "$HOME/SRC/python-tui-lib/hooks/$name" | awk '{print $1}')
rec=$(jq -r --arg n "$name" '.[$n]' "$HOME/.claude/hook-checksums.json")
[ "$live" = "$rec" ] && echo "MATCH ✓" || echo "MISMATCH: live=$live rec=$rec"
```

Trigger the hook once more (e.g. edit any `.md` for `md-preview.sh`) and confirm
the `checksum mismatch` warning is gone.

## Rollback

The only state changed is `~/.claude/hook-checksums.json` (and, if you did step 2,
a python-tui-lib commit). To revert the manifest, re-run the regen against the
prior python-tui-lib state, or restore the file from git/backup.

## Notes

- This is the manifest side of hook integrity. The complementary check is
  **`broken-hook-paths`** (a hook command points at a script that doesn't exist).
- After a `git pull` in python-tui-lib, regenerating the manifest is expected
  housekeeping — audit the pulled diff, then regen.
