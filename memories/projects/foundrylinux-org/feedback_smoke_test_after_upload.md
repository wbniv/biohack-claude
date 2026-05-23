---
name: feedback-smoke-test-after-upload
description: "Always run smoke tests automatically after uploads — never ask, just do it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 880e268d-f572-4a85-9862-802108438961
---

After any upload (R2, Cloudflare, apt repo, etc.), immediately run verification without asking: curl the remote sha256/checksum, compare to local, verify the resource is reachable and the right size. This applies to everything — ISOs, packages, manifests, site deploys.

**Why:** Will expects verification to be automatic. Asking "should I verify?" wastes a round-trip and signals that the work isn't done.

**How to apply:** After `rclone copy`, `task iso-upload`, `task deploy`, or any upload command: immediately curl or fetch the uploaded artifact, compare checksums/sizes, and report PASS/FAIL inline. Only proceed to the next step on PASS.
