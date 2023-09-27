terraform {
#  backend "s3" {}
  required_providers {
    smallstep = {
      source = "smallstep/smallstep"
      version = "~> 0.3"
    }
  }
}
