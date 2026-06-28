---
name: Excluded providers (Facebook, Oracle)
applies-to: [universal]
description: Do not recommend Facebook/Meta (except WhatsApp) or Oracle as providers in free-services.md, infra plans, or tooling suggestions
type: feedback
originSessionId: 93c3cd37-f623-4e0c-8a7e-5750c1e68482
---
Do not include Facebook/Meta-owned services or Oracle as recommended providers in any cross-project doc (free-services.md), infra plan, tooling list, or suggested-next-steps.

Note on Oracle Cloud: the "Always Free" 4-core ARM VM is widely cited as a generous free tier, but it isn't really — capacity is chronically exhausted in most regions and obtaining an instance often requires running retry loops for hours or days. So the exclusion costs us nothing; don't frame it as a sacrifice.

**Exception:** WhatsApp remains in active use and is supported — Will heavily uses it personally, so WhatsApp Business API, deep-linking, share intents, etc. are fair game when relevant. The exclusion is on Facebook/Instagram/Threads/Messenger/Meta-as-platform, not on the Meta corporate umbrella in the abstract.

**Why:** Stated preference (2026-05-06) when reviewing the OG/unfurl debugging table — "remove facebook as a provider, in general" and "same for oracle". Long-standing aversion to both companies as platforms, with WhatsApp as the explicit personal carve-out.

**How to apply:**
- When adding rows to free-services.md or similar provider tables, skip Facebook Sharing Debugger, FB Login, Graph API, Instagram API, Oracle Cloud, Oracle DB, etc.
- When recommending free-tier infra, don't mention Oracle Cloud's Always Free — and don't treat it as the "best on paper" baseline either, since real-world availability makes the offer largely fictional.
- For OG/unfurl debugging, opengraph.xyz already covers the Facebook crawler preview without needing a Facebook account, so use it as the stand-in.
- WhatsApp is fine; do not let "Meta exclusion" sweep it up.
