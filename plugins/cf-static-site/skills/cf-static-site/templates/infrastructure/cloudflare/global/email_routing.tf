# Cloudflare Email Routing for <DOMAIN>.
#
# Four resources cover the full setup:
#
#   1. settings — flip Email Routing on for the zone.
#   2. dns      — auto-create the MX (route1/2/3.mx.cloudflare.net) and
#                 SPF TXT records. Cloudflare picks priorities.
#   3. address  — register the destination as a verified address. One
#                 manual step on first apply: Cloudflare emails a
#                 verification link to that inbox — click it. The
#                 destination won't receive forwarded mail until verified.
#   4. rule     — forward hello@<DOMAIN> → the destination.
#
# The address resource is account-scoped; the others are zone-scoped.

resource "cloudflare_email_routing_settings" "main" {
  zone_id = cloudflare_zone.main.id
}

resource "cloudflare_email_routing_dns" "main" {
  zone_id = cloudflare_zone.main.id
  # `name` is for routing on a SUBDOMAIN. For the zone apex, omit it —
  # Cloudflare auto-derives it.

  depends_on = [cloudflare_email_routing_settings.main]
}

resource "cloudflare_email_routing_address" "destination" {
  account_id = var.account_id
  email      = var.email_destination
}

resource "cloudflare_email_routing_rule" "hello" {
  zone_id  = cloudflare_zone.main.id
  name     = "Forward hello@ to ${var.email_destination}"
  enabled  = true
  priority = 0

  matchers = [{
    type  = "literal"
    field = "to"
    value = "hello@${var.domain}"
  }]

  actions = [{
    type  = "forward"
    value = [var.email_destination]
  }]

  depends_on = [
    cloudflare_email_routing_settings.main,
    cloudflare_email_routing_address.destination,
  ]
}
