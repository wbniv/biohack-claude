---
name: feedback_task_bump
description: "Use 'task bump' to sync and release foundry-apt — no need to know/supply the next version number"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cacd9c0b-f1b9-49d4-893c-918d40599239
---

Use `task bump` to sync `foundry-apt/` to GitHub and tag a new release. It auto-increments the patch version (e.g. v0.0.4 → v0.0.5) — no TAG variable needed.

**Why:** User corrected after I used `task release TAG=v0.0.5` manually.

**How to apply:** For any foundry-apt release in this repo, reach for `task bump` first. Only use `task release TAG=vX.Y.Z` when intentionally targeting a specific version (minor/major bump, rollback, etc.).
