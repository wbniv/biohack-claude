---
name: Balances-stale bugs are a class, not instances — fix the contract
description: When the user reports "Balances didn't refresh after X", audit BOTH client-mutation BLoCs AND server-event surfaces (push, lifecycle, future WebSocket). Add a regression test for the contract.
type: feedback
originSessionId: 0037487c-4f0a-4501-9c80-54d0c6ffcc76
---
When the user reports that the Balances tab is stale after some event
(create transaction, confirm transaction, other party confirmed, app
resumed from background, etc.), do **not** just add a `HomeRefresh`
dispatch on that single path and call it done.

**Why:** This same bug class has been reported four times as of 2026-04-26.
Each previous fix closed exactly the path the user complained about and
missed an adjacent one. The user is visibly frustrated with the
recurrence. The 2026-04-26 audit (`docs/investigations/2026-04-26-balances-stale-second-class.md`)
discovered that "balance-affecting event" has TWO sub-classes; the
original plan only modeled the first.

**How to apply:** When you see this kind of report, audit BOTH dimensions:

### Dimension 1 — Client mutations (what the user just did)

1. Audit *every* BLoC that performs a write — `TransactionBloc`,
   `TransactionDetailBloc`, `ContactBloc`, `RecurringBloc`, `TripBloc`,
   `SettingsBloc`, anything new — against `mutationRefreshListeners()` in
   `lib/app/mutation_refresh.dart`. Anything that can cause
   `BalanceService.summary` to return different data must end in a
   `HomeRefresh` event.
2. The architectural contract is: **balance-affecting mutations dispatch
   `HomeRefresh` via the app-level listener.** Mutations that bypass that
   listener (e.g. page-scoped blocs whose state never reaches the app shell)
   are the bug.
3. Be skeptical of "the existing listener handles it" — verify the listener
   can actually observe the bloc that emits the state. Page-scoped
   `BlocProvider`s are invisible to listeners above the route.

### Dimension 2 — Server-driven events (what changed while the user wasn't looking)

The server can flip a balance without any client mutation: the OTHER
party confirmed, recurring auto-accept fired, late-rate fill landed.
The client only learns via push or by reloading on resume. Audit:

1. **`PushService._messageSub` (foreground push)** — must call
   `_onForegroundMessage`, which must end up calling
   `refreshAfterServerEvent(home, notif, settings)`.
2. **`PushService._handleTap` (push tap from background)** — must fire
   the activity callback before navigating, same path as foreground.
3. **`_AppState.didChangeAppLifecycleState` (lifecycle resume)** — must
   call `_refreshAfterServerSideEvent()`, not just refresh the badge.
4. **Any future server-streaming surface** (WebSocket subscription,
   long-poll, server-sent events) — must route through
   `refreshAfterServerEvent` from its event handler.

`refreshAfterServerEvent` is the bloc-explicit twin of
`refreshAfterMutation` — used by triggers that don't have a live
`BuildContext` (push handler, lifecycle observer).

### Always add a contract test

Table-driven widget test in `test/presentation/app_refresh_listener_test.dart`
that emits each mutation state AND each server-event call site, and
asserts `HomeRefresh` was dispatched. The test is split into two groups:
`mutationRefreshListeners contract` (Dimension 1) and
`refreshAfterServerEvent (push / lifecycle path)` (Dimension 2). Add a
case to the matching group whenever you wire a new event source. Without
the test, the next added pathway will silently re-introduce the bug.
