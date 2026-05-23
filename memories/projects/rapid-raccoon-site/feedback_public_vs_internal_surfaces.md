---
name: feedback-public-vs-internal-surfaces
description: "Public marketing pages (homepage, colophon, about) describe the visible artifact — never internal infrastructure (repo URLs, project predecessors, deploy pipeline, IaC paths)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9fad4a04-f48e-41a5-9d79-f8da7e3da752
---

When drafting copy for public-facing pages, keep internal/infrastructure details out. Audit for and cut: repo URLs, predecessor-project references, deploy pipeline specifics, SSM/IaC paths, the names of internal companion projects (e.g. "finding-your-way's infrastructure pattern"), and "where the source code lives" links. The colophon is the obvious trap — a colophon describes the *visible craft* (type, palette, stack at a high level), not the development infrastructure.

**Why:** On the indri.studio colophon plan, Will cut two sections in a row for this reason:

1. A "Predecessors and patterns" block (mentioned rapid-raccoon.com as the prior site and finding-your-way as the infrastructure pattern source). Will: *"yeah, not"* — inside-baseball, leaks internal project structure onto a public page.
2. A SOURCE section (repo URL, plans path, deploy pipeline note). Will: *"do you know why?"* — testing whether I understood. Same logic: repos for a marketing site are typically private, and a colophon's job is craft on display, not pointing at the source tree.

**How to apply:** Before any public-page content lands, scan it for: (a) names of other internal projects, (b) repo/source links, (c) deployment/CI mechanics — including tag patterns and build commands like `wrangler deploy`, (d) IaC or secret-storage paths — including project-root prefixes like `/indri-studio/` in SSM, (e) migration history that names the prior brand. If it's there, cut or generalize. Mention stack at a category level ("Cloudflare Workers", "Astro 6", "AWS SSM Parameter Store", "GitHub Actions") not at an operational level ("`/indri-studio/cloudflare/api_token` in SSM", "`v*` tags trigger `wrangler deploy`").

**Reinforce: audit existing drafts when the rule is fresh.** On the colophon plan I wrote the rule down as a memory after Will cut two leaks (predecessors, SOURCE) — then immediately failed to scan the rest of the THE STACK list against the same rule. Will had to point out two more leaks (SSM path suffix, GitHub Actions tag-pattern parenthetical) one entry at a time. Writing the rule down isn't application; **when a new rule is identified mid-task, retroactively scan the existing draft for the same pattern before declaring it done**. Note: this is distinct from the visual-fingerprint concern in [[feedback-seed-dont-clone]] — that one is about *aesthetic* leakage between sister sites; this one is about *infrastructure* leakage onto a public surface.
