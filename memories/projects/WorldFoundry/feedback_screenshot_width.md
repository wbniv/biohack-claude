---
name: Screenshot width in docs
description: Verification screenshots in investigation docs must be no more than 800px wide
type: feedback
originSessionId: c2a51ce3-3e14-44b4-99c9-977b15ecd216
---
Use `<img src="..." style="max-width:800px">` instead of `![]()` markdown syntax for all screenshots in investigation docs and verification sections.

**Why:** Caps wide screenshots at 800px without upscaling images that are already smaller.

**How to apply:** Any time a screenshot is added to `docs/investigations/` or a verification section, emit `<img src="path" style="max-width:800px">` rather than standard markdown image syntax. Never use a fixed `width="800"` — that forces upscaling on smaller images.
