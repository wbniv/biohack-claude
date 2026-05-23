---
name: Manual testing checklist lives at docs/manual-testing.md
description: Where device-only / human-eyes test items get parked when neither of us can verify them right now
type: reference
originSessionId: 6f71888f-0f6f-4f9f-8152-5748d2151594
---
`docs/manual-testing.md` is the catch-all for verification work that
can't run as `dart test` / `flutter test` — iPad share-sheet anchoring,
Android deep-link verification, balances-stale class watch list, etc.

Use it when:
- Shipping behavior we can't exercise from this dev box (no iPad, no
  signed Android build, no real iCloud account, etc.).
- A class of bug has recurred and we want a pre-flight checklist for
  related changes.
- A plan defers verification until later; park the verification items
  here so they don't get lost.

Format: status-legend checklist (`[ ]` `[~]` `[x]` `[!]`). Group items
under a feature heading; mark verified ones with date + platform.
