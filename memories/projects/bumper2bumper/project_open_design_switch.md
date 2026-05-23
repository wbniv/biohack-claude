---
name: SplitLedger design tooling switched to Open Design (2026-05-03)
description: As of 2026-05-03, new UI work goes through local Open Design instead of cloud claude.ai/design — same export discipline, different source
type: project
originSessionId: 11d5d0e4-4efa-48be-a468-40eb56d4cd62
---
On 2026-05-03 the SplitLedger design tooling switched from cloud claude.ai/design to local **Open Design** ([nexu-io/open-design](https://github.com/nexu-io/open-design), Apache-2.0), installed at `~/SRC/open-design` and started with `pnpm tools-dev run web` (Node 24 via fnm). OD drives Claude Code on PATH as its design agent.

**Live URLs are ephemeral.** `tools-dev` binds daemon + web to OS-assigned ports that change every boot — discover them with `cd ~/SRC/open-design && pnpm tools-dev status` (or read `.tmp/tools-dev/default/logs/{daemon,web}/latest.log`). The QUICKSTART's `:5175` (web) and `:7457` (daemon) are CLI defaults for `od` standalone, not what `tools-dev` uses. (Initial CLAUDE.md/memory edits on 2026-05-03 incorrectly hardcoded those ports; corrected 2026-05-04.)

**Why:** Local-first ownership; remove the cloud dependency; OD wraps the same artifact-first design loop without locking the project to a single hosted canvas.

**How to apply:**
- New UI decisions, new screens, design refinements: pose to OD, don't open claude.ai/design.
- Aesthetic choice (orange/teal warm fintech, Geist/Fraunces, off-white background) is unchanged — see `project_redesign_direction.md` for the original 2026-04-25 decision.
- Export discipline is unchanged: extract to `docs/designs/redesign-YYYY-MM-DD-rN/`, commit alongside the plan, add **Design references** table to the plan. See `feedback_claude_design_workflow.md` for the original workflow steps; the only differences are (a) source is OD's web UI not claude.ai/design, (b) `rN` is now manually incremented (OD has no canvas-round concept), (c) export format may be HTML/ZIP/PDF from OD instead of just zip.
- Priming: OD has no shared cloud canvas — each OD project is a fresh local sandbox. Prime warm-fintech tokens + the existing 7 mobile + 1 web baseline (`docs/designs/redesign-2026-04-25/`) on the first prompt of any new OD project.
- Historical artifacts under `docs/designs/redesign-2026-04-2X-rN/` (rounds r10–r12) came from claude.ai/design. Don't rewrite them; new rounds continue the `rN` numbering.
- The CLAUDE.md "New UI decisions" subsection has been updated in-place to point at OD; the older claude.ai/design URL is no longer there.
