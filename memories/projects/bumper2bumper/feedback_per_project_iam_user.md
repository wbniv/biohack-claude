---
name: Per-project Terraform IAM user convention
description: Each project gets its own `{abbr}-terraform` IAM user (e.g. `sl-terraform` for SplitLedger); never reuse a shared `terraform` user across projects.
type: feedback
originSessionId: 5243d3ca-8596-41e8-9c68-081d7d9e34db
---
For each new project that uses AWS Terraform, create a dedicated
`{abbr}-terraform` IAM user using a short project abbreviation
(e.g. `sl-terraform` for SplitLedger), not the full project name.

**Why:** blast-radius isolation per project. If one project's TF state or
laptop credentials leak, other projects' AWS resources aren't exposed.
Per-project users also make billing/usage attribution easier. Short
abbreviations keep `~/.aws/credentials` profile names compact.

**How to apply:**
- When provisioning AWS infra for a new project, create the IAM user first.
  Note: the existing shared `terraform` user typically does NOT have
  `iam:CreateUser` (intentionally — privilege-escalation prevention), so
  bootstrap from an admin profile or the AWS console.
- Attach `AdministratorAccess` (simplest) or a tightly-scoped policy.
- Generate access keys and store them under
  `~/.aws/credentials` as `[{abbr}-terraform]`, with a matching
  `[profile {abbr}-terraform]` block in `~/.aws/config`.
- The Terraform module should accept an `aws_profile` variable (default
  `{abbr}-terraform`) so `terraform plan/apply` doesn't require
  `AWS_PROFILE=...` env override.
