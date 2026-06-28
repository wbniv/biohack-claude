---
name: feedback_always_astro_tailwind
applies-to: [web]
description: "Always scaffold Astro + Tailwind 4 + @theme palette tokens, even when design is undecided"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5fcd0ba-2cf5-4281-a94f-d8ef04da3279
---

Always use Astro + Tailwind 4 + `@theme` palette token scaffold as the minimum baseline for any new site, regardless of whether the design is decided.

**Why:** "I don't know what it looks like" ≠ skip the framework. The scaffolding is always the same; the design (colors, fonts, layout) gets layered on later. Starting with plain HTML means migrating to Astro later, which is pure churn.

**How to apply:**
- Never propose plain HTML as the starting point for a new site.
- The distinction between Path 1 and Path 2 in the cf-static-site skill is about *infra* (Workers+Terraform vs Pages-only), not about frontend framework.
- Both paths get: Astro, Tailwind 4 via `@tailwindcss/vite`, `@theme` block in `global.css` defining semantic names (`--color-fg`, `--color-bg`, `--color-accent`, etc.).
- Every CSS rule references these tokens — no hardcoded hex values inline, ever.
- If design is undecided: use neutral/greyscale values as placeholders and leave a `TODO: brand colors` comment. The token names stay stable; only the values change when the design arrives.
