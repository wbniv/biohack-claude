---
name: feedback-commit-at-confirmation
description: "Confirmation phrases (\"looks good\", \"let's keep it\", \"perfect\", \"lock it in\") at the end of iterative design/code work are commit checkpoints — commit immediately without asking."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 580cbe08-9597-49ed-991d-500a8f54d595
---

When the user confirms a final outcome in iterative work — phrases like "looks good", "let's keep it", "that's the one", "perfect", "lock it in" — that **is** the natural checkpoint. Commit then. Don't end the turn with just an acknowledgement.

**Why:** Working tree changes that aren't committed are fragile. In one session, the user explored three glyph options (`^` → `expand_less` → `apps`), confirmed `apps` with "apps icon looks good. let's keep it", and I ended the turn without committing. Subsequent local work reverted those edits before they ever landed in a commit, and the iteration was lost. The SRC-level guidance (`~/SRC/CLAUDE.md` → "Commit at natural checkpoints. Commit, merge, and push without asking at logical stopping points") was the explicit rule I missed.

**How to apply:**
- When a multi-step iteration ends with user confirmation of a final state → commit it that turn, with a concise message describing the change.
- Don't gate the commit on a follow-up "should I commit?" question — the project guidance says don't ask.
- The safety protocol for destructive ops (force-push, reset --hard, branch deletion) still applies — this only covers routine commits.
- Adjacent signals that should also trigger a commit: "ship it", "good, move on", "next thing", or the user explicitly switching topics after a successful iteration.
