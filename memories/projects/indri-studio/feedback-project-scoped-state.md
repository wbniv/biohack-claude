---
name: feedback-project-scoped-state
description: "Per-project state (secrets bucket, bootstrap cache, CF token) must be project-scoped, NOT GH-org-scoped — one GH org often hosts multiple projects that must not collide"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d096a769-3247-49b9-ab32-b7940a4a978a
---

When bootstrapping infrastructure for a project, derive resource names from the *project identity* (zone slug, custom domain) — never from the GitHub org/owner.

**Why:** Will's `wbniv` GitHub org hosts multiple distinct projects (worldfoundry.org, indri.studio, biohack.net, …). Bootstrap defaults of the form `${GH_ORG}-secrets`, `/tmp/${GH_ORG}-bootstrap.env`, `${GH_ORG}-operator` would silently collide and merge state across unrelated projects. He explicitly called this out as "poor choices/defaults" on 2026-05-21 during the apt.indri.studio bootstrap.

**How to apply:**
- R2 secrets bucket: `<zone-slug>-secrets` (e.g. `indri-studio-secrets`, `biohack-net-secrets`)
- Bootstrap cache file: `/tmp/<zone-slug>-bootstrap.env`
- CF API token name: `<CUSTOM_DOMAIN>` (e.g. `apt.indri.studio`) — token name is a UI label, so make it self-explanatory in the dashboard
- IAM users, Terraform state buckets, SSM prefixes, etc.: same rule — derive from the project, not the org

The GH org name is fine for: GitHub org/owner (it IS the GH org), and that's it. Anything else should pull from `<zone-name>`, `<PKG_NAME>`, or `<CUSTOM_DOMAIN>`.

Patches applied 2026-05-21:
- `~/.claude/skills/new-web-apt-repo/SKILL.md` — derivation table updated for SECRETS_BUCKET, BOOTSTRAP_CACHE, CF_OPERATOR_TOKEN_NAME
- `~/SRC/indri.studio/scripts/bootstrap-apt.sh` — instance values switched from `wbniv-*` to `indri-studio-*` / `apt.indri.studio`

Related: [[project-apt-repos-on-cloudflare]] catalogues the existing + planned apt repos under wbniv.
