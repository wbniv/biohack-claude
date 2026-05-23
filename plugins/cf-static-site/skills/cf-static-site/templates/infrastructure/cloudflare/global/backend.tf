terraform {
  backend "s3" {
    bucket         = "<SLUG>-terraform-state"
    key            = "global/terraform.tfstate"
    region         = "<REGION>"
    dynamodb_table = "<SLUG>-terraform-locks"
    encrypt        = true
    profile        = "<SLUG>-terraform"
  }
}
