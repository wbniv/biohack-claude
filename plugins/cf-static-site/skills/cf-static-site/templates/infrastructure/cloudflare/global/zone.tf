# The Cloudflare zone for <DOMAIN>.
#
# Resource-managed (cloudflare_zone): TF creates and owns the zone, with
# `lifecycle.prevent_destroy = true` so an accidental `terraform destroy`
# can't wipe it. If the zone is registered through Cloudflare Registrar
# (or was created via the dashboard), switch to a data source with a
# `terraform import` instead.

resource "cloudflare_zone" "main" {
  account = {
    id = var.account_id
  }
  name = var.domain
  type = "full"

  lifecycle {
    prevent_destroy = true
  }
}

# Always-Use-HTTPS — every http:// request 301s to https://. Survives any
# manual UI toggle because TF reverts drift on the next apply.
resource "cloudflare_zone_setting" "always_use_https" {
  zone_id    = cloudflare_zone.main.id
  setting_id = "always_use_https"
  value      = "on"
}

# Belt-and-braces: also turn on Automatic HTTPS Rewrites, so any http://
# subresources in HTML get rewritten to https:// at the edge.
resource "cloudflare_zone_setting" "automatic_https_rewrites" {
  zone_id    = cloudflare_zone.main.id
  setting_id = "automatic_https_rewrites"
  value      = "on"
}
