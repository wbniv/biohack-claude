---
name: Trim screenshots before embedding in plan/verification
description: When the user provides a screenshot for verification, crop it to just the browser, save under `docs/plans/screenshots/`, and embed in the plan with `<img src="screenshots/...">`.
type: feedback
originSessionId: e3762679-c1b7-45bd-8a19-56279eef4d47
---
When the user shares a screenshot to confirm a verification step, don't just acknowledge in chat — capture it into the plan:

1. **Trim** the raw `~/.claude/image-cache/<id>/<n>.png` to just the browser window with `convert <src> -crop WxH+X+Y +repage <dst>`. Typical 1920×1200 desktop capture with maximized Chrome trims as `1850x1170+58+30`; smaller browser windows need different offsets — eyeball them.
2. **Save** to `docs/plans/screenshots/<plan-date>-<topic>-<descriptor>.png`. Match the parent plan's filename prefix so future scanning groups them.
3. **Embed** in the plan's verification section with `<img src="screenshots/<file>" width="400">`. CLAUDE.md suggests `width="700"` but the user has explicitly asked for smaller embeds — use `400`. `<img>` over `![]()` so bracket-ambiguous markdown doesn't break.
4. **Commit** the screenshots alongside the plan / close-out commit so reviewers see the evidence inline.

**Why:** The user explicitly asked for this ("trim screenshots i provide to just the browser and add to plan/verification steps") so future work-in-progress UI verification steps land in the durable plan doc rather than scrolling chat history. CLAUDE.md already specifies the `<img>` width and the screenshots dir; this memory closes the loop on what to do *with* user-provided screenshots.

**How to apply:** Whenever the user pastes a screenshot during a verification pass, immediately trim → save → embed → commit. Don't wait for an explicit ask. Multiple breakpoint shots (mobile / compact / extended) get separate files.
