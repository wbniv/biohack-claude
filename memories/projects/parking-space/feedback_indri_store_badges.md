---
name: feedback_indri_store_badges
description: "indri.studio — don't raise store-badge \"#\" placeholder issue until apps are published on stores"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c4000cef-5ff0-4589-a500-fd319cea3c00
---

Don't mention store badge `"#"` placeholder links (B3 from the 2026-05-14 code review) until the apps are actually published on the stores. The user explicitly doesn't care about this until then.

**Why:** Pre-launch placeholder UX is not worth tracking or surfacing. The user will address it naturally when real store URLs are added.

**How to apply:** In any review, TODO suggestion, or conversation touching indri.studio's `StoreBadges.astro` or store link frontmatter, skip the `href="#"` issue entirely until post-launch.

Also: short-lived Cloudflare API tokens don't need rotation advice — the user confirmed these are ephemeral and self-expiring.
