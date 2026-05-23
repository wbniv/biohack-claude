variable "project" {
  description = "Project slug. Used in tags and SSM paths."
  type        = string
  default     = "<SLUG>"
}

variable "domain" {
  description = "Apex domain (canonical host). www gets redirected here."
  type        = string
  default     = "<DOMAIN>"
}

variable "account_id" {
  description = "Cloudflare account ID hosting the <DOMAIN> zone. Source-of-truth value lives in SSM at /<SLUG>/cloudflare/account_id; mirrored here for TF clarity."
  type        = string
  # TODO: set the actual account ID before first apply (or pass via
  # TF_VAR_account_id, which `task tf-apply` does from .env).
  default = ""
}

variable "worker_name" {
  description = "Wrangler Worker name (matches `name` in wrangler.toml)."
  type        = string
  default     = "<SLUG>"
}

variable "email_destination" {
  description = "Verified destination address for Email Routing forwards."
  type        = string
  default     = "<EMAIL_DEST>"
}
