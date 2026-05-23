---
name: Keep deferred-work audit updated as you work
description: Standing instruction — when shipping any work tracked in 2026-04-26-deferred-work-audit.md, strike the corresponding row in the same conversation, with commit hash + brief shipped-summary. Don't wait to be asked.
type: feedback
originSessionId: 8eeaac3f-7f9c-419f-8241-045ae88f52e6
---
When working on anything tracked in `docs/investigations/2026-04-26-deferred-work-audit.md` — strike the corresponding row(s) immediately as work ships. Don't wait for a separate "now update the audit" instruction.

**Why:** User has reminded twice ("keep audit updated as you work" + an earlier verbatim repeat). The audit is the single index of in-flight deferred work; if it goes stale during a session, the next conversation can't tell what's actually open.

**How to apply:**
- After any commit that closes (or partially closes) an audit-tracked item, edit the audit doc in the same turn.
- Look at: the TL;DR table near the top, the Tier 1–5 implementation-order list, the headline-findings paragraphs, and the three sub-tables (cross-cutting blockers / stuck / floating follow-ups). An item often appears in multiple of these — strike all references.
- Strike syntax used in this doc: `~~old text~~` plus a `**Phase N shipped 2026-04-26** (commit \`abc1234\`)` annotation, or `**— Phase N ready to ship 2026-04-26**` if not yet committed.
- For multi-phase plans (e.g. slice 4b, slice 9b), strike each phase as it ships and add "**All N phases shipped; slice-X fully drained.**" once the last one closes.
- Periodically scan recent `git log` for ships that other (parallel) workers landed without updating the audit — those count too.
- Commit the audit edit separately or fold into the work commit; either is acceptable, but don't leave it dirty across context boundaries.
