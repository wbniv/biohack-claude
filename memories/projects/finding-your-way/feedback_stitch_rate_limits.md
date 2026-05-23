---
name: Stitch MCP operational quirks
description: Rate-limit + prompt-length guidance for Stitch MCP calls — keep seeds short, iterate via generate_variants
type: feedback
originSessionId: f962ffdb-20aa-40d3-9c46-5fb51f176ef2
---
Two independent failure modes on Stitch MCP, both fix-able by
changing how you call it:

**1. Rate limiting on primary endpoints (free tier)**

`mcp__stitch__generate_screen_from_text` and
`mcp__stitch__edit_screens` hit per-endpoint daily quotas and start
timing out after a few calls. `mcp__stitch__generate_variants` is
either unmetered or has a much higher limit — not noticeably
rate-limited in practice.

*Why:* confirmed hands-on by the user in `~/SRC/parking-space/`.
Full tracking lives at `~/SRC/parking-space/.claude/memory/`.

**2. First-call timeouts on long prompts**

Every long `generate_screen_from_text` prompt times out on first
attempt; a shorter retry succeeds. Undocumented in the SDK or
`stitch.withgoogle.com/docs` (verified 2026-04), but the pattern is
reproducible across sessions. Likely cause: server-side processing
budget (underlying Gemini 3.x call) rather than a hard char cap.

*Why:* user's observation from this project's Phase 4 work plus
prior sessions. The SDK default timeout is 5 min; the practical
"how big can a prompt be and still return" ceiling is much lower.

**How to apply — both together:**
1. **Seed short.** Keep `generate_screen_from_text` prompts under
   ~400–600 chars / 3–6 sentences. Describe the goal, the feel, and
   one or two key elements; don't stuff every detail in.
2. **One seed per target screen.** Don't burn quota regenerating
   from scratch.
3. **Iterate via `generate_variants`.** Variants aren't
   rate-limited and let you push details through `creativeRange`
   (REFINE / EXPLORE / REIMAGINE) and `aspects` (LAYOUT,
   COLOR_SCHEME, IMAGES, TEXT_FONT, TEXT_CONTENT).
4. **If the first seed call times out, shorten and retry — don't
   retry the same prompt verbatim.** The timeout is the signal the
   prompt was too complex for the server budget, not a transient
   network blip.
5. Assume daily reset — don't assume primary endpoints are
   permanently broken after one bad day.
