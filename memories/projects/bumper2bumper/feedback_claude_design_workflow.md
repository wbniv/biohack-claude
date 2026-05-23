---
name: Claude Design workflow — consult, export, commit
description: How to use claude.ai/design for SplitLedger design decisions and persist the output
type: feedback
originSessionId: 51994a6b-e56a-4593-8cfa-a358f58fef19
---
When a design question arises (undesigned breakpoint, new screen, UI decision), consult **SplitLedger on claude.ai/design**: <https://claude.ai/design/p/7c6cdc5c-27e8-4681-bdb3-4936f2443a2a?file=splitledger_v2> (project `7c6cdc5c-27e8-4681-bdb3-4936f2443a2a`, file `splitledger_v2`). Do not use Stitch; do not spawn an agent to write JSX manually.

The canvas already carries warm-fintech tokens (orange/teal, Geist/Fraunces, off-white) and the existing 7 mobile screens + 1 web dashboard. State the *new* requirement only — don't re-prime the aesthetic.

After Claude Design answers:
1. Download the zip from claude.ai/design.
2. Extract it into `docs/designs/redesign-YYYY-MM-DD-rN/` (date + round number from the canvas).
3. Add a **Design references** table at the top of the relevant plan doc pointing to the new path.
4. Update the plan with the design decision and cite the specific JSX file/function.

**Why:** Keeps design artifacts in the repo alongside the plans that reference them; makes decisions auditable and reproducible without relying on the cloud project staying live.

**How to apply:** Any plan that involves a UI decision consulted at claude.ai/design should have a Design references section. The zip goes in the repo before the plan is considered complete.

**Superseded 2026-05-03:** the design tool is now local Open Design at `~/SRC/open-design` (URL is ephemeral — `pnpm tools-dev status` prints it), not claude.ai/design. The export-to-`docs/designs/YYYY-MM-DD-rN/` discipline and the **Design references** plan table are unchanged. See `project_open_design_switch.md` for the switch details and the small workflow deltas (`rN` is now manually incremented; OD export formats are HTML/ZIP/PDF).
