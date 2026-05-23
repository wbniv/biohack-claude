# Provider block for the iam-self config. Run with a short-lived
# bootstrap token (Account API Tokens: Edit + User API Tokens: Edit) so
# Terraform can mint/rotate the narrow project token. The AWS S3 state
# backend is declared separately in backend.tf.

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
