---
name: Don't block waiting on remote ops; monitor and report progress
description: For long-running remote operations (deploys, terraform apply, instance boots, cert provisioning), don't block. Run in background and report periodic status to the user.
type: feedback
originSessionId: 5243d3ca-8596-41e8-9c68-081d7d9e34db
---
For long-running remote operations — Terraform applies, instance boots,
cloud-init bootstraps, cert provisioning, image pulls — don't block with
`sleep` or schedule a single wake-up far out and disappear.

Instead:
- Use `run_in_background: true` on the long-running command.
- Check the task's output file periodically (`tail` the
  `/tmp/claude-1000/.../tasks/<id>.output` path).
- Report progress to the user as it happens — what step is in progress, how
  long it's been, what the next milestone is.
- Use ScheduleWakeup only as a safety net for genuinely-idle waits (e.g.
  "check back in 5 min if no progress"), not as the primary monitoring loop.

**Why:** the user wants visibility into what's happening, not silence
followed by a single status dump. They flagged this directly after I kicked
off a Lightsail bootstrap with `run_in_background` then immediately scheduled
a wake-up 4 min out and stopped reporting.

**How to apply:** any time you start a remote operation that'll take >30s,
plan to check on it 1-2 times before the user expects a final answer. If
nothing's happening yet, say so. If it's progressed, say what step.
