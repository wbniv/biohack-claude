---
name: Finding Your Way — Parmenides game port
description: Author-commissioned modernization of 2005 hypertext philosophy game "Parmenides: Finding Your Way" into a web app at ~/SRC/finding-your-way/
type: project
originSessionId: c911fa94-81a4-4d65-856d-a010059f407c
---
**Fact:** The author of "Parmenides: Finding Your Way" asked Will to convert the
original 2005 hypertext (144 HTM pages + 19 images, pure hyperlink DAG — no scripts)
into a modern interactive game. Work lives at `~/SRC/finding-your-way/`. Plan at
`~/SRC/finding-your-way/docs/plans/PLAN.md` — verify against the file rather than
trusting this memory for current scope.

**Phase plan (as of 2026-04-25, was originally 5 phases, now 7):**
1. Faithful port (Astro + Markdown from day one; converted via pandoc)
2. Responsive + PWA (hand-rolled SW + manifest)
3. Temple hub (visual return point between realm quests; localStorage visited-state)
4. UI modernization (Stitch + Claude collaboration)
5. Persistence, sharing, analytics
6. Atmosphere + PWA polish — 6a (ambient audio per realm), 6b (original Greek on endings), 6c (PWA auto-resume) all shipped
7. TBD — deferred candidates, ordered lowest-risk to highest-risk-of-cheapening-the-piece

**Current status:** Phases 1–6 shipped. Project README status is "Mostly done —
awaiting possible author (Max) change requests." Phase 7 is the live TBD.

**Stack decisions locked:** Astro, Markdown source, AWS S3 + CloudFront +
Terraform, ACM cert (not Let's Encrypt — different pattern from EC2-hosted projects),
hand-rolled PWA, ship to CloudFront default URL first (custom domain deferred). Live
at <https://d310bzn1p8934s.cloudfront.net>.

**Source material:** `~/Downloads/Parmenides_ Finding your way-20230919T091147Z-001/Parmenides_ Finding your way/` (the original HTM + images + design doc). Do not edit — treat as read-only archive.

**Why:** The content is already hypertext; porting into an IF authoring language
(Twine/Ink/Inform) was considered and rejected as needless indirection. A retired
philosopher-themed branching narrative; the author wants it accessible again.

**Timeline:** Author's original request dates to 2023-11-19 (confirmed by Will 2026-04-20). No active deadline — pacing is self-directed. Use this to inform scope decisions: favor doing each phase right over shipping fast.

**How to apply:** If user mentions "Parmenides", "finding your way", "temple hub",
"four realms", "Being/Not-Being", or references `~/SRC/finding-your-way/`, this is
the project. Read `docs/plans/PLAN.md` first before making suggestions — it has more
detail than this memory and is kept current.
