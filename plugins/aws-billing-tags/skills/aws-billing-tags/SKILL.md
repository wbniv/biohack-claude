---
name: aws-billing-tags
description: Use this skill when setting up AWS cost tracking, billing tags, budget alerts, or Cost Explorer for a project. Trigger phrases: "set up billing", "add budget alert", "track AWS costs", "cost explorer", "tag compliance", "check untagged resources", "billing setup", "spending alert", "monthly cost report".
version: 1.0.0
---

# AWS Billing Tags & Cost Tracking

Wires up per-project cost visibility in AWS: tag schema, Cost Explorer activation, budget alerts as Terraform, and tag compliance verification.

## When to use

- Setting up cost tracking for a new project (run after or alongside `iam-bootstrap`)
- Adding a budget alert to an existing project
- Auditing which resources are missing required tags
- Setting up a Cost Explorer saved filter for a project

## What you need from the user (ask upfront)

1. **Project slug** — e.g. `gustos-colores`, `parking-space`
2. **Monthly budget limit** — in USD. If unsure, suggest starting with $50 for a small project.
3. **Alert email** — where to send budget breach notifications
4. **AWS profile** — e.g. `<project>-terraform`
5. **AWS account ID** — detect with `aws sts get-caller-identity` if unknown

---

## Tag schema

### Required on every resource (enforced via `default_tags`)

| Tag | Values | Purpose |
|-----|--------|---------|
| `Project` | `<project>` (slug) | Cross-project cost split in Cost Explorer |
| `ManagedBy` | `Terraform` or `Manual` | Audit trail; helps spot drift |
| `Environment` | `prod`, `staging`, `dev` | Per-env cost breakdown |

### Optional (add as the project grows)

| Tag | Example values | When to add |
|-----|---------------|-------------|
| `Feature` | `image-gen`, `waitlist`, `api` | When you want per-feature cost breakdown |
| `Owner` | `will` | Multi-person teams |

### Enforcement

Tags flow automatically to all resources via `default_tags` in every `providers.tf`. **Never** write a `provider "aws"` block without it:

```hcl
provider "aws" {
  # ...
  default_tags {
    tags = {
      Project     = "<project>"
      ManagedBy   = "Terraform"
      Environment = "<environment>"
    }
  }
}
```

`default_tags` doesn't reach resources created outside Terraform (manually, via CLI, via Lambda). Audit for those with the compliance check below.

---

## Step 1 — Activate cost allocation tags (manual, one-time per account)

Tags only appear in Cost Explorer after they're activated as cost allocation tags. This is a per-account setting, not per-resource.

→ https://us-east-1.console.aws.amazon.com/billing/home#/tags

Activate: `Project`, `ManagedBy`, `Environment`, plus any optional tags in use.

**Note:** tags only appear in this list after at least one resource has been tagged with them. If a tag isn't listed yet, create any tagged resource (Phase B of `iam-bootstrap` does this), then come back and activate.

Propagation takes up to 24 h. Cost Explorer data before activation is not retroactively tagged.

---

## Step 2 — Budget alert Terraform (`infrastructure/aws/global/budgets.tf`)

Add to the project's global Terraform module. Creates a hard monthly budget with an 80% forecast alert and a 100% actual alert.

```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "<project>-monthly"
  budget_type  = "COST"
  limit_amount = "<monthly_limit>"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["Project$<project>"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["<alert_email>"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["<alert_email>"]
  }
}
```

**IAM note:** `aws_budgets_budget` requires `budgets:*` permissions. Add to `iam-self/policy.tf` if not present:
```hcl
{
  Sid      = "Budgets"
  Effect   = "Allow"
  Action   = ["budgets:*"]
  Resource = "*"
}
```

Apply: `cd infrastructure/aws/global && terraform apply`

---

## Step 3 — Cost Explorer saved filter (manual, one-time)

AWS doesn't support creating Cost Explorer saved filters via Terraform or CLI — console only.

→ https://us-east-1.console.aws.amazon.com/cost-management/home#/cost-explorer

1. Set **Group by**: `Service`
2. Add filter: **Tag** → `Project` → `<project>`
3. Click **Save to report library** → name: `<project> — by service`

Repeat with **Group by**: `Tag: Environment` for a per-env breakdown.

---

## Step 4 — Tag compliance verification

Check for resources that exist but are missing required tags. Run periodically or in CI.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROFILE="<project>-terraform"
REQUIRED_TAGS="Project ManagedBy Environment"

echo "=== Untagged resources in account ==="
for tag in $REQUIRED_TAGS; do
  echo "--- Missing tag: $tag ---"
  aws resourcegroupstaggingapi get-resources \
    --profile "$PROFILE" \
    --tag-filters "Key=$tag" \
    --query 'ResourceTagMappingList[].ResourceARN' \
    --output text | wc -l | xargs echo "  resources WITH $tag:"

  # Resources missing the tag (inverse: all resources minus tagged)
  aws resourcegroupstaggingapi get-resources \
    --profile "$PROFILE" \
    --query 'ResourceTagMappingList[?!Tags[?Key==`'"$tag"'`]].ResourceARN' \
    --output text
done
```

Or use the simpler targeted check:
```bash
# List all resources missing the Project tag
aws resourcegroupstaggingapi get-resources \
  --profile "<project>-terraform" \
  --resource-type-filters ec2:instance rds:db s3:bucket \
  --query 'ResourceTagMappingList[?!Tags[?Key==`Project`]].[ResourceARN]' \
  --output table
```

Resources that consistently escape `default_tags` (Lambda event sources, some RDS parameter groups, CloudWatch log groups) should be tagged explicitly in their Terraform resource blocks:
```hcl
resource "aws_cloudwatch_log_group" "app" {
  name = "/aws/<project>/app"
  tags = {
    Feature = "app-logs"  # Project/ManagedBy/Environment come from default_tags
  }
}
```

---

## Day-2: Adding a per-feature cost breakdown

When a major feature ships and you want to see its AWS cost separately:

1. Add `Feature = "<feature-name>"` to the relevant resources in Terraform (alongside `default_tags`, not instead of them)
2. Activate `Feature` as a cost allocation tag in AWS Billing (same console step as above)
3. Add a Cost Explorer filter for `Tag: Feature = <feature-name>`

---

## Invariants

- Never create a `provider "aws"` block without `default_tags` containing all three required tags
- Activate cost allocation tags immediately after the first tagged resource is created — don't wait until "later"
- Budget alerts are Terraform — never create them manually in the console
- Tag compliance check belongs in CI or as a periodic task once the project has real spend
