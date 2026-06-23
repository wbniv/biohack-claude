# statusline

A two-line [Claude Code](https://claude.ai/code) status line.

```
[work] ⏺ Opus ⏺ high ⏺ ~/SRC/biohack-claude (main) ±3 ↑1
ctx ▬▬▬─ 38% ⏺ 5h ▬▬▬▬ 73% ↺2h15m ⏺ 7d ▬─── 23% ⏺ $1.23
```

- **Line 1** — account (from `CLAUDE_CONFIG_DIR`) · model · effort (colour-coded) · `~`-collapsed cwd · git branch with dirty/ahead/behind counts.
- **Line 2** — context-window usage bar · 5-hour rate-limit bar with reset countdown · 7-day rate-limit bar · running session cost.

The script reads Claude Code's JSON status context from stdin and prints the two
lines. Requires [`jq`](https://jqlang.github.io/jq/) and `git`.

## Install

```
/plugin install statusline@biohack-claude
/install-statusline
```

`/install-statusline` is a one-shot command: it copies the script to a stable
path (`~/.local/bin/claude-status`), wires `statusLine` into your
`~/.claude/settings.json` (backing up the old one first), verifies the output,
then removes itself.

> A Claude Code plugin can't set the main `statusLine` on its own — that key is
> user-scoped — so the installer writes it into your settings for you.

## Manual install

If you'd rather not run the installer, copy
[`bin/claude-status`](bin/claude-status) anywhere stable and add this to
`~/.claude/settings.json` (or a project's `.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.local/bin/claude-status"
  }
}
```
