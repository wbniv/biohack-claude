---
name: feedback-prefer-proper-fix
description: "When choosing between fix scopes, default to the proper/architectural solution — don't anchor on the minimal/targeted option."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9fad4a04-f48e-41a5-9d79-f8da7e3da752
---

When presenting fix options between a minimal/targeted fix and a proper/architectural one, **default to the proper one**. Don't lead with the minimal fix as "recommended" just because it's smaller. If both options are real, present the architectural one as the default unless the user has indicated they want surgical scope.

**Why:** When offered A (targeted) vs B (proper) for the indri.studio cross-page header animation issue, I marked A as "recommended" and B as a "bigger architectural call." Will responded: *"i want it solved properly, ofc. have we met? heh. remember that"* — making clear this is a standing preference, not specific to that one decision. The minimal fix is a workaround; the proper fix removes the underlying constraint.

**How to apply:** When framing fix options, lead with the architectural answer. Only suggest the targeted version if it offers something the proper version doesn't (e.g., reversibility, lower risk under a deadline). Don't preemptively shrink scope to "save effort" — Will sees that as anchoring on the wrong default. Related: [[feedback-renaming-and-refactors-welcome]] cascade rule from `~/SRC/CLAUDE.md` ("Renaming and large refactors are welcome. The only constraint is nothing breaks.") — same shape, applied to all sized changes.
