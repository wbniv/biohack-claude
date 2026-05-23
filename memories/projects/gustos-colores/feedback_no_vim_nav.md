---
name: No j/k as arrow-key alternatives
description: In TUIs, don't add vim-style j/k navigation alongside arrow keys
type: feedback
originSessionId: 12f73360-41c5-4c96-b172-19b8b7760c8a
---
In TUIs (e.g. `cobrands/tui.py`), do NOT support `j`/`k` as alternatives
to `↓`/`↑` for navigation. Arrow keys only.

**Why:** User explicitly rejected vim-nav when auditing the help dialog —
"i have no interest in supporting j/k for arrow keys". Leaves `j`/`k`
free for semantic bindings (e.g. Brainstorm's `k` = keywords modal).

**How to apply:** When adding list-nav to a new tab/modal/picker, wire
only `curses.KEY_UP` / `curses.KEY_DOWN`. Don't write
`if ch in (curses.KEY_UP, ord('k'))`. Also don't document `j`/`k`
in the help dialog as nav keys.
