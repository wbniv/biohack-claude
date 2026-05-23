terraform {
  backend "s3" {
    bucket         = "<SLUG>-terraform-state"
    key            = "iam-self/terraform.tfstate"
    region         = "<REGION>"
    dynamodb_table = "<SLUG>-terraform-locks"
    encrypt        = true
    profile        = "<SLUG>-terraform"
  }
}
