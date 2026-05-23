---
description: Install the Claude Usage Indicator GNOME extension, then remove this command.
allowed-tools: Bash
---

Install the Claude Usage Indicator GNOME extension by running these steps in order:

1. Create `~/src/` if it doesn't exist:
   ```
   mkdir -p ~/src
   ```

2. Clone the repo (skip if `~/src/claude-usage` already exists):
   ```
   git clone https://github.com/wbniv/claude-usage ~/src/claude-usage
   ```

3. Create the extensions directory if needed and symlink the extension:
   ```
   mkdir -p ~/.local/share/gnome-shell/extensions
   ln -sf ~/src/claude-usage/gnome-extension ~/.local/share/gnome-shell/extensions/claude-usage@indri.studio
   ```

4. Enable the extension:
   ```
   gnome-extensions enable claude-usage@indri.studio
   ```

5. Confirm success by running:
   ```
   gnome-extensions show claude-usage@indri.studio
   ```
   Report the State field to the user.

6. Self-remove this one-shot installer:
   ```
   /plugin uninstall install-gnome-usage@biohack-claude
   ```

Tell the user the extension is live and that the installer has been removed.
