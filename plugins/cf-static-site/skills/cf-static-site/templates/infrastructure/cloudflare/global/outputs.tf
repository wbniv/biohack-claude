output "zone_id" {
  description = "Cloudflare zone ID for <DOMAIN>. Mirror this into iam-self/token.tf's zone_id default after the first apply."
  value       = cloudflare_zone.main.id
}

output "name_servers" {
  description = "Cloudflare nameservers — point the domain registrar at these on first activation."
  value       = cloudflare_zone.main.name_servers
}

output "apex_url" {
  description = "Canonical site URL."
  value       = "https://${var.domain}/"
}

output "www_url" {
  description = "www host — 301s to apex."
  value       = "https://www.${var.domain}/"
}
