terraform {
  backend "s3" {}
  required_providers {
    azuread = {
      version = "~> 2"
    }
  }
}
