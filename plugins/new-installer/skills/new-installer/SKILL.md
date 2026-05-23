---
name: new-installer
description: >
  Scaffold a new one-shot self-removing installer command for any Claude Code plugin marketplace
  or as a standalone slash command. The generated command runs a set of bash steps, verifies
  success, then removes itself — leaving no residual token cost once the thing is installed.
  Use when adding any software, extension, or tool that only needs to be set up once per machine.
  Trigger phrases: "new installer", "add an installer", "one-shot install",
  "make an install command", "/new-installer".
version: 2.0.0
---

# New One-Shot Installer

Scaffolds a self-removing installer slash command. Works in two modes:

- **Marketplace plugin** — generates a full plugin directory for a Claude Code marketplace repo (e.g. `username/my-plugins`). Users install with `/plugin install <name>@<marketplace>` and self-removal uses `/plugin uninstall`.
- **Standalone command** — generates a single `.md` file to drop into `.claude/commands/` (project-local) or `~/.claude/commands/` (global). Self-removal deletes the file via bash.

## Pattern

A one-shot installer is a slash command that:

1. Runs the bash steps needed to install something
2. Verifies the install succeeded
3. Removes itself — so it can never run twice and wastes no tokens after use

## What to collect upfront

Ask for all of these in one message before doing anything:

1. **Mode** — marketplace plugin or standalone command?
   - If marketplace: what is the repo handle (e.g. `alice/my-plugins`) and the short plugin name?
   - If standalone: where should the file land — project-local (`.claude/commands/`) or global (`~/.claude/commands/`)?
2. **Command name** — kebab-case. Convention: start with `install-` to signal one-shot intent (e.g. `install-gnome-usage`, `install-volta`), but not required.
3. **What it installs** — one sentence for the description.
4. **Install steps** — the ordered bash commands. Ask the user to paste them or describe them precisely. Capture `mkdir -p`, clone URLs, symlink targets, enable/activate commands exactly as they should run.
5. **Verification command** — a single command whose output confirms success (e.g. `gnome-extensions show <uuid>`, `which <binary>`, `<tool> --version`, `systemctl status <service>`). If none is obvious, ask.

Do not proceed until you have all of these.

## Marketplace plugin mode

### Directory structure

```
plugins/<name>/
  .claude-plugin/plugin.json
  commands/<name>.md
```

**`plugin.json`** — populate author from `git config user.name` and `git config user.email`; ask for a URL if the user has one:

```json
{
  "name": "<name>",
  "description": "<one-sentence description>. Self-removes after install.",
  "author": {
    "name": "<git user.name>",
    "url": "<author url, or omit field if none>"
  }
}
```

**`commands/<name>.md`:**

```markdown
---
description: <one-sentence description>. Self-removes after install.
allowed-tools: Bash
---

Install <what it installs> by running these steps in order:

1. <step 1 description>:
   ```
   <bash command>
   ```

[... remaining steps ...]

N. Verify the install succeeded:
   ```
   <verification command>
   ```
   Report the output to the user. If it indicates failure, stop here — do not proceed to removal.

N+1. Self-remove this one-shot installer:
   ```
   /plugin uninstall <name>@<marketplace-handle>
   ```

Tell the user what was installed and that the installer has been removed.
```

### README entry

If the repo has a `README.md` with a plugin table, add a row. Match the existing table format. If no table exists, add a `## Installers` section with a new one:

```markdown
| [`<name>`](plugins/<name>/) | One-shot installer for <what>. Self-removes after install. |
```

### Commit

```bash
git add plugins/<name>/ README.md
git commit -m "feat(<name>): add one-shot installer for <what>"
git push
```

Use whatever branch the repo is currently on.

---

## Standalone command mode

Generate a single file. Ask where to place it:

- **Project-local**: `.claude/commands/<name>.md` — available only in this project
- **Global**: `~/.claude/commands/<name>.md` — available in all projects

**`<name>.md`:**

```markdown
---
description: <one-sentence description>. Self-removes after install.
allowed-tools: Bash
---

Install <what it installs> by running these steps in order:

1. <step 1 description>:
   ```
   <bash command>
   ```

[... remaining steps ...]

N. Verify the install succeeded:
   ```
   <verification command>
   ```
   Report the output to the user. If it indicates failure, stop here — do not proceed to removal.

N+1. Self-remove this one-shot installer:
   ```
   rm <full-path-to-this-file>
   ```

Tell the user what was installed and that the installer has been removed.
```

Replace `<full-path-to-this-file>` with the actual absolute path (e.g. `~/.claude/commands/<name>.md` or `$PWD/.claude/commands/<name>.md`).

---

## Invariants (both modes)

- Every bash block must be a fenced code block on its own numbered step — no inline commands
- The verify step must always come immediately before self-removal
- Self-removal is always the very last action — nothing after it
- If self-removal might fail silently, add a note telling the user to remove it manually if the command persists after running
- Keep `plugin.json` description under 120 chars
- `allowed-tools: Bash` is the only tool a pure installer needs; don't add others unless the install requires file edits
