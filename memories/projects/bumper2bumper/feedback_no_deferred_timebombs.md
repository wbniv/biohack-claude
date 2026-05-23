---
name: don't bury real future work as TODO footnotes — finish the job now
description: If the work has to be done at some point, do it now. A "captured as separate TODO" / "small follow-up" / "out of scope" line is just a footnote on work that still has to be done — and that work falls on the user later. The narrow "same files/lifecycle" test is too forgiving; the real test is "does this still have to be done?".
type: feedback
originSessionId: 3ec77330-7c83-4eb1-b903-1239bafea483
---
**The actual rule, in the user's own words:** *"to me, personally, it's about leaving work that HAS TO BE DONE AT SOME POINT LATER. HAS TO BE DONE STILL. and it's just a footnote."*

If a piece of work has to be done at some point — by SOMEONE — then writing "captured as a separate TODO" or "deferred" or "out of scope" doesn't make it not-work. It just transfers it to a footnote the user will have to come back to. The TODO entry is the timebomb.

The narrow "same files / same lifecycle / asymmetric with rest of code" framing I had before was too forgiving — it lets me dodge same-scope work that's *also* easy to spot from a code-symmetry angle. The actual test is broader and simpler:

> **Does this work have to be done at some point?**
>
> - **Yes** → do it now. Even if it's in different files, even if it's nominally "another commit's concern."
> - **Only if some user action happens first (external prereq the user must take)** → fine to defer with a clear gate (e.g., "Apple Dev Program enrollment needed before the iOS Codemagic cron can fire").
> - **No, it's purely speculative / might never actually need doing** → fine to leave out entirely (don't even TODO it; speculative TODOs are noise).

**Tells that I'm about to footnote real work:**
- "Captured as a separate TODO" / "moved to follow-up"
- "Small follow-up"
- "We'll do this when X happens" with no specific external gate on X
- "Orthogonal — could be a follow-up" (often it's the same lifecycle)
- "If anyone ever needs Y" (the user already knows whether anyone needs Y)

**Why:** user explicitly flagged 2026-05-11: *"you REALLY like leaving me timebombs, eh? FFS"*. The pattern that triggered it:
- Turnstile cron: shipped + deferred SSM-source-of-truth → user said "not out of scope"
- Same plan: deferred TF-drift / cloud-init read-from-SSM → user said "not out of scope" AGAIN
- Three rounds in one feature.

User then clarified the rule isn't about same-files; it's about *real work has to be done*.

**How to apply:**
- When tempted to write a deferred-TODO line, ask: "Will I (or someone) have to do this later?" If yes — do it now. Don't write the line.
- Exception: external prereqs where someone outside-the-keyboard has to act (Apple Dev Program signup, vendor dashboard step). Those are legitimate gates and the TODO captures the gate, not deferred work.
- When the work IS legit-deferrable (different vendor, different release, different team), still ask before deferring — not after. "Should I include X?" beats "I deferred X."
- Speculative TODOs are noise. If you can't say "this WILL need doing," don't write the TODO at all.
