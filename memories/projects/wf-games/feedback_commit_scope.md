---
name: Don't broaden commit scope beyond what was asked
description: When the user says "commit X" or "commit the others," resolve the scope from the conversation's most recent enumeration — not from git status sweeping
type: feedback
originSessionId: 7a75d2d6-3cbc-48c2-b163-993638e3b490
---
When the user requests a commit ("commit", "commit the others", "commit those"),
the scope is whatever the conversation has just enumerated — typically the
specific files I named in my previous message. **Do not** widen that to "every
file git status shows as modified or untracked."

**Why:** Pre-existing pending work in `git status` is often there *deliberately* —
queued for reasons the user has but I haven't been told. Sweeping it into a
commit batch (even with thoughtful per-file commit messages) ships work that
wasn't ready and forces a revert. CLAUDE.md says it explicitly: "stage only the
files you modified, verify git diff --cached matches what you touched, and leave
any other in-progress changes unstaged."

Specific incident (2026-05-08): Previous message had listed two specific
preserved-unstaged files (`SRC/free-services.md`, `MEMORY.md`). User said
"commit the others, sure". I read "the others" as "every pending modification
in the repo" and made 6 commits spanning settings.json, glossary, three
projects' memory dirs, and an investigation doc. User had to ask for a revert.
The right reading was: the two files I'd just enumerated.

**How to apply:**
- Pronouns resolve against the *conversation*, not the working tree. Re-read my
  own most recent message before staging.
- If "the others" is genuinely ambiguous (no clear antecedent), ask one
  clarifying question or take the narrowest reading. Both are fine in auto mode.
- Auto mode shortcuts permission prompts, not scope. It is not a license to
  expand what was requested.
- Pre-existing pending state that didn't come up in this conversation is *not
  mine to commit* even if I'm the sole apparent author.
