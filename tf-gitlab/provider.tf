terraform {
  required_providers {
    gitlab = {
      source = "gitlabhq/gitlab"
    }
  }
}

variable "admin_token" {
  description = "Owner/Maintainer PAT token with the api scope applied."
  type = string
}

variable "base_url" {
  description = "the base url of the gitlab instance"
  type = string
}

provider "gitlab" {
  token = var.admin_token
  base_url = var.base_url
}
