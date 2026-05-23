---
description: Provision a new web-hosted signed APT repo on Cloudflare R2.
argument-hint: [gh-org/repo zone-name [subdomain [key-email]]]
---
Provision a new web-hosted signed APT repo on Cloudflare R2.

Usage: `/new-web-apt-repo [gh-org/repo zone-name [subdomain [key-email]]]`

Examples:
- `/new-web-apt-repo` — use existing config in bootstrap.sh (foundry-apt)
- `/new-web-apt-repo worldfoundry/wf-apt worldfoundry.org apt packages@worldfoundry.org`
