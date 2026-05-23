---
name: Fix forward, not in place — live box is the test bench, scripts are the source of truth
description: SSH-fixing the live box is the fast feedback loop; once validated, land the fix in the source script (or recognize it's not a code fix at all)
type: feedback
originSessionId: 9f7defe2-be07-4d44-89ad-5b20f0ccd5b2
---
SSH into the broken instance and test the fix directly on the live box — iterating against real state is 100× faster feedback than cycling a replacement. Once validated, land the fix in the source: [cloud-init.sh](https://github.com/wbniv/splitledger/blob/main/infrastructure/aws-lightsail/cloud-init.sh), [Caddyfile](https://github.com/wbniv/splitledger/blob/main/infrastructure/aws-lightsail/Caddyfile), `*.tf`, or whatever script owns that configuration. The live box is the test bench; the scripts are the source of truth. Cycle or redeploy afterward to confirm the fix flows through cleanly end-to-end.

**But "fix" doesn't always mean code.** If the problem is stale data or a legacy artifact that won't recur, clean it up and move on. Don't add defensive code for one-off issues.

**Why:** If a manual patch goes onto the box but never into source, the next instance recreate (terraform apply touching user_data, snapshot bake, instance recreate after corruption) silently undoes it. Source is what reproduces. But the inverse mistake is also bad: don't refuse to SSH-fix on the grounds of "fix forward" purity — that just trades fast iteration for slow cycle-and-pray.

**How to apply:**
- Default to SSH-iterate when something is broken on the live box. That's the test bench.
- After the live fix works, write the source change immediately — same turn as the SSH session, not "later."
- A "manual fix on live box" recommendation IS legitimate when the source change has already shipped (or will ship in the same turn). The manual application is convergence, not a substitute for the source change.
- For changes whose verification path requires a box recreate that destroys data (e.g. cloud-init bootstrap changes when there's no off-host DB backup), the SSH application IS the only practical path — the source change waits to be verified end-to-end until the prerequisite (e.g. off-host backup) lands.
- Before deciding it's a "fix," ask whether the problem will recur. Stale data, one-off corruption, a legacy file from a deprecated path → just clean it up; no code change needed.

**Origin:** 2026-04-30 conversation about IH5 passwords.yaml chmod 640. Cloud-init.sh was already patched (a7882d6). I first offered a "manual fix on live box" command (correct), then over-corrected to "never SSH-fix, always cycle" (wrong), then user clarified twice: SSH-fixing IS the right primary path; the rule is just that the validated fix must also land in source (when there is one).
