# Provider block for the global config. Cloudflare for the actual
# resources; the AWS S3 state backend is declared separately in
# backend.tf.
#
# CLOUDFLARE_API_TOKEN reads from the environment by default — `task
# secrets-pull` writes it into the local .env from SSM at
# /<SLUG>/cloudflare/api_token. CI reads it from the GitHub Actions
# secret of the same name.

terraform {
  required_version = ">= 1.5"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

provider "cloudflare" {
  # api_token sourced from CLOUDFLARE_API_TOKEN env var.
}
