---
name: SplitLedger redesign aesthetic — Claude Design "warm fintech"
description: The chosen visual direction for SplitLedger is the orange/teal Claude Design output, not the cool grey Stitch direction
type: project
originSessionId: 47825233-5074-4be9-84bc-31c52ada7d4e
---
After comparing two parallel design tracks on 2026-04-25, the user chose **Claude Design's "warm Splitwise reimagined" direction** as the canonical aesthetic for the SplitLedger redesign. The Stitch "quiet premium" navy/grey direction was rejected.

**Why:** User enthusiastically endorsed the Claude Design output ("looks fantastic!") after reviewing the runnable HTML preview. The warm orange/teal palette + Geist/Fraunces typography + sparkline-rich dashboard cards landed better than the restrained Inter-only navy/grey approach.

**How to apply:**
- Source of truth: `docs/designs/redesign-2026-04-25/` (full handoff: tokens.css, primitives.jsx, screens-1/2/web.jsx, README.md, runnable HTML preview).
- Primary `#f25e0b` (orange-500), secondary `#0e8e6a` (teal-500). Status semantics: teal = "owes you" (positive), orange-dark = "you owe" (urgent — explicitly NOT red, to avoid alarming friend debts).
- Typography: Geist (UI) + Fraunces (display, serif) + Geist Mono (tabular money). Both OFL-licensed.
- Background `#fbf8f1` warm off-white. NOT the `#F4F6F7` cool grey from the Stitch direction.
- 7 mobile screens (390×844) + 1 web dashboard (1280×820) are spec'd. Confirmation flow UI + Payment/Exchange/Adjustment forms are NOT yet designed — flagged as follow-ups.
- Component → Flutter widget mapping is in the handoff README's "Components to extract" table. Use those names (`SLAvatar`, `SLPill`, `SLBottomNav`, `SLMoneyText`, `SLSparkline`, etc.) when porting.
- The Stitch outputs in `docs/designs/legacy-stitch/` (relocated from `docs/plans/stitch-screens/` on 2026-05-06) are obsolete artifacts — keep for history but don't reference for the implementation.
- When new screens or design decisions are needed, use **https://claude.ai/design** (not Stitch). Paste the design brief there; output gets saved back into `docs/designs/redesign-2026-04-25/` as a new JSX function. **Superseded 2026-05-03:** new UI work now goes through local Open Design at `~/SRC/open-design` (URL ephemeral; run `pnpm tools-dev status` to print it) — see `project_open_design_switch.md`. The aesthetic choice (orange/teal, Geist/Fraunces, off-white) is unchanged.
