---
name: Stitch generate_variants returns one screen per call
description: generate_variants with multiple selectedScreenIds still produces only ONE output, so refine each screen with its own call
type: feedback
originSessionId: 47825233-5074-4be9-84bc-31c52ada7d4e
---
`mcp__stitch__generate_variants` accepts `selectedScreenIds` as an array, but the call returns only ONE refined screen — Stitch picks one of the inputs and ignores the rest. Don't batch unrelated screens into a single call expecting per-screen outputs.

**Why:** Confirmed empirically 2026-04-25 in SplitLedger redesign: passed [screenA, screenB] with a "fix labels" prompt and only screenA was refined; screenB was unchanged. Wasted a round-trip and required a separate call to fix screenB.

**How to apply:** One `generate_variants` call per source screen when refining. Use `variantCount` to get multiple alternatives of the SAME source screen, not one alternative each across multiple sources. If you need the same fix applied to N screens, fire N parallel calls.
