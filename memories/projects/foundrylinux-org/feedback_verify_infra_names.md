---
name: feedback-verify-infra-names
description: "Never assert infrastructure names (tokens, buckets, keys) from script defaults — only from Will's confirmation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 77903b99-6e8e-4648-89d3-0b96e59d78c3
---

When I give Will instructions to create a named credential (token, bucket, secret), record that name in memory immediately — don't wait to be asked.

**Why:** Instructed Will to create the `foundry-operator` Cloudflare token but didn't record it, then second-guessed the name later with "or similar." The name came from my own instructions — I should have been certain.

**How to apply:** Any time a script or instruction tells Will to name something, write it to project_cloudflare_credentials.md (or equivalent) in the same turn.
