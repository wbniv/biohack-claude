---
name: feedback-illustration-style
description: "For Indri character/mascot illustrations, prefer 3D Pixar-render style over flat-vector — the .glass-card hard-edge brand applies to UI components, not character art."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fed084cb-c46e-4099-9135-1a51d584bbdd
---

For Indri character / mascot / illustration assets (lemurs, app mascots, decorative figures), default to **3D Pixar-render style** in image-gen prompts — fluffy fur with visible strands, soft volumetric shading, studio lighting, charming expressions. Avoid "flat vector", "print-block aesthetic", "hard edges, no gradients" framings for character art.

**Why:** Confronted with two ChatGPT/DALL-E renders of the same ring-tailed lemur — one flat-vector with brand-correct purple-eyes-and-cream palette, one 3D Pixar fluffy character — the user picked the Pixar render decisively ("i wanted it more 3d", "that's exactly what i want!!!!"). The flat-vector version was "brand-correct but cold"; what makes a mascot land is personality, expression, warmth — which 3D rendering carries and flat vector flattens out.

**How to apply:**
- Image-gen prompts for Indri characters should use: "3D Pixar-style render", "fluffy fur with visible strands", "volumetric shading", "studio lighting", "character portrait", "charming / cheeky / expressive".
- The site's `.glass-card` / print-block / flat-fill aesthetic still governs UI surfaces (cards, buttons, dividers). Don't conflate component design with illustration style — different layers, different rules.
- Brand-correct color accents (Phosphor purple `#b026ff` for eye-pupils, etc.) can still be specified in 3D-render prompts; they don't require flat-vector framing.

**Prompt template** (starting point, tweak the species/pose/expression per job):

```
3D Pixar-style character render of a [SUBJECT], close-up portrait, head-on,
looking directly at the camera with [EXPRESSION — e.g. charming and slightly
cheeky / curious / amused]. Fluffy fur with visible strands, soft volumetric
shading, subsurface scattering on lighter areas. Studio lighting, soft
neutral grey background, transparent if possible. Production-render quality,
Pixar-quality character art.

Brand colour notes: any Phosphor-purple accent (#b026ff) should land on
[specific feature, e.g. eye pupils with amber/orange iris halo]. Otherwise
natural species colouring.
```

Worked first try in ChatGPT (DALL-E / GPT-4o image gen) on 2026-05-13 for the
404-page ring-tailed lemur — purple pupils, tail-over-head composition, slight
smirk, transparent background. Flux Schnell on Workers AI did NOT respect the
flat-style or purple-accent constraints; DALL-E / GPT-4o is much better at
character art and at obeying specific colour-placement instructions. Trade-off:
DALL-E is paid (per `~/SRC/free-services.md`), Workers AI is free — for
ongoing/automated work that's character-shaped, plan accordingly.

Related: [[feedback-commit-at-confirmation]]
