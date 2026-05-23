---
name: feedback-seed-dont-clone
description: "When seeding a new site from an existing one, swapping the wordmark + accent color isn't enough — the visual fingerprint of the source carries through. Plan and execute the distinctive elements, don't defer them."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a2f3a3df-e9b7-4d7d-8c72-4da26442c032
---

When user asks to seed a new site from an existing template (e.g., indri.studio from rapid-raccoon-site), do NOT just swap the wordmark and accent color and call it adapted. The visual fingerprint of the source — italicized lowercase headline style, dot-grid background, glass-card components, Material-style token names, header/footer rhythm — all carry through unchanged and the result looks like a recolored clone of the source.

**Why:** Will explicitly walked us through inspiration sites (Hoox, clerk.com, Droneland) and articulated a distinct brand vocabulary (ringtail greys, neon Phosphor purple, pixel-grid motion bands, stripe motif). I seeded from rapid-raccoon-site, swapped cyan to purple, and stopped. Will's reaction: "you made me a site that looks like every other site you've already made me, heavy sigh." Right.

**How to apply:**

1. **Plan the distinctive elements first, build them first.** The signature visual (StripedGridMotion in this case, or whatever the brand's anchor is) ships in the same iteration as the seed, not as a follow-up. The seed without the distinctive elements is a clone with a different name.

2. **Audit the seed for fingerprint elements before adapting.** Things to interrogate: wordmark style (italic? lowercase? all-caps? size?), background texture (dots? gradient? noise? plain?), component shapes (glass-card? hard borders? brutalist blocks?), token naming (Material? custom?), header layout, footer layout, section rhythm. If the inspiration brief diverges on any of these, change them BEFORE shipping the first commit.

3. **Cross-check against inspiration sites concretely.** For each piece of structural copy (e.g., "italicized lowercase 'indri'"), can the user point to the inspiration site (Hoox / clerk / etc.) and say "yes, that"? If not, it's a seed fingerprint, not a brand choice.

4. **"Mechanical color swap" is the failure mode.** If the only diff from the source is `s/cyan/purple/g` + wordmark text, the result will read as a clone. Need at least one of: structural change (section rhythm), texture change (bg replacement), or signature component added (motion module, distinctive imagery).

5. When the user has gone through the effort of articulating a brand brief, **respect the brief by execution**, not by future intent. "We'll add the motion module later" is a polite way to ship a generic site now.

Related: [[feedback-tooling-choices]] — same family: do the distinctive work, don't defer it.
