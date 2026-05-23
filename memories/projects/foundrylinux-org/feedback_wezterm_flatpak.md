---
name: wezterm-flatpak-cli
description: How to interact with WezTerm Flatpak GUI tabs from outside the sandbox
type: feedback
---

WezTerm Flatpak CLI access requires `flatpak enter <instance>`, not `flatpak run --command=wezterm` (which creates a new sandbox that can't connect). Must connect to the GUI socket (`gui-sock-*`), not the mux socket (`sock`) — only the GUI socket sees actual GUI tabs.

**Why:** `flatpak run` spawns a new sandbox. `wezterm cli list` via mux socket shows 1 tab per window; GUI socket shows all tabs.

**How to apply:** When scripting WezTerm tab operations (workspace launcher, tab switching), always use `flatpak enter` + `WEZTERM_UNIX_SOCKET=<gui-sock>`.
