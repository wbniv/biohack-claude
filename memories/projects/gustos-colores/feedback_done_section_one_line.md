---
name: DONE entries are one tight line
description: When checking off a TODO item or compiling DONE history, each DONE entry must be a single line ~120-150 chars including prefix; compress retroactively if you see long ones
type: feedback
originSessionId: d56cc664-0e56-4c47-ad1a-919e483d3029
---
In `TODO.md`'s `## DONE` section, every entry is **one tight line, ~120-150 chars including the `- [x] \`YYYY-MM-DD\`` prefix, written as a GFM checked checkbox.** No multi-sentence retrospectives, no commit-message-style breakdowns, no "Shipped:" preambles. Strip the bundled-test counts, file paths, debugging history, and inline rationale — they live in the linked plan and the git commit body, not here. Keep: date, headline, terse what-changed clause, plan link.

**Why:** This is also stated in `~/SRC/CLAUDE.md` ("TODO done section"), but I drifted — many existing DONE entries were 800-2000 char paragraphs, which made the file painful to scan. The user flagged this directly with a sad face, so it's a real preference, not a passing nit. The `- [x]` checkbox prefix (instead of a plain `- ` bullet) was added 2026-05-07 so the DONE section pairs visually with the open `- [ ]` items above; rendered as a uniform task list.

**How to apply:**
- When promoting an open `- [ ]` to done, the substitution is `[ ]` → `[x]` (keep the brackets) and rewrite the description to one ~120-150 char line in the same edit.
- When you encounter long pre-existing DONE entries during any TODO.md edit, compress them retroactively as part of that edit — don't leave them long because "they were already there."
- Order: reverse-chronological under the `## DONE` heading.
- Format: `` - [x] `YYYY-MM-DD` <Headline> — <terse what-changed clause> — [plan](path) [review](path) `` (links optional). Aim for 120-150 chars total including the `- [x] ` prefix.
- Use abbreviated test counts (`+13 tests, 99 total` not "+13 covering A, B, C, D, E…").
