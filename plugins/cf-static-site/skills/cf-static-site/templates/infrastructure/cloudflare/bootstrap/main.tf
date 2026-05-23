# Bootstrap: create the S3 bucket + DynamoDB table that hold Terraform
# remote state for the global/ and iam-self/ configs.
#
# Even though <DOMAIN>'s actual resources live on Cloudflare, the
# TF *state* sits on AWS S3 — one state bucket per project.
#
# Chicken-and-egg: this dir uses LOCAL state because the backend it
# creates can't yet exist. The local terraform.tfstate file is
# .gitignored.
#
# Usage (one-time, from repo root):
#   cd infrastructure/cloudflare/bootstrap
#   terraform init
#   terraform apply

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = "<REGION>"
  profile = "<SLUG>-terraform"
}

variable "project" {
  type    = string
  default = "<SLUG>"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project}-terraform-state"

  tags = {
    Project = var.project
    Purpose = "Terraform remote state"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.project}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Project = var.project
    Purpose = "Terraform state locking"
  }

  lifecycle {
    prevent_destroy = true
  }
}

output "state_bucket" {
  value = aws_s3_bucket.terraform_state.id
}

output "lock_table" {
  value = aws_dynamodb_table.terraform_locks.name
}
