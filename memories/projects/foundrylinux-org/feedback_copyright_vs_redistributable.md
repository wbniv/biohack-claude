---
name: feedback-copyright-vs-redistributable
description: "Use \"non-redistributable\" / \"not freely redistributable\" rather than \"copyrighted\" when discussing why a package is held back from a publicly-pulled image or multiverse-only — the issue is redistribution rights, not copyright."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 86de474c-e0d7-401b-bf23-c4da70277f30
---

When writing about why certain packages can't ship in publicly-pulled images or main/universe — emulator ROMs (vice, atari800, fbzx), BIOS blobs, firmware, non-free codecs, mame-extra samples, etc. — reach for **"non-redistributable"** or **"not freely redistributable"**, not "copyrighted" or "proprietary".

**Why:** GPL code is copyrighted too. *Everything* original is copyrighted by default. The reason Ubuntu shoves vice's ROM blobs into multiverse isn't that they're copyrighted — it's that Canonical doesn't have a licence to redistribute them. Conflating the two is technically wrong, and on a topic where being technically right matters (legal positioning of a distro's image, what's safe to bundle in a public GHCR push, multiverse split rationale) the sloppy framing erodes credibility. Caught during the phase-2 devbox plan review on 2026-05-21 — 9 occurrences swept to "non-redistributable" in one pass.

**How to apply:** Default to "non-redistributable" / "not freely redistributable" / "with restricted redistribution rights" when the *real* concern is shipping the bits. Reserve "copyrighted" for cases where copyright itself is the topic (DMCA, attribution, GPL compliance). When in doubt: ask "is the problem that someone owns this, or that we can't ship it?" — almost always it's the latter.
