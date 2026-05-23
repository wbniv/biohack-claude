# gnome/ — GNOME Shell extensions

Claude-related GNOME Shell extensions. Catalogued in `extensions.json`.

| Extension | What it does | Repo |
|-----------|-------------|------|
| [Claude Usage Indicator](https://github.com/wbniv/claude-usage) | Shows Claude.ai weekly usage % in the top panel and dock | wbniv/claude-usage |

## Install

Clone the repo and symlink (or copy) the `gnome-extension/` directory into
`~/.local/share/gnome-shell/extensions/<uuid>/`, then enable via GNOME Extensions.

```bash
git clone https://github.com/wbniv/claude-usage
ln -s "$PWD/claude-usage/gnome-extension" \
  ~/.local/share/gnome-shell/extensions/claude-usage@indri.studio
gnome-extensions enable claude-usage@indri.studio
```
