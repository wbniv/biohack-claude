---
name: feedback-package-skill-iterate
description: "When running /package, treat each invocation as a chance to refine the skill itself — capture lessons learned and edit ~/.claude/skills/package/SKILL.md (and templates/) in the same session as the package commit."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a721a77a-785a-4a05-a4f8-843a9087f1b6
---

When packaging anything via `/package`, treat the run as a feedback loop for the skill itself — not just the package. Each real run typically surfaces something the skill should have warned about: a lintian tag we hadn't tabled, a debhelper override the template doesn't mention, an upstream quirk worth flagging, a tooling gap (mandoc vs man -l), a stale reference in a comparison table.

**Why:** User asked explicitly "keep the package skill updated as we package 2 more things" after the f9dasm run already taught us several skill improvements (man pages as Policy §12.1 non-negotiable, lintian-clean-before-upload gate, `# shellcheck disable=SC2064` for the trap, mandoc-Tlint vs groff for man-page validation). The skill gets sharper with each real package; the lessons are lost otherwise.

**How to apply:** When running /package for libvgm or vgmstream (next two), and any future runs:

1. As lessons emerge during the run, queue them as TODOs for the skill — note them in the conversation so they aren't lost.
2. Before the final commit of the package, also edit `~/.claude/skills/package/SKILL.md` and any relevant `templates/` files.
3. Land both commits in the same push: one to `foundrylinux.org` (the package), one to `~/.claude` (the skill refinement).
4. The skill commit message should name the package that surfaced the lesson, for traceability.

Examples of skill-update triggers (from prior runs):
- New lintian warning encountered → add to the warnings table in Step 4 with the real fix.
- New `debian/rules` override pattern (e.g. cmake out-of-tree, autotools subdir) → add to Step 3 §4's examples.
- Upstream layout quirk (vendored libs, weird Makefile, missing install target) → note in Step 3 with the right approach.
- Tooling discovery (better validator, better build tool, new dh helper) → adopt in templates and document.
- Stale references (retired packages, renamed paths, old command-line flags) → fix immediately.

Don't defer skill updates to "I'll batch them later" — by next session the rationale is gone. Edit the skill in-line with the package work.
