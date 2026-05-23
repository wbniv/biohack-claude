---
name: Use task feature-start for all non-trivial work
description: From the next non-trivial task forward, start every feature in an isolated git worktree via task feature-start instead of editing plans/ directly on main
type: feedback
originSessionId: 5f0fa48e-a358-411e-9828-28df4d9bf0e6
---
For any non-trivial task in `parking-space`, **start by running `task feature-start NAME=<slug>` from the main checkout**. Do not create plan files directly in `plans/` and do not work on `main`.

**Why:** The legacy flow used a `PostToolUse` `Write` hook that auto-created `plan/<date>-<slug>` branches in the shared checkout — silent branch switching, no source isolation, features colliding on `.env` and generated dirs. The hook was deleted on 2026-04-10 and replaced with explicit `task feature-start` + git worktrees under `.worktrees/<date>-<slug>/`. The new flow only works if I actually use it. The user explicitly reminded me of this after building it: *"YOU are the one that's going to have to start following the feature workflow, you know that, right?"*

**How to apply:**
1. From `main` (no uncommitted changes): `task feature-start NAME=<slug>`. This commits a plan skeleton + TODO entry on `main` and creates the worktree.
2. `cd .worktrees/<date>-<slug>` and do all coding there. Open new Claude Code sessions in that directory if needed.
3. Only one worktree at a time can run `task dev` (postgres/redis/backend ports are fixed). To switch active dev: `task dev-stop`, then `task dev` in the new worktree.
4. When done: `task feature-finish` from inside the worktree — handles merge / push PR / keep / discard and tears down the dev stack if owned.

**Exceptions** (where staying on `main` is fine):
- Trivial fixes (typo, single-line edit, status check).
- Work that's already in progress on `main` when this rule was introduced — finish it where it is, then start using the flow on the next task.
- Read-only investigation.

**Reference:** [docs/feature-workflow.md](../../../SRC/parking-space/docs/feature-workflow.md), [plans/2026-04-10-feature-worktree-flow.md](../../../SRC/parking-space/plans/2026-04-10-feature-worktree-flow.md).
