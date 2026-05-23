---
name: feedback-render-design-artifacts
description: "In design docs and reference files, always render visual elements as actual HTML — never substitute text descriptions for icons, swatches, or type samples."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b2e05232-0aa8-4773-b271-65537f724a28
---

When writing a design reference doc (DESIGN.md, colophon, style guide), render visual elements as actual rendered HTML — never write text substitutes like `smartphone` when the icon itself can be shown, or a hex value when a color swatch can be rendered.

**Why:** User called it out explicitly when the iconography section listed symbol names (`smartphone`, `tablet`, etc.) instead of rendering the actual Material Symbols icons. The fix — loading the Google Fonts stylesheet and rendering `<span class="material-symbols-outlined">` elements — took one edit. Not doing it from the start was lazy and produced a useless reference.

**How to apply:**
- Icons → load the icon font via `<link>` and render actual glyphs in a visual grid.
- Colors → render `<div>` swatches with the actual background color, not just hex strings in a table.
- Typefaces → load the font and render sample text in the actual typeface at the documented sizes/weights.
- Spacing/radius → consider rendering labeled boxes to make values tangible.
- The `md-to-pdf` renderer passes through any line starting with `<` as raw HTML, so HTML blocks are fully supported in `.md` files previewed via `task md`.
- Related: [[feedback-plan-preview-in-browser]] — same instinct: make it real, not described.
