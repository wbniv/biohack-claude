---
name: Google Stitch design project for Rapid Raccoon
description: Pointer to the Stitch project that generated the corporate-website design concepts adopted for the reskin
type: reference
originSessionId: 3a2c7a5b-1164-4180-b510-acc729b9a71e
---
Google Stitch project `projects/16261848696001807042` — title "Rapid Raccoon Corporate Website" — contains 16 screens (Home variants with and without mascot, Services, Solutions, Technology, Network & Sustainability, About, Contact, plus a mascot image).

The live site uses the **Mascot Home variant** as the source of truth for design tokens (screen id `fcb034ff74c34b37a61d75f5f2715073`). Palette, fonts, glass-card/glow-sm/grit-texture utilities all originated there.

**How to apply:** If the user references "the Stitch designs" or asks to pull in another page (Services, About, etc.), start with `mcp__stitch__list_screens` on project `16261848696001807042` to find the screen, then `mcp__stitch__get_screen` + download the `htmlCode.downloadUrl`. Remember: Stitch's fictional "urban logistics" copy is rejected — adopt visual structure only, rewrite copy to fit the indie game studio voice.

The mascot image on the Stitch home is served from an ephemeral `lh3.googleusercontent.com/aida/…` CDN URL and is NOT safe to hot-link. The live site uses `public/mascot.svg` as a placeholder; final mascot asset still pending from the user.
