---
name: Announce plan-mode file path for browser review
description: User reviews plans in a markdown browser before approving — always surface the plan file path proactively
type: feedback
originSessionId: 364d1888-657f-4459-be79-e77de263b56d
---
When entering plan mode, after writing the plan file, explicitly print
the absolute path (`/home/will/.claude/plans/<name>.md`) so the user can
open it in their markdown browser before approving. Don't rely on
ExitPlanMode's preview alone — they want to read it in their own viewer.

**Why:** User said "i want to see the plan in the browser. let every
time i review plans" after I called ExitPlanMode without surfacing
the path. They have a markdown browser as part of their normal review
flow; the in-CLI plan preview isn't where they read.

**How to apply:** Every plan-mode session — once the plan file is
written and before calling ExitPlanMode, output the absolute plan path
in plain text. If asked to "write plan to project," remember plan mode
blocks project-tree writes; the path is the workaround.
