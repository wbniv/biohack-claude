---
name: copy-style-pitches
description: "When reviewing, writing, or revising any app pitch / marketing copy / per-app section in this repo, default to outcome-stated headlines, single-audience focus, aggressive artifact removal, AND link every third-party product/service name."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a951e92a-938e-4a46-a472-f0f800c2fd2c
---

For app pitches / `b2b:` lines / per-app marketing sections / app descriptions in this repo — both when the user delegates judgment ("whatever you think best") AND when they're reviewing copy and signal doubt ("hmmm", "thoughts?", flagging a passage):

- Prefer **outcome-stated headlines** over descriptive labels. "Your unused space is income" beats "For condo owners with an unused space."
- Prefer **tight single-audience** pitches over multi-audience coverage. Drop bullets that name secondary roles even if the product supports them — coverage dilutes the pitch.
- **Aggressively remove artifacts** of any old framing when pivoting. Closing paragraphs that only made sense for the previous audience, mentions of hardware, etc. go even if not explicitly asked.
- **Link every third-party product/service name on first mention.** Poly Haven, OpenGameArt, Sketchfab, Flutter, App Store, Steam, Anthropic, Blender, etc. all get linked. The site uses `rehype-external-links` (configured in `astro.config.mjs`) which auto-applies `target="_blank"`, `rel="noopener noreferrer"`, and `data-external="true"`. The prose CSS in `src/pages/apps/[...slug].astro` renders a ↗ glyph after any `a[data-external]` automatically — so just write the markdown link `[Name](https://…)` and the rest happens. **Pattern is "as usual"** — i.e. if you're reviewing or writing copy that mentions third-party names without links, that's the recurring miss the user keeps flagging.

**Why:** Validated 2026-05-13 (ParkingSpace b2b copy: outcome headline, single audience, artifact removal) and 2026-05-14 (blender-asset-searcher: user flagged unlinked provider names with "LINKS LINKS LINKS" after I repeatedly missed it during review).

**How to apply:** Marketing/pitch text only (`b2b:` frontmatter, per-app landing pitch sections, homepage card copy, content collection app `.md` files). Technical docs, READMEs, plan files stay descriptive and complete — they have different goals. For the linking rule specifically: applies anywhere in content collections where a third-party brand/product/service is named, not just pitches.
