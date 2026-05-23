---
name: Terraform state lock — diagnose before force-unlocking
description: Don't call a state lock "stale" without checking pgrep first; force-unlocking an active lock corrupts state
type: feedback
originSessionId: 4aba1971-a766-4b9d-a3e6-8391efd91660
---
Never call a Terraform state lock "stale" without first verifying no process is holding it.

**Why:** I made this mistake in conversation on 2026-04-19 — saw a `.terraform.tfstate.lock.info` file from "5 minutes ago" and proposed `terraform force-unlock` to the user, when in fact the lock was held by an actively-running `cobrand publish` doing real AWS infrastructure provisioning (ACM cert validation + CloudFront distribution — both legitimately take 5-15 minutes). Force-unlocking would have corrupted state mid-apply. The user caught it: "is it stale? or just in use?"

**How to apply:** Before suggesting `force-unlock` or `rm` of a `.tfstate.lock.info`:

1. `pgrep -af terraform` — is a terraform process actually running?
2. Check the lock's `Created` timestamp — anything under ~30 minutes is plausibly an active apply (ACM, CloudFront, RDS can run long)
3. `fuser <lockfile>` — does any process have the file open?
4. Read the `Who` field — if it's the current host/user, look harder for a matching process before assuming it crashed
5. If a fresh-looking lock has no matching process, it MAY be stale (e.g. crashed apply); ask the user before force-unlocking

The parking-space project keeps this same rule in its memory. Same wisdom belongs here.