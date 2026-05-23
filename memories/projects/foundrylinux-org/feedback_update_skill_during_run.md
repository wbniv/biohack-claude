---
name: feedback-update-skill-during-run
description: "When running the new-web-apt-repo skill to set up a new apt repo, update the SKILL.md with anything learned from that real run."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8177dafa-2bab-4871-9b4b-d74f37d6ca52
---

When executing the `new-web-apt-repo` skill for a real repo, update `~/.claude/skills/new-web-apt-repo/SKILL.md` (or create it if missing) with any gaps, corrections, or new patterns discovered during that run.

**Why:** Every real `/package` run is a feedback loop for that skill — same principle applies here. The skill should evolve to match actual behaviour, not just theoretical steps.

**How to apply:** At the end of each apt repo bootstrap run, review what differed from the skill description and commit the skill update alongside the repo changes.
