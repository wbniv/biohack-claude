---
name: new-installer
description: >
  Scaffold a new one-shot self-removing installer command in the biohack-claude marketplace.
  The generated command runs a set of bash steps, then calls `/plugin uninstall` on itself so
  it leaves no residual token cost once the thing is installed. Use when adding any software,
  extension, or tool that only needs to be set up once per machine.
  Trigger phrases: "new installer", "add an installer", "one-shot install", "make an install command", "/new-installer".
version: 1.0.0
---

# New One-Shot Installer

Scaffolds a self-removing installer plugin in the biohack-claude marketplace repo.

## Pattern

A one-shot installer is a Claude Code plugin containing a single slash command that:

1. Runs the bash steps needed to install something
2. Verifies the install succeeded
3. Calls `/plugin uninstall <name>@biohack-claude` to remove itself

Once run, the command is gone — zero ongoing token cost, nothing stale in the user's config.

## What to collect upfront

Ask for all of these in one message before doing anything:

1. **Plugin name** — kebab-case, e.g. `install-gnome-usage`. Must start with `install-` by convention.
2. **What it installs** — one sentence for the plugin description and README entry.
3. **Install steps** — the ordered bash commands. Ask the user to paste them or describe them precisely. Capture any `mkdir -p`, clone URL, symlink targets, enable commands exactly.
4. **Verification command** — a single command whose output confirms success (e.g. `gnome-extensions show <uuid>`, `which <binary>`, `systemctl status <service>`). If none obvious, ask.
5. **Where it should appear on biohack.net/claude/** — which section (techops / design / personal / new section), and whether it should be featured.

Do not proceed until you have all five.

## What to create

Working directory is the root of the `biohack-claude` repo (i.e. the directory containing `plugins/` and `README.md`).

### 1. Plugin directory

```
plugins/<name>/
  .claude-plugin/plugin.json
  commands/<name>.md
```

**`plugin.json`:**
```json
{
  "name": "<name>",
  "description": "<one-sentence description>. Self-removes after install.",
  "author": {
    "name": "Will Norris",
    "url": "https://biohack.net"
  }
}
```

**`commands/<name>.md`** — follow this template exactly, substituting the real steps:

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

2. <step 2 description>:
   ```
   <bash command>
   ```

[... remaining steps ...]

N. Verify the install succeeded:
   ```
   <verification command>
   ```
   Report the output to the user. If it shows an error, stop and report — do not proceed to removal.

N+1. Self-remove this one-shot installer:
   ```
   /plugin uninstall <name>@biohack-claude
   ```

Tell the user what was installed and that the installer has been removed.
```

Rules for the command file:
- Every bash block must be a fenced code block on its own numbered step — no inline commands
- The verify step must come before the self-remove step, always
- If self-removal might fail silently, tell the user to run `/plugin uninstall <name>@biohack-claude` manually if the command persists

### 2. README.md entry

Add a row to the appropriate table in `README.md`:

```markdown
| [`<name>`](plugins/<name>/) | One-shot installer for <what>. Self-removes after install. |
```

Place it in the section that matches where it will appear on biohack.net/claude/.

### 3. biohack.net/claude/ page

Edit `../biohack.net/src/pages/claude.astro`. Add a card in the correct section:

```html
<div class="plugin">
  <p class="plugin-name"><name></p>
  <p class="plugin-desc"><one-sentence description>. Self-removes after install.</p>
  <pre>/plugin install <name>@biohack-claude</pre>
</div>
```

If the user said "featured", use `<div class="plugin featured">` and add `<span class="featured-flag">Featured</span>` before the name.

### 4. Commit and publish

Stage and commit in `biohack-claude`:
```
git add plugins/<name>/ README.md
git commit -m "feat(<name>): add one-shot installer for <what>"
git push origin main
```

Then in `biohack.net`:
```
git add src/pages/claude.astro
git commit -m "feat(claude): add <name> installer to /claude/ page"
task bump
```

## Invariants

- Plugin name must start with `install-` — it signals one-shot intent to users browsing the marketplace
- The verify step is non-negotiable — never self-remove without confirming success first
- `allowed-tools: Bash` is the only tool a pure installer needs; don't add others unless the install requires file edits
- The self-removal line is always the very last action — nothing after it
- Keep `plugin.json` description under 120 chars
