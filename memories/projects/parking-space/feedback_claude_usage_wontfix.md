---
name: feedback_claude_usage_wontfix
description: "During claude-usage code reviews, always read docs/wont-fix.md first to avoid re-raising permanently closed items; keep the file updated with new won't-fix entries as they are decided."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 306b596d-3f9a-4f39-983d-db2690410854
---

Before raising any issue in a claude-usage code review, check `/home/will/SRC/claude-usage/docs/wont-fix.md`. It lists all permanently deferred items with their rationale. Re-raising a won't-fix item wastes review cycles.

**Why:** BUG-4, BUG-5, BUG-6, CQ6-6, CQ6-7, and CQ8 were each flagged multiple times across 7 review passes before being formally closed. A reference doc prevents that recurrence.

**How to apply:** At the start of any code review pass on claude-usage, read `docs/wont-fix.md`. When a new item is permanently deferred (won't-fix, not-a-bug, by-design), add it to that file in the same commit as the decision.
