---
name: No Claude Co-Authored-By trailer in commits
description: A local hook blocks `Co-Authored-By: Claude …` in commit messages as fabricated-identity content; omit the trailer
type: feedback
originSessionId: 3d2c00e4-af49-46a0-8e59-0a8fc63af5c7
---
Do not include a `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` (or any similar Claude model identity) trailer in commit messages for this repo. A pre-tool hook rejects it as a content-integrity violation.

**Why:** The user has a local hook that flags any Claude co-authorship trailer as a fabricated model identity, even the one the default Claude Code prompt suggests. Encountered 2026-04-22 when committing the `nav:` refactor — the commit was denied until the trailer was removed.

**How to apply:** When drafting commit messages in this repo, skip the Co-Authored-By line entirely. Follow the repo's existing commit style (short `prefix: lowercase subject`, optional body) without any AI-attribution trailer.
