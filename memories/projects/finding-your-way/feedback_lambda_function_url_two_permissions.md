---
name: Lambda Function URL needs TWO permissions when deployed via Terraform
description: AuthType=NONE Lambda Function URLs need both lambda:InvokeFunctionUrl and lambda:InvokeFunction (with invoked_via_function_url=true) — Terraform doesn't add the second one automatically
type: feedback
originSessionId: 657be929-b48d-4bf9-9dec-2e15a61faf6e
---
When provisioning a public Lambda Function URL (`AuthType=NONE`) via Terraform, two `aws_lambda_permission` resources are required, not one:

1. `action = "lambda:InvokeFunctionUrl"`, `principal = "*"`, `function_url_auth_type = "NONE"`
2. `action = "lambda:InvokeFunction"`, `principal = "*"`, `invoked_via_function_url = true`

Missing #2 returns **HTTP 403 "Forbidden"** with `x-amzn-ErrorType: AccessDeniedException` and a body pointing at `https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html` — with no hint that a second permission is needed. The resource policy appears correct, `simulate-principal-policy` can even say "allowed" for the first action. `OPTIONS` preflight returns 200 (because CORS is handled before auth), so the symptom looks like "every non-preflight request is blocked."

`invoked_via_function_url = true` requires the AWS Terraform provider **v6.x or later**. On v5.x the argument isn't recognized and `terraform plan` fails with `An argument named "invoked_via_function_url" is not expected here.` — bump the provider constraint to `~> 6.0`.

**Why:** The October 2025 Function URL auth-model change split the grant into two. AWS's Console auto-adds both permissions silently; Terraform doesn't. The error message is deeply misleading — I've burned hours of diagnostics on this (testing SCPs, trying every region, filing AWS support cases, pivoting to API Gateway) before finding the pattern documented in another project's `lambda.tf`. Don't diagnose — check for the second permission first.

**How to apply:**
- Any time a Terraform-managed Lambda Function URL returns 403 "Forbidden" with `AccessDeniedException`, this is almost certainly the cause. Check for the `invoked_via_function_url = true` permission before anything else.
- When scaffolding a new Function URL in Terraform, always add both permissions up-front. Reference gustos-colores `deploy/terraform/lambda.tf` for the canonical pattern.
- If the provider is on `~> 5.0`, bump to `~> 6.0` before trying to set `invoked_via_function_url`.
