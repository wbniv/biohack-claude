---
name: iam-bootstrap
description: Use this skill when setting up AWS IAM credentials for a new project — creating the per-project Terraform IAM user, bootstrapping state backend, and self-narrowing permissions so the user never has to touch the AWS console again after the one-time setup. Trigger phrases: "set up AWS credentials", "bootstrap IAM", "create terraform user", "set up IAM for this project", "new project AWS setup".
version: 1.2.0
---

# Self-Narrowing Terraform IAM Bootstrap

Sets up a `<project>-terraform` IAM user that starts with broad permissions, then uses Terraform to narrow its own privileges — so all future permission changes are pure `terraform apply`, never a console click.

## When to use

A new project needs its own AWS Terraform credentials and doesn't have them yet. This is always a per-project user — never share a `terraform` user across projects.

## What you need from the user (ask upfront, all at once)

Before doing anything else, collect:

1. **Project slug** — the short kebab-case name used as a resource prefix (e.g. `gustos-colores`, `finding-your-way`, `my-app`). All AWS resources for this project must be prefixed `<slug>-*`.
2. **Primary AWS region** — e.g. `ap-south-1`, `us-east-1`.
3. **AWS account ID** — 12-digit number. If unknown, offer to detect it after Phase A with `aws sts get-caller-identity`.
4. **Environment** — default environment tag for this project's resources (e.g. `prod`, `staging`, `dev`). Most projects start with `prod`.

If the project already has `infrastructure/aws/bootstrap/` or `infrastructure/aws/iam-self/`, read those files before proceeding — don't overwrite existing work.

---

## Phase A — One manual step (human only, ~3 min)

**This is the only thing the user does manually.** Everything after is automated.

Tell the user:

> Please do these steps in the AWS console — this is the only manual part:
>
> 1. **Create the IAM user** → https://us-east-1.console.aws.amazon.com/iam/home#/users/create
>    - Name: `<project>-terraform`
>    - No console access
>
> 2. **Attach two managed policies** on the "Set permissions" screen:
>    - Select **"Attach policies directly"** (not "Add user to group")
>    - Filter by Type → **AWS managed - job function**
>    - Search `AdministratorAccess` → check it
>    - Search `ReadOnlyAccess` → check it (also in "AWS managed - job function" — no filter switch needed)
>    - Click the **"Policies selected" tab** to confirm both are checked
>    - Next → Create user
>
> 3. **Create an access key** for the user:
>    - Navigate to the user → Security credentials → Create access key
>    - Use case: **CLI** → acknowledge the prompt
>    - Description tag: `<project>-terraform-<your-hostname>`
>    - Copy both values immediately (secret shown once). Add to `~/.aws/credentials`:
>      ```ini
>      [<project>-terraform]
>      aws_access_key_id = AKIA...
>      aws_secret_access_key = ...
>      ```
>    - Add to `~/.aws/config`:
>      ```ini
>      [profile <project>-terraform]
>      region = <region>
>      output = json
>      ```
>
> 4. Confirm it works: `AWS_PROFILE=<project>-terraform aws sts get-caller-identity`
>
> 5. **Activate cost allocation tags** (do it now — tags only appear in Cost Explorer once activated; activation takes up to 24 h to propagate):
>    → https://us-east-1.console.aws.amazon.com/billing/home#/tags
>    - Find `Project` → **Activate**
>    - Find `ManagedBy` → **Activate**
>    - Find `Environment` → **Activate**
>    _(Tags only appear in this list after at least one tagged resource exists. If they're not listed yet, come back after Phase B/C completes and activate them then — don't skip this step.)_
>
> Tell me when this is done.

Wait for confirmation before proceeding.

---

## Phase B — Bootstrap state backend

**Use the shared template** — copy and substitute rather than writing from scratch:

```bash
mkdir -p infrastructure/aws/bootstrap
cp ../python-tui-lib/templates/flutter-cloud/infrastructure/aws/bootstrap/main.tf \
   infrastructure/aws/bootstrap/main.tf
sed -i 's/__PROJECT__/<project>/g' infrastructure/aws/bootstrap/main.tf
```

Then open the file, set `state_region` default to `<region>` and `aws_profile` default to `<project>-terraform`.

Apply via `tf-safe-apply.sh` (handles lock diagnosis, auto-init, stale DynamoDB digest repair):

```bash
../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/bootstrap init
../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/bootstrap apply -auto-approve
```

**Add an `aws-bootstrap` task to the Taskfile** that codifies the full flow — profile setup + bootstrap Terraform — so future machines only need `task aws-bootstrap`. Model it on this pattern:

