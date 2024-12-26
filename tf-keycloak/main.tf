resource "keycloak_realm" "realm" {
  realm   = "my-realm"
  enabled = true
}

resource "keycloak_oidc_identity_provider" "realm_identity_provider" {
  realm             = keycloak_realm.realm.id
  alias             = "elephant-frog-idp"
  authorization_url = "https://airflow-ui.elephant-frog.ts.net"
  client_id         = "clientID"
  client_secret     = "clientSecret"
  token_url         = "https://tokenurl.com"

  extra_config = {
    "clientAuthMethod" = "client_secret_post"
  }
}
