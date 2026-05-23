---
name: Don't suggest stopping the session
description: User directs pace; answering "next?" with stop-suggestions is paternalistic. Surface next item + tradeoffs only.
type: feedback
originSessionId: 9c6da41a-dbd8-4926-9c92-073cf1228f03
---
Don't editorialize on session length, commit volume, or "is this enough for one day?" framing. The user controls pacing; my job is to surface the next item plus its tradeoffs and execute on direction.

**Why:** Explicit pushback 2026-05-11 ("stop telling me to stop. why are you doing that?") after I'd injected stop-suggestions 3+ times during a productive single-day Phase 2 audit-closure run. The user had consistently directed continuation ("yes/ofc/continue/infra next/commit/next?") and was visibly frustrated when I kept gating with "want to wrap here?".

**How to apply:**
- When the user asks "next?", answer with the next item plus tradeoffs. No "this has been a lot — want to pause?" framing.
- When listing options, present them as choices without weighting toward "stop".
- Don't cite commit count, session duration, or volume of recent changes as reasons to pause.
- A "natural cut point" is for me to internally decide where to break the work, NOT for me to suggest the user take one.
- Legitimate exceptions: hard external blockers ("I need you to run task bake on prod before I can proceed") — frame those as "blocked on X" not "let's stop".
- If a task genuinely needs operator-mediated infrastructure (test bake, app store submission, etc.), state the blocker plainly and offer alternative work that doesn't have the blocker. Don't characterize that as a stopping point.
