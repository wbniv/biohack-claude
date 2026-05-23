---
name: feedback-forced-reflow-first-paint
description: "When client scripts read layout (scrollY, innerHeight, getBoundingClientRect, offsetHeight, etc.) and then write styles on initial paint, that read forces a sync layout right before the first frame — Lighthouse flags it as `forced-reflow-insight` and it inflates TBT on long pages."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b64e4c37-e45b-4c43-b8f2-de94cd0f2a02
---

When a client script reads layout properties (`scrollY`, `innerHeight`, `getBoundingClientRect`, `offsetHeight`, `offsetWidth`, etc.) and then writes styles / CSS variables on initial page load, the read forces a synchronous layout right before the first frame paints. Lighthouse flags this as `forced-reflow-insight`; on long pages it adds 100–300 ms of TBT.

**Why:** Browsers batch style mutations and layout calculations between frames. Reading a layout-dependent property *during* the same task that has pending style writes forces the engine to flush layout synchronously to give you an accurate answer. On initial paint, every CSS rule has just been applied, every node has just been laid out — there's a lot of pending work, so a single read can stall paint significantly. rAF doesn't fix this if the rAF callback itself does the read; it runs right before paint, which is the worst place to flush layout.

**How to apply:** Three-step pattern for any script that reads layout to compute a write on first paint:

1. **Avoid the read entirely when the answer is predictable.** If the CSS default for the value you're computing matches what you'd compute at `scrollY === 0` (or whatever the resting state is), just skip on first load — no read, no write. Most "scroll-shrink", "sticky-header", "in-view fade-in" scripts only need to act when the user has actually moved off the resting state.
2. **For the cases where the read is unavoidable (hash anchors, restored scroll, etc.), defer to `requestIdleCallback`** with a `setTimeout(0)` fallback for Safari (which still doesn't ship rIC). This pushes the layout flush off the critical path so it lands after the first paint, not before.
3. **Subsequent runs (post-view-transition, post-scroll, post-resize) should NOT use rIC** — they need to be prompt. Track first vs. subsequent with a boolean flag; gate only the initial call.

Concrete reference: the fix in `src/layouts/Base.astro` for the scroll-shrink script (commit landing 2026-05-13 against Lighthouse audit recommendation #7).

Related: [[feedback-plan-first-before-code]] — when a perf issue has a known fix in an audit/plan, apply it directly rather than re-investigating.
