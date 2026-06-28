---
name: feedback_node24_everywhere
applies-to: [web, app]
description: Always use Node 24 on all platforms that support it; maintain the confirmed-support list below
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5fcd0ba-2cf5-4281-a94f-d8ef04da3279
---

Always use Node 24 (not 22, not 20) on every platform that supports it.

**Why:** Node 20 is deprecated on GitHub Actions runners (forced to 24 by 2026-06-02, removed 2026-09-16). Use the latest everywhere for consistency.

**How to apply:** When writing or editing any CI/CD config, build script, or `.nvmrc`, default to 24. When discovering a new platform, verify Node 24 support and add it to the list below.

## Confirmed Node 24 support

| Platform | How to specify |
|----------|---------------|
| GitHub Actions | `node-version: '24'` in `actions/setup-node@v6` |
| Codemagic.io | Node 24 available |

## Update this list

When you confirm a new platform supports Node 24, add it to the table above.
