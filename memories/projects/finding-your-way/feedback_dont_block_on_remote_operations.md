---
name: Don't block on remote operations — monitor and report
description: For deploys, Terraform applies, cert provisioning, instance boots, etc., don't block with sleep loops. Use run_in_background, ScheduleWakeup, or periodic checks; report status and move on.
type: feedback
originSessionId: 657be929-b48d-4bf9-9dec-2e15a61faf6e
---
When waiting for remote operations to complete (GitHub Actions deploys, `terraform apply`, AWS resource provisioning, cert issuance, instance boots, DNS propagation, etc.):

- **Do not** block with `sleep`, `while ... sleep`, or `until ... sleep` polling loops that tie up the conversation. The harness blocks long leading `sleep`s specifically to discourage this.
- **Do** use `run_in_background` on the Bash tool and let the runtime notify when the command finishes.
- **Do** use `ScheduleWakeup` for idle check-backs when waiting on something slower than a cache window (≥5 minutes) with no specific signal to watch.
- **Do** check status periodically — *report the current state to the user each time*, rather than silently looping. A "checking, still pending, will look again in 30s" beat keeps the user informed.
- If polling really is the right shape (e.g., a `gh run list` to check a deploy), keep the poll interval sensible: prefer `run_in_background` + a short until-loop inside, so the notification comes when the loop exits, OR use Monitor to stream process output line-by-line.

**Why:** blocking the conversation on a 3-minute deploy wastes the user's time and burns cache windows. Periodic visible progress is better than a silent wait followed by a result.

**How to apply:**
- GitHub Actions deploys → `run_in_background` the `gh run watch <id>` (it exits when the run completes); OR just kick it and come back with `gh run view <id>` later.
- `terraform apply` of something slow (CloudFront distribution changes, RDS snapshots) → background it, report intermediate state.
- Sleeping between iterations is fine *if* each iteration prints something and total wait is short; don't use sleep as "pause the conversation."
