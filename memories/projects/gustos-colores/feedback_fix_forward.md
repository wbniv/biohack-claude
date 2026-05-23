---
name: Fix forward, not in place
description: When debugging a broken instance/deploy, SSH in to diagnose — but the fix must land in the source scripts/templates, then cycle the instance to verify the fix flows through
type: feedback
originSessionId: 75408592-77b2-4e64-a6f5-927a07f6de19
---
**Rule.** When debugging a broken instance (user-data failures, misconfigs, etc.), SSH in to diagnose and test fixes interactively. But the fix must land in the source scripts/templates (`deploy.sh`, `user-data.sh`, `Caddyfile.tpl`, terraform modules, etc.) — not just on the instance. The instance is a scratchpad; the scripts are the source of truth. After fixing the scripts, cycle the instance (terminate + ASG replace, or redeploy) to verify the fix flows through cleanly.

**Why:** Patching a live instance "just to get it working" leaves the source broken — the next deploy or ASG replacement recreates the bug, often at the worst time. Verifying the cycle-through is the only way to know the fix is durable.

**How to apply:**
- Diagnose on the instance; prototype the fix there if helpful.
- Then port the fix back to the source script/template/module.
- Trigger a full cycle (terminate + redeploy, or `terraform apply` that recreates the resource) and confirm the fresh instance comes up healthy.
- Applies to any infrastructure fix, not just EC2 — terraform modules, Dockerfiles, user-data, init scripts, CI config, etc.
