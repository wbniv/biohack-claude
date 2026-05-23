---
name: project-cloudflare-credentials
description: "Cloudflare token and credential names actually used in this project — don't guess from script defaults"
metadata: 
  node_type: memory
  type: project
  originSessionId: 77903b99-6e8e-4648-89d3-0b96e59d78c3
---

Cloudflare tokens and R2 credentials for this project. These names came from bootstrap.sh instructions given to Will — record them here so future sessions don't second-guess what we told him to create.

**Why:** I instructed Will to create tokens with specific names but then failed to record those names, leading to circular "look for X or similar" prompts.

**How to apply:** Assert these names confidently in prompts and scripts. Update this file as new credentials are created.

## Important: Cloudflare token values are write-once
Cloudflare never shows a token value after initial creation. To get the value of an existing token you must **Roll** it (... → Roll), which invalidates the old value and issues a new one. Any scripts or secrets that stored the old value must be updated immediately after rolling.

## Cloudflare operator token
- **Name:** `foundry-linux-operator`
- **Permissions:** Account.API Tokens, Account.Cloudflare Pages +4
- **Stored in:** r2://foundry-secrets/CF_API_TOKEN and /tmp/foundry-bootstrap.env (local cache)
- **To use:** Roll it → copy new value → paste into bootstrap script → cache + r2 auto-updated

## R2 CI tokens
- **foundry-apt-ci** — shows "No permissions" in dashboard (may need investigation); secrets in foundry-linux/foundry-apt
- **foundry-iso-ci** — to be created during bootstrap-r2.sh, Object Read & Write on `foundry-iso` bucket

## Other tokens visible in dashboard
- `foundrylinux-site-ci` — Account.Cloudflare Pages (site deploy CI)
- `apt.indri.studio` — Account.Workers R2 Storage, Zone.Transform Rules (unrelated project)

## GitHub Actions secrets
- foundry-linux/foundry-apt: GPG_PRIVATE_KEY, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT
- foundry-linux/foundry-iso: GPG_PRIVATE_KEY, R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT (set by bootstrap-r2.sh)
