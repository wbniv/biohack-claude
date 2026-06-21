---
plugin: aws-cost-optimization
upstream: https://github.com/ahmedasmar/devops-claude-skills
state: kept-reference
tier: recommended
stars: 4
last-reviewed: 2026-06-21
last-upstream-commit: 1489c33ad8829a11219e423327d6b59f8339cee4
---

## What it does

AWS cost / FinOps workflows: discover waste (unattached EBS, idle Elastic IPs),
rightsize EC2/RDS, evaluate Spot, migrate to Graviton and newer instance
generations, compare Reserved Instances vs Savings Plans, set up Budgets, and run a
monthly cost review. One plugin (`aws-cost-optimization`) out of a 6-plugin upstream
marketplace — referenced here via `git-subdir` so only that subdir is installed.

## Notes

- ✓ Genuinely *complements* my `aws-billing-tags` skill rather than duplicating it:
  mine sets up tagging + budgets + Cost Explorer; this drives the ongoing optimization
  loop (discover → rightsize → commit → monitor) on top of that foundation.
- ✓ Matches my conventions out of the box — Graviton-first, generation upgrades,
  tag-based cost allocation, monthly reviews. Concrete `aws ce` / `aws compute-optimizer`
  CLI recipes, not hand-waving.
- ✗ **No LICENSE file** — all-rights-reserved by default. Safe to reference (install
  pulls from the author's repo; I redistribute nothing), but this can **never** become
  a `kept-fork`: I can't legally copy or modify the code. Hard ceiling on the relationship.
- ✗ Tagging/Budgets guidance overlaps the setup half of my `aws-billing-tags`; use this
  for the optimization half only, or the two will give parallel advice.

## My modifications

None, and none are *permitted* (no license). `source: git-subdir`, path
`aws-cost-optimization`, pinned `sha`.

## Re-review trigger

If upstream adds an OSI license (unblocks fork), or at my next quarterly AWS cost review.
