---
name: feedback-colored-checkmarks
description: Prefer green ✅ and red ❌ emoji over plain ✓/✗ checkmarks in reports and tables that user reads
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 147d0941-29ff-46c9-9030-fc0102706674
---

When emitting status markers (present/missing, pass/fail, yes/no) in reports,
markdown tables, or any visual output the user reads, prefer the **colored
emoji variants**:

- ✅ (green check, U+2705) for present / true / pass
- ❌ (red cross, U+274C) for absent / false / fail

Not the plain glyphs ✓ (U+2713) / ✗ (U+2717) — those render as monochrome
black-on-white and harder to scan at a glance.

**Why:** User explicitly asked for "green checkmarks and red x's" (2026-05-19).
The plain glyphs were used by default; emoji variants are the preference.

**How to apply:**
- Tables: use ✅/❌ for boolean status columns.
- Inline prose: same.
- Plain dashes (—) for n/a stay unchanged.
- Logs / shell output / hook stderr: plain ✓/✗ acceptable if emoji would clutter (terminal-only contexts).
