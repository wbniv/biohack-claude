---
name: Survey full vendor ecosystems, not just the famous two
description: When listing SaaS/API options in plans, enumerate the ecosystem layer (BSPs, resellers, alternative providers) rather than truncating to two well-known brands.
type: feedback
originSessionId: aad77eb3-bd7c-47a0-82fa-d37df8e1739a
---
When proposing options for an external service in a plan, list the realistic ecosystem — not just the two best-known names. Cover:

- Direct/first-party access (e.g. Meta Cloud API for WhatsApp)
- The reseller / BSP / aggregator layer (Twilio, 360dialog, Vonage, Sinch, Infobip, MessageBird, Gupshup for WhatsApp)
- SaaS layers built on top (Wati, AiSensy)
- Reverse-engineered / unofficial routes, with their ToS caveats

Even if the recommendation collapses to one option, name the alternatives and the axis they differ on (price, setup overhead, dev ergonomics, ToS risk).

**Why:** User flagged a WhatsApp send-side options block in [`docs/plans/2026-05-10-whatsapp-interactive-notifications.md`](../../../../SRC/bumper2bumper/docs/plans/2026-05-10-whatsapp-interactive-notifications.md) that listed only Twilio and Meta direct — missing the entire BSP reseller ecosystem (360dialog, Vonage, Infobip, Sinch, etc.). A two-vendor list reads like a false dichotomy and may steer the project toward the wrong choice (e.g. Twilio when 360dialog would be a better long-run fit).

**How to apply:** Whenever a plan section weighs "options" for a SaaS, API, or vendor decision — pause and ask: is there a reseller layer? An open-source alternative? An unofficial route? A BSP/aggregator tier? Name them, even briefly. Two-bullet vendor comparisons are usually a sign you stopped surveying too early.
