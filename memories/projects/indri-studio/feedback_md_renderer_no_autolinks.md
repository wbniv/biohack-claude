---
name: feedback-md-renderer-no-autolinks
description: "Always link external references in markdown — products, libraries, frameworks, fonts, websites, people, places. Bare names are a recurring blind spot. Use `[label](url)` form, never `<url>` shorthand (md-to-pdf.sh silently drops it)."
metadata:
  node_type: memory
  type: feedback
  originSessionId: a2f3a3df-e9b7-4d7d-8c72-4da26442c032
---

# The rule

**Every URL or external reference in a markdown file gets a real link.** This is broader than "third-party products" — it includes:

- Products, libraries, frameworks, fonts, design systems, tools (Astro, Tailwind, Space Grotesk, Inter, GitHub Actions)
- Third-party websites, blog posts, docs (MDN, Wikipedia, clerk.com, hoox archive)
- People, foundries, organizations (Florian Karsten, Rasmus Andersson, Google Design)
- **Local dev URLs** (`localhost:4321` in a verification step)
- **Production URLs** (the actual deployed site you're verifying)
- Specific deep URLs (the apex vs www, a specific route, a doc anchor)

If it's a URL, link it. If it's a name that maps to a URL, link it with that URL. **Bare names or URLs in plain text are a defect.**

Use **`[label](url)`** form. Never use **`<https://…>`** shorthand: the shared `~/SRC/python-tui-lib/scripts/md-to-pdf.sh` regex (`re.sub(r'\[([^\]]+)\]\(([^)]+)\)', ...)`) has no rule for angle-bracket autolinks and silently drops them, leaving a blank where the URL should be. Even when the URL is the label (e.g. `clerk.com` linking to `https://clerk.com` or `localhost:4321/colophon` linking to `http://localhost:4321/colophon`), still write it as `[label](url)`.

# Why this gets its own loud memory

This is a **recurring blind spot** Will has called out repeatedly:

- The original `<url>` autolinks failure (twice in indri.studio, flagged session `a2f3a3df`).
- Inert product names in the colophon-route plan (2026-05-13): wrote `Astro 6`, `Tailwind CSS v4`, `Cloudflare Workers`, `Terraform`, `AWS SSM`, `GitHub Actions`, `pnpm`, `Space Grotesk`, `Inter`, `Material Symbols Outlined`, `Hoox`, `clerk.com`, `droneland.au` — every single one a bare name pointing at a real external thing, none linked. Will: *"this really is a blind spot for you. i do have to remind you to do it all the fucking time."*
- **Same plan, verification section** (2026-05-13, same day, after rewriting this memory): `localhost:4321` and `localhost:4321/colophon` in code-backticks rather than as links; no production URL mentioned at all. Will: *"it's funny that you don't have a link to the prod url in verification."* I had narrowed the rule in my head to "third-party products"; it applies equally to dev URLs and production URLs.

Each failure is a different surface (paragraph autolinks → list of products → references → docs → local dev/prod URLs), but the underlying mistake is identical: I treat anything-that-could-be-a-link as plain text instead of as a link.

# How to apply

**Default behavior before any markdown lands:** scan the diff for proper nouns / capitalized names / bare hostnames that refer to external things. If a noun refers to an external product, library, font, framework, person, blog, website, or service that has a canonical URL — link it. Even if the URL feels obvious. Even if it appears multiple times. The reader should be able to *click* every external reference.

Examples — left side wrong, right side right:

- `Astro 6 — static site generation` → `[Astro 6](https://astro.build) — static site generation`
- `Tailwind CSS v4` → `[Tailwind CSS v4](https://tailwindcss.com)`
- `Space Grotesk` → `[Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk)`
- `clerk.com` → `[clerk.com](https://clerk.com)`
- `Built with Hoox` → `Built with [Hoox](https://hoox-archive-or-similar.example)`
- `Open <https://example.com/docs>` → `Open [example.com/docs](https://example.com/docs)`

**Audit step**: before declaring a markdown file done, grep mentally (or actually) for the names of external products/sites in it. If any appear without surrounding `[…](…)`, that's a bug.

Related: [[feedback-run-task-md]] (the workflow rule that triggers the render), [[feedback-public-vs-internal-surfaces]] (don't include *internal* references at all — but the external ones that *do* belong must be linked).
