---
name: feedback-tailwind-and-layer-base-double-declared
description: "Body (and other root-ish elements) get styled in TWO places — Tailwind utility class on the element + @layer base rule in global.css. Override one, the other still wins."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c9691632-dd52-4976-9d86-f2d6896494ba
---

When changing styles on `<body>` (or any element that's likely styled in both spots), check BOTH:

1. The Tailwind utility class on the element in the Astro layout (`src/layouts/Base.astro`). For body: line ~159, currently `<body class="min-h-screen flex flex-col text-on-surface font-body">`.
2. The matching `body {}` rule in `src/styles/global.css` `@layer base` block. Currently around line 180.

Same properties (`background-color`, `color`, `font-family`) are declared in both. Removing from only one leaves the other applying, and the visual change doesn't land. I made this exact mistake repeatedly in one session — first the Tailwind class, then later the CSS rule, then was confused why nothing changed.

**Why:** This double-declaration is a deliberate pattern in this codebase (and likely other Tailwind v4 + Astro projects). The Tailwind utility provides the editable-from-markup surface; the @layer base rule sets the same value as a CSS fallback / source of truth. They don't conflict because they set the same value, but they DO conflict during edits.

**How to apply:** Before saying "I removed X from body" or making any body-style change, grep both files in one shot:
```
grep -n "bg-surface\|<body" src/layouts/Base.astro
grep -n "body {" src/styles/global.css   # then read the rule
```
Confirm both are updated before declaring the change done. This pattern likely applies to `<html>` too (color-scheme + bg-color set both in markup and CSS).
