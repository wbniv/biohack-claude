---
name: mvp branch is just as much production as main — port operational changes
description: mvp.splitledger.rapid-raccoon.com is a live production deployment alongside main. Port infra/CI/monitoring/deployment changes; never port UI/app/product code.
type: feedback
originSessionId: 7d73bad1-7ea7-4c96-a00e-df4732577a1f
---
mvp branch is a parallel production environment. Both `main` and `mvp` are deployed to production (`splitledger.rapid-raccoon.com` and `mvp.splitledger.rapid-raccoon.com` respectively). Both must continue to deploy successfully and stay reachable.

When shipping a commit on main, classify it before considering whether mvp needs it:

- **Port to mvp**: infrastructure (TF, IAM, OIDC trust policies, Cloudflare config), CI/CD workflows (`.github/workflows/*`), deployment scripts (`scripts/lightsail-*.sh`, `scripts/rotate-*.sh`, `scripts/secrets-*.sh`), Caddyfile + cloud-init (when mvp has its own copy), monitoring/observability hooks, secret rotations, repo-config (Dependabot, branch protection).
- **Do NOT port to mvp**: anything under `mobile/` or `backend/splitledger_server/` (UI / business logic / API code), feature work, refactors of product code, doc-only changes about product features.

**Why:** user stated this directly 2026-05-09 after the `sl-github-actions-ci` IAM-role retirement (IH3, 2026-04-30) silently broke mvp deploys for 9 days because the operational change wasn't ported. The break was invisible until someone tried to deploy mvp; mvp's runtime kept serving stale code in the meantime.

**How to apply:**
- After committing any infra/CI/deployment change on main, immediately consider whether mvp's tree needs the same change. Common shape: cherry-pick the commit onto mvp, or directly copy the file (`git checkout origin/main -- <path>` from the mvp branch).
- Verify via `gh workflow run frontend-release-mvp.yml --ref mvp` after the port — confirms mvp deploys still work end-to-end.
- mvp's tree of `infrastructure/aws-lightsail/*.tf` and `scripts/*.sh` is mostly **decorative** at runtime — TF is applied from main against shared AWS state, and operators usually run scripts from main. So porting these isn't load-bearing day-to-day, but stale TF on mvp can confuse a future operator who tries to run `task tf-plan` from mvp's tree.
- The genuinely load-bearing mvp-tree files are: `.github/workflows/frontend-release-mvp.yml`, `mobile/`, `backend/splitledger_server/`, `infrastructure/docker/Dockerfile.server`. The first is operational (port). The rest are product code (don't port).
