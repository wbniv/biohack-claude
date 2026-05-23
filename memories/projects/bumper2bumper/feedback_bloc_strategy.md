---
name: Flutter: writes must go through BLoC events
description: In the SplitLedger Flutter app, every server-mutating API call must be dispatched as a bloc event. No direct Injection.apiClient.* calls from widgets.
type: feedback
originSessionId: 1dc95c9f-26ca-40a4-95a2-0d4fe883dbcd
---
In this codebase, all writes (any call that changes server state — propose, delete, cancel, confirm, upload, etc.) MUST be modeled as bloc events. Never call `Injection.apiClient.instance.<endpoint>.<method>` directly from a widget for a mutation.

**Why:** The user explicitly asked for this. Historical bug: the transaction list rendered stale data after a detail-page delete because the mutation bypassed the bloc and there was a race between Navigator.pop and a follow-up LoadList dispatch. Going through the bloc makes the post-mutation state (fresh list) authoritative by construction and eliminates pop/refresh races. It also makes the widgets testable.

**How to apply:**
- For any new feature with a write path, add an event + handler on the relevant bloc. The handler should perform the mutation and emit the fresh state (e.g. `TransactionLoaded` with refreshed list) as the terminal state, not rely on a follow-up LoadList dispatch.
- Success-signal states (TransactionCreated/Updated/etc.) should extend the Loaded state and carry the refreshed data, so BlocBuilders that key off `is TransactionLoaded` keep working and pages that listen for the signal can still pop on success.
- Reads that are shared across pages or that mutations need to invalidate should also live in a bloc (e.g. per-transaction splits/confirmations/attachments — use a TransactionDetailBloc, not ad-hoc `_loadData()` inside StatefulWidget).
- One-off pure queries (e.g. an exchange-rate lookup that populates a form field without persisting) are fine to call directly — they're not state mutations.
- Local UI preferences (sort mode, filter selections on a single page) can stay as StatefulWidget local state — but if they need to persist or be tested, promote them to the relevant bloc.
