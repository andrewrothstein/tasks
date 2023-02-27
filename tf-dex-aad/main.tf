resource "azuread_application" "dex-dev" {
  display_name = "dex-dev"

}

resource "time_rotating" "dex-dev-pwd-ttl" {
  rotation_days = 90
}

resource "azuread_application_password" "dex-dev-pwd" {
  display_name = "dex-dev-pwd"
  application_object_id = azuread_application.dex-dev.object_id
  rotate_when_changed = {
    rotation = time_rotating.dex-dev-pwd-ttl.id
  }
}
