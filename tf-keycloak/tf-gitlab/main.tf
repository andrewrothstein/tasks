resource "gitlab_group" "devops" {
  name              = "devops"
  path              = "devops"
  description       = "The DevOps Team"
  wiki_access_level = "private"
}

resource "gitlab_user" "arothste" {
  email            = "andrew.rothstein@gmail.com"
  name             = "Andrew Rothstein"
  username         = "arothste"
  namespace_id     = 42
  is_admin         = true
  can_create_group = true
  reset_password   = true
}

resource "gitlab_group_membership" "devops_team_lead" {
  group_id     = gitlab_group.devops.id
  access_level = "maintainer"
  user_id      = gitlab_user.arothste.id
}
