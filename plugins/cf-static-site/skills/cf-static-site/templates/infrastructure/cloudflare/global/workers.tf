# Bind the <SLUG> Worker to both <DOMAIN> (canonical apex) and
# www.<DOMAIN> (which worker/index.ts 301-redirects to apex).
#
# `cloudflare_workers_custom_domain` is the modern primitive — it
# auto-creates the DNS record and the TLS cert binding in one resource.
# Wrangler must NOT also declare a [[routes]] block in wrangler.toml (it
# doesn't) so there's no fight over ownership.

resource "cloudflare_workers_custom_domain" "apex" {
  account_id = var.account_id
  zone_id    = cloudflare_zone.main.id
  hostname   = var.domain
  service    = var.worker_name
}

resource "cloudflare_workers_custom_domain" "www" {
  account_id = var.account_id
  zone_id    = cloudflare_zone.main.id
  hostname   = "www.${var.domain}"
  service    = var.worker_name
}
