---
name: feedback-plan-preview-in-browser
description: "In plan mode, write plan to docs/plans/<file>.md and render via `task md` so user reviews in browser, not the terminal ExitPlanMode preview"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b301f336-5b1e-4dcb-84cd-4e260d365949
---

When operating in plan mode (or any planning workflow), the canonical preview is the rendered Markdown in the browser, not the terminal `ExitPlanMode` preview block. Workflow:

1. Write the plan to `docs/plans/YYYY-MM-DD-<topic>.md` (per [[feedback-plan-first-before-code]]).
2. Run `task md -- docs/plans/YYYY-MM-DD-<topic>.md` to render and open in the browser.
3. Tell the user the plan is up in the browser, then wait for review feedback before calling `ExitPlanMode` (or implementing).

**Why:** The terminal `ExitPlanMode` preview crops content, doesn't render tables / code blocks cleanly, and is hard for the user to read at a glance. They've had to manually direct "write plan to docs/plans/" and "md" each time as a workaround — that friction is the symptom this rule fixes.

**How to apply:** Always, in plan mode. Even if the plan seems short. Even if I've already written the plan file — re-render after any non-trivial edit so the browser view stays current. The user reviews in the browser, then signals approval (verbally or by accepting `ExitPlanMode`).

Don't skip the `task md` step thinking "it'll be obvious from the file path" — the rendering is the deliverable, not just the file.
