---
plugin: devops-skills
upstream: https://github.com/lgbarn/devops-skills
state: evaluating
tier: recommended
stars: 4
last-reviewed: 2026-06-21
last-upstream-commit: 8a37cc3fe5983e7fa2b2dcaa98c94449d5356f06
---

## What it does

A fork of [`superpowers`](https://github.com/obra/superpowers) (Jesse Vincent) that
keeps the original methodology skills — TDD, systematic-debugging, writing/executing
plans, git-worktrees, code-review, verification-before-completion — and adds an
infrastructure layer: `terraform-plan-review`, `terraform-drift-detection`,
`terraform-state-operations`, `aws-profile-management`, safety hooks that block
`terraform apply`/`destroy`/`-auto-approve`, plus `/plan` `/drift` `/review-infra`
commands. MIT-licensed.

## Notes

- ✓ The closest fit of any candidate to how I already work — "never auto-apply",
  plan-first, worktrees, verification-before-completion, 3-strikes debugging. It reads
  like someone codified my CLAUDE.md and bolted Terraform safety onto it.
- ✓ MIT — unlike ahmedasmar's, this one *can* be forked and modified.
- ✗ **Does not install as-is.** Its `.claude-plugin/plugin.json` ships `homepage: ""`,
  which Claude Code 2.1.185 rejects at install time: `homepage: Invalid URL`. Verified
  against the pinned sha. This is the blocker on promoting it to `kept-reference`.
- ✗ Being a `superpowers` fork, it overlaps the `superpowers` plugin I already have from
  `claude-plugins-official` (currently disabled); the net-new value is the Terraform/AWS
  safety layer, not the inherited methodology skills.

## My modifications

None yet. The fix is trivial (drop the empty `homepage`, or set a real URL). Decision
pending: **kept-fork** — fork `wbniv/devops-skills`, apply the one-line fix, reference
the fork, and open an upstream PR to lgbarn — **vs. reject** over a broken manifest.
Holding as `evaluating` (not in `marketplace.json`) until that call is made.

## Re-review trigger

When the `homepage` defect is resolved — whether by an upstream fix/PR merge or by
forking — re-test install and promote to `kept-reference` (or `kept-fork`).