```yaml
aws-bootstrap:
  desc: "One-time: create <project>-terraform IAM profile locally and bootstrap S3/DynamoDB state backend."
  cmds:
    - |
      set -euo pipefail

      read_masked() {
        local prompt="$1" result="" char
        printf "%s" "$prompt" >/dev/tty
        while IFS= read -r -s -n1 char </dev/tty; do
          if [[ -z "$char" ]]; then break
          elif [[ "$char" == $'\x7f' || "$char" == $'\b' ]]; then
            [[ -n "$result" ]] && { result="${result%?}"; printf "\b \b" >/dev/tty; }
          else
            result+="$char"; printf "*" >/dev/tty
          fi
        done
        printf "\n" >/dev/tty
        printf "%s" "$result"
      }

      PROFILE="<project>-terraform"
      CREDS=~/.aws/credentials
      CONFIG=~/.aws/config

      if aws sts get-caller-identity --profile "$PROFILE" &>/dev/null; then
        echo "✓ AWS profile ${PROFILE} already configured — skipping key entry."
      else
        echo ""
        echo "━━━ Phase A: Create the IAM user (one manual step, ~3 min) ━━━"
        echo ""
        echo "1. Create the IAM user:"
        echo "   https://us-east-1.console.aws.amazon.com/iam/home#/users/create"
        echo "   Name: <project>-terraform  |  No console access"
        echo ""
        echo "2. Attach policies on 'Set permissions' → 'Attach policies directly':"
        echo "   Filter by Type: AWS managed - job function"
        echo "   Search and check: AdministratorAccess"
        echo "   Search and check: ReadOnlyAccess"
        echo "   (both in same category — no filter switch needed)"
        echo "   Click 'Policies selected' tab to verify both are checked, then create."
        echo ""
        echo "3. Security credentials → Create access key → CLI → Description: <project>-terraform-$(hostname)"
        echo ""
        printf "Paste Access Key ID:     " >/dev/tty
        read -r KEY_ID </dev/tty
        KEY_SECRET=$(read_masked "Paste Secret Access Key: ")

        grep -q "^\[<project>-terraform\]" "$CREDS" 2>/dev/null \
          || printf "\n[<project>-terraform]\naws_access_key_id = %s\naws_secret_access_key = %s\n" \
               "$KEY_ID" "$KEY_SECRET" >> "$CREDS"
        grep -q "^\[profile <project>-terraform\]" "$CONFIG" 2>/dev/null \
          || printf "\n[profile <project>-terraform]\nregion = <region>\noutput = json\n" >> "$CONFIG"
        echo "✓ Profile written."
      fi

      echo ""
      echo "Verifying profile…"
      aws sts get-caller-identity --profile "$PROFILE"

      if aws s3api head-bucket --bucket <project>-terraform-state --profile "$PROFILE" &>/dev/null; then
        echo "✓ State backend already exists — skipping bootstrap Terraform."
      else
        echo ""
        echo "━━━ Phase B: Bootstrap Terraform state backend ━━━"
        ../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/bootstrap init
        ../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/bootstrap apply -auto-approve
        echo "✓ State bucket and lock table created."
      fi

      echo ""
      echo "━━━ AWS bootstrap complete. ━━━"
      echo ""
      echo "Activate cost allocation tags (once, after first tagged resource exists):"
      echo "  https://us-east-1.console.aws.amazon.com/billing/home#/tags"
      echo "  → Activate: Project, ManagedBy, Environment"
```

---

## Phase C — Self-narrowing IAM (`infrastructure/aws/iam-self/`)

Create four files. This directory's only job is managing the project's own IAM user.

**`backend.tf`:**
```hcl
terraform {
  backend "s3" {
    bucket         = "<project>-terraform-state"
    key            = "iam-self/terraform.tfstate"
    region         = "<region>"
    profile        = "<project>-terraform"
    use_lockfile   = true
    encrypt        = true
  }
}
```

**`providers.tf`:**
```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  profile = "<project>-terraform"
  region  = "<region>"
  default_tags {
    tags = {
      Project     = "<project>"
      ManagedBy   = "Terraform"
      Environment = "<environment>"
    }
  }
}
```

**`data.tf`:**
```hcl
data "aws_caller_identity" "current" {}

data "aws_iam_user" "self" {
  user_name = "<project>-terraform"
}
```

