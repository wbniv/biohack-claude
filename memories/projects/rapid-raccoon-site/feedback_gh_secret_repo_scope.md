---
name: Always pass -R to gh secret set
description: User has multiple repo clones in parallel; gh commands default to the current dir's repo and secrets have silently landed on the wrong repo
type: feedback
originSessionId: 3a2c7a5b-1164-4180-b510-acc729b9a71e
---
When directing the user to set GitHub repository secrets (or variables, or any other repo-scoped `gh` command), pass `-R <owner>/<repo>` explicitly rather than relying on the current working directory.

Example: `gh secret set -R wbniv/rapid-raccoon-site CLOUDFLARE_API_TOKEN` — not just `gh secret set CLOUDFLARE_API_TOKEN`.

**Why:** On 2026-04-24, we spent real time debugging a "missing CLOUDFLARE_API_TOKEN" deploy failure that traced back to `gh secret set` being run from a different repo clone (`parking-space`) — the secret landed there and `rapid-raccoon-site` had no secrets at all. Cloudflare API tokens are revealed once at creation, so the lost value also meant rolling a fresh token. Painful loop.

**How to apply:** For any `gh secret set` / `gh secret list` / `gh variable set` / `gh run rerun` / etc. in instructions to the user, always include `-R <owner>/<repo>`. Same goes when demonstrating in scripts or docs. This is cheap insurance against multi-checkout footguns — the user keeps several repos open simultaneously.
