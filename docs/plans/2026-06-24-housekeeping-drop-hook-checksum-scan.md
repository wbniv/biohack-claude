# claude-housekeeping: drop the hook-checksum/hook-runner coupling

**Date:** 2026-06-24
**Scope:** `plugins/claude-housekeeping/skills/claude-housekeeping/` (biohack-claude) + its byte-identical live mirror at `~/.claude/skills/claude-housekeeping/` (home repo)

## Context

The sha256 hook-integrity mechanism was removed (see python-tui-lib plan
`2026-06-24-remove-hook-checksum-mechanism.md`; commits `41ab1c3`/`fc18728`/`4c14b5a`).
The `claude-housekeeping` skill still *audits* that mechanism. It degrades
gracefully — `scan_hook_checksum_drift()` no-ops when the manifest is absent, and
`scan_global_hooks_sanity` normalizes both invocation forms — so nothing nags or
breaks. But the coupling is now dead code + stale docs, which "remove it entirely"
should scrub.

Two tracked copies must stay byte-identical (the skill's own `skill-install-drift`
scan checks this):
- **A** — `~/SRC/biohack-claude/plugins/claude-housekeeping/skills/claude-housekeeping/` (plugin source)
- **B** — `~/.claude/skills/claude-housekeeping/` (live global skill, tracked in the `/home/will` repo)

Marketplace/cache copies under `~/.claude/plugins/**` are regenerated from A on
plugin update — not hand-edited.

## Approach

Edit copy A, then mirror the changed files to B; delete the dead runbook in both.

### scanner.py
1. `CATEGORIES_ORDER`: remove the `("hook-checksum-drift", …)` entry.
2. `SCAN_DESCRIPTIONS`: remove the `"hook-checksum-drift": …` entry.
3. `Project.hook_runner` property: remove.
4. `_normalize_hook_cmd`: keep the basename logic (still used by
   `scan_global_hooks_sanity`); drop the hook-runner mention from the docstring.
5. `scan_broken_hook_paths`: keep logic; update the two comments that cite
   `hook-runner.sh`'s bare arg (no longer a thing) to a generic phrasing.
6. `scan_hook_checksum_drift()`: delete the whole function.
7. State-table renderers (×2): remove the `"✅ (hr)"` hook-runner marker branch.
8. `render_mermaid_dependency`: remove the `uses_hr` set and its node emission;
   only the `no_settings` divergence remains.
9. Legend line: drop the `` `(hr)` `` clause.
10. `main`: remove `recs.extend(scan_hook_checksum_drift())`.

### SKILL.md
- Remove scan **#8 "Hook checksum drift"**; renumber #9→#8, #10→#9, #11→#10.
- Scan #7: drop the dangling `(see scan #8)` parenthetical (already a stale ref).
- New #9 (broken shared-library refs): drop the trailing "Manifest-routed hooks
  then need `hook-checksums.json` regenerated." sentence.

### runbooks/
- Delete `hook-checksum-remediation.md`.
- `global-hooks-baseline.md`: rewrite the "Hook command form" section + JSON
  snippet to the direct form `bash $HOME/SRC/python-tui-lib/hooks/<name>.sh`
  (matches the now-live settings.json); drop the "Part E: hook-runner.sh" ref.

## Verification

1. `python3 -m py_compile scanner.py` clean (copy A and B).
2. No residual references in either copy:
   ```
   grep -rl 'hook-checksum\|hook-runner\|hook_runner\|regen-hook' A/ B/   # expect none
   ```
3. Scanner runs and emits no `hook-checksum-drift` category:
   ```
   python3 scanner.py --report-only 2>&1 | tail; # exits 0, no hook-checksum rows
   ```
4. A and B byte-identical (modulo `.history/`, `__pycache__/`):
   ```
   diff -rq --exclude=.history --exclude=__pycache__ A/ B/   # no diffs
   ```

## Verification — evidence

1. `python3 -m py_compile scanner.py` → `OK: scanner.py compiles`. **PASS**
2. Residual refs in copy A: `none — copy A clean` (grep for
   hook-checksum/hook-runner/hook_runner/regen-hook/(hr)). `sha256_of` retained
   (still used by lines 549/957/958). **PASS**
3. `python3 scanner.py --report-only` → exit 0; report has **no**
   `hook-checksum-drift` category; `global-hooks` category = 0 recommendations
   (the rewired settings.json passes the baseline check). The only
   "hook-checksum" strings in the report are the `uncommitted` scan listing this
   change's own in-flight files (deleted runbook + plan filename) — they vanish
   once committed. **PASS**
4. `diff -rq --exclude=.history --exclude=__pycache__ A B` → `IDENTICAL`. **PASS**

## Status

Done — coupling removed from `scanner.py`, `SKILL.md`, and `global-hooks-baseline.md`;
`hook-checksum-remediation.md` deleted. Plugin source (biohack-claude) and live
mirror (home repo) updated identically and committed per repo.
