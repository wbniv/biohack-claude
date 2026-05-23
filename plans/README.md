# plans/ — Curated plan exemplars (reference only)

Plans are how Will thinks through non-trivial changes before touching code —
see the plan-first workflow in [CLAUDE.md](https://github.com/wbniv/SRC/blob/main/CLAUDE.md).

The `~/.claude/plans/` and `~/SRC/*/docs/plans/` directories hold hundreds of plans,
many half-formed or abandoned. The ones published here are **hand-picked exemplars**
that illustrate the workflow well.

**Claude Code does not auto-load plans from third-party repos.**
Like memories: copy to your own machine if useful; don't expect them to auto-apply.

## What makes a plan worth publishing here

- Demonstrates the plan-first workflow end-to-end (context → design → verification)
- Shows how to scope a non-trivial multi-file or multi-repo change
- Illustrates a pattern that recurs (infra setup, skill migration, plugin design)
- The verification section has real output (PASS/FAIL evidence, not blanks)

## Adding a plan

1. Copy the plan file here from wherever it lives locally.
2. Prepend a short exemplar note inside the plan (after the title):
   > *Exemplar: shows how to scope a Claude marketplace bootstrap from scratch.*
3. Commit. No automation — curation is intentional.

## sync-from-claude.sh does NOT touch this directory.
