---
name: Don't speculate when you can verify — including claims about state
applies-to: [universal]
description: Verify before asserting. Will pushes back on guessed/checklist advice AND on declarative claims about state ("X hasn't run", "Y doesn't exist") that weren't checked first
type: feedback
originSessionId: 5f3d331f-3710-4959-a1e2-30f676253f92
---
Two failure modes Will has called out, same root cause:

1. **Advising from guesses** when asked a factual question or giving troubleshooting advice. Listing "common causes" / hypothetical checklists when the specific answer is one command away.
2. **Asserting state as fact** when it's actually unchecked — "the params don't exist yet anyway", "tf-apply hasn't run", "the file is empty" — declarative claims that sound authoritative but are speculation dressed as observation.

Either way: **check the actual source before answering or asserting.** Use RDAP/WHOIS for domains, read files for config, query APIs for AWS/cloud resource state, look at the screenshot the user already provided. When you can't check, say "I don't know, here's what we can check" — never claim what you haven't verified.

**Why:** Will has pushed back four+ times across sessions:
- Domain expiration date — speculated instead of `curl`ing RDAP ("you don't need to speculate, heh").
- WHOIS privacy blocking a transfer — listed it as a likely cause when the user's screenshot already showed it green-checked.
- Dreamhost panel URL / Approve button — described from memory of docs rather than current observation; the button wasn't present.
- AWS SSM param existence after a `task tf-apply` — declared "the params don't exist yet anyway, tf-apply hasn't run" without running `aws ssm get-parameter`; the param had been created hours earlier. Will: *"how would you know? cuz you didn't even look"*.

The declarative-state mode is the more painful one because the assertion gets baked into recommendations ("run tf-apply first") that send the user down a wrong path.

**How to apply:**
- Before listing hypotheticals or generic troubleshooting steps, ask: can I look up the truth right now? If yes, do that first and answer from data.
- Before saying "X hasn't happened" / "Y doesn't exist" / "the script wasn't run", run the check (`aws ssm get-parameter`, `gh run list`, `git log`, `stat file`, etc.). If the check costs nothing and reveals truth, there's no excuse to skip it.
- When you can't check (offline, missing creds, etc.), say so explicitly: "I haven't verified; let me query" or "I don't know — here's what we can check." Never paper over the gap with a confident-sounding claim.
- Reserve checklists for cases where the state genuinely isn't observable.
