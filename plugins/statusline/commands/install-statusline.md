---
description: Install the two-line status line into your Claude Code settings, then remove this command.
allowed-tools: Bash
---

Install the `statusline` status line by running these steps in order. If any step
fails, stop and report the error to the user rather than continuing.

1. Locate the bundled script and copy it to a stable, update-proof path
   (`~/.local/bin/claude-status`). The plugin's own directory is versioned and
   changes on every update, so we copy out of it rather than point at it:
   ```bash
   set -euo pipefail
   SRC="${CLAUDE_PLUGIN_ROOT:-}/bin/claude-status"
   if [ ! -f "$SRC" ]; then
     SRC=$(find "$HOME/.claude/plugins" -path '*statusline*/bin/claude-status' -type f 2>/dev/null | head -n1 || true)
   fi
   [ -n "$SRC" ] && [ -f "$SRC" ] || { echo "could not locate the bundled claude-status script" >&2; exit 1; }
   mkdir -p "$HOME/.local/bin"
   install -m 0755 "$SRC" "$HOME/.local/bin/claude-status"
   echo "installed -> $HOME/.local/bin/claude-status"
   ```

2. Confirm `jq` is available — both the status script and this installer need it:
   ```bash
   command -v jq >/dev/null || { echo "jq is required (e.g. sudo apt install jq)"; exit 1; }
   ```

3. Wire it into your user settings (`~/.claude/settings.json`), backing up first.
   We write an **absolute** path so a future plugin update can never break it:
   ```bash
   set -euo pipefail
   SETTINGS="$HOME/.claude/settings.json"
   mkdir -p "$HOME/.claude"
   [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
   cp "$SETTINGS" "$SETTINGS.bak.$(date -u +%Y%m%dT%H%M%SZ)"
   tmp=$(mktemp)
   jq --arg cmd "bash $HOME/.local/bin/claude-status" \
      '.statusLine = {type: "command", command: $cmd}' "$SETTINGS" > "$tmp"
   mv "$tmp" "$SETTINGS"
   echo "statusLine set in $SETTINGS"
   ```

4. Verify it renders by feeding the script a sample context object:
   ```bash
   echo '{"model":{"display_name":"Opus"},"workspace":{"current_dir":"'"$HOME"'"},"effort":{"level":"high"},"context_window":{"used_percentage":38},"rate_limits":{"five_hour":{"used_percentage":73},"seven_day":{"used_percentage":23}},"cost":{"total_cost_usd":1.23}}' | bash "$HOME/.local/bin/claude-status"; echo
   ```
   Show the two-line output to the user. It takes effect on the next assistant
   message (the status line refreshes per turn).

5. Self-remove this one-shot installer:
   ```
   /plugin uninstall statusline@biohack-claude
   ```

Tell the user the status line is live, that the script was installed to
`~/.local/bin/claude-status`, that their previous settings were backed up to
`~/.claude/settings.json.bak.*`, and that this installer has removed itself.