**`policy.tf`** — the load-bearing file; widen this when Terraform needs new permissions:
```hcl
resource "aws_iam_policy" "scoped" {
  name        = "<project>-terraform-scoped"
  description = "Scoped permissions for <project>-terraform. Widen here, never in the console."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3FullProjectScope"
        Effect = "Allow"
        Action = ["s3:*"]
        Resource = [
          "arn:aws:s3:::<project>-*",
          "arn:aws:s3:::<project>-*/*"
        ]
      },
      {
        Sid    = "DynamoDBFullProjectScope"
        Effect = "Allow"
        Action = ["dynamodb:*"]
        Resource = "arn:aws:dynamodb:*:${data.aws_caller_identity.current.account_id}:table/<project>-*"
      },
      {
        Sid    = "IAMProjectScope"
        Effect = "Allow"
        Action = ["iam:*"]
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/<project>-*",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/<project>-*",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        ]
      },
      {
        Sid    = "IAMSelfManagement"
        Effect = "Allow"
        Action = [
          "iam:AttachUserPolicy",
          "iam:DetachUserPolicy",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion",
          "iam:ListPolicyVersions",
          "iam:TagUser",
          "iam:UntagUser"
        ]
        Resource = [
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/<project>-terraform",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/<project>-terraform-scoped"
        ]
      },
      {
        Sid      = "ReadAll"
        Effect   = "Allow"
        Action   = ["*:Get*", "*:Describe*", "*:List*"]
        Resource = "*"
      },
      {
        Sid      = "STSCallerIdentity"
        Effect   = "Allow"
        Action   = ["sts:GetCallerIdentity"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "scoped" {
  user       = data.aws_iam_user.self.user_name
  policy_arn = aws_iam_policy.scoped.arn
}
```

Apply via `tf-safe-apply.sh`:

```bash
../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/iam-self init
../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/iam-self apply -auto-approve
```

At this point the user has three policies: `AdministratorAccess` + `ReadOnlyAccess` + `<project>-terraform-scoped`. No regression yet — still has full power.

---

## Phase D — Verify + detach the broad policies

**Verify** the scoped policy alone is sufficient:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::<account_id>:user/<project>-terraform \
  --action-names s3:CreateBucket s3:PutObject dynamodb:CreateTable iam:CreateRole sts:GetCallerIdentity \
  --resource-arns \
    "arn:aws:s3:::<project>-terraform-state" \
    "arn:aws:s3:::<project>-terraform-state/iam-self/terraform.tfstate" \
    "arn:aws:dynamodb:<region>:<account_id>:table/<project>-terraform-locks" \
    "arn:aws:iam::<account_id>:role/<project>-example" \
    "*"
```

All results should be `EvalDecision: allowed`. If any are `implicitDeny`: widen `policy.tf`, re-apply, re-simulate.

**Detach** Admin and ReadOnly by importing their attachments into TF state (so TF can remove them), then applying with no corresponding resource blocks:

```bash
cd infrastructure/aws/iam-self

terraform import \
  aws_iam_user_policy_attachment.admin \
  '<project>-terraform/arn:aws:iam::aws:policy/AdministratorAccess'

terraform import \
  aws_iam_user_policy_attachment.readonly \
  '<project>-terraform/arn:aws:iam::aws:policy/ReadOnlyAccess'

# Do NOT add resource blocks for these — TF will detach them on next apply.
../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/iam-self apply -auto-approve
```

**Confirm end state:**
```bash
AWS_PROFILE=<project>-terraform aws iam list-attached-user-policies \
  --user-name <project>-terraform
# Must show ONLY: <project>-terraform-scoped
```

---

## Day-2: Widening permissions (new service needed)

1. Edit `iam-self/policy.tf` — add the new actions/resources to the relevant statement
2. `../python-tui-lib/scripts/tf-safe-apply.sh infrastructure/aws/iam-self`
3. Continue with the infra change

**No console action required.** That's the whole point.

---

## Invariants (enforce throughout)

- Every AWS resource name must be prefixed `<project>-*` — the scoped policy's ARN patterns depend on this
- Every `providers.tf` block must include `default_tags` with **all three required tags**: `Project`, `ManagedBy`, `Environment` — missing any breaks Cost Explorer filtering and the CloudFront tag-condition guardrail
- Never inline `aws_iam_user_policy` — always use managed policies + attachments
- Never detach `<project>-terraform-scoped` without a broad policy attached (lockout risk)
- Keep `prevent_destroy = true` on the state bucket and lock table
- Activate `Project`, `ManagedBy`, `Environment` as cost allocation tags in AWS Billing (Phase A step 5) — without this, tags exist on resources but Cost Explorer can't filter by them
- Document the emergency escape hatch in `infrastructure/README.md`: root account can always re-attach `AdministratorAccess`
- Always use `../python-tui-lib/scripts/tf-safe-apply.sh <dir> [op]` instead of bare `terraform apply` — it handles lock diagnosis, stale DynamoDB digest auto-repair, and auto-init

## Services that need special handling

- **CloudFront**: can't be ARN-scoped in IAM — add `cloudfront:*` on `"*"` with a tag condition on resource-mutation actions. Add `"aws:ResourceTag/Project": "<project>"` condition to `UpdateDistribution`, `DeleteDistribution`, `TagResource`, `UntagResource`.
- **Account-level resources** (Route 53 hosted zones, SES identities, ACM certs): may need broader ARN scope or a separate shared-infra credentials config.
