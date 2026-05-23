---
description: Run one complete review-and-fix pass — comprehensive code review, then close every finding mechanically until the backlog is empty.
argument-hint: [scope hint — e.g. "since v1.2", "diff only", or omit for full sweep]
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

## TL;DR

> [!NOTE]
> **Drain any `[verify]`-marked TODOs from prior passes** (do the work,
> run plan verification, promote to `[x]`) → review pass → fix every
> finding (mechanical fixes land directly; design calls become new TODO
> entries) → update the resolution log. Use the latest pass doc in
> `docs/investigations/` as the format template. Terminate when a review
> pass surfaces nothing substantive.

---

## Context

You are running an end-to-end **review-and-fix pass** for the repo at the
current working directory. The user has opted out of driving the loop by
hand — you are the loop driver. Do not gate on user approval for mechanical
fixes; default is to fix and commit.

Argument from the user (may be empty): **$ARGUMENTS**

Repo state:

!`git rev-parse --show-toplevel && git status --short && git log --oneline -10`

Likely review-doc locations:

!`for d in docs/investigations docs/reviews reviews; do [ -d "$d" ] && ls "$d" | head -20; done; true`

Likely test command (use whatever the project actually uses — check
`Taskfile.yml`, `package.json` scripts, `Makefile`, `pyproject.toml`,
`cargo.toml`, etc.):

!`for f in Taskfile.yml taskfile.yml package.json Makefile pyproject.toml Cargo.toml composer.json go.mod; do [ -f "$f" ] && echo "$f"; done; true`

## Your job

Drive a full review-and-fix cycle to completion. The cycle has four
phases — drain, review, fix, log — and terminates when a review surfaces
nothing substantive.

---

### Phase 0 — Drain the approved queue

**Before reviewing recent changes, drain any carried-forward TODO items
the user has approved since the last pass.** The user signals approval
by changing `- [ ]` → `- [verify]` on a TODO line (matches the CLAUDE.md
convention: "I think this is ready; do the verification step now").

For every `[verify]` line in TODO.md whose body links to a
`docs/investigations/*-code-review-pass*.md` or `docs/plans/*.md`:

1. **Do the work the TODO describes.** This is the implementation step
   the original review filed as a design-decision deferral — the user
   has now picked the design (the `[verify]` flip IS the picking), so
   execute. Follow the project's existing patterns; commit when green.

2. **Verify.**
   - If the item links to a plan file with a `## Verification` section,
     run each numbered step exactly as written. Paste the raw command
     output in a code block below each step. Add PASS/FAIL. Write the
     output back to the plan file (per CLAUDE.md's plan-verification
     contract).
   - If no plan exists (the item links only to a review doc), verify
     via the project's natural gates: run the test suite + lints + any
     project-specific acceptance command from the Taskfile. The closing
     commit's message documents what was checked.

3. **Promote `[verify]` → `[x]`.** Move the entry to TODO.md's `## Done`
   section in reverse-chronological order with the one-line summary
   format the project uses. Commit the TODO edit alongside the work or
   as a follow-on commit.

