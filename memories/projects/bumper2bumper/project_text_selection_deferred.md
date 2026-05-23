---
name: Text-selection on Flutter Web — re-deferred even after gate met
description: Phase A is technically ready (3 attempts, last reverted before manual checklist) but user has explicitly re-deferred this in multiple sessions including 2026-05-08 with gate met. Don't proactively recommend.
type: project
originSessionId: 0a025489-aaa9-4897-a2c0-be7262406292
---
**2026-05-08 update:** the "redesign-completion" gate that originally parked this work has been met since 2026-04-26 (per the 2026-05-07 audit refresh). Despite that, the user explicitly re-deferred 5.1 on 2026-05-08 when offered as a next-pickup candidate ("STILL deferred"). Treat as durable: don't suggest it as a "next thing to ship" when surveying open work; only act on explicit user prompt.

Three attempts, all reverted. Code is clean on main. The plan at `docs/plans/text-selection-flutter-web.md` is fully up to date.

**Attempt 1** (commit `302acee` → reverted `b36a3df`): `MaterialApp.router` `builder:` wrap. Red-screen: no Overlay ancestor.

**Attempt 2** (working-tree only, reverted): per-shell wrap in `app.dart`. Rendered but Activity/Balances flooded with 30+ hit-test errors per frame.

**Attempt 3** (2026-04-27, reverted before manual checklist): Phase A staged rollout — `SelectionArea(child: ...)` on `body:` of 10 static-text pages. Analyze clean, 129/129 tests pass, selection confirmed working on Settings in browser. Zero measurable load-time impact. Reverted before running the manual checklist.

**Why:** User wanted the work recorded and the tree clean; pickup requires manual checklist first.

**How to apply when re-attempting:** The plan "Phase A implementation" section lists the exact 10 files and the one-line change per file (`body: SelectionArea(child: ...)` / `body: SelectionArea(child: BlocConsumer...`). Do NOT wrap at `MaterialApp.router` `builder:` (Attempt 1 failure). Do NOT wrap in `app.dart` shell builders (Attempt 2 failure). Per-page `body:` wrapping only, static-text pages first.

**Next pickup steps:**
1. Re-apply Phase A (10 files from plan)
2. Run 11-item manual checklist (Settings + login + onboarding)
3. If clean → commit
4. Run `task test-boot-cleanliness` on `/` before starting Phase B (main tabs)
