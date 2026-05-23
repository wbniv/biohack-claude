---
name: CLI-only is fine for rare reverse-flow operations
description: For infrequent, deliberate operations that reverse a forward flow (decommission restore, undo-style commands), CLI-only is an acceptable surface — don't build TUI affordances just because the forward flow has them.
type: feedback
originSessionId: ae41ac14-aef4-4a0c-a7a4-048be5e9986c
---
For infrequent, deliberate operations that reverse a forward flow (e.g.
restoring a decommissioned cobrand), CLI-only is an acceptable user
surface. Don't assume TUI parity is required just because the forward
flow (publish) has a TUI affordance.

**Why:** user explicitly said "CLI-only is acceptable" when asked about
restoring decommissioned cobrands, adding "talk about a process that
nearly never happens!" — rarity is the explicit justification.
Decommissioned cobrands today are invisible in the TUI (not shown in
any tab's filters), and restoration goes through
`./cobrand.py publish <slug>` which already accepts `decommissioned`
as a valid source status. User accepted this gap rather than asking
for a new tab or expanded filter.

**How to apply:** when proposing follow-up work for rare reverse-flow
commands (un-decommission, un-publish, un-brainstorm etc.), default to
CLI-first. Don't preemptively offer TUI integrations unless the user
signals they'd use it. Applies to this repo's cobrand pipeline; generalises
to other "one-way-mostly" workflows where the reverse is an exception
path.
