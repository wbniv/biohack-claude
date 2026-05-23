# <SLUG>-cf-token: the project-scoped Cloudflare API token used by both
# the global/ Terraform config and the CI deploy workflow.
#
# Scope covers everything global/ manages and nothing else:
#
#   Zone (<DOMAIN>):
#     - Zone Write           — cloudflare_zone refresh + future changes
#     - Zone Settings Write  — always_use_https, automatic_https_rewrites
#     - DNS Write            — email_routing_dns auto-MX/SPF records
#     - Workers Routes Write — workers_custom_domain bindings (apex + www)
#     - Email Routing Rules Write — email_routing_settings + _rule
#
#   Account:
#     - Workers Scripts Write         — wrangler deploy of the <SLUG> Worker
#     - Email Routing Addresses Write — destination address registration
#
# Still meaningfully narrower than a full account-admin token: cannot
# list other zones, cannot mint/revoke other tokens, no R2/D1/Pages
# access. If a future workflow needs more, add it here explicitly —
# never broaden to account-wide.

variable "project" {
  description = "Project slug — used in token name."
  type        = string
  default     = "<SLUG>"
}

variable "account_id" {
  description = "Cloudflare account ID — sourced from SSM /<SLUG>/cloudflare/account_id."
  type        = string
  # TODO: set the actual account ID before first apply (or pass via
  # TF_VAR_account_id, which `task tf-apply-iam` does from .env).
  default = ""
}

variable "zone_id" {
  description = "<DOMAIN> zone ID. Stable Cloudflare-managed value; mirror it from `terraform -chdir=../global output -raw zone_id` after the global zone is created."
  type        = string
  # TODO: set after the global/ zone exists.
  default = ""
}

# Permission group IDs are CF-managed UUIDs and stable across accounts.
# Hardcoded rather than looked up via data source because the data
# source returns the full catalogue (~500 entries) with duplicate
# display names across different scopes, which breaks any name→id map.
locals {
  permission_groups = {
    # Zone scope
    dns_write                 = "4755a26eedb94da69e1066d98aa820be"
    workers_routes_write      = "28f4b596e7d643029c524985477ae49a"
    zone_write                = "e6d2666161e84845a636613608cee8d5"
    zone_settings_write       = "3030687196b94b638145a3953da2b699"
    email_routing_rules_write = "79b3ec0d10ce4148a8f8bdc0cc5f97f2"
    # Account scope
    workers_scripts_write         = "e086da7e2179491d91ee5f35b3ca210a"
    email_routing_addresses_write = "e4589eb09e63436686cd64252a3aebeb"
  }
}

resource "cloudflare_account_token" "wf_org_cf_token" {
  account_id = var.account_id
  name       = "<SLUG>-cf-token"

  # Policy ordering note: the Cloudflare API returns policies in its own
  # order, which is not the order they're declared here. The TF provider
  # matches policies by index, so config order must match what the API
  # returns or `apply` hits "provider produced inconsistent result after
  # apply". Empirically the API returns the account-scoped policy first,
  # then the zone-scoped policy.
  policies = [
    {
      effect = "allow"
      resources = jsonencode({
        "com.cloudflare.api.account.${var.account_id}" = "*"
      })
      permission_groups = [
        { id = local.permission_groups.workers_scripts_write },
        { id = local.permission_groups.email_routing_addresses_write },
      ]
    },
    {
      effect = "allow"
      resources = jsonencode({
        "com.cloudflare.api.account.zone.${var.zone_id}" = "*"
      })
      # permission_groups are matched by list index (not set equality) by
      # the CF TF provider — order must match what the API returns or the
      # apply hits "inconsistent result". The API sorts by UUID, so list
      # these in UUID ascending order:
      #   28f4b... workers_routes_write
      #   30306... zone_settings_write
      #   47552... dns_write
      #   79b3e... email_routing_rules_write
      #   e6d26... zone_write
      permission_groups = [
        { id = local.permission_groups.workers_routes_write },
        { id = local.permission_groups.zone_settings_write },
        { id = local.permission_groups.dns_write },
        { id = local.permission_groups.email_routing_rules_write },
        { id = local.permission_groups.zone_write },
      ]
    },
  ]
}

output "token_value" {
  description = "Newly minted (or updated) token value. Push this to SSM at /<SLUG>/cloudflare/api_token and the GitHub Actions CLOUDFLARE_API_TOKEN secret, then revoke any prior bootstrap token."
  value       = cloudflare_account_token.wf_org_cf_token.value
  sensitive   = true
}
