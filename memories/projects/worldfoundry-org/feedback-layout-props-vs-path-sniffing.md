---
name: layout-props-vs-path-sniffing
description: Prefer layout props over Astro.url.pathname checks for page-specific layout behavior
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 03884842-25e7-4e05-95a4-afd6612a96ad
---

Prefer passing props to the layout over checking `Astro.url.pathname` for page-specific layout variations.

**Why:** Path strings are brittle — they break silently on renames and scatter routing logic into the layout. A prop like `gallery` on `Base.astro` is explicit, typed, and declared at the page that owns the behavior.

**How to apply:** When a page needs to alter shared layout (hide a nav item, swap a link, change a section), add an optional boolean or enum prop to the layout and set it on that page's `<Base>` call. Reserve `Astro.url.pathname` for cases where the layout genuinely can't know ahead of time — e.g. marking the active nav item across many pages, or middleware-level redirects.
