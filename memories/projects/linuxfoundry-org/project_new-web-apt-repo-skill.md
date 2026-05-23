---
name: new-web-apt-repo-skill-reuse
description: /new-web-apt-repo skill is intended to be reused for WorldFoundry repo APT setup
metadata: 
  node_type: memory
  type: project
  originSessionId: 3fb17b3e-1052-44aa-aee2-528de0dcd50d
---

The `/new-web-apt-repo` skill (`.claude/commands/new-web-apt-repo.md`) was designed to be
generic — not just for `foundry-apt`. The user plans to reuse it when setting up an APT repo
for the WorldFoundry repo (wbniv org).

**Why:** Avoid duplicating the bootstrap process; one skill covers any new web-hosted APT repo.

**How to apply:** Before running the skill for WorldFoundry, review `scripts/bootstrap.sh` config
vars at the top (GH_ORG, PKG_NAME, KEY_EMAIL, R2_BUCKET, CUSTOM_DOMAIN) — they'll need to be
parameterized or the script will need a WorldFoundry-specific variant.
