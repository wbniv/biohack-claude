---
name: WF camera system design history
description: The WF camera system grew powerful because the designer kept changing which game he was making — forced progressive generalization
type: project
originSessionId: eb231410-0aea-40fe-ae32-0051d1fe1e55
---
The WF camera system became powerful "in self defense" — the designer kept pivoting between games, and each pivot required a new axis of freedom. The result is the CamShot per-axis Absolute/Relative locking mechanism that can express every camera mode in the catalog without new code per game.

**Why:** Non-obvious design history; won't be in the code.

**How to apply:** When discussing camera work in any game brief, note that the underlying system already exists — what's "new" per brief is a CamShot configuration, not new engine code. Documented in `wf-games/investigations/2026-04-30-camera-system-overview.md`.
