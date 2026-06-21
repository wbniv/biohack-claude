---
plugin: cc-devops-skills
upstream: https://github.com/akin-ozer/cc-devops-skills
state: kept-reference
tier: recommended
stars: 4
last-reviewed: 2026-06-21
last-upstream-commit: feaf2b2f3c9544aa559836731cc80e363183f788
---

## What it does

A broad DevOps skill pack — 31 skills paired as 16 generators + 14 validators + 1
k8s debugger — scaffolding and linting production configs for Terraform, Terragrunt,
Ansible, Dockerfiles, Helm, GitHub Actions, GitLab CI, Jenkins, Azure Pipelines,
Kubernetes YAML, Makefiles, and the Loki/Prometheus (LogQL/PromQL) observability
stack. Referenced into this marketplace under the name `cc-devops-skills` (upstream
names the plugin `devops-skills`, which collides with lgbarn's — see that eval).

## Notes

- ✓ The generator↔validator pairing is the strong idea: scaffold *and* check, so speed
  doesn't skip correctness. Reputable (Apache-2.0, listed in Awesome Claude Code, ~236★).
- ✓ `terraform-generator`/`-validator` and `terragrunt-*` are directly usable alongside
  my own infra work; `dockerfile-*` and `github-actions-*` are general-purpose wins.
- ✗ Breadth dilutes relevance for *my* stack — Azure Pipelines, Jenkins, GitLab CI,
  Helm, Fluent Bit, Loki are dead weight for an AWS+Cloudflare+Debian shop. I'd use
  maybe a third of the 31.
- ✗ Generic by design — none of it knows my conventions (SSM secrets, per-project IAM,
  Graviton-first, Terraform-module-per-role). Good scaffolding, not opinionated like mine.

## My modifications

None — kept as an upstream reference (`source: git-subdir`, path `devops-skills-plugin`,
pinned `sha`). Install pulls from akin-ozer's repo directly.

## Re-review trigger

If I start using Kubernetes / GitLab / Jenkins seriously, promote relevant skills to
"essential". Otherwise re-pin the `sha` on the next major upstream release.
