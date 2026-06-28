---
name: wayland-keybinding-architecture
applies-to: [desktop]
description: How Ctrl+Shift+Left/Right tab switching works across Chrome, WezTerm, and Ptyxis on GNOME Wayland
type: feedback
---

GNOME custom keybindings intercept ALL apps (XWayland and Wayland-native). The key is consumed before apps see it. For Wayland apps, ydotool sends synthetic keys via /dev/uinput but CANNOT clear physically-held modifiers — Mutter combines modifier state across all keyboards. So ydotool's Ctrl+PageDown arrives as Ctrl+Shift+PageDown when user holds Shift. Both WezTerm and Ptyxis are configured to switch tabs on Ctrl+Shift+PageDown to work around this.

**Why:** Spent significant time discovering this through trial and error. xdotool --clearmodifiers works for XWayland but nothing equivalent exists for Wayland.

**How to apply:** When adding keybinding remaps involving modifier keys on Wayland, account for physically-held modifiers combining with synthetic events.
