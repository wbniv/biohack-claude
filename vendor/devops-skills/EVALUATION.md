---
plugin: devops-skills
upstream: https://github.com/lgbarn/devops-skills
state: kept-fork
tier: recommended
stars: 4
last-reviewed: 2026-06-21
last-upstream-commit: 8a37cc3fe5983e7fa2b2dcaa98c94449d5356f06
fork: https://github.com/wbniv/devops-skills
pr: https://github.com/lgbarn/devops-skills/pull/1
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
- ✗ **Upstream doesn't install as-is** (the reason this is a fork, not a reference): its
  `.claude-plugin/plugin.json` ships `homepage: ""` (and `repository: ""`), which Claude
  Code 2.1.185 rejects at install — `homepage: Invalid URL`. Fixed in my fork; PR'd upstream.
- ✗ Being a `superpowers` fork, it overlaps the `superpowers` plugin I already have from
  `claude-plugins-official` (currently disabled); the net-new value is the Terraform/AWS
  safety layer, not the inherited methodology skills.

## My modifications

Forked to [`wbniv/devops-skills`](https://github.com/wbniv/devops-skills) and set the
empty `homepage`/`repository` to the repo URL (fork commit `482bd9c`) so it installs.
Opened [lgbarn/devops-skills#1](https://github.com/lgbarn/devops-skills/pull/1) upstream
with the same two-line fix. The marketplace entry references the fork (`github` source,
pinned to `482bd9c`) until the PR lands — install verified against it.

## Re-review trigger

When the upstream PR merges: re-point the marketplace entry at `lgbarn/devops-skills`,
flip this back to `kept-reference`, and retire the fork. If the PR stalls, leave as-is.
