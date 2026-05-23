---
name: Stitch MCP rate limiting strategy
description: Free-tier Stitch MCP endpoints are rate-limited daily; fall back to generate_variants when others stop working
type: feedback
originSessionId: 47825233-5074-4be9-84bc-31c52ada7d4e
---
For Stitch MCP screen generation, prefer `edit_screens` and `generate_screen_from_text` as they give more precise control. These endpoints are rate-limited on the free tier and will start failing after a few calls per day. When they do, switch to `generate_variants` which appears to have a much higher (or no) rate limit.

**Why:** Free Stitch account has per-endpoint daily quotas. The "timeout" failures are likely rate-limit rejections, not actual timeouts. `generate_variants` is either intentionally unmetered or has a significantly higher cap. Confirmed in parking-space project sessions; same MCP server, same account, so the behavior is universal.

**How to apply:** Start each session using whichever endpoint fits the task best. When calls begin failing (timeouts, errors), switch to `generate_variants` for the remainder of the day. For tasks that need many screens (e.g., redesigning 8 pages), structure the plan to lean on `generate_variants` from the outset — generate one anchor screen with text, then variant-fan from there.
