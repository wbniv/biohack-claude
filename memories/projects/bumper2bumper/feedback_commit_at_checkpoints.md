---
name: Commit at natural checkpoints — never ask permission
description: When work reaches a logical stopping point (verified phase, plan written, fix applied + tested), commit immediately without asking. Asking is the failure mode the user has explicitly flagged.
type: feedback
originSessionId: 586fada5-92b6-4cd2-b4ab-913e73feacaa
---
At any natural checkpoint — feature complete, fix verified, plan written, phase landed — commit immediately. **Do not** ask "want me to commit?" or "should I commit now?" or "should I bundle?". Just commit.

**Why:** [SRC CLAUDE.md](../../../CLAUDE.md) already says "Commit, merge, and push without asking at logical stopping points — don't gate routine git operations on user approval." The user has reinforced this explicitly: *"commit. always commit. why do you keep asking me? whenever you think it's worth asking me to commit, just bloody commit already"* (2026-05-10, after Phase 0 of the mvp-breakage detection plan landed end-to-end and I asked for permission to commit instead of committing).

The cost of asking is real: it interrupts flow, adds latency, treats the user as a permission-gate rather than a collaborator, and accumulates uncommitted state when work is at a perfectly committable point.

**How to apply:**
- After verifying a step works (apply succeeds, tests pass, smoke test passes) → stage your files, commit. No prompt.
- After writing a plan that the user explicitly asked for → stage + commit. No prompt.
- After a coherent unit of fix/refactor/feature work → stage + commit. No prompt.
- After moving a TODO item to done → stage + commit.
- Multiple checkpoints in one task = multiple commits. One natural unit of work = one commit. Don't accumulate.
- If the next user-visible message would be "want me to commit?", skip the message and just commit. Then report what happened in the closing summary.
- Pushing: try it. If the harness blocks (e.g. direct-push-to-main protection), state that the push was denied and continue — don't ask "should I push?" upfront.

**Exceptions (still need confirmation per the safety protocol):**
- Destructive ops: `git push --force`, `reset --hard`, `branch -D`, `checkout .` to discard uncommitted work.
- Committing files that look secret (`.env`, `credentials.json`, `*.pem`).
- Committing files clearly authored by another agent / programmer not in this session (per the "Only commit your work" rule).

Everything else: commit. Then say what happened.
