---
name: project-apt-repos-on-cloudflare
description: "Will runs multiple apt repos on his single Cloudflare account — current+planned list, naming convention, why state must be project-scoped"
metadata: 
  node_type: memory
  type: project
  originSessionId: d096a769-3247-49b9-ab32-b7940a4a978a
---

Will hosts multiple web-distributed apt repos under his single Cloudflare account and `wbniv` GitHub org. Resources MUST be scoped per-project (per-zone), not per-org.

**Current:**
- `apt.worldfoundry.org` — wbniv/worldfoundry.org monorepo, R2 bucket `worldfoundry-apt`
- `apt.indri.studio` — wbniv/indri.studio monorepo, R2 bucket `indri-apt`, secrets bucket `indri-studio-secrets`, operator token name `apt.indri.studio`, bootstrap cache `/tmp/indri-studio-bootstrap.env` (first package: claude-usage v0.11.20)

**Planned:**
- `apt.biohack.net` — not yet started; will reuse `new-web-apt-repo` skill

**Why:** the `new-web-apt-repo` skill originally defaulted `SECRETS_BUCKET=${GH_ORG}-secrets` and `BOOTSTRAP_CACHE=/tmp/${GH_ORG}-bootstrap.env` — which would collide across these repos. Skill updated 2026-05-21 to scope these off `<zone-slug>` (`indri-studio`, `biohack-net`) and use `<CUSTOM_DOMAIN>` for the CF operator token name. See [[feedback-project-scoped-state]] for the general principle.

**How to apply:** when bootstrapping a new apt repo for Will, never reuse another project's secrets bucket, bootstrap cache, or CF operator token. Each gets its own. The CF token name should be the apt subdomain (`apt.biohack.net`) for memorability in the dashboard.
