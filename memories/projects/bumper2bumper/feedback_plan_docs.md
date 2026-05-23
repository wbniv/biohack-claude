---
name: Save plans to docs/plans, investigations to docs/investigations
description: User wants every plan written to a durable file in the repo, not just the ephemeral plan-mode scratch file
type: feedback
originSessionId: cdfc8cd0-590a-442d-90a0-d695bda66511
---
When you write a plan in plan mode, also save a copy to `docs/plans/YYYY-MM-DD-<kebab-topic>.md` in this repo (or `docs/investigations/YYYY-MM-DD-<topic>.md` for read-only research outputs). The ephemeral plan file at `~/.claude/plans/...` is fine for plan-mode workflow but the user wants durable, committable plan docs by default — they've had to ask three+ times.

**Why:** The user has explicitly redirected at least three times (AWS deployment plan → `docs/investigations/`; balances sort toggle plan → `docs/plans/`; B11 plan 2026-05-05 — "write plan to docs/plans/"). Each redirect interrupts implementation flow. Plans become reference material as features land; ephemeral plan files don't survive the session.

**How to apply:**
- For implementation plans (something will be built), write to `docs/plans/YYYY-MM-DD-<kebab-topic>.md`.
- For research / investigation outputs (no immediate code change), write to `docs/investigations/YYYY-MM-DD-<topic>.md`.
- Date prefix matches the existing convention (e.g. `2026-05-05-b3-import-validation.md`, `2026-05-05-b5-recurring-tick-race.md`).
- Still update the plan-mode scratch file too — plan mode requires it before `ExitPlanMode` — but treat the `docs/` copy as the primary deliverable. Write to docs/plans/ FIRST or in parallel; never rely on the user to ask for it.
- Keep the two in sync; if the user iterates on the plan, mirror updates to both.
