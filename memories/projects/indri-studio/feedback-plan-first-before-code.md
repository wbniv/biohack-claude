---
name: feedback-plan-first-before-code
description: "Write the plan to docs/plans/ BEFORE touching code, even if the user seems impatient — a verbal-only plan disappeared in a computer crash"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 89f01913-20df-47da-bc08-7ecf1dc2531c
---

Always write the plan to `docs/plans/YYYY-MM-DD-<topic>.md` BEFORE writing any code (TF, Astro, scripts, etc.), even when the user seems impatient or in a hurry to "just do it."

**Why:** 2026-05-13 incident — Will and a previous Claude session designed the Cloudflare Email Routing setup for `hello@indri.studio` entirely over chat. The plan was never written to `docs/plans/`. The computer then crashed before any code was committed. The next session found nothing recoverable — no plan file, no branch, no stash, no commits, no TODO entry. The whole conversation had to be re-created from scratch. This is exactly the loss the project's CLAUDE.md plan-first convention exists to prevent: "The plan is the contract; code follows it."

**How to apply:** For any non-trivial change (new feature, infra resource, multi-file edit), the FIRST artifact landed is the plan file at `docs/plans/YYYY-MM-DD-<topic>.md`. Not chat-only, not just the harness's `~/.claude/plans/`. The project `docs/plans/` location is the durable, repo-tracked location. Add a `TODO.md` entry pointing to it in the same step. Only then write code. If the user pushes back ("just do it"), do the plan first anyway — it takes 90 seconds and survives any crash.

Related: [[feedback-commit-at-confirmation]].
