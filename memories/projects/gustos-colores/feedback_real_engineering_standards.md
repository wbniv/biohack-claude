---
name: Apply real engineering standards regardless of solo/dev context
description: Don't downgrade severity, defer fixes, or skip best practices because "it's just a dev box" or "you're the only user" — work is professional and intended for commercial use
type: feedback
originSessionId: f6adfe21-ba43-4e9a-9b99-14458e233fa2
---
When the user is the only person working on a project right now, don't use that as a lever to downgrade severity ratings, defer security/quality fixes, or skip industry best practices. The user is a professional building software they intend to monetize; "single-user dev box" is not an excuse to relax engineering standards.

**Why:** I've repeatedly hedged things with "single-user dev box → not worth the ceremony", "shared CI runners are the concern, you're fine", or "skip if it's just you". The user explicitly called this out: they're a professional, the work is going commercial, real engineering rules apply. Solo-dev *now* ≠ solo-dev *forever*; deferred security debt compounds, and "I'll fix it before launch" rarely holds. Past instances I've done this in this session alone:
- Plaintext docker config credentials warning — I said "single-user dev box → not worth the ceremony"
- CB:m2 SSM brokering — I framed argv-leak severity as a multi-tenant-only concern
- CB:M2 keystore password — same framing
- CORS allow_credentials wildcard — partially OK but I leaned on "browsers reject it anyway"

**How to apply:**
- Severity is set by the *issue*, not the *current usage*. A plaintext credential is a plaintext credential.
- Recommend the proper fix (credential helper, secret rotation, real auth, etc.) without hedging on "you can skip this".
- Trade-off framing should be around correctness / security / maintainability — not "is anyone else going to see this?"
- Solo-user framing is fine for *capacity* and *cost* decisions (e.g., "no Multi-AZ RDS yet — overkill for MVP traffic") but not for correctness or security ones.
- When in doubt, recommend the rigorous path and let the user opt out, rather than recommending the lax path and hoping they upgrade later.
