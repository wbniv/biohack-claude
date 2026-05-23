---
name: feedback-canonical-not-always-biggest
description: "When consolidating duplicated scripts, audit each copy's unique features before declaring one \"canonical\" — line count is not a proxy for completeness"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 147d0941-29ff-46c9-9030-fc0102706674
---

When you find several copies of the same script across a codebase and need
to pick one as the source of truth, **don't assume the longest file (most
lines / most features) is the canonical one**. Each copy may have a
feature the others lack.

**Why:** 2026-05-19 — `md-to-pdf.sh` lived in 4 places. I assumed the
809-line `python-tui-lib` copy was canonical (it was the longest and the
one referenced by `CLAUDE.md`'s `python-tui-lib is the shared script and
hook library` rule). But the 586-line `WorldFoundry-wbniv` copy had
**GitHub-style alert callout support (`> [!NOTE]`, `> [!TIP]`)** that
the 809-line "canonical" did not. If I had just symlinked the three
shorter copies to the longer "canonical", the user would have lost
working `[!TIP]` rendering — which they had already complained about
("ugly") in the housekeeping report.

**How to apply:**
- Before declaring a winner, **grep every copy for distinctive
  features** (`grep -cE '<unique syntax>' file` across all candidates).
- For non-zero hits in non-canonical copies, **port the feature into
  the canonical first**, then symlink. Don't let consolidation regress
  features.
- Line count + filename + path are heuristics, not authority. Diff the
  unique blocks. Look at git log on each.
- The user prefers porting forward over picking a different canonical —
  the structural "shared library" location wins, but the canonical
  inherits all unique features before stale copies are replaced.