4. **If the user marked `[verify]` on something with no plan AND no
   review-doc reference, or on something that's structurally not
   verifiable** (e.g. a design call where there's nothing to test):
   surface the mismatch to the user instead of forcing it through. Don't
   silently demote — let them see the ambiguity.

After every `[verify]` item is either resolved or surfaced, advance to
Phase 1. Phase 1 will then audit the changes Phase 0 just landed — which
is exactly the loop pattern that has caught regressions in prior passes
(TS-2, AR-2).

---

### Phase 1 — Review

1. **Determine scope.** If `$ARGUMENTS` names a commit/tag/range, review
   that. If it says "diff only" or similar, diff against the last review's
   HEAD. Otherwise: locate the most recent review document in the repo
   (likely `docs/investigations/*-code-review-pass*.md` — but match whatever
   convention the project uses). Extract its `HEAD:` hash. If no prior
   review exists, do a full-codebase sweep.

2. **Skip if nothing new.** If reviewing-since-last and
   `git log <last_head>..HEAD --oneline` returns fewer than 3 commits,
   write a one-line "no review needed: N commits since the last pass"
   note alongside the prior review and **stop the pass entirely** — there
   is nothing to do.

3. **Spawn parallel review agents.** Send 3-5 general-purpose agents in a
   single message (one tool-call block, multiple Agent uses) so they run
   concurrently. Each agent covers a different surface:
   - **Recent changes** — diff-focused, biased toward the day's churn.
   - **Per major language** — one agent per JS / Python / shell / config
     surface the project uses.
   - **Infrastructure** — CI, packaging, install scripts, security model.

   Brief each agent like a smart colleague who hasn't seen the
   conversation: state the goal, list specific surfaces to scrutinize,
   require **severity-ranked findings** (Critical/High/Medium/Low/Info)
   with `file:line` evidence and concrete fix sketches. Aim for 6-12
   findings per agent. Tell agents to report directly with findings —
   not to write to disk.

4. **Synthesize.** Write the findings into a single new review document
   following whatever format the most recent prior pass uses (typically:
   Executive Summary table → per-finding sections for High/Medium → brief
   one-liners for Low → items dismissed → recommended fix order →
   **carried-forward TODOs section** → resolution log placeholder). Name
   with the next sequential pass number in the project's convention.
   Commit the review doc as a single commit so the diff-from-prior-pass
   is preserved in history.

   **Carried-forward TODOs:** every review doc must include a section
   listing every currently-open TODO item (a `- [ ]` line in `TODO.md`)
   that was filed by an earlier review-and-fix pass — i.e., items whose
   body links to a `docs/investigations/*-code-review-pass*.md` file.
   These are the design-decision items the user hasn't yet acted on.
   Carrying them forward in EVERY review keeps them visible until the
   user resolves them; when the user marks the TODO `[x]`, it disappears
   from the next review's carry-forward section automatically. Source of
   truth is always `TODO.md` — grep for unchecked items that reference
   the review-doc dir. If none are open, say so explicitly ("Carry-
   forward backlog: empty — every deferred item from prior passes has
   been resolved").

---

### Phase 2 — Fix

5. **Mechanical findings (most Low + most Info, plus High/Medium that
   follow established patterns):** fix and commit directly. Use the
   project's existing patterns rather than introducing new ones. Each fix
   batch:
   - Groups thematically (one batch per file/system area).
   - Commits with the finding IDs in the message subject and body
     (`fix(L-3, L-5): …`).
   - **Strikethroughs each closed finding's row in the review doc's
     Executive Summary table as part of the same commit** —
     `**ID**` → `~~**ID**~~` and title → `~~title~~`. The strikethrough
     IS the live progress indicator; future readers (and the resolution
     log) trust it. Match the convention of pass-16 and earlier docs.
   - Verifies green: run the project's test/lint command after each batch
     and only commit if it passes. If tests fail before you started,
     **stop**, write a "pass blocked by pre-existing test failure" note,
     and commit nothing.

6. **Design-decision findings (High/Medium that require taste calls,
   architecture changes, new permissions, new dependencies, anything
   touching user-facing security or data semantics):** do NOT fix
   autonomously. File each as a TODO entry referencing the review doc
   and finding ID. Mark the finding in the review doc as "deferred —
   needs design decision". The user opted out of finding-by-finding
   approval but not out of architecture-level judgement calls.

7. **Structural opportunities.** If multiple findings share a root cause
   (drift between schema and consumers, duplicated logic across files,
   missing test coverage of a whole module), prefer **one architectural
   fix** that closes the cluster over patching each site. Document the
   collapse in the commit message — note which finding IDs the change
   closes at once. This is the move that prevents the same drift class
   from recurring next pass.

---

### Phase 3 — Log

8. **Resolution log.** When all findings are addressed (fixed or filed),
   amend the review doc with a `§N Resolution log` section: one table row
   per finding with ID, title, and the commit hash that closed it (or
   "deferred → TODO" for design-decision items). This is the future-self
   audit trail; without it, the next pass can't tell which findings have
   been historically closed.

   **Then mirror a single rollup entry into TODO.md's `## Done` section**
   following the project's existing convention. One line:
   `- [x] YYYY-MM-DD — Pass-N landing: …closed/deferred counts, structural
   changes if any, suite-size delta… [Review](docs/investigations/…).`
   The review doc holds the per-finding detail; TODO.md Done holds the
   per-pass rollup. Together they form a chronologically scannable index
   of every pass that's landed. Commit this as part of the same commit
   that adds the resolution log.

9. **Final test run.** Confirm the test suite is green at HEAD. Confirm
   any project-specific lints pass. If anything's red, fix it before
   declaring the pass complete — green-on-green is the contract.

10. **Summary report** to the user (one paragraph): commits-since-last,
    severity counts found this pass, count closed vs deferred,
    structural changes if any, suite size before/after.

11. **Surface the new TODO entries.** Below the summary, present an
    explicit list of every TODO entry added during this pass — the
    design-decision findings from step 6 that you filed instead of
    fixing. One bullet per item: finding ID, title, the TODO path it
    landed at, and (in one sentence) the judgement call being deferred.
    This is the user's queue: it's the only thing they need to act on
    from this pass, so don't bury it in the summary paragraph. If no
    TODOs were added, say so explicitly ("Nothing deferred — backlog
    fully closed").

12. **Loop.** Go back to Phase 1 step 1 with the new HEAD. The previous
    pass's fixes themselves could have introduced bugs (pass-17 → pass-18
    surfaced TS-2, a Critical regression I caused). The pass terminates
    cleanly only when:
      - Phase 1 step 2 fires ("fewer than 3 commits since the last pass")
        — meaning the fixes from this iteration are too small to warrant
        another full review, OR
      - The new review pass produces ZERO substantive findings (only
        Info-tier observations / confirmations, nothing severity-ranked
        Low or above).

    Do NOT terminate after one pass just because all findings were
    addressed — addressing findings IS what produces the next pass's
    input. The loop ends when the codebase stabilizes, not when the
    backlog empties for the first time.

---

## Discipline

- **Default is fix.** Don't gate Low/Info on user approval; the loop's
  point is the user is not driving.
- **Don't add features.** The pass closes findings, not "while I'm in
  here, let me also…". A finding is the unit of work.
- **Commit hygiene.** Small thematic commits, finding IDs in messages,
  green tests per batch. The commit log IS the audit trail.
- **No new findings without evidence.** Every severity-ranked claim
  needs `file:line` and a reproducible justification — same bar the
  user would hold the review to.
- **Trust the prior pass.** Findings that the most recent review marked
  closed (~~strikethrough~~ or in a Resolution log) are off-limits for
  re-litigation unless the evidence shows the fix didn't hold. Don't
  re-discover what's already resolved.
- **Stop conditions are real.** Phase 1 step 2 (nothing new) and the
  pre-existing-test-failure case in step 5 both abort the pass. Don't
  push through; report and stop.
