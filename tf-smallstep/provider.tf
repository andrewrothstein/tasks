provider "smallstep" {
  client_certificate = {
    certificate = file("~/nj.crt")
    private_key = file("~/nj.key")
    team_id = "drewfus"
  }
}
